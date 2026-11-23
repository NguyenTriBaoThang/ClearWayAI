"""Corridor Moving-Horizon Coordination & MMU Safety Endpoints (`apps.api.src.routers.corridor`)."""

from __future__ import annotations

import json
import time

from fastapi import APIRouter, HTTPException, Query, status

from ai.state.traffic_state_estimator import ApproachTrafficState
from apps.api.src.database import DecisionAuditLogRecord, SignalLogRecord, db
from apps.api.src.routers.missions import mission_manager
from apps.api.src.schemas import (
    CorridorPlanResponse,
    PreclearanceDecisionResponse,
    PreclearanceEvaluateRequest,
    RecoveryInitiateRequest,
    RecoveryStatusResponse,
    SafetyAuditResponse,
    VMSBoardStatusResponse,
    VMSCorridorStatusResponse,
)
from controller.audit.decision_audit import DecisionType, decision_audit_service
from controller.recovery.recovery_controller import PostClearanceRecoveryController
from controller.safety.signal_safety_gateway import SignalSafetyGateway
from controller.scheduler.corridor_coordinator import MovingHorizonCorridorCoordinator
from controller.scheduler.preclearance_controller import PreclearanceController
from controller.vms.vms_manager import vms_manager

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

    report = corridor_coordinator.update_corridor(
        mission=active_mission,
        traffic_states=None,
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

    # Log explainable decision audit record
    audit_rec = decision_audit_service.record_preclearance_decision(
        decision=decision,
        mission=mission,
        approach_state=approach_state,
        sim_time_sec=req.sim_time,
    )
    db.log_decision_audit(
        DecisionAuditLogRecord(
            decision_id=audit_rec.decision_id,
            timestamp=audit_rec.timestamp,
            sim_time_sec=audit_rec.sim_time_sec,
            node_id=audit_rec.node_id,
            decision_type=str(audit_rec.decision_type),
            commanded_phase=audit_rec.commanded_phase,
            previous_phase=audit_rec.previous_phase,
            mission_id=audit_rec.mission_id,
            vehicle_id=audit_rec.vehicle_id,
            ev_eta_sec=audit_rec.ev_eta_sec,
            queue_length_m=audit_rec.queue_length_m,
            queued_vehicle_count=audit_rec.queued_vehicle_count,
            predicted_clearance_sec=audit_rec.predicted_clearance_sec,
            transition_time_sec=audit_rec.transition_time_sec,
            safety_buffer_sec=audit_rec.safety_buffer_sec,
            delta_trigger_sec=audit_rec.delta_trigger_sec,
            confidence_score=audit_rec.confidence_score,
            model_name=audit_rec.model_name,
            explanation_narrative=audit_rec.explanation_narrative,
            feature_attributions_json=json.dumps(audit_rec.feature_attributions),
            safety_status=str(audit_rec.safety_status),
            provenance=audit_rec.provenance,
        )
    )

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

    # Log explainable recovery decision audit
    rec_audit = decision_audit_service.record_decision(
        node_id=req.node_id,
        decision_type=DecisionType.RECOVERY_INITIATED,
        commanded_phase=status.commanded_phase,
        sim_time_sec=req.sim_time,
        override_reason=status.reason,
    )
    db.log_decision_audit(
        DecisionAuditLogRecord(
            decision_id=rec_audit.decision_id,
            timestamp=rec_audit.timestamp,
            sim_time_sec=rec_audit.sim_time_sec,
            node_id=rec_audit.node_id,
            decision_type=str(rec_audit.decision_type),
            commanded_phase=rec_audit.commanded_phase,
            previous_phase=rec_audit.previous_phase,
            mission_id=None,
            vehicle_id=None,
            ev_eta_sec=0.0,
            queue_length_m=req.cross_queue_meters,
            queued_vehicle_count=int(req.cross_queue_meters / 5.0),
            predicted_clearance_sec=0.0,
            transition_time_sec=0.0,
            safety_buffer_sec=2.0,
            delta_trigger_sec=0.0,
            confidence_score=1.0,
            model_name="post_clearance_recovery",
            explanation_narrative=rec_audit.explanation_narrative,
            feature_attributions_json=json.dumps(rec_audit.feature_attributions),
            safety_status=str(rec_audit.safety_status),
            provenance=rec_audit.provenance,
        )
    )

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
    plan = corridor_coordinator.update_corridor(
        mission=active_mission,
        traffic_states=None,
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


@router.get("/vms", response_model=VMSCorridorStatusResponse)
def get_corridor_vms_status(
    sim_time: float | None = Query(default=None, description="Simulation timestamp"),
) -> VMSCorridorStatusResponse:
    """Get real-time bilingual safety advisory status for all 4 overhead VMS gantries."""
    t_now = sim_time if sim_time is not None else time.time()
    active_mission = mission_manager.get_active_mission()
    ev_active = bool(active_mission and active_mission.is_active)
    ev_x = active_mission.current_position_m if ev_active and active_mission else None
    ev_spd = active_mission.current_speed_mps if ev_active and active_mission else None
    ev_id = active_mission.vehicle_id if ev_active and active_mission else "AMB-339"

    corridor_vms = vms_manager.evaluate_corridor(
        ev_active=ev_active,
        ev_x=ev_x,
        ev_speed_mps=ev_spd,
        ev_id=ev_id,
        sim_time=t_now,
    )
    return VMSCorridorStatusResponse(**corridor_vms.to_dict())


@router.get("/vms/{node_id}", response_model=VMSBoardStatusResponse)
def get_node_vms_status(
    node_id: str,
    sim_time: float | None = Query(default=None, description="Simulation timestamp"),
) -> VMSBoardStatusResponse:
    """Get real-time safety advisory status for a specific overhead VMS gantry (node_a through node_d)."""
    t_now = sim_time if sim_time is not None else time.time()
    active_mission = mission_manager.get_active_mission()
    ev_active = bool(active_mission and active_mission.is_active)
    ev_x = active_mission.current_position_m if ev_active and active_mission else None
    ev_spd = active_mission.current_speed_mps if ev_active and active_mission else None
    ev_id = active_mission.vehicle_id if ev_active and active_mission else "AMB-339"

    try:
        board_status = vms_manager.evaluate_board(
            node_id=node_id,
            ev_active=ev_active,
            ev_x=ev_x,
            ev_speed_mps=ev_spd,
            ev_id=ev_id,
            sim_time=t_now,
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VMS board for node '{node_id}' not found. Valid nodes: node_a, node_b, node_c, node_d.",
        ) from None
    return VMSBoardStatusResponse(**board_status.to_dict())
