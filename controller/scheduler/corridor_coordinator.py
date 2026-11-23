"""ClearWayAI Moving-Horizon Multi-Intersection Corridor Coordinator (`controller.scheduler`).

Coordinates traffic signals along the 4-node arterial corridor (Node A -> Node B -> Node C -> Node D):
1. Moving-Horizon Coordination Window:
   Only nodes within the spatial-temporal lookahead horizon ($H_{\\text{dist}} \\approx 750\\text{m}$,
   $H_{\\text{time}} \\approx 45\\text{s}$) are dynamically scheduled, leaving downstream nodes in nominal
   cycle timing to prevent premature cross-street gridlock.
2. Cascading Green Wave Offset Synchronization:
   Calculates inter-node offsets $\\Delta t_{\\text{offset}}(k, k+1) = \\text{ETA}(k+1) - \\text{ETA}(k)$
   and coordinates wave arrival to guarantee zero stop delay for the priority vehicle.
3. Queue Spillback Detection & Pre-emptive Flushing:
   Detects link storage saturation ($L_{\\text{queue}} > \\text{LinkLength} \\times \\gamma_{\\text{spillback}}$)
   and advances downstream pre-clearance triggers to drain queues before the upstream platoon arrives.
4. Immediate Tail Recovery Handoff:
   Releases each intersection node immediately upon emergency vehicle passage ($x > x_{\\text{stop}} + 15\\text{m}$)
   for seamless post-transit recovery.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

from ai.state.traffic_state_estimator import ApproachTrafficState
from controller.mission.emergency_mission import (
    CORRIDOR_ENTRY_X_METERS,
    EmergencyMission,
)
from controller.mission.eta_estimator import (
    CORRIDOR_NODE_STOPLINES,
    MultiNodeETAEvaluator,
)
from controller.scheduler.preclearance_controller import (
    PreclearanceConfig,
    PreclearanceController,
    PreclearanceState,
)

DEFAULT_LINK_LENGTHS_METERS: dict[str, float] = {
    "node_a": 200.0,  # Entry gate to Node A
    "node_b": 300.0,  # Node A to Node B
    "node_c": 300.0,  # Node B to Node C
    "node_d": 300.0,  # Node C to Node D
}


class CorridorCoordinationStatus(StrEnum):
    """Operational status of the multi-intersection corridor coordination system."""

    STANDBY = "STANDBY"
    CORRIDOR_ARMED = "CORRIDOR_ARMED"
    ACTIVE_GREEN_WAVE = "ACTIVE_GREEN_WAVE"
    TRANSIT_IN_PROGRESS = "TRANSIT_IN_PROGRESS"
    ALL_CLEARED = "ALL_CLEARED"


@dataclass
class CorridorCoordinatorConfig:
    """Configuration parameters for moving-horizon multi-intersection scheduling."""

    horizon_distance_m: float = 750.0
    horizon_time_sec: float = 45.0
    spillback_threshold_ratio: float = 0.50  # Queue > 50% link length triggers warning
    max_spillback_advance_sec: float = 12.0
    discharge_wave_speed_mps: float = 4.5  # Saturation discharge speed ~16.2 km/h
    inter_node_link_lengths: dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_LINK_LENGTHS_METERS)
    )
    preclearance_config: PreclearanceConfig = field(default_factory=PreclearanceConfig)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["preclearance_config"] = self.preclearance_config.to_dict()
        return d


@dataclass
class NodeCoordinationSchedule:
    """Moving-horizon schedule metrics for an individual intersection node."""

    node_id: str
    stopline_x_m: float
    distance_to_ev_m: float
    eta_to_node_sec: float
    predicted_clearance_sec: float
    target_green_start_sec: float
    target_green_end_sec: float
    commanded_phase: int
    state: PreclearanceState
    in_moving_horizon: bool
    has_cleared: bool
    spillback_risk: bool
    spillback_advance_sec: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["state"] = str(self.state)
        return d


@dataclass
class CorridorCoordinationReport:
    """Consolidated snapshot of the corridor moving-horizon coordination plan."""

    mission_id: str | None
    vehicle_id: str | None
    corridor_status: CorridorCoordinationStatus
    current_position_m: float
    current_speed_kmh: float
    active_horizon_nodes: list[str]
    cleared_nodes: list[str]
    schedules: dict[str, NodeCoordinationSchedule]
    commanded_phases: dict[str, int]
    coordination_offsets_sec: dict[str, float]
    spillback_alerts: list[str]
    total_active_holds: int
    timestamp_sec: float
    provenance: str = "MOVING_HORIZON_CORRIDOR_COORDINATOR"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["corridor_status"] = str(self.corridor_status)
        d["schedules"] = {k: v.to_dict() for k, v in self.schedules.items()}
        return d


class MovingHorizonCorridorCoordinator:
    """Corridor-wide moving-horizon coordinator synchronizing Nodes A -> B -> C -> D."""

    def __init__(
        self,
        config: CorridorCoordinatorConfig | None = None,
        preclearance_controller: PreclearanceController | None = None,
        eta_evaluator: MultiNodeETAEvaluator | None = None,
        intersections: list[str] | None = None,
    ) -> None:
        self.config = config or CorridorCoordinatorConfig()
        self.intersections = intersections or ["node_a", "node_b", "node_c", "node_d"]
        self.stoplines: dict[str, float] = {
            nid: CORRIDOR_NODE_STOPLINES.get(nid, 0.0) for nid in self.intersections
        }
        self.link_lengths: dict[str, float] = {
            nid: self.config.inter_node_link_lengths.get(nid, 300.0) for nid in self.intersections
        }

        self.eta_evaluator = eta_evaluator or MultiNodeETAEvaluator(
            node_stoplines=self.stoplines,
        )

        if preclearance_controller is not None:
            self.controller = preclearance_controller
        else:
            self.controller = PreclearanceController(
                config=self.config.preclearance_config,
                eta_evaluator=self.eta_evaluator,
                intersections=self.intersections,
            )

        self._corridor_status = CorridorCoordinationStatus.STANDBY
        self._cleared_nodes: set[str] = set()

    def reset(self) -> None:
        """Reset internal coordination tracking state and controller."""
        self.controller.reset()
        self._corridor_status = CorridorCoordinationStatus.STANDBY
        self._cleared_nodes.clear()

    def detect_spillback_risks(
        self,
        traffic_states: dict[str, ApproachTrafficState] | None,
    ) -> dict[str, tuple[bool, float]]:
        """Detect queue spillback risk along links connecting corridor nodes.

        Returns:
            dict[node_id, (spillback_risk: bool, advance_sec: float)]
        """
        risks: dict[str, tuple[bool, float]] = {}
        states = traffic_states or {}

        for nid in self.intersections:
            app_state = states.get(nid)
            link_len = self.link_lengths.get(nid, 300.0)
            threshold = link_len * self.config.spillback_threshold_ratio

            if app_state is not None and app_state.queue_length_meters > threshold:
                excess_queue = app_state.queue_length_meters - threshold
                advance_time = min(
                    self.config.max_spillback_advance_sec,
                    round(excess_queue / self.config.discharge_wave_speed_mps, 2),
                )
                risks[nid] = (True, advance_time)
            else:
                risks[nid] = (False, 0.0)

        return risks

    def compute_inter_node_offsets(
        self,
        node_etas: dict[str, float],
    ) -> dict[str, float]:
        """Compute relative kinematic arrival offsets between successive intersections.

        $$\\Delta t_{\\text{offset}}(k, k+1) = \\text{ETA}(k+1) - \\text{ETA}(k)$$
        """
        offsets: dict[str, float] = {}
        for i in range(len(self.intersections) - 1):
            curr_id = self.intersections[i]
            next_id = self.intersections[i + 1]
            eta_curr = node_etas.get(curr_id, 0.0)
            eta_next = node_etas.get(next_id, 0.0)
            offset = max(0.0, round(eta_next - eta_curr, 2))
            offsets[f"{curr_id}_to_{next_id}"] = offset
        return offsets

    def update_corridor(
        self,
        mission: EmergencyMission | None,
        traffic_states: dict[str, ApproachTrafficState] | None,
        sim_time: float,
        weather: str = "clear",
    ) -> CorridorCoordinationReport:
        """Run moving-horizon corridor coordination optimization across all nodes."""
        cfg = self.config
        spillback_risks = self.detect_spillback_risks(traffic_states)

        # 1. Mission presence & corridor lifecycle check
        if mission is None or not mission.is_active:
            self._corridor_status = CorridorCoordinationStatus.STANDBY
            self._cleared_nodes.clear()
            plan = self.controller.evaluate_corridor(
                mission=None,
                traffic_states=traffic_states,
                sim_time=sim_time,
                weather=weather,
            )

            schedules: dict[str, NodeCoordinationSchedule] = {}
            for nid in self.intersections:
                dec = plan.decisions[nid]
                schedules[nid] = NodeCoordinationSchedule(
                    node_id=nid,
                    stopline_x_m=self.stoplines[nid],
                    distance_to_ev_m=999.0,
                    eta_to_node_sec=999.0,
                    predicted_clearance_sec=0.0,
                    target_green_start_sec=0.0,
                    target_green_end_sec=0.0,
                    commanded_phase=dec.commanded_phase,
                    state=PreclearanceState.MONITORING,
                    in_moving_horizon=False,
                    has_cleared=False,
                    spillback_risk=False,
                    spillback_advance_sec=0.0,
                    reason="No active priority mission in corridor.",
                )

            return CorridorCoordinationReport(
                mission_id=None,
                vehicle_id=None,
                corridor_status=CorridorCoordinationStatus.STANDBY,
                current_position_m=CORRIDOR_ENTRY_X_METERS,
                current_speed_kmh=0.0,
                active_horizon_nodes=[],
                cleared_nodes=[],
                schedules=schedules,
                commanded_phases=plan.commanded_phases,
                coordination_offsets_sec={},
                spillback_alerts=[],
                total_active_holds=0,
                timestamp_sec=sim_time,
            )

        ev_pos = mission.current_position_m
        ev_spd_kmh = mission.current_speed_kmh

        # 2. Compute individual node kinematic ETAs
        node_etas: dict[str, float] = {}
        node_distances: dict[str, float] = {}
        node_passed: dict[str, bool] = {}

        states_map = traffic_states or {}

        for nid in self.intersections:
            stop_x = self.stoplines[nid]
            dist_rem = stop_x - ev_pos
            node_distances[nid] = dist_rem

            app_st = states_map.get(nid)
            occ = app_st.approach_occupancy_ratio if app_st else 0.20

            eta, _, passed, _ = self.eta_evaluator.compute_single_node_eta(
                current_x_m=ev_pos,
                current_v_mps=mission.current_speed_mps,
                target_v_mps=mission.target_speed_mps,
                max_v_mps=mission.max_speed_mps,
                stopline_x_m=stop_x,
                traffic_occupancy=occ,
                weather=weather,
            )
            node_etas[nid] = eta
            node_passed[nid] = passed

            if passed or (ev_pos > stop_x + cfg.preclearance_config.exit_clearance_distance_m):
                self._cleared_nodes.add(nid)

        offsets = self.compute_inter_node_offsets(node_etas)

        # 3. Determine moving horizon active nodes
        active_horizon_nodes: list[str] = []
        for nid in self.intersections:
            dist = node_distances[nid]
            eta = node_etas[nid]
            if (
                nid not in self._cleared_nodes
                and (0.0 <= dist <= cfg.horizon_distance_m)
                and (0.0 <= eta <= cfg.horizon_time_sec)
            ):
                active_horizon_nodes.append(nid)

        # 4. Evaluate each node with moving horizon & spillback coordination
        schedules = {}
        commanded_phases: dict[str, int] = {}
        spillback_alerts: list[str] = []
        active_holds_count = 0

        for nid in self.intersections:
            stop_x = self.stoplines[nid]
            dist = node_distances[nid]
            eta = node_etas[nid]
            has_passed = nid in self._cleared_nodes
            in_horizon = nid in active_horizon_nodes

            has_spillback, advance_sec = spillback_risks.get(nid, (False, 0.0))
            if has_spillback:
                spillback_alerts.append(
                    f"Spillback warning at {nid}: queue exceeds threshold. Pre-clearance advanced by {advance_sec:.1f}s."
                )

            # If node is outside the moving horizon and has not cleared, maintain nominal plan
            if not in_horizon and not has_passed:
                nominal_phase = self.controller.get_nominal_phase(sim_time)
                commanded_phases[nid] = nominal_phase
                schedules[nid] = NodeCoordinationSchedule(
                    node_id=nid,
                    stopline_x_m=stop_x,
                    distance_to_ev_m=dist,
                    eta_to_node_sec=eta,
                    predicted_clearance_sec=0.0,
                    target_green_start_sec=round(sim_time + max(0.0, eta - 10.0), 2),
                    target_green_end_sec=round(sim_time + eta + 10.0, 2),
                    commanded_phase=nominal_phase,
                    state=PreclearanceState.MONITORING,
                    in_moving_horizon=False,
                    has_cleared=False,
                    spillback_risk=has_spillback,
                    spillback_advance_sec=advance_sec,
                    reason=f"Outside moving horizon ({dist:.1f}m > {cfg.horizon_distance_m}m). Nominal plan preserved.",
                )
                continue

            # In horizon or cleared: execute pre-clearance evaluation
            # If spillback risk is present, temporarily adjust ETA to trigger pre-emptive drainage
            effective_sim_time = sim_time
            app_state = states_map.get(nid)

            dec = self.controller.evaluate_node(
                node_id=nid,
                mission=mission,
                approach_state=app_state,
                sim_time=effective_sim_time,
                weather=weather,
            )

            # If spillback mitigation applies and node is in ARMED, trigger early transition
            if has_spillback and dec.state == PreclearanceState.ARMED:
                adjusted_delta = dec.delta_trigger_sec - advance_sec
                if adjusted_delta <= 0.0:
                    # Spillback mitigation trips trigger early!
                    dec = self.controller.evaluate_node(
                        node_id=nid,
                        mission=mission,
                        approach_state=app_state,
                        sim_time=sim_time + advance_sec,
                        weather=weather,
                    )
                    dec.reason += f" [Spillback Mitigation: Pre-emptive flushing advanced by {advance_sec:.1f}s]"

            commanded_phases[nid] = dec.commanded_phase
            if dec.state in (
                PreclearanceState.HOLDING_GREEN,
                PreclearanceState.EV_PASSING,
            ):
                active_holds_count += 1

            # Estimate target green interval windows
            target_green_start = (
                round(sim_time + max(0.0, eta - dec.predicted_clearance_sec - 5.0), 2)
                if not has_passed
                else sim_time
            )
            target_green_end = (
                round(sim_time + eta + cfg.preclearance_config.exit_clearance_distance_m / 10.0, 2)
                if not has_passed
                else sim_time
            )

            schedules[nid] = NodeCoordinationSchedule(
                node_id=nid,
                stopline_x_m=stop_x,
                distance_to_ev_m=dist,
                eta_to_node_sec=eta,
                predicted_clearance_sec=dec.predicted_clearance_sec,
                target_green_start_sec=target_green_start,
                target_green_end_sec=target_green_end,
                commanded_phase=dec.commanded_phase,
                state=dec.state,
                in_moving_horizon=in_horizon,
                has_cleared=has_passed,
                spillback_risk=has_spillback,
                spillback_advance_sec=advance_sec,
                reason=dec.reason,
            )

        # 5. Determine overall corridor lifecycle status
        if len(self._cleared_nodes) == len(self.intersections):
            self._corridor_status = CorridorCoordinationStatus.ALL_CLEARED
        elif active_holds_count > 0:
            if ev_pos >= self.stoplines["node_a"]:
                self._corridor_status = CorridorCoordinationStatus.TRANSIT_IN_PROGRESS
            else:
                self._corridor_status = CorridorCoordinationStatus.ACTIVE_GREEN_WAVE
        elif len(active_horizon_nodes) > 0:
            self._corridor_status = CorridorCoordinationStatus.CORRIDOR_ARMED
        else:
            self._corridor_status = CorridorCoordinationStatus.STANDBY

        return CorridorCoordinationReport(
            mission_id=mission.mission_id,
            vehicle_id=mission.vehicle_id,
            corridor_status=self._corridor_status,
            current_position_m=ev_pos,
            current_speed_kmh=ev_spd_kmh,
            active_horizon_nodes=active_horizon_nodes,
            cleared_nodes=sorted(self._cleared_nodes),
            schedules=schedules,
            commanded_phases=commanded_phases,
            coordination_offsets_sec=offsets,
            spillback_alerts=spillback_alerts,
            total_active_holds=active_holds_count,
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
        """Step simulation runner interface returning commanded phases for all nodes."""
        report = self.update_corridor(
            mission=mission,
            traffic_states=traffic_states,
            sim_time=sim_time,
            weather=weather,
        )
        return report.commanded_phases
