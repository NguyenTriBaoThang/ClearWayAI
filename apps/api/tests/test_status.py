"""Tests for API system status endpoint."""

from apps.api.src.main import app


def test_system_status_route_registered():
    """Verify GET /api/v1/system/status is registered."""
    routes = {r.path: r for r in app.routes if hasattr(r, "methods")}
    assert "/api/v1/system/status" in routes
    assert "GET" in routes["/api/v1/system/status"].methods


def test_system_status_adheres_to_safety_boundaries():
    """Verify system status strictly adheres to safety modes and provenance."""
    routes = {r.path: r for r in app.routes if hasattr(r, "methods")}
    endpoint = routes["/api/v1/system/status"].endpoint
    status_resp = endpoint()

    # Core operational status
    assert status_resp.status == "operational"
    assert status_resp.mode == "SIMULATION"

    # Strict Safety Invariants
    assert status_resp.simulation_only is True
    assert status_resp.public_signal_control_permitted is False
    assert status_resp.data_provenance in ["DEMO_FIXTURE", "SUMO_SIMULATED"]

    # Modules verification
    modules = status_resp.modules
    assert modules.simulation in ["PLANNED", "IN_PROGRESS", "IMPLEMENTED", "VERIFIED"]
    assert modules.ai_clearance in ["PLANNED", "IN_PROGRESS", "IMPLEMENTED", "VERIFIED"]
    assert modules.traffic_signals in ["PLANNED", "IN_PROGRESS", "IMPLEMENTED", "VERIFIED"]
    assert modules.digital_twin in ["PLANNED", "IN_PROGRESS", "IMPLEMENTED", "VERIFIED"]
    assert modules.v2x_telemetry in ["UNAVAILABLE", "SIMULATED", "CONNECTED"]
