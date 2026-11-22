"""Verification test for Task 06: Operations Dashboard UI Layout & Blueprint Adherence."""

import os

WEB_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "web", "src"))


def test_dashboard_reusable_components_exist():
    """Verify that all core design tokens and reusable layout components are defined."""
    expected_components = [
        "components/PanelFrame.tsx",
        "components/StatusPill.tsx",
        "components/KpiTile.tsx",
        "components/LoadingSkeleton.tsx",
        "components/EmptyState.tsx",
        "components/DisconnectedBanner.tsx",
    ]
    for comp in expected_components:
        full_path = os.path.join(WEB_SRC, comp)
        assert os.path.exists(full_path), f"Component {comp} must exist in apps/web/src!"


def test_topbar_structure_and_provenance():
    """Verify TopBar has brand, provenance gate, simulation time, and emergency corridor status."""
    topbar_path = os.path.join(WEB_SRC, "layout", "TopBar.tsx")
    assert os.path.exists(topbar_path)
    with open(topbar_path, encoding="utf-8") as f:
        content = f.read()

    assert "CLEARWAY AI" in content
    assert "DIGITAL TWIN OPS" in content
    assert "SIMULATION ONLY" in content
    assert "DEMO FIXTURE" in content
    assert "AMB-339" in content
    assert "INT-0457" in content


def test_sidebar_structure_and_safety_locks():
    """Verify Sidebar navigation has active links and safety interlock indicators."""
    sidebar_path = os.path.join(WEB_SRC, "layout", "Sidebar.tsx")
    assert os.path.exists(sidebar_path)
    with open(sidebar_path, encoding="utf-8") as f:
        content = f.read()

    assert "/dashboard" in content
    assert "/digital-twin" in content
    assert "/simulation" in content
    assert "/experiments" in content
    assert "Safety Interlock" in content


def test_dashboard_page_panels_and_proportions():
    """Verify DashboardPage renders all 5 required operational panels around the 3D viewport."""
    page_path = os.path.join(WEB_SRC, "pages", "DashboardPage.tsx")
    assert os.path.exists(page_path)
    with open(page_path, encoding="utf-8") as f:
        content = f.read()

    assert "V2XHardwareCard" in content
    assert "PhaseTimingCard" in content
    assert "AdaptiveSignalCard" in content
    assert "DigitalTwinCanvas" in content
    assert "IoTSensorsCard" in content
    assert "AnalyticsCard" in content
    assert "dashboard-grid-top" in content
    assert "dashboard-grid-bottom" in content


def test_threejs_canvas_has_floating_hud_without_pointer_blocking():
    """Verify DigitalTwinCanvas includes WebGL canvas, HUD overlays, and pointerEvents='none' container."""
    canvas_path = os.path.join(WEB_SRC, "features", "digital-twin", "DigitalTwinCanvas.tsx")
    assert os.path.exists(canvas_path)
    with open(canvas_path, encoding="utf-8") as f:
        content = f.read()

    # Must initialize true Three.js and scene modules
    assert "THREE.WebGLRenderer" in content
    assert "SceneController" in content
    assert "SceneEnvironment" in content

    # Must contain floating HUD layers
    assert "pointerEvents: 'none'" in content or 'pointerEvents: "none"' in content
    assert "ISO" in content
    assert "TOP" in content
    assert "CHASE" in content
    assert "AMB-339" in content
    assert "Safety Interlock ACTIVE" in content

    # Must never import dashboard-target.png as scene texture
    assert "dashboard-target.png" not in content, "Canvas must NEVER fake 3D with the target image!"


def test_css_variables_and_responsive_grids():
    """Verify index.css contains blueprint color tokens and responsive grid rules."""
    css_path = os.path.join(WEB_SRC, "index.css")
    assert os.path.exists(css_path)
    with open(css_path, encoding="utf-8") as f:
        content = f.read()

    assert "--bg-main: #070d1e;" in content
    assert "--accent-cyan: #00e5ff;" in content
    assert "--accent-green: #06d6a0;" in content
    assert "--accent-yellow: #ffd166;" in content
    assert "--accent-red: #ef476f;" in content
    assert ".dashboard-grid-top" in content
    assert ".dashboard-grid-bottom" in content
