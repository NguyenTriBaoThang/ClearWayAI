"""Root smoke tests for ClearWayAI repository."""

import sys
import os

# Add apps/api/src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "api", "src")))

from apps.api.src.main import app, root, health_check


def test_api_root_endpoint():
    """Smoke test root service discovery endpoint."""
    res = root()
    assert res["service"] == "ClearWayAI API"
    assert res["safety_mode"] == "SIMULATION"
    assert res["provenance"] == "DEMO_FIXTURE"


def test_api_smoke_health():
    """Smoke test health endpoint."""
    res = health_check()
    assert res.status == "healthy"
    assert res.service == "clearway-api"


def test_reference_image_exists():
    """Ensure assets/reference/dashboard-target.png is present and has proper size."""
    ref_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "reference", "dashboard-target.png"))
    assert os.path.exists(ref_path), "assets/reference/dashboard-target.png must exist!"
    assert os.path.getsize(ref_path) > 100000, "assets/reference/dashboard-target.png must not be empty!"
