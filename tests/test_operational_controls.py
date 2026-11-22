"""Verification test suite for Task 19: Interactive Operational Controls, Mission Drawer & Unified Inspector."""

import os

WEB_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "web", "src"))
SHARED_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages", "shared", "src"))


def test_operational_control_files_exist():
    """Verify that SimulationControls, MissionDrawer, and UnifiedInspector exist."""
    sim_path = os.path.join(WEB_SRC, "features", "operations", "SimulationControls.tsx")
    mission_path = os.path.join(WEB_SRC, "features", "operations", "MissionDrawer.tsx")
    inspector_path = os.path.join(WEB_SRC, "features", "operations", "UnifiedInspector.tsx")

    assert os.path.exists(sim_path), f"File {sim_path} must exist!"
    assert os.path.exists(mission_path), f"File {mission_path} must exist!"
    assert os.path.exists(inspector_path), f"File {inspector_path} must exist!"


def test_dashboard_page_integrates_controls_and_drawers():
    """Verify DashboardPage mounts SimulationControls, MissionDrawer, and UnifiedInspector."""
    page_path = os.path.join(WEB_SRC, "pages", "DashboardPage.tsx")
    with open(page_path, encoding="utf-8") as f:
        content = f.read()

    assert "SimulationControls" in content
    assert "MissionDrawer" in content
    assert "UnifiedInspector" in content
    assert "isMissionDrawerOpen" in content
    assert "isInspectorOpen" in content


def test_simulation_controls_playback_and_scenarios():
    """Verify SimulationControls supports play/pause, step, reset, speed multipliers, and scenarios."""
    sim_path = os.path.join(WEB_SRC, "features", "operations", "SimulationControls.tsx")
    with open(sim_path, encoding="utf-8") as f:
        content = f.read()

    # Playback controls
    assert "handlePlayToggle" in content or "PAUSE" in content
    assert "handleStep" in content or "Step" in content
    assert "handleReset" in content or "Reset" in content
    assert "speedMultiplier" in content

    # Scenarios
    assert "amb_emergency" in content
    assert "normal_mixed" in content
    assert "peak_congestion" in content
    assert "adverse_weather" in content


def test_mission_drawer_corridor_and_telemetry():
    """Verify MissionDrawer has AMB-339 telemetry, ETA countdown, 4-node chain, and preemption."""
    mission_path = os.path.join(WEB_SRC, "features", "operations", "MissionDrawer.tsx")
    with open(mission_path, encoding="utf-8") as f:
        content = f.read()

    # Ambulance & target
    assert "AMB-339" in content
    assert "Metropolitan General Hospital" in content
    assert "etaSeconds" in content
    assert "speedKmh" in content

    # 4-Node chain
    assert "INT-0455" in content
    assert "INT-0456" in content
    assert "INT-0457" in content
    assert "INT-0458" in content

    # Preemption controls
    assert "DISENGAGE CORRIDOR PRE-EMPTION" in content or "ENGAGE CORRIDOR PRE-EMPTION" in content
    assert "DEMO_FIXTURE" in content


def test_unified_inspector_tabs_and_actions():
    """Verify UnifiedInspector supports multi-entity tabs, ping diagnostics, and telemetry export."""
    inspector_path = os.path.join(WEB_SRC, "features", "operations", "UnifiedInspector.tsx")
    with open(inspector_path, encoding="utf-8") as f:
        content = f.read()

    # 4 entity tabs
    assert "vehicles" in content
    assert "signals" in content
    assert "sensors" in content
    assert "intersection" in content

    # Diagnostics and actions
    assert "handlePing" in content or "Ping Entity" in content
    assert "handleExportJson" in content
    assert "Track Camera" in content


def test_zero_static_fake_assets():
    """Verify no raster mock images are used."""
    for fn in ["SimulationControls.tsx", "MissionDrawer.tsx", "UnifiedInspector.tsx"]:
        fp = os.path.join(WEB_SRC, "features", "operations", fn)
        with open(fp, encoding="utf-8") as f:
            content = f.read()
        assert "dashboard-target.png" not in content
        assert "placeholder.png" not in content

