"""Automated verification test for Task 07: Three.js Interactive 3D Canvas & Isometric Perspective."""

import os

DIGITAL_TWIN_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "apps", "web", "src", "features", "digital-twin")
)


def test_digital_twin_modules_exist():
    """Verify all core 3D scene modules exist."""
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "DigitalTwinCanvas.tsx"))
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "SceneController.ts"))
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "SceneEnvironment.ts"))


def test_scene_environment_lighting_and_pedestal():
    """Verify SceneEnvironment defines cyberpunk lighting rigs, dual-tier grid, and pedestal."""
    env_path = os.path.join(DIGITAL_TWIN_DIR, "SceneEnvironment.ts")
    with open(env_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Lighting verification
    assert "THREE.AmbientLight" in content
    assert "THREE.DirectionalLight" in content
    assert "0x00f5d4" in content  # Key light cyan/teal
    assert "0xffd166" in content  # Fill light warm amber
    assert "0x00e5ff" in content  # Cyber cyan accent

    # Grid & platform verification
    assert "THREE.GridHelper" in content
    assert "RoadNetworkMesh" in content
    assert "setupCardinalMarkers" in content
    assert "setupCorridorRibbon" in content


def test_scene_controller_orbitcontrols_and_cameras():
    """Verify SceneController supports dual cameras, OrbitControls, and bounded pitch."""
    ctrl_path = os.path.join(DIGITAL_TWIN_DIR, "SceneController.ts")
    with open(ctrl_path, "r", encoding="utf-8") as f:
        content = f.read()

    # OrbitControls & Cameras
    assert "OrbitControls" in content
    assert "THREE.PerspectiveCamera" in content
    assert "THREE.OrthographicCamera" in content

    # Boundary protection (no clipping underground)
    assert "maxPolarAngle" in content
    assert "minDistance" in content
    assert "maxDistance" in content
    assert "enableDamping = true" in content

    # Presets
    assert "iso:" in content
    assert "top:" in content
    assert "close:" in content
    assert "chase:" in content


def test_canvas_component_hud_and_metrics():
    """Verify DigitalTwinCanvas integrates WebGL, presets, projection switcher, and diagnostics."""
    canvas_path = os.path.join(DIGITAL_TWIN_DIR, "DigitalTwinCanvas.tsx")
    with open(canvas_path, "r", encoding="utf-8") as f:
        content = f.read()

    # WebGL initialization
    assert "THREE.WebGLRenderer" in content
    assert "powerPreference" in content

    # HUD Controls
    assert "handleSelectPreset('iso')" in content
    assert "handleSelectPreset('top')" in content
    assert "handleSelectPreset('close')" in content
    assert "handleSelectPreset('chase')" in content
    assert "handleToggleProjection" in content
    assert "handleToggleAutoRotate" in content

    # Diagnostics
    assert "FPS" in content
    assert "calls" in content
    assert "tris" in content
    assert "Safety Interlock ACTIVE" in content

    # Strict rule: No static screenshot fake
    assert "dashboard-target.png" not in content, "Scene must never use static target image!"

