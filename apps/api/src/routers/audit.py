"""Explainable AI Decision Audit & Telemetry Endpoints (`apps.api.src.routers.audit`)."""

from __future__ import annotations

import contextlib
import json

from fastapi import APIRouter, HTTPException, Query, status

from apps.api.src.database import DecisionAuditLogRecord, db
from apps.api.src.schemas import (
    DecisionAuditListResponse,
    DecisionAuditSchema,
    DecisionAuditSummaryResponse,
    ExplainDecisionRequest,
    ExplainDecisionResponse,
)
from controller.audit.decision_audit import (
    DecisionAuditRecord,
    DecisionType,
    SafetyStatus,
    decision_audit_service,
)
from controller.scheduler.preclearance_controller import PreclearanceConfig, PreclearanceController

router = APIRouter(prefix="/api/v1/audit", tags=["AI Decision Audit & Explainability"])
preclearance_controller = PreclearanceController()


def _to_schema(r: DecisionAuditRecord | DecisionAuditLogRecord) -> DecisionAuditSchema:
    """Map internal decision audit record to response schema."""
    if isinstance(r, DecisionAuditLogRecord):
        attributions = (
            json.loads(r.feature_attributions_json) if r.feature_attributions_json else {}
        )
        return DecisionAuditSchema(
            decision_id=r.decision_id,
            timestamp=r.timestamp,
            sim_time_sec=r.sim_time_sec,
            node_id=r.node_id,
            decision_type=r.decision_type,
            commanded_phase=r.commanded_phase,
            previous_phase=r.previous_phase,
            mission_id=r.mission_id,
            vehicle_id=r.vehicle_id,
            ev_eta_sec=r.ev_eta_sec,
            queue_length_m=r.queue_length_m,
            queued_vehicle_count=r.queued_vehicle_count,
            predicted_clearance_sec=r.predicted_clearance_sec,
            transition_time_sec=r.transition_time_sec,
            safety_buffer_sec=r.safety_buffer_sec,
            delta_trigger_sec=r.delta_trigger_sec,
            confidence_score=r.confidence_score,
            model_name=r.model_name,
            explanation_narrative=r.explanation_narrative,
            feature_attributions=attributions,
            safety_status=r.safety_status,
            provenance=r.provenance,
        )

    return DecisionAuditSchema(
        decision_id=r.decision_id,
        timestamp=r.timestamp,
        sim_time_sec=r.sim_time_sec,
        node_id=r.node_id,
        decision_type=str(r.decision_type),
        commanded_phase=r.commanded_phase,
        previous_phase=r.previous_phase,
        mission_id=r.mission_id,
        vehicle_id=r.vehicle_id,
        ev_eta_sec=r.ev_eta_sec,
        queue_length_m=r.queue_length_m,
        queued_vehicle_count=r.queued_vehicle_count,
        predicted_clearance_sec=r.predicted_clearance_sec,
        transition_time_sec=r.transition_time_sec,
        safety_buffer_sec=r.safety_buffer_sec,
        delta_trigger_sec=r.delta_trigger_sec,
        confidence_score=r.confidence_score,
        model_name=r.model_name,
        explanation_narrative=r.explanation_narrative,
        feature_attributions=dict(r.feature_attributions),
        safety_status=str(r.safety_status),
        provenance=r.provenance,
    )


@router.get("/decisions", response_model=DecisionAuditListResponse)
def list_decisions(
    node_id: str | None = Query(default=None, description="Filter by node ID"),
    decision_type: str | None = Query(default=None, description="Filter by decision type"),
    mission_id: str | None = Query(default=None, description="Filter by mission ID"),
    limit: int = Query(default=50, ge=1, le=500, description="Max records to return"),
) -> DecisionAuditListResponse:
    """Retrieve filtered stream of explainable AI decision audit logs."""
    actual_node = node_id if isinstance(node_id, str) else None
    actual_type = decision_type if isinstance(decision_type, str) else None
    actual_mission = mission_id if isinstance(mission_id, str) else None
    actual_limit = limit if isinstance(limit, int) else 50

    # Check database first
    db_records = db.query_decision_audits(
        node_id=actual_node,
        decision_type=actual_type,
        mission_id=actual_mission,
        limit=actual_limit,
    )

    if db_records:
        schemas = [_to_schema(r) for r in db_records]
        return DecisionAuditListResponse(
            total_count=len(schemas),
            returned_count=len(schemas),
            decisions=schemas,
        )

    # Fallback to in-memory history
    enum_type = None
    if actual_type:
        with contextlib.suppress(ValueError):
            enum_type = DecisionType(actual_type)

    mem_records = decision_audit_service.query_decisions(
        node_id=actual_node,
        decision_type=enum_type,
        mission_id=actual_mission,
        limit=actual_limit,
    )
    schemas = [_to_schema(r) for r in mem_records]
    return DecisionAuditListResponse(
        total_count=len(schemas),
        returned_count=len(schemas),
        decisions=schemas,
    )


@router.get("/decisions/{decision_id}", response_model=DecisionAuditSchema)
def get_decision(decision_id: str) -> DecisionAuditSchema:
    """Retrieve full audit record and explainability details for a single decision."""
    # Check database
    db_rec = db.get_decision_audit(decision_id)
    if db_rec:
        return _to_schema(db_rec)

    # Check in-memory
    mem_rec = decision_audit_service.get_decision(decision_id)
    if mem_rec:
        return _to_schema(mem_rec)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Decision audit record with ID '{decision_id}' not found.",
    )


@router.get("/summary", response_model=DecisionAuditSummaryResponse)
def get_decision_summary() -> DecisionAuditSummaryResponse:
    """Aggregate corridor-wide decision indices, safety interventions, and trigger statistics."""
    db_summary = db.get_decision_audit_summary()
    if db_summary["total_decisions"] > 0:
        return DecisionAuditSummaryResponse(**db_summary)

    mem_summary = decision_audit_service.get_summary_metrics()
    return DecisionAuditSummaryResponse(**mem_summary)


@router.post("/explain", response_model=ExplainDecisionResponse)
def evaluate_and_explain_decision(req: ExplainDecisionRequest) -> ExplainDecisionResponse:
    """On-the-fly evaluation and explainability generation for specific traffic state & EV kinematics."""
    cfg = PreclearanceConfig()

    # Calculate transition overhead
    t_trans = preclearance_controller.compute_transition_overhead(
        current_phase=req.current_signal_phase,
        phase_elapsed_sec=req.phase_elapsed_sec,
    )

    # Predicted clearance duration
    t_clear = (
        req.predicted_clearance_sec
        if req.predicted_clearance_sec is not None
        else max(2.0, req.queued_vehicle_count * 1.8 + req.queue_length_m * 0.08)
    )

    # Compute trigger delta
    delta = PreclearanceController.compute_trigger_delta(
        ev_eta_sec=req.ev_eta_sec,
        predicted_clearance_sec=t_clear,
        transition_time_sec=t_trans,
        safety_buffer_sec=cfg.safety_buffer_sec,
    )

    should_actuate = delta <= 0.0
    dec_type = (
        DecisionType.PRE_CLEARANCE_TRIGGER if should_actuate else DecisionType.NOMINAL_MAINTAINED
    )
    cmd_phase = cfg.arterial_phase_green if should_actuate else req.current_signal_phase

    narrative = decision_audit_service.generate_narrative(
        decision_type=dec_type,
        node_id=req.node_id,
        vehicle_id=req.vehicle_id,
        ev_eta_sec=req.ev_eta_sec,
        queue_length_m=req.queue_length_m,
        queued_count=req.queued_vehicle_count,
        predicted_clearance_sec=t_clear,
        transition_time_sec=t_trans,
        safety_buffer_sec=cfg.safety_buffer_sec,
        delta_trigger_sec=delta,
    )

    attributions = decision_audit_service.compute_feature_attributions(
        ev_eta_sec=req.ev_eta_sec,
        predicted_clearance_sec=t_clear,
        transition_time_sec=t_trans,
        safety_buffer_sec=cfg.safety_buffer_sec,
        delta_trigger_sec=delta,
        queue_length_m=req.queue_length_m,
    )

    return ExplainDecisionResponse(
        decision_type=str(dec_type),
        should_actuate=should_actuate,
        commanded_phase=cmd_phase,
        delta_trigger_sec=round(delta, 2),
        ev_eta_sec=round(req.ev_eta_sec, 2),
        predicted_clearance_sec=round(t_clear, 2),
        transition_time_sec=round(t_trans, 2),
        safety_buffer_sec=round(cfg.safety_buffer_sec, 2),
        explanation_narrative=narrative,
        feature_attributions=attributions,
        safety_status=str(SafetyStatus.SAFE),
    )
