"""ClearWayAI Pre-Clearance Coordination Algorithm (`controller.scheduler`).

Implements the Just-in-Time (JIT) pre-clearance algorithm:
$$\\Delta t_{\\text{trigger}} = \\text{ETA}_{\\text{EV}} - \\hat{T}_{\\text{clear}} - T_{\\text{transition}} - T_{\\text{buffer}}$$

Coordinates traffic signals along the arterial corridor ahead of approaching
emergency vehicles by scheduling phase transitions so the conflicting queue
discharges completely just as the emergency vehicle arrives at the stopline.

Key capabilities:
1. Deterministic Pre-Clearance State Machine:
   MONITORING -> ARMED -> TRANSITIONING -> HOLDING_GREEN -> EV_PASSING -> CLEARED -> RECOVERING.
2. Dynamic ETA & Queue Clearance Coupling:
   Connects MultiNodeETAEvaluator (kinematic trajectory) with UnifiedClearancePredictor
   (ML/heuristic queue discharge shockwave).
3. Zero-Delay Arrival with Minimal Cross-Street Disruption:
   Prevents premature green holding by actuating only when $\\Delta t_{\\text{trigger}} \\le 0$.
4. Safety Boundaries & Watchdog Guards:
   Enforces NEMA minimum green (10s), deterministic yellow (3s) and all-red (2s),
   and fail-safe anti-starvation maximum green hold watchdog (60s).
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

from ai.clearance.model_registry import (
    ClearanceModelRegistry,
    ClearancePredictionResult,
    UnifiedClearancePredictor,
)
from ai.state.traffic_state_estimator import ApproachTrafficState
from controller.mission.emergency_mission import (
    CORRIDOR_ENTRY_X_METERS,
    EmergencyMission,
)
from controller.mission.eta_estimator import (
    CORRIDOR_NODE_STOPLINES,
    MultiNodeETAEvaluator,
)


class PreclearanceState(StrEnum):
    """Operational states of the intersection pre-clearance coordinator."""

    MONITORING = "MONITORING"
    ARMED = "ARMED"
    TRANSITIONING = "TRANSITIONING"
    HOLDING_GREEN = "HOLDING_GREEN"
    EV_PASSING = "EV_PASSING"
    CLEARED = "CLEARED"
    RECOVERING = "RECOVERING"


@dataclass
class PreclearanceConfig:
    """Configuration parameters for pre-clearance timing and safety guards."""

    yellow_duration_sec: float = 3.0
    all_red_duration_sec: float = 2.0
    safety_buffer_sec: float = 2.0
    min_green_duration_sec: float = 10.0
    max_green_hold_sec: float = 60.0
    passing_zone_distance_m: float = 50.0
    exit_clearance_distance_m: float = 15.0
    nominal_cycle_time_sec: float = 72.0
    horizon_detection_distance_m: float = 1500.0

    # NEMA Standard Phase Mapping
    arterial_phase_green: int = 0
    arterial_phase_yellow: int = 1
    arterial_phase_all_red: int = 2
    cross_phase_green: int = 3
    cross_phase_yellow: int = 4
    cross_phase_all_red: int = 5

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PreclearanceDecision:
    """Pre-clearance decision output for a specific intersection node."""

    node_id: str
    state: PreclearanceState
    should_actuate: bool
    commanded_phase: int
    delta_trigger_sec: float
    ev_eta_sec: float
    predicted_clearance_sec: float
    transition_time_sec: float
    safety_buffer_sec: float
    active_green_hold_sec: float
    reason: str
    provenance: str = "CLEARWAY_JIT_PRE_CLEARANCE"
    timestamp_sec: float = field(default_factory=time.time)
    is_emergency_priority: bool = False
    fallback_used: bool = False
    confidence_score: float = 1.00

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["state"] = str(self.state)
        return d


@dataclass
class CorridorPreclearancePlan:
    """Consolidated corridor-wide coordination plan covering all intersections."""

    mission_id: str | None
    vehicle_id: str | None
    current_position_m: float
    current_speed_kmh: float
    decisions: dict[str, PreclearanceDecision]
    commanded_phases: dict[str, int]
    active_preemptions_count: int
    timestamp_sec: float
    provenance: str = "CLEARWAY_CORRIDOR_PRE_CLEARANCE"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["decisions"] = {k: v.to_dict() for k, v in self.decisions.items()}
        return d


class PreclearanceController:
    """Moving-horizon Just-In-Time (JIT) pre-clearance coordinator for arterial intersections."""

    def __init__(
        self,
        config: PreclearanceConfig | None = None,
        eta_evaluator: MultiNodeETAEvaluator | None = None,
        clearance_predictor: UnifiedClearancePredictor | None = None,
        intersections: list[str] | None = None,
    ) -> None:
        self.config = config or PreclearanceConfig()
        self.eta_evaluator = eta_evaluator or MultiNodeETAEvaluator()

        if clearance_predictor is not None:
            self.clearance_predictor = clearance_predictor
        else:
            registry = ClearanceModelRegistry()
            self.clearance_predictor = UnifiedClearancePredictor(registry=registry)

        self.intersections = intersections or ["node_a", "node_b", "node_c", "node_d"]
        self.stoplines: dict[str, float] = {
            nid: CORRIDOR_NODE_STOPLINES.get(nid, 0.0) for nid in self.intersections
        }

        # Internal tracking per intersection node
        self._node_states: dict[str, PreclearanceState] = dict.fromkeys(
            self.intersections, PreclearanceState.MONITORING
        )
        self._current_phase: dict[str, int] = dict.fromkeys(
            self.intersections, self.config.arterial_phase_green
        )
        self._phase_start_time: dict[str, float] = dict.fromkeys(self.intersections, 0.0)
        self._transition_start_time: dict[str, float | None] = dict.fromkeys(self.intersections)
        self._green_hold_start_time: dict[str, float | None] = dict.fromkeys(self.intersections)
        self._cleared_timestamp: dict[str, float | None] = dict.fromkeys(self.intersections)
        self._watchdog_tripped: dict[str, bool] = dict.fromkeys(self.intersections, False)

    def reset(self) -> None:
        """Reset all internal controller tracking states to initial baseline."""
        for nid in self.intersections:
            self._node_states[nid] = PreclearanceState.MONITORING
            self._current_phase[nid] = self.config.arterial_phase_green
            self._phase_start_time[nid] = 0.0
            self._transition_start_time[nid] = None
            self._green_hold_start_time[nid] = None
            self._cleared_timestamp[nid] = None
            self._watchdog_tripped[nid] = False

    def get_nominal_phase(self, sim_time: float) -> int:
        """Standard Webster cycle phase timing for 72s NEMA cycle.

        Phases:
        - [0.0, 35.0): Arterial EB/WB Green (Phase 0)
        - [35.0, 39.0): Arterial Yellow (Phase 1)
        - [39.0, 41.0): Arterial All-Red (Phase 2)
        - [41.0, 66.0): Cross Street NB/SB Green (Phase 3)
        - [66.0, 70.0): Cross Street Yellow (Phase 4)
        - [70.0, 72.0): Cross Street All-Red (Phase 5)
        """
        cycle_pos = sim_time % self.config.nominal_cycle_time_sec
        if cycle_pos < 35.0:
            return self.config.arterial_phase_green
        elif cycle_pos < 39.0:
            return self.config.arterial_phase_yellow
        elif cycle_pos < 41.0:
            return self.config.arterial_phase_all_red
        elif cycle_pos < 66.0:
            return self.config.cross_phase_green
        elif cycle_pos < 70.0:
            return self.config.cross_phase_yellow
        else:
            return self.config.cross_phase_all_red

    def compute_transition_overhead(
        self,
        current_phase: int,
        phase_elapsed_sec: float = 0.0,
    ) -> float:
        """Compute mandatory safety clearance time needed to switch to Arterial Green.

        Guarantees non-zero deterministic intervals:
        - If already Arterial Green (Phase 0): 0.0s transition required.
        - If Arterial Yellow (Phase 1): remaining yellow + all-red.
        - If Arterial All-Red (Phase 2): remaining all-red.
        - If Cross Green (Phase 3): remaining min green + full yellow (3s) + full all-red (2s).
        - If Cross Yellow (Phase 4): remaining yellow + full all-red (2s).
        - If Cross All-Red (Phase 5): remaining all-red (2s).
        """
        cfg = self.config
        if current_phase == cfg.arterial_phase_green:
            return 0.0

        if current_phase == cfg.arterial_phase_yellow:
            rem_yellow = max(0.0, cfg.yellow_duration_sec - phase_elapsed_sec)
            return rem_yellow + cfg.all_red_duration_sec

        if current_phase == cfg.arterial_phase_all_red:
            return max(0.0, cfg.all_red_duration_sec - phase_elapsed_sec)

        if current_phase == cfg.cross_phase_green:
            rem_min_green = max(0.0, cfg.min_green_duration_sec - phase_elapsed_sec)
            return rem_min_green + cfg.yellow_duration_sec + cfg.all_red_duration_sec

        if current_phase == cfg.cross_phase_yellow:
            rem_yellow = max(0.0, cfg.yellow_duration_sec - phase_elapsed_sec)
            return rem_yellow + cfg.all_red_duration_sec

        if current_phase == cfg.cross_phase_all_red:
            return max(0.0, cfg.all_red_duration_sec - phase_elapsed_sec)

        # Conservative fallback
        return cfg.yellow_duration_sec + cfg.all_red_duration_sec

    @staticmethod
    def compute_trigger_delta(
        ev_eta_sec: float,
        predicted_clearance_sec: float,
        transition_time_sec: float,
        safety_buffer_sec: float = 2.0,
    ) -> float:
        """Calculate the Pre-clearance trigger time difference.

        $$\\Delta t_{\\text{trigger}} = \\text{ETA}_{\\text{EV}} - \\hat{T}_{\\text{clear}} - T_{\\text{transition}} - T_{\\text{buffer}}$$

        Interpretation:
        - $\\Delta t > 0$: Arrival is comfortably in the future; do not disrupt normal traffic.
        - $\\Delta t \\le 0$: Transition must begin immediately to guarantee queue is completely
                           flushed when the emergency vehicle reaches the stopline.
        """
        return ev_eta_sec - predicted_clearance_sec - transition_time_sec - safety_buffer_sec

    def evaluate_node(
        self,
        node_id: str,
        mission: EmergencyMission | None,
        approach_state: ApproachTrafficState | None,
        sim_time: float,
        current_signal_phase: int | None = None,
        phase_elapsed_sec: float | None = None,
        weather: str = "clear",
    ) -> PreclearanceDecision:
        """Evaluate pre-clearance state and command phase for a specific node."""
        cfg = self.config
        stopline_x = self.stoplines.get(node_id, 0.0)

        # 1. Determine active baseline phase & elapsed time
        if current_signal_phase is None:
            active_phase = self._current_phase.get(node_id, self.get_nominal_phase(sim_time))
        else:
            active_phase = current_signal_phase

        if phase_elapsed_sec is None:
            active_elapsed = max(0.0, sim_time - self._phase_start_time.get(node_id, 0.0))
        else:
            active_elapsed = phase_elapsed_sec

        current_state = self._node_states.get(node_id, PreclearanceState.MONITORING)

        # 2. Case: Mission not active or no mission
        if mission is None or not mission.is_active:
            self._node_states[node_id] = PreclearanceState.MONITORING
            self._transition_start_time[node_id] = None
            self._green_hold_start_time[node_id] = None
            nominal = self.get_nominal_phase(sim_time)
            return PreclearanceDecision(
                node_id=node_id,
                state=PreclearanceState.MONITORING,
                should_actuate=False,
                commanded_phase=nominal,
                delta_trigger_sec=999.0,
                ev_eta_sec=999.0,
                predicted_clearance_sec=0.0,
                transition_time_sec=0.0,
                safety_buffer_sec=cfg.safety_buffer_sec,
                active_green_hold_sec=0.0,
                reason="No active priority mission in corridor.",
                timestamp_sec=sim_time,
                is_emergency_priority=False,
            )

        # 3. Kinematic ETA evaluation for this node
        eta_sec, dist_rem, has_passed, eta_conf = self.eta_evaluator.compute_single_node_eta(
            current_x_m=mission.current_position_m,
            current_v_mps=mission.current_speed_mps,
            target_v_mps=mission.target_speed_mps,
            max_v_mps=mission.max_speed_mps,
            stopline_x_m=stopline_x,
            traffic_occupancy=(approach_state.approach_occupancy_ratio if approach_state else 0.20),
            weather=weather,
        )

        ev_pos = mission.current_position_m

        # 4. Check if EV has already cleared this intersection
        if has_passed or ev_pos > (stopline_x + cfg.exit_clearance_distance_m):
            if current_state in (
                PreclearanceState.HOLDING_GREEN,
                PreclearanceState.EV_PASSING,
                PreclearanceState.TRANSITIONING,
            ):
                self._node_states[node_id] = PreclearanceState.CLEARED
                self._cleared_timestamp[node_id] = sim_time
                self._green_hold_start_time[node_id] = None
                self._transition_start_time[node_id] = None

            # Handoff to recovery / nominal
            nominal = self.get_nominal_phase(sim_time)
            return PreclearanceDecision(
                node_id=node_id,
                state=self._node_states[node_id],
                should_actuate=False,
                commanded_phase=nominal,
                delta_trigger_sec=0.0,
                ev_eta_sec=0.0,
                predicted_clearance_sec=0.0,
                transition_time_sec=0.0,
                safety_buffer_sec=cfg.safety_buffer_sec,
                active_green_hold_sec=0.0,
                reason=f"Emergency vehicle has cleared node ({ev_pos:.1f}m > stopline {stopline_x:.1f}m + {cfg.exit_clearance_distance_m:.1f}m).",
                timestamp_sec=sim_time,
                is_emergency_priority=False,
                confidence_score=1.00,
            )

        # 5. Clearance Time Prediction
        pred_res: ClearancePredictionResult = self.clearance_predictor.predict(
            states=approach_state,
            node_id=node_id,
            weather=weather,
        )
        t_clear = pred_res.predicted_clearance_sec
        t_trans = self.compute_transition_overhead(active_phase, active_elapsed)
        delta_trigger = self.compute_trigger_delta(eta_sec, t_clear, t_trans, cfg.safety_buffer_sec)

        # 6. Check Anti-Starvation Watchdog
        hold_start = self._green_hold_start_time.get(node_id)
        active_hold_duration = (sim_time - hold_start) if hold_start is not None else 0.0

        if active_hold_duration >= cfg.max_green_hold_sec:
            # Watchdog timeout: abort green hold to prevent cross-street gridlock
            self._node_states[node_id] = PreclearanceState.MONITORING
            self._watchdog_tripped[node_id] = True
            nominal = self.get_nominal_phase(sim_time)
            return PreclearanceDecision(
                node_id=node_id,
                state=PreclearanceState.MONITORING,
                should_actuate=False,
                commanded_phase=nominal,
                delta_trigger_sec=delta_trigger,
                ev_eta_sec=eta_sec,
                predicted_clearance_sec=t_clear,
                transition_time_sec=t_trans,
                safety_buffer_sec=cfg.safety_buffer_sec,
                active_green_hold_sec=active_hold_duration,
                reason=f"Safety Watchdog Tripped: Max green hold ({cfg.max_green_hold_sec}s) exceeded.",
                timestamp_sec=sim_time,
                is_emergency_priority=False,
                fallback_used=True,
                confidence_score=0.50,
            )

        # 7. Check if EV is in passing zone (within passing_zone_distance_m of stopline)
        if 0.0 <= dist_rem <= cfg.passing_zone_distance_m:
            self._node_states[node_id] = PreclearanceState.EV_PASSING
            if self._green_hold_start_time.get(node_id) is None:
                self._green_hold_start_time[node_id] = sim_time

            return PreclearanceDecision(
                node_id=node_id,
                state=PreclearanceState.EV_PASSING,
                should_actuate=True,
                commanded_phase=cfg.arterial_phase_green,
                delta_trigger_sec=delta_trigger,
                ev_eta_sec=eta_sec,
                predicted_clearance_sec=t_clear,
                transition_time_sec=0.0,
                safety_buffer_sec=cfg.safety_buffer_sec,
                active_green_hold_sec=(
                    sim_time - self._green_hold_start_time[node_id]  # type: ignore[operator]
                ),
                reason=f"Emergency vehicle in passing zone ({dist_rem:.1f}m <= {cfg.passing_zone_distance_m}m). Locking Arterial Green.",
                timestamp_sec=sim_time,
                is_emergency_priority=True,
                fallback_used=pred_res.fallback_used,
                confidence_score=min(eta_conf, pred_res.confidence_score),
            )

        # 8. State Machine Progression
        # Case A: If already HOLDING_GREEN
        if current_state == PreclearanceState.HOLDING_GREEN:
            return PreclearanceDecision(
                node_id=node_id,
                state=PreclearanceState.HOLDING_GREEN,
                should_actuate=True,
                commanded_phase=cfg.arterial_phase_green,
                delta_trigger_sec=delta_trigger,
                ev_eta_sec=eta_sec,
                predicted_clearance_sec=t_clear,
                transition_time_sec=0.0,
                safety_buffer_sec=cfg.safety_buffer_sec,
                active_green_hold_sec=active_hold_duration,
                reason=f"Holding Arterial Green for approaching EV (ETA: {eta_sec:.1f}s, queue clearing).",
                timestamp_sec=sim_time,
                is_emergency_priority=True,
                fallback_used=pred_res.fallback_used,
                confidence_score=min(eta_conf, pred_res.confidence_score),
            )

        # Case B: If TRANSITIONING
        if current_state == PreclearanceState.TRANSITIONING:
            t_trans_start = self._transition_start_time.get(node_id) or sim_time
            trans_elapsed = sim_time - t_trans_start

            if active_phase == cfg.cross_phase_green:
                # Truncate Cross Green: switch to Cross Yellow
                commanded = cfg.cross_phase_yellow
                self._current_phase[node_id] = commanded
                self._phase_start_time[node_id] = sim_time
            elif active_phase == cfg.cross_phase_yellow:
                if trans_elapsed >= cfg.yellow_duration_sec:
                    # Switch to Cross All-Red
                    commanded = cfg.cross_phase_all_red
                    self._current_phase[node_id] = commanded
                    self._phase_start_time[node_id] = sim_time
                else:
                    commanded = cfg.cross_phase_yellow
            elif active_phase == cfg.cross_phase_all_red:
                if trans_elapsed >= (cfg.yellow_duration_sec + cfg.all_red_duration_sec):
                    # Transition complete! Switch to Arterial Priority Green
                    self._node_states[node_id] = PreclearanceState.HOLDING_GREEN
                    self._green_hold_start_time[node_id] = sim_time
                    commanded = cfg.arterial_phase_green
                    self._current_phase[node_id] = commanded
                    self._phase_start_time[node_id] = sim_time
                else:
                    commanded = cfg.cross_phase_all_red
            else:
                # Already in Arterial Green or other phase -> switch to Green Hold
                self._node_states[node_id] = PreclearanceState.HOLDING_GREEN
                self._green_hold_start_time[node_id] = sim_time
                commanded = cfg.arterial_phase_green

            return PreclearanceDecision(
                node_id=node_id,
                state=self._node_states[node_id],
                should_actuate=True,
                commanded_phase=commanded,
                delta_trigger_sec=delta_trigger,
                ev_eta_sec=eta_sec,
                predicted_clearance_sec=t_clear,
                transition_time_sec=t_trans,
                safety_buffer_sec=cfg.safety_buffer_sec,
                active_green_hold_sec=0.0,
                reason=f"Pre-clearance transition in progress ({trans_elapsed:.1f}s / {cfg.yellow_duration_sec + cfg.all_red_duration_sec}s).",
                timestamp_sec=sim_time,
                is_emergency_priority=True,
                fallback_used=pred_res.fallback_used,
                confidence_score=min(eta_conf, pred_res.confidence_score),
            )

        # Case C: If ARMED or MONITORING: Evaluate JIT Trigger Condition
        if delta_trigger <= 0.0:
            # Trigger tripped! Actuate pre-clearance
            if active_phase == cfg.arterial_phase_green:
                # Arterial Green is already active: immediately hold it!
                self._node_states[node_id] = PreclearanceState.HOLDING_GREEN
                self._green_hold_start_time[node_id] = sim_time
                commanded = cfg.arterial_phase_green
                reason = f"JIT Pre-clearance triggered (delta: {delta_trigger:.2f}s <= 0). Corridor already green; holding."
            else:
                # Cross traffic active: begin safety transition
                self._node_states[node_id] = PreclearanceState.TRANSITIONING
                self._transition_start_time[node_id] = sim_time
                commanded = cfg.cross_phase_yellow
                self._current_phase[node_id] = commanded
                self._phase_start_time[node_id] = sim_time
                reason = f"JIT Pre-clearance triggered (delta: {delta_trigger:.2f}s <= 0). Transitioning to Yellow."

            return PreclearanceDecision(
                node_id=node_id,
                state=self._node_states[node_id],
                should_actuate=True,
                commanded_phase=commanded,
                delta_trigger_sec=delta_trigger,
                ev_eta_sec=eta_sec,
                predicted_clearance_sec=t_clear,
                transition_time_sec=t_trans,
                safety_buffer_sec=cfg.safety_buffer_sec,
                active_green_hold_sec=0.0,
                reason=reason,
                timestamp_sec=sim_time,
                is_emergency_priority=True,
                fallback_used=pred_res.fallback_used,
                confidence_score=min(eta_conf, pred_res.confidence_score),
            )
        else:
            # Arrival is in the future (delta_trigger > 0)
            self._node_states[node_id] = PreclearanceState.ARMED
            nominal = self.get_nominal_phase(sim_time)
            return PreclearanceDecision(
                node_id=node_id,
                state=PreclearanceState.ARMED,
                should_actuate=False,
                commanded_phase=nominal,
                delta_trigger_sec=delta_trigger,
                ev_eta_sec=eta_sec,
                predicted_clearance_sec=t_clear,
                transition_time_sec=t_trans,
                safety_buffer_sec=cfg.safety_buffer_sec,
                active_green_hold_sec=0.0,
                reason=f"ARMED: JIT delta is {delta_trigger:.2f}s > 0. Maintaining normal plan.",
                timestamp_sec=sim_time,
                is_emergency_priority=False,
                fallback_used=pred_res.fallback_used,
                confidence_score=min(eta_conf, pred_res.confidence_score),
            )

    def evaluate_corridor(
        self,
        mission: EmergencyMission | None,
        traffic_states: dict[str, ApproachTrafficState] | None,
        sim_time: float,
        weather: str = "clear",
    ) -> CorridorPreclearancePlan:
        """Evaluate pre-clearance plan across all corridor intersections simultaneously."""
        decisions: dict[str, PreclearanceDecision] = {}
        commanded_phases: dict[str, int] = {}
        preemption_count = 0

        states_map = traffic_states or {}

        for nid in self.intersections:
            app_state = states_map.get(nid)
            dec = self.evaluate_node(
                node_id=nid,
                mission=mission,
                approach_state=app_state,
                sim_time=sim_time,
                weather=weather,
            )
            decisions[nid] = dec
            commanded_phases[nid] = dec.commanded_phase
            if dec.should_actuate:
                preemption_count += 1

        ev_pos = mission.current_position_m if mission else CORRIDOR_ENTRY_X_METERS
        ev_spd = mission.current_speed_kmh if mission else 0.0

        return CorridorPreclearancePlan(
            mission_id=mission.mission_id if mission else None,
            vehicle_id=mission.vehicle_id if mission else None,
            current_position_m=ev_pos,
            current_speed_kmh=ev_spd,
            decisions=decisions,
            commanded_phases=commanded_phases,
            active_preemptions_count=preemption_count,
            timestamp_sec=sim_time,
        )

    def step(
        self,
        sim_time: float,
        mission: EmergencyMission | None,
        traffic_states: dict[str, ApproachTrafficState] | None = None,
        dt: float = 0.1,
        weather: str = "clear",
    ) -> dict[str, int]:
        """Simulation step method returning the commanded phase for each intersection."""
        plan = self.evaluate_corridor(
            mission=mission,
            traffic_states=traffic_states,
            sim_time=sim_time,
            weather=weather,
        )
        return plan.commanded_phases
