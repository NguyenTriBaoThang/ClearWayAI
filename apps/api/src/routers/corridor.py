"""Corridor Moving-Horizon Coordination & MMU Safety Endpoints (`apps.api.src.routers.corridor`)."""

from __future__ import annotations

import time

from fastapi import APIRouter, Query

from ai.state.traffic_state_estimator import ApproachTrafficState
from apps.api.src.database import SignalLogRecord, db
from apps.api.src.routers.missions import mission_manager
from apps.api.src.schemas import (
    CorridorPlanResponse,
    PreclearanceDecisionResponse,
    PreclearanceEvaluateRequest,
    RecoveryInitiateRequest,
    RecoveryStatusResponse,
    SafetyAuditResponse,
)
from controller.recovery.recovery_controller import PostClearanceRecoveryController
from controller.safety.signal_safety_gateway import SignalSafetyGateway
from controller.scheduler.corridor_coordinator import MovingHorizonCorridorCoordinator
from controller.scheduler.preclearance_controller import PreclearanceController

router = APIRouter(prefix="/api/v1/corridor", tags=["Corridor Coordination"])

# Shared controller instances for API lifecycle
preclearance_controller = PreclearanceController()
corridor_coordinator = MovingHorizonCorridorCoordinator(
    preclearance_controller=preclearance_controller,
)
recovery_controller = PostClearanceRecoveryController()
safety_gateway = SignalSafetyGateway()


@router.get("/plan", response_model=CorridorPlanResponse)
def get_corridor_coordination_plan(
    sim_time: float | None = Query(default=None, description="Current simulation timestamp"),
    weather: str = Query(default="clear", description="Current weather condition"),
) -> CorridorPlanResponse:
    """Evaluate real-time moving-horizon coordination plan across the arterial corridor."""
    t_now = sim_time if sim_time is not None else time.time()
    active_mission = mission_manager.get_active_mission()

    report = corridor_coordinator.coordinate(
        mission=active_mission,
        sim_time=t_now,
        weather=weather,
    )

    return CorridorPlanResponse(
        mission_id=report.mission_id,
        vehicle_id=report.vehicle_id,
        corridor_status=str(report.corridor_status),
        current_position_m=report.current_position_m,
        current_speed_kmh=report.current_speed_kmh,
        active_horizon_nodes=list(report.active_horizon_nodes),
        cleared_nodes=list(report.cleared_nodes),
        commanded_phases=report.commanded_phases,
        coordination_offsets_sec=report.coordination_offsets_sec,
        spillback_alerts=list(report.spillback_alerts),
        total_active_holds=report.total_active_holds,
        timestamp_sec=report.timestamp_sec,
        provenance=report.provenance,
    )


@router.post("/preclearance/evaluate", response_model=PreclearanceDecisionResponse)
def evaluate_preclearance(req: PreclearanceEvaluateRequest) -> PreclearanceDecisionResponse:
    """Evaluate Just-in-Time pre-clearance trigger for a specific intersection."""
    mission = None
    if req.mission_id:
        mission = mission_manager.get_mission(req.mission_id)
    if mission is None:
        mission = mission_manager.get_active_mission()

    approach_state = ApproachTrafficState(
        approach_id="EB",
        timestamp_sec=req.sim_time,
        vehicle_count=req.queued_vehicle_count,
        counts_by_class={},
        motorcycle_ratio=0.65,
        queue_length_meters=req.queue_length_meters,
        queued_vehicle_count=req.queued_vehicle_count,
        approach_occupancy_ratio=min(1.0, req.queue_length_meters / 100.0),
        traffic_density_vpm=25.0,
        mean_speed_kmh=10.0,
    )

    decision = preclearance_controller.evaluate_node(
        node_id=req.node_id,
        mission=mission,
        approach_state=approach_state,
        sim_time=req.sim_time,
    )

    # Log signal event to database
    log_rec = SignalLogRecord(
        id=None,
        timestamp=req.sim_time,
        node_id=req.node_id,
        phase=decision.commanded_phase,
        operational_mode=str(decision.state),
        is_safe=True,
        intervention_reason=decision.reason,
        details_json=f'{{"delta_trigger": {decision.delta_trigger_sec:.2f}, "eta": {decision.ev_eta_sec:.2f}}}',
    )
    db.log_signal_event(log_rec)

    return PreclearanceDecisionResponse(
        node_id=decision.node_id,
        state=str(decision.state),
        should_actuate=decision.should_actuate,
        commanded_phase=decision.commanded_phase,
        delta_trigger_sec=decision.delta_trigger_sec,
        ev_eta_sec=decision.ev_eta_sec,
        predicted_clearance_sec=decision.predicted_clearance_sec,
        reason=decision.reason,
    )


@router.post("/recovery/initiate", response_model=RecoveryStatusResponse)
def initiate_recovery(req: RecoveryInitiateRequest) -> RecoveryStatusResponse:
    """Initiate post-clearance multi-cycle smooth green debt recovery for an intersection."""
    status = recovery_controller.initiate_recovery(
        node_id=req.node_id,
        preemption_duration_sec=req.preemption_duration_sec,
        cross_queue_meters=req.cross_queue_meters,
        sim_time=req.sim_time,
    )

    # Log to signal log
    log_rec = SignalLogRecord(
        id=None,
        timestamp=req.sim_time,
        node_id=req.node_id,
        phase=status.commanded_phase,
        operational_mode="RECOVERY_COMPENSATING",
        is_safe=True,
        intervention_reason=status.reason,
        details_json=f'{{"initial_debt": {status.initial_green_debt_sec:.1f}, "cycle": {status.current_recovery_cycle}}}',
    )
    db.log_signal_event(log_rec)

    return RecoveryStatusResponse(
        node_id=status.node_id,
        state=str(status.state),
        initial_green_debt_sec=status.initial_green_debt_sec,
        remaining_green_debt_sec=status.remaining_green_debt_sec,
        current_recovery_cycle=status.current_recovery_cycle,
        bonus_green_allocated_sec=status.bonus_green_allocated_sec,
        commanded_phase=status.commanded_phase,
        is_recovered=status.is_recovered,
        reason=status.reason,
    )


@router.get("/safety/audit", response_model=SafetyAuditResponse)
def audit_corridor_safety(
    sim_time: float | None = Query(default=None, description="Simulation timestamp"),
) -> SafetyAuditResponse:
    """Perform hardware-level MMU/CMU safety audit across all corridor signals."""
    t_now = sim_time if sim_time is not None else time.time()
    active_mission = mission_manager.get_active_mission()

    # Get commanded phases from coordinator
    plan = corridor_coordinator.coordinate(
        mission=active_mission,
        sim_time=t_now,
    )

    # Audit via independent safety gateway
    audit = safety_gateway.audit_corridor_phases(
        proposed_phases=plan.commanded_phases,
        sim_time=t_now,
    )

    # Log any interventions
    for nid, report in audit.reports_by_node.items():
        if report.intervention:
            log_rec = SignalLogRecord(
                id=None,
                timestamp=t_now,
                node_id=nid,
                phase=report.sanitized_phase,
                operational_mode=str(report.operational_mode),
                is_safe=report.is_safe,
                intervention_reason=report.intervention.description,
            )
            db.log_signal_event(log_rec)

    return SafetyAuditResponse(
        all_nodes_safe=audit.all_nodes_safe,
        sanitized_phases=audit.sanitized_phases,
        total_interventions_corridor=audit.total_interventions_corridor,
        timestamp_sec=audit.timestamp_sec,
        provenance=audit.provenance,
    )

