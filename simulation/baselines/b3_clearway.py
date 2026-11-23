"""
ClearWayAI - Baseline B3 / Proposed System: Moving-Horizon Predictive Pre-Clearance Controller.

Implements the complete ClearWayAI signal coordination architecture:
1. Moving-Horizon Spatial-Temporal Coordination Window (750m / 45s lookahead)
2. JIT Pre-Clearance Triggering based on ML Queue Shockwave Clearance Prediction
3. Inter-Node Cascading Green Wave Offsets
4. Smooth Post-Clearance Recovery with Green Debt Amortization
5. Hardware MMU Safety Interlock Gateway (SignalSafetyGateway, INV-01 to INV-06)
"""

from __future__ import annotations

import time
from typing import Any

from ai.clearance.model_registry import ClearancePredictionResult, FallbackTier
from ai.state.traffic_state_estimator import ApproachTrafficState
from controller.mission.emergency_mission import (
    CORRIDOR_ENTRY_X_METERS,
    EmergencyMission,
    EmergencyVehicleType,
    MissionStatus,
)
from controller.recovery.recovery_controller import (
    PostClearanceRecoveryController,
    RecoveryConfig,
)
from controller.safety.signal_safety_gateway import SignalSafetyGateway
from controller.scheduler.corridor_coordinator import (
    CorridorCoordinatorConfig,
    MovingHorizonCorridorCoordinator,
)
from controller.scheduler.preclearance_controller import (
    PreclearanceConfig,
    PreclearanceController,
    PreclearanceState,
)
from simulation.baselines.base_controller import BaseSignalController


class StaticClearancePredictor:
    """Fallback predictor for ablation experiments (without machine learning shockwave model)."""

    def predict(
        self,
        states: ApproachTrafficState | list[ApproachTrafficState] | None,
        node_id: str = "node_a",
        weather: str = "clear",
    ) -> ClearancePredictionResult:
        if isinstance(states, list) and states:
            st = states[-1]
        elif isinstance(states, ApproachTrafficState):
            st = states
        else:
            st = None

        queued = st.queued_vehicle_count if st else 5
        # Static baseline: 2.2 seconds per queued vehicle
        pred_time = float(max(2.0, queued * 2.2))

        return ClearancePredictionResult(
            predicted_clearance_sec=pred_time,
            confidence_score=0.50,
            model_name="Static_Linear_Discharge_Ablation",
            model_type="heuristic",
            fallback_used=True,
            fallback_tier=FallbackTier.TIER_1_KINEMATIC_PHYSICS,
            fallback_reason="Ablation: ML model disabled",
            latency_ms=0.05,
            provenance="ABLATION_STATIC_PREDICTOR",
            timestamp_sec=time.time(),
        )


class B3ClearWayController(BaseSignalController):
    """
    ClearWayAI Proposed Controller:
    Moving-Horizon Predictive Pre-Clearance with AI Shockwave Estimation and Smooth Recovery.
    """

    def __init__(
        self,
        intersections: list[str] | None = None,
        cycle_time: float = 72.0,
        enable_ai_prediction: bool = True,
        enable_moving_horizon: bool = True,
        enable_recovery: bool = True,
        weather: str = "clear",
        motorcycle_ratio: float = 0.60,
    ) -> None:
        super().__init__(intersections=intersections, cycle_time=cycle_time)
        self.enable_ai_prediction = enable_ai_prediction
        self.enable_moving_horizon = enable_moving_horizon
        self.enable_recovery = enable_recovery
        self.weather = weather
        self.motorcycle_ratio = motorcycle_ratio

        # Configure JIT Preclearance
        p_cfg = PreclearanceConfig(nominal_cycle_time_sec=cycle_time)
        predictor = None if enable_ai_prediction else StaticClearancePredictor()  # type: ignore[assignment]
        self.preclear_ctrl = PreclearanceController(
            config=p_cfg,
            clearance_predictor=predictor,  # type: ignore[arg-type]
            intersections=self.intersections,
        )

        # Configure Moving-Horizon Coordinator
        c_cfg = CorridorCoordinatorConfig(
            horizon_distance_m=750.0 if enable_moving_horizon else 120.0,
            horizon_time_sec=45.0 if enable_moving_horizon else 8.0,
            preclearance_config=p_cfg,
        )
        self.coordinator = MovingHorizonCorridorCoordinator(
            config=c_cfg,
            preclearance_controller=self.preclear_ctrl,
            intersections=self.intersections,
        )

        # Recovery Controller & MMU Safety Gateway
        self.recovery_ctrl = PostClearanceRecoveryController(
            config=RecoveryConfig(nominal_cycle_sec=cycle_time),
            intersections=self.intersections,
        )
        self.safety_gateway = SignalSafetyGateway()

        # Operational tracking state
        self.active_mission: EmergencyMission | None = None
        self.is_corridor_preempted: bool = False
        self.preempted_nodes: set[str] = set()
        self._node_preempt_start: dict[str, float | None] = dict.fromkeys(self.intersections, None)
        self._node_preempt_duration: dict[str, float] = dict.fromkeys(self.intersections, 0.0)
        self._node_recovered: set[str] = set()
        self.reset()

    def reset(self) -> None:
        """Reset internal state for a fresh simulation run."""
        self.metrics.total_steps = 0
        self.metrics.preemption_events = 0
        self.metrics.total_preemption_duration_sec = 0.0
        self.metrics.emergency_stops = 0
        self.metrics.emergency_transit_time_sec = 0.0
        self.metrics.cross_street_delay_sec = 0.0

        self.preclear_ctrl.reset()
        self.coordinator.reset()
        self.recovery_ctrl.reset()
        self.safety_gateway.reset()

        self.active_mission = None
        self.is_corridor_preempted = False
        self.preempted_nodes.clear()
        self._node_preempt_start = dict.fromkeys(self.intersections, None)
        self._node_preempt_duration = dict.fromkeys(self.intersections, 0.0)
        self._node_recovered.clear()

    def _update_emergency_mission(
        self,
        active_vehicles: dict[str, dict[str, Any]],
        sim_time: float,
    ) -> None:
        """Detect and synchronize the emergency vehicle status with the priority mission."""
        ev_data = None
        for vid, v in active_vehicles.items():
            if v.get("is_emergency") or "AMB" in vid or "fire" in v.get("type", ""):
                ev_data = v
                break

        if ev_data is not None:
            pos_x = float(ev_data.get("x", CORRIDOR_ENTRY_X_METERS))
            speed_mps = float(ev_data.get("speed", 18.5))
            if self.active_mission is None:
                self.active_mission = EmergencyMission(
                    mission_id="AMB-339",
                    vehicle_id=str(ev_data.get("id", "AMB-339")),
                    vehicle_type=EmergencyVehicleType.AMBULANCE,
                    status=MissionStatus.CORRIDOR_TRANSIT,
                    current_position_m=pos_x,
                    current_speed_mps=speed_mps,
                    depart_time_sec=sim_time,
                )
            else:
                self.active_mission.current_position_m = pos_x
                self.active_mission.current_speed_mps = speed_mps
                self.active_mission.status = MissionStatus.CORRIDOR_TRANSIT
        elif self.active_mission is not None:
            if self.active_mission.current_position_m >= 950.0:
                self.active_mission.status = MissionStatus.ARRIVED
            else:
                self.active_mission.status = MissionStatus.COMPLETED

    def _estimate_traffic_states(
        self,
        active_vehicles: dict[str, dict[str, Any]],
        sim_time: float,
    ) -> dict[str, ApproachTrafficState]:
        """Synthesize approach traffic states for coordinator input."""
        states = {}
        for nid in self.intersections:
            stopline = self.coordinator.stoplines.get(nid, 0.0)
            # Count queued vehicles near stopline
            nearby = [
                v
                for v in active_vehicles.values()
                if abs(float(v.get("x", 0.0)) - stopline) <= 120.0
                and ("eb" in str(v.get("route", "")) or "through" in str(v.get("route", "")))
            ]
            queued = sum(1 for v in nearby if float(v.get("speed", 10.0)) < 2.0)
            q_len = max(queued * 4.5, 5.0)
            v_count = max(len(nearby), 1)
            moto_count = int(v_count * self.motorcycle_ratio)
            car_count = v_count - moto_count

            states[nid] = ApproachTrafficState(
                approach_id="EB",
                timestamp_sec=sim_time,
                vehicle_count=v_count,
                counts_by_class={"motorcycle": moto_count, "car": car_count},
                motorcycle_ratio=self.motorcycle_ratio,
                queue_length_meters=q_len,
                queued_vehicle_count=queued,
                approach_occupancy_ratio=min(0.95, 0.20 + (queued * 0.06)),
                traffic_density_vpm=float(v_count),
                mean_speed_kmh=42.0,
                emergency_vehicle_detected=bool(
                    self.active_mission and self.active_mission.is_active
                ),
            )
        return states

    def step(
        self,
        sim_time: float,
        active_vehicles: dict[str, dict[str, Any]],
        dt: float = 0.1,
    ) -> dict[str, int]:
        """
        Advance the ClearWayAI coordination cycle:
        1. Synchronize emergency mission kinematics
        2. Update moving-horizon schedule & cascading offsets
        3. Trigger smooth post-clearance recovery for cleared nodes
        4. Sanitize commanded phases through MMU Safety Gateway
        """
        self.metrics.total_steps += 1
        self._update_emergency_mission(active_vehicles, sim_time)
        traffic_states = self._estimate_traffic_states(active_vehicles, sim_time)

        # 1. Moving-Horizon Corridor Coordination
        report = self.coordinator.update_corridor(
            mission=self.active_mission,
            traffic_states=traffic_states,
            sim_time=sim_time,
            weather=self.weather,
        )
        commanded = dict(report.commanded_phases)

        # 2. Track Preemption Active Nodes
        newly_preempted = set()
        for nid, sched in report.schedules.items():
            if sched.state in (
                PreclearanceState.ARMED,
                PreclearanceState.TRANSITIONING,
                PreclearanceState.HOLDING_GREEN,
                PreclearanceState.EV_PASSING,
            ):
                newly_preempted.add(nid)
                if self._node_preempt_start[nid] is None:
                    self._node_preempt_start[nid] = sim_time
                    self.metrics.preemption_events += 1
                self._node_preempt_duration[nid] += dt

        self.preempted_nodes = newly_preempted
        self.is_corridor_preempted = len(self.preempted_nodes) > 0
        if self.is_corridor_preempted:
            self.metrics.total_preemption_duration_sec += dt

        # 3. Post-Clearance Smooth Recovery
        if self.enable_recovery:
            for nid in report.cleared_nodes:
                if (
                    nid not in self._node_recovered
                    and not self.recovery_ctrl.is_recovering(nid)
                    and self._node_preempt_start[nid] is not None
                ):
                    dur = self._node_preempt_duration[nid]
                    self.recovery_ctrl.initiate_recovery(
                        node_id=nid,
                        preemption_duration_sec=dur,
                        cross_queue_meters=18.0,
                        sim_time=sim_time,
                    )
                    self._node_recovered.add(nid)

                if self.recovery_ctrl.is_recovering(nid):
                    rec_status = self.recovery_ctrl.evaluate_node(nid, sim_time=sim_time, dt=dt)
                    commanded[nid] = rec_status.commanded_phase

        # 4. MMU Safety Gateway Sanitation across all 4 intersections
        sanitized_phases: dict[str, int] = {}
        for nid in self.intersections:
            raw_phase = commanded.get(nid, 0)
            res = self.safety_gateway.verify_and_sanitize_command(
                node_id=nid,
                proposed_phase=raw_phase,
                sim_time=sim_time,
            )
            sanitized_phases[nid] = res.sanitized_phase

        return sanitized_phases
