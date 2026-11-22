"""Tests for API health endpoints."""

from apps.api.src.main import app


def test_health_route_registered():
    """Verify GET /health is registered in FastAPI routes."""
    routes = {r.path: r for r in app.routes if hasattr(r, "methods")}
    assert "/health" in routes
    assert "GET" in routes["/health"].methods


def test_health_endpoint_response():
    """Verify /health endpoint returns valid HealthResponse."""
    routes = {r.path: r for r in app.routes if hasattr(r, "methods")}
    endpoint = routes["/health"].endpoint
    response = endpoint()

    assert response.status == "healthy"
    assert response.service == "clearway-api"
    assert response.version == "0.1.0"
    assert response.environment in ["development", "production", "test"]
    assert response.timestamp is not None


def test_api_v1_health_alias():
    """Verify GET /api/v1/health is registered and consistent."""
    routes = {r.path: r for r in app.routes if hasattr(r, "methods")}
    assert "/api/v1/health" in routes
    assert "GET" in routes["/api/v1/health"].methods

    endpoint = routes["/api/v1/health"].endpoint
    response = endpoint()
    assert response.status == "healthy"
