"""Comprehensive Test Suite for ClearWayAI REST API Endpoints (Task 42).

Tests:
1. Simulation lifecycle (create, list, get, step, stop) with database persistence.
2. Emergency priority missions (dispatch, list, telemetry, multi-node arrival ETAs).
3. AI queue clearance shockwave prediction & Model Registry catalog.
4. Corridor coordination (moving horizon plan, JIT pre-clearance, recovery, MMU safety audit).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from apps.api.src.database import DatabaseManager
from apps.api.src.main import app


@pytest.fixture
def client(tmp_path) -> TestClient:
    """Fixture providing isolated TestClient with clean temporary database."""
    from apps.api.src import database
    from apps.api.src.routers import missions

    temp_db_path = tmp_path / "test_clearway.db"
    test_db = DatabaseManager(db_path=temp_db_path)

    # Monkeypatch singleton db
    original_db = database.db
    database.db = test_db
    from apps.api.src.routers import clearance, corridor, simulations

    simulations.db = test_db
    missions.db = test_db
    clearance.db = test_db
    corridor.db = test_db

    # Reset in-memory runners
    simulations._active_runners.clear()

    with TestClient(app) as test_client:
        yield test_client

    database.db = original_db
    simulations.db = original_db
    missions.db = original_db
    clearance.db = original_db
    corridor.db = original_db


def test_root_and_health_endpoints(client: TestClient) -> None:
    """Verify root and health endpoints return operational contracts."""
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "ClearWayAI API"
    assert "health" in data

    health_resp = client.get("/api/v1/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "healthy"

    status_resp = client.get("/api/v1/system/status")
    assert status_resp.status_code == 200
    s_data = status_resp.json()
    assert s_data["status"] == "operational"
    assert s_data["simulation_only"] is True
    assert s_data["modules"]["simulation"] == "VERIFIED"
    assert s_data["modules"]["ai_clearance"] == "VERIFIED"
    assert s_data["modules"]["traffic_signals"] == "VERIFIED"


def test_simulation_lifecycle(client: TestClient) -> None:
    """Verify simulation episode creation, retrieval, stepping, and stopping."""
    # 1. Create Simulation
    create_payload = {
        "name": "Oak Corridor Test",
        "scenario_id": "normal",
        "use_synthetic_engine": True,
    }
    create_resp = client.post("/api/v1/simulations", json=create_payload)
    assert create_resp.status_code == 201
    sim_data = create_resp.json()
    sim_id = sim_data["simulation_id"]
    assert sim_data["status"] == "RUNNING"
    assert sim_data["name"] == "Oak Corridor Test"

    # 2. List Simulations
    list_resp = client.get("/api/v1/simulations")
    assert list_resp.status_code == 200
    sim_list = list_resp.json()
    assert any(s["simulation_id"] == sim_id for s in sim_list)

    # 3. Get Details
    get_resp = client.get(f"/api/v1/simulations/{sim_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["simulation_id"] == sim_id

    # 4. Advance Step
    step_resp = client.post(
        f"/api/v1/simulations/{sim_id}/step",
        json={"dt": 0.1, "active_mission_id": None},
    )
    assert step_resp.status_code == 200
    step_data = step_resp.json()
    assert step_data["total_steps"] == 1
    assert step_data["sim_time_sec"] > 0.0
    assert "traffic_lights" in step_data

    # 5. Stop Simulation
    stop_resp = client.post(f"/api/v1/simulations/{sim_id}/stop")
    assert stop_resp.status_code == 200
    assert stop_resp.json()["status"] == "STOPPED"
    assert stop_resp.json()["stopped_at"] is not None

    # 6. Not Found Error Handling
    err_resp = client.get("/api/v1/simulations/non-existent-sim-id")
    assert err_resp.status_code == 404


def test_emergency_mission_lifecycle_and_eta(client: TestClient) -> None:
    """Verify emergency mission creation, telemetry updates, and multi-node kinematic ETAs."""
    # 1. Create and dispatch mission
    dispatch_payload = {
        "vehicle_id": "AMB-991",
        "vehicle_type": "emergency_ambulance",
        "origin": "West Feeder Gate",
        "destination": "Metropolitan Trauma Center",
        "target_speed_mps": 18.5,
        "priority_level": 1,
    }
    dispatch_resp = client.post("/api/v1/missions", json=dispatch_payload)
    assert dispatch_resp.status_code == 201
    m_data = dispatch_resp.json()
    m_id = m_data["mission_id"]
    assert m_data["vehicle_id"] == "AMB-991"
    assert m_data["is_active"] is True

    # 2. List Missions
    list_resp = client.get("/api/v1/missions")
    assert list_resp.status_code == 200
    missions = list_resp.json()
    assert any(m["mission_id"] == m_id for m in missions)

    # 3. Get Mission by ID
    get_resp = client.get(f"/api/v1/missions/{m_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["vehicle_id"] == "AMB-991"

    # 4. Multi-node Kinematic ETA Evaluation
    eta_resp = client.get(f"/api/v1/missions/{m_id}/eta?weather=clear")
    assert eta_resp.status_code == 200
    eta_data = eta_resp.json()
    assert eta_data["mission_id"] == m_id
    assert "node_a" in eta_data["etas_by_node"]
    assert "node_d" in eta_data["etas_by_node"]
    assert eta_data["etas_by_node"]["node_a"]["eta_seconds"] > 0.0
    assert eta_data["hospital_eta_sec"] > 0.0

    # 5. Telemetry Update
    telem_resp = client.post(f"/api/v1/missions/{m_id}/telemetry?position_m=-50.0&speed_mps=15.0")
    assert telem_resp.status_code == 200
    updated_m = telem_resp.json()
    assert updated_m["current_position_m"] == -50.0
    assert updated_m["current_speed_kmh"] == 54.0

    # 6. 404 for invalid mission
    err_resp = client.get("/api/v1/missions/non-existent-mission")
    assert err_resp.status_code == 404


def test_clearance_prediction_and_registry_catalog(client: TestClient) -> None:
    """Verify AI clearance prediction endpoint and Model Registry catalog discovery."""
    # 1. Prediction request
    pred_payload = {
        "node_id": "node_b",
        "approach_id": "EB",
        "queue_length_meters": 30.0,
        "queued_vehicle_count": 10,
        "vehicle_count": 15,
        "motorcycle_ratio": 0.60,
        "approach_occupancy_ratio": 0.40,
        "weather": "clear",
    }
    pred_resp = client.post("/api/v1/clearance/predict", json=pred_payload)
    assert pred_resp.status_code == 200
    pred_data = pred_resp.json()
    assert pred_data["node_id"] == "node_b"
    assert pred_data["predicted_clearance_sec"] > 0.0
    assert pred_data["confidence_score"] >= 0.50
    assert pred_data["model_name"] != ""
    assert "fallback_tier" in pred_data

    # 2. Registry Catalog
    reg_resp = client.get("/api/v1/clearance/registry")
    assert reg_resp.status_code == 200
    reg_data = reg_resp.json()
    assert reg_data["registry_version"] == "1.0.0"
    assert "gradient_boosting" in reg_data["champion_tabular"]
    assert "clearance_gru" in reg_data["champion_sequential"]
    assert len(reg_data["models"]) >= 2


def test_corridor_coordination_and_safety_audit(client: TestClient) -> None:
    """Verify corridor moving horizon plan, JIT preclearance, recovery, and MMU safety audit."""
    # 1. Moving Horizon Coordination Plan
    plan_resp = client.get("/api/v1/corridor/plan?sim_time=10.0&weather=clear")
    assert plan_resp.status_code == 200
    plan_data = plan_resp.json()
    assert "commanded_phases" in plan_data
    assert "node_a" in plan_data["commanded_phases"]

    # 2. JIT Preclearance Evaluation
    preclear_payload = {
        "node_id": "node_a",
        "queue_length_meters": 25.0,
        "queued_vehicle_count": 8,
        "sim_time": 15.0,
    }
    preclear_resp = client.post("/api/v1/corridor/preclearance/evaluate", json=preclear_payload)
    assert preclear_resp.status_code == 200
    preclear_data = preclear_resp.json()
    assert preclear_data["node_id"] == "node_a"
    assert preclear_data["commanded_phase"] in [0, 1, 2, 3, 4, 5]
    assert preclear_data["predicted_clearance_sec"] >= 0.0

    # 3. Post-Clearance Smooth Recovery Initiation
    recovery_payload = {
        "node_id": "node_a",
        "preemption_duration_sec": 30.0,
        "cross_queue_meters": 35.0,
        "sim_time": 45.0,
    }
    rec_resp = client.post("/api/v1/corridor/recovery/initiate", json=recovery_payload)
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    assert rec_data["node_id"] == "node_a"
    assert rec_data["initial_green_debt_sec"] > 0.0
    assert rec_data["current_recovery_cycle"] == 1
    assert rec_data["commanded_phase"] in [0, 1, 2, 3, 4, 5]

    # 4. MMU Signal Safety Gateway Audit
    audit_resp = client.get("/api/v1/corridor/safety/audit?sim_time=50.0")
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()
    assert audit_data["all_nodes_safe"] is True
    assert "node_a" in audit_data["sanitized_phases"]
    assert audit_data["provenance"] == "INDEPENDENT_SIGNAL_SAFETY_GATEWAY"
