"""Comprehensive Test Suite for Explainable AI Decision Telemetry & Audit Trails (Task 49).

Verifies:
1. Deterministic narrative generation and feature attribution calculation.
2. Anti-starvation aborts and MMU safety override handling.
3. Database persistence, index querying, and summary metric aggregation.
4. FastAPI REST API endpoints:
   - GET /api/v1/audit/decisions
   - GET /api/v1/audit/decisions/{decision_id}
   - GET /api/v1/audit/summary
   - POST /api/v1/audit/explain
5. Preclearance evaluation audit integration in corridor router.
6. Frontend DecisionAuditDrawer component structure and contract compliance.
"""

from __future__ import annotations

import os

import pytest
from fastapi import HTTPException

from apps.api.src.database import DatabaseManager, DecisionAuditLogRecord
from apps.api.src.main import app
from apps.api.src.routers import audit, corridor
from apps.api.src.schemas import (
    ExplainDecisionRequest,
    PreclearanceEvaluateRequest,
)
from controller.audit.decision_audit import (
    DecisionAuditRecord,
    DecisionType,
    ExplainableDecisionAuditService,
    SafetyStatus,
    decision_audit_service,
)


def test_decision_audit_service_narrative_and_attributions():
    """Verify ExplainableDecisionAuditService generates exact narratives and mathematical feature attributions."""
    service = ExplainableDecisionAuditService(max_in_memory=100)
    service.clear()

    rec = service.record_decision(
        node_id="node_a",
        decision_type=DecisionType.PRE_CLEARANCE_TRIGGER,
        commanded_phase=0,
        previous_phase=3,
        sim_time_sec=14.2,
        mission_id="EM-2026-088",
        vehicle_id="AMB-339",
        ev_eta_sec=22.5,
        queue_length_m=35.0,
        queued_vehicle_count=8,
        predicted_clearance_sec=14.5,
        transition_time_sec=5.0,
        safety_buffer_sec=2.0,
        delta_trigger_sec=-1.0,
        confidence_score=0.985,
    )

    assert isinstance(rec, DecisionAuditRecord)
    assert rec.node_id == "node_a"
    assert rec.decision_type == DecisionType.PRE_CLEARANCE_TRIGGER
    assert rec.commanded_phase == 0
    assert rec.previous_phase == 3
    assert rec.vehicle_id == "AMB-339"

    # Narrative verification
    assert "Actuated pre-clearance green phase at node_a" in rec.explanation_narrative
    assert "AMB-339 ETA is 22.5s" in rec.explanation_narrative
    assert "Trigger delta Δt is -1.0s (<= 0)" in rec.explanation_narrative

    # Mathematical feature attributions verification
    attribs = rec.feature_attributions
    assert "delta_margin_sec" in attribs
    assert "ev_eta_sec" in attribs
    assert "queue_clearance_demand_sec" in attribs
    assert "transition_overhead_sec" in attribs
    assert "safety_buffer_sec" in attribs
    assert attribs["delta_margin_sec"] == -1.0
    assert attribs["ev_eta_sec"] == 22.5
    assert attribs["queue_clearance_demand_sec"] == 14.5
    assert attribs["transition_overhead_sec"] == 5.0
    assert attribs["safety_buffer_sec"] == 2.0


def test_anti_starvation_and_safety_interventions():
    """Verify narrative synthesis for anti-starvation aborts and MMU safety overrides."""
    service = ExplainableDecisionAuditService(max_in_memory=50)

    # Watchdog abort
    abort_rec = service.record_decision(
        node_id="node_b",
        decision_type=DecisionType.ANTI_STARVATION_ABORT,
        commanded_phase=3,
        sim_time_sec=65.0,
        safety_status=SafetyStatus.WATCHDOG_TRIPPED,
        hold_duration_sec=61.2,
        max_hold_sec=60.0,
    )
    assert "Watchdog anti-starvation limit tripped at node_b" in abort_rec.explanation_narrative
    assert abort_rec.safety_status == SafetyStatus.WATCHDOG_TRIPPED

    # MMU intervention
    mmu_rec = service.record_decision(
        node_id="node_c",
        decision_type=DecisionType.MMU_SAFETY_OVERRIDE,
        commanded_phase=2,  # All-Red
        sim_time_sec=70.0,
        safety_status=SafetyStatus.OVERRIDDEN_BY_MMU,
        override_reason="Conflicting vehicular green on East-West approach",
    )
    assert (
        "Conflict Monitor Unit (MMU) Gateway intervened at node_c" in mmu_rec.explanation_narrative
    )
    assert mmu_rec.safety_status == SafetyStatus.OVERRIDDEN_BY_MMU


def test_database_persistence_and_queries(tmp_path):
    """Verify SQLite database persistence, query filters, and summary calculations."""
    db_file = str(tmp_path / "test_audit.db")
    test_db = DatabaseManager(db_file)

    rec1 = DecisionAuditLogRecord(
        decision_id="dec-test-01",
        timestamp=100.0,
        sim_time_sec=10.0,
        node_id="node_a",
        decision_type="PRE_CLEARANCE_TRIGGER",
        commanded_phase=0,
        previous_phase=3,
        mission_id="m1",
        vehicle_id="AMB-339",
        ev_eta_sec=20.0,
        queue_length_m=30.0,
        queued_vehicle_count=6,
        predicted_clearance_sec=12.0,
        transition_time_sec=5.0,
        safety_buffer_sec=2.0,
        delta_trigger_sec=-1.0,
        confidence_score=0.99,
        model_name="gradient_boosting_champion",
        explanation_narrative="Test trigger narrative",
        feature_attributions_json='{"delta_margin_sec": -1.0}',
        safety_status="SAFE",
    )
    rec2 = DecisionAuditLogRecord(
        decision_id="dec-test-02",
        timestamp=110.0,
        sim_time_sec=20.0,
        node_id="node_b",
        decision_type="GREEN_HOLD_EXTENDED",
        commanded_phase=0,
        previous_phase=0,
        mission_id="m1",
        vehicle_id="AMB-339",
        ev_eta_sec=15.0,
        queue_length_m=10.0,
        queued_vehicle_count=2,
        predicted_clearance_sec=4.0,
        transition_time_sec=0.0,
        safety_buffer_sec=2.0,
        delta_trigger_sec=-9.0,
        confidence_score=0.98,
        model_name="gradient_boosting_champion",
        explanation_narrative="Test green hold narrative",
        feature_attributions_json='{"delta_margin_sec": -9.0}',
        safety_status="SAFE",
    )

    test_db.log_decision_audit(rec1)
    test_db.log_decision_audit(rec2)

    # Retrieval by ID
    fetched = test_db.get_decision_audit("dec-test-01")
    assert fetched is not None
    assert fetched.node_id == "node_a"
    assert fetched.to_dict()["feature_attributions"] == {"delta_margin_sec": -1.0}

    # Query with node filter
    node_b_list = test_db.query_decision_audits(node_id="node_b")
    assert len(node_b_list) == 1
    assert node_b_list[0].decision_id == "dec-test-02"

    # Query with decision_type filter
    trigger_list = test_db.query_decision_audits(decision_type="PRE_CLEARANCE_TRIGGER")
    assert len(trigger_list) == 1
    assert trigger_list[0].decision_id == "dec-test-01"

    # Summary metrics
    summary = test_db.get_decision_audit_summary()
    assert summary["total_decisions"] == 2
    assert summary["preemption_triggers"] == 1
    assert summary["green_holds"] == 1
    assert summary["safe_ratio"] == 1.0


def test_fastapi_audit_endpoints():
    """Verify REST API audit endpoints registration and function handlers in FastAPI."""
    paths = app.openapi()["paths"]
    assert "/api/v1/audit/decisions" in paths
    assert "get" in paths["/api/v1/audit/decisions"]
    assert "/api/v1/audit/decisions/{decision_id}" in paths
    assert "get" in paths["/api/v1/audit/decisions/{decision_id}"]
    assert "/api/v1/audit/summary" in paths
    assert "get" in paths["/api/v1/audit/summary"]
    assert "/api/v1/audit/explain" in paths
    assert "post" in paths["/api/v1/audit/explain"]

    # Seed in-memory service
    rec = decision_audit_service.record_decision(
        node_id="node_a",
        decision_type=DecisionType.PRE_CLEARANCE_TRIGGER,
        commanded_phase=0,
        previous_phase=3,
        sim_time_sec=15.0,
        mission_id="EM-2026-088",
        vehicle_id="AMB-339",
        ev_eta_sec=22.0,
        queue_length_m=35.0,
        queued_vehicle_count=8,
        predicted_clearance_sec=14.0,
        transition_time_sec=5.0,
        safety_buffer_sec=2.0,
        delta_trigger_sec=-1.0,
        confidence_score=0.99,
    )

    # 1. list_decisions
    resp = audit.list_decisions(limit=10)
    assert resp.total_count >= 1
    assert len(resp.decisions) >= 1

    # 2. get_decision
    single = audit.get_decision(rec.decision_id)
    assert single.decision_id == rec.decision_id
    assert single.node_id == "node_a"

    # 3. get_decision non-existent -> 404
    with pytest.raises(HTTPException) as exc_info:
        audit.get_decision("non-existent-dec-999")
    assert exc_info.value.status_code == 404

    # 4. get_decision_summary
    summary = audit.get_decision_summary()
    assert summary.total_decisions >= 1
    assert summary.safe_ratio == 1.0

    # 5. evaluate_and_explain_decision
    explain_req = ExplainDecisionRequest(
        node_id="node_a",
        ev_eta_sec=21.0,
        queue_length_m=30.0,
        queued_vehicle_count=8,
        predicted_clearance_sec=14.4,
        current_signal_phase=3,
        phase_elapsed_sec=15.0,
        vehicle_id="AMB-339",
        sim_time_sec=12.0,
    )
    exp = audit.evaluate_and_explain_decision(explain_req)
    assert exp.should_actuate is True
    assert exp.decision_type == "PRE_CLEARANCE_TRIGGER"
    assert exp.commanded_phase == 0
    assert exp.delta_trigger_sec <= 0.0
    assert "explanation_narrative" in exp.model_dump()
    assert "feature_attributions" in exp.model_dump()


def test_corridor_preclearance_audit_integration():
    """Verify that evaluating preclearance in corridor router logs an explainable audit record."""
    eval_req = PreclearanceEvaluateRequest(
        node_id="node_a",
        mission_id="test-corridor-audit-mission",
        queue_length_meters=25.0,
        queued_vehicle_count=6,
        sim_time=18.5,
    )

    resp = corridor.evaluate_preclearance(eval_req)
    assert resp.node_id == "node_a"

    # Verify decision recorded in audit service
    history = decision_audit_service.query_decisions(node_id="node_a")
    assert len(history) >= 1
    assert any(h.node_id == "node_a" for h in history)


def test_frontend_decision_audit_drawer_structure():
    """Verify frontend DecisionAuditDrawer component structure and exported contracts."""
    drawer_file = os.path.join(
        "apps", "web", "src", "features", "operations", "DecisionAuditDrawer.tsx"
    )
    assert os.path.exists(drawer_file), f"{drawer_file} must exist"

    with open(drawer_file, encoding="utf-8") as f:
        content = f.read()

    assert "AI DECISION AUDIT & EXPLAINABILITY" in content
    assert "WHY AI MADE THIS DECISION" in content
    assert "MATHEMATICAL PRE-CLEARANCE PROOF" in content
    assert "FEATURE ATTRIBUTION WEIGHTS" in content
    assert "NEMA TS2 AUDITED" in content
    assert "StatusPill" in content
    assert "fetchDecisionAudits" in content
