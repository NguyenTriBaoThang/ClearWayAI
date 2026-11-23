"""Comprehensive Test Suite for ClearWayAI REST API Endpoints (Task 42).

Verifies:
1. Route registration and HTTP method binding in FastAPI app.
2. Simulation lifecycle (create, list, get, step, stop) with database persistence.
3. Emergency priority missions (dispatch, list, telemetry, multi-node arrival ETAs).
4. AI queue clearance shockwave prediction & Model Registry catalog.
5. Corridor coordination (moving horizon plan, JIT pre-clearance, recovery, MMU safety audit).
6. Exception and boundary handling (HTTP 404, invalid IDs).
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from apps.api.src.database import DatabaseManager
from apps.api.src.main import app
from apps.api.src.routers import clearance, corridor, missions, replay, simulations
from apps.api.src.schemas import (
    ClearancePredictRequest,
    MissionCreateRequest,
    PreclearanceEvaluateRequest,
    RecoveryInitiateRequest,
    SimulationCreateRequest,
    SimulationStepRequest,
)


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    """Provide isolated SQLite database for each test run."""
    from apps.api.src import database

    temp_db_path = tmp_path / "test_clearway.db"
    test_db = DatabaseManager(db_path=temp_db_path)

    orig_db = database.db
    database.db = test_db
    simulations.db = test_db
    missions.db = test_db
    clearance.db = test_db
    corridor.db = test_db
    replay.db = test_db

    # Clean in-memory runners & replays
    simulations._active_runners.clear()
    replay._active_replays.clear()

    yield test_db

    database.db = orig_db
    simulations.db = orig_db
    missions.db = orig_db
    clearance.db = orig_db
    corridor.db = orig_db
    replay.db = orig_db


def test_routes_registered_in_app() -> None:
    """Verify all REST API router paths and methods are mounted in FastAPI application."""
    paths = app.openapi()["paths"]

    # Core endpoints
    assert "/health" in paths
    assert "/api/v1/system/status" in paths

    # Simulation router
    assert "/api/v1/simulations" in paths
    assert "post" in paths["/api/v1/simulations"]
    assert "get" in paths["/api/v1/simulations"]
    assert "/api/v1/simulations/{simulation_id}" in paths
    assert "/api/v1/simulations/{simulation_id}/step" in paths
    assert "/api/v1/simulations/{simulation_id}/stop" in paths

    # Mission router
    assert "/api/v1/missions" in paths
    assert "post" in paths["/api/v1/missions"]
    assert "get" in paths["/api/v1/missions"]
    assert "/api/v1/missions/{mission_id}" in paths
    assert "/api/v1/missions/{mission_id}/eta" in paths
    assert "/api/v1/missions/{mission_id}/telemetry" in paths

    # Clearance router
    assert "/api/v1/clearance/predict" in paths
    assert "post" in paths["/api/v1/clearance/predict"]
    assert "/api/v1/clearance/registry" in paths
    assert "get" in paths["/api/v1/clearance/registry"]

    # Corridor router
    assert "/api/v1/corridor/plan" in paths
    assert "/api/v1/corridor/preclearance/evaluate" in paths
    assert "/api/v1/corridor/recovery/initiate" in paths
    assert "/api/v1/corridor/safety/audit" in paths

    # Replay & Snapshots router
    assert "/api/v1/simulations/{simulation_id}/replay/load" in paths
    assert "/api/v1/simulations/{simulation_id}/replay/play" in paths
    assert "/api/v1/simulations/{simulation_id}/replay/pause" in paths
    assert "/api/v1/simulations/{simulation_id}/replay/seek" in paths
    assert "/api/v1/simulations/{simulation_id}/replay/speed" in paths
    assert "/api/v1/simulations/{simulation_id}/replay/step" in paths
    assert "/api/v1/simulations/{simulation_id}/replay/status" in paths
    assert "/api/v1/simulations/{simulation_id}/snapshots" in paths


def test_simulation_lifecycle() -> None:
    """Verify simulation episode creation, retrieval, stepping, and stopping."""
    # 1. Create Simulation
    req = SimulationCreateRequest(
        name="Oak Corridor Unit Test",
        scenario_id="normal",
        use_synthetic_engine=True,
    )
    sim = simulations.create_simulation(req)
    assert sim.status == "RUNNING"
    assert sim.name == "Oak Corridor Unit Test"
    sim_id = sim.simulation_id

    # 2. List Simulations
    all_sims = simulations.list_simulations()
    assert any(s.simulation_id == sim_id for s in all_sims)

    # 3. Get Details
    fetched = simulations.get_simulation(sim_id)
    assert fetched.simulation_id == sim_id

    # 4. Advance Step
    step_resp = simulations.step_simulation(sim_id, SimulationStepRequest(dt=0.1))
    assert step_resp.total_steps == 1
    assert step_resp.sim_time_sec > 0.0
    assert "node_a" in step_resp.traffic_lights

    # 5. Stop Simulation
    stopped = simulations.stop_simulation(sim_id)
    assert stopped.status == "STOPPED"
    assert stopped.stopped_at is not None

    # 6. Not Found Error Handling
    with pytest.raises(HTTPException) as exc_info:
        simulations.get_simulation("non-existent-sim-id")
    assert exc_info.value.status_code == 404


def test_emergency_mission_lifecycle_and_eta() -> None:
    """Verify emergency mission creation, telemetry updates, and multi-node kinematic ETAs."""
    # 1. Create and dispatch mission
    m_req = MissionCreateRequest(
        vehicle_id="AMB-991",
        vehicle_type="emergency_ambulance",
        origin="West Feeder Gate",
        destination="Metropolitan Trauma Center",
        target_speed_mps=18.5,
        priority_level=1,
    )
    m = missions.create_and_dispatch_mission(m_req)
    assert m.vehicle_id == "AMB-991"
    assert m.is_active is True
    m_id = m.mission_id

    # 2. List Missions
    all_missions = missions.list_missions()
    assert any(item.mission_id == m_id for item in all_missions)

    # 3. Get Mission by ID
    fetched_m = missions.get_mission(m_id)
    assert fetched_m.mission_id == m_id

    # 4. Multi-node Kinematic ETA Evaluation
    eta_report = missions.get_mission_eta(m_id, weather="clear")
    assert eta_report.mission_id == m_id
    assert "node_a" in eta_report.etas_by_node
    assert "node_d" in eta_report.etas_by_node
    assert eta_report.etas_by_node["node_a"].eta_seconds > 0.0
    assert eta_report.hospital_eta_sec > 0.0

    # 5. Telemetry Update
    updated_m = missions.update_mission_telemetry(
        mission_id=m_id,
        position_m=-50.0,
        speed_mps=15.0,
    )
    assert updated_m.current_position_m == -50.0
    assert updated_m.current_speed_kmh == 54.0

    # 6. 404 for invalid mission
    with pytest.raises(HTTPException) as exc_info:
        missions.get_mission("non-existent-mission")
    assert exc_info.value.status_code == 404


def test_clearance_prediction_and_registry_catalog() -> None:
    """Verify AI clearance prediction endpoint and Model Registry catalog discovery."""
    # 1. Prediction request
    pred_req = ClearancePredictRequest(
        node_id="node_b",
        approach_id="EB",
        queue_length_meters=30.0,
        queued_vehicle_count=10,
        vehicle_count=15,
        motorcycle_ratio=0.60,
        approach_occupancy_ratio=0.40,
        weather="clear",
    )
    pred_res = clearance.predict_queue_clearance(pred_req)
    assert pred_res.node_id == "node_b"
    assert pred_res.predicted_clearance_sec > 0.0
    assert pred_res.confidence_score >= 0.50
    assert pred_res.model_name != ""
    assert pred_res.fallback_tier in [
        "TIER_0_AI",
        "TIER_1_KINEMATIC_PHYSICS",
        "TIER_2_CONSERVATIVE_DEFAULT",
    ]

    # 2. Registry Catalog
    catalog = clearance.get_model_registry_catalog()
    assert catalog.registry_version == "1.0.0"
    assert "gradient_boosting" in catalog.champion_tabular
    assert "clearance_gru" in catalog.champion_sequential
    assert len(catalog.models) >= 2


def test_corridor_coordination_and_safety_audit() -> None:
    """Verify corridor moving horizon plan, JIT preclearance, recovery, and MMU safety audit."""
    # 1. Moving Horizon Coordination Plan
    plan = corridor.get_corridor_coordination_plan(sim_time=10.0, weather="clear")
    assert "node_a" in plan.commanded_phases
    assert plan.provenance == "MOVING_HORIZON_CORRIDOR_COORDINATOR"

    # 2. JIT Preclearance Evaluation
    preclear_req = PreclearanceEvaluateRequest(
        node_id="node_a",
        queue_length_meters=25.0,
        queued_vehicle_count=8,
        sim_time=15.0,
    )
    decision = corridor.evaluate_preclearance(preclear_req)
    assert decision.node_id == "node_a"
    assert decision.commanded_phase in [0, 1, 2, 3, 4, 5]
    assert decision.predicted_clearance_sec >= 0.0

    # 3. Post-Clearance Smooth Recovery Initiation
    rec_req = RecoveryInitiateRequest(
        node_id="node_a",
        preemption_duration_sec=30.0,
        cross_queue_meters=35.0,
        sim_time=45.0,
    )
    recovery = corridor.initiate_recovery(rec_req)
    assert recovery.node_id == "node_a"
    assert recovery.initial_green_debt_sec > 0.0
    assert recovery.current_recovery_cycle == 1
    assert recovery.commanded_phase in [0, 1, 2, 3, 4, 5]

    # 4. MMU Signal Safety Gateway Audit
    audit = corridor.audit_corridor_safety(sim_time=50.0)
    assert audit.all_nodes_safe is True
    assert "node_a" in audit.sanitized_phases
    assert audit.provenance == "INDEPENDENT_SIGNAL_SAFETY_GATEWAY"
