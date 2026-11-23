"""Automated verification test for Task 46: Multi-Intersection 3D WebGL World (Phase H).

Verifies the procedural 3D road network spanning the 1,000m arterial corridor (5th Avenue)
with 4 sequential intersections (Nodes A, B, C, D) and Trauma Center Hospital approach,
complete 3D urban context, 16 physical signal poles with multi-phase controls, and
corridor camera navigation presets.
"""

import os
import re

DIGITAL_TWIN_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "apps", "web", "src", "features", "digital-twin")
)


def test_corridor_modules_exist():
    """Verify all Task 46 multi-intersection 3D modules exist."""
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "MultiIntersectionRoadNetwork.ts"))
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "CorridorCityEnvironment.ts"))
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "MultiSignalController.ts"))
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "SceneEnvironment.ts"))
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "SceneController.ts"))
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "DigitalTwinCanvas.tsx"))


def test_arterial_node_topology_and_roadway():
    """Verify ARTERIAL_NODES topology, 1,000m continuous roadway, 4 cross streets, and markings."""
    road_path = os.path.join(DIGITAL_TWIN_DIR, "MultiIntersectionRoadNetwork.ts")
    with open(road_path, encoding="utf-8") as f:
        content = f.read()

    # 4 Sequential Intersections: Node A, B, C, D
    assert "ARTERIAL_NODES" in content
    assert "node_a" in content
    assert "node_b" in content
    assert "node_c" in content
    assert "node_d" in content

    # Exact intersection coordinates (0m, 250m, 500m, 750m)
    assert "xMeters: 0" in content
    assert "xMeters: 250" in content
    assert "xMeters: 500" in content
    assert "xMeters: 750" in content

    # Cross street names
    assert "Maple St" in content
    assert "Oak St" in content
    assert "Pine St" in content
    assert "Elm St" in content

    # Roadway geometry: 1,050m continuous arterial roadway (4 lanes, 14m width)
    assert "1050" in content
    assert "14.0" in content or "roadWidth = 14" in content
    assert "buildArterialCorridorRoadway" in content
    assert "buildCrossStreets" in content
    assert "buildCenterDividers" in content
    assert "buildLaneMarkings" in content
    assert "buildStopLinesAndCrosswalks" in content
    assert "buildConflictBoxes" in content


def test_corridor_city_environment_urban_context():
    """Verify corridor cyber towers, Trauma Center Hospital, V2X RSUs, and West Feeder Portal."""
    city_path = os.path.join(DIGITAL_TWIN_DIR, "CorridorCityEnvironment.ts")
    with open(city_path, encoding="utf-8") as f:
        content = f.read()

    # Distributed cyber towers across inter-node blocks
    assert "buildCityBlockBuildings" in content
    assert "createTower" in content

    # Trauma Center Hospital at x = 850m with helipad and emergency beacon
    assert "buildTraumaCenterHospital" in content
    assert "hospX = 850" in content
    assert "Helipad" in content
    assert "beaconMaterial" in content

    # V2X RSU transceivers at all 4 intersections (RSU-01 through RSU-04)
    assert "buildV2XRSUNodes" in content
    assert "rsuPolesGroup" in content

    # Boulevard infrastructure
    assert "buildStreetlights" in content
    assert "buildBoulevardTrees" in content
    assert "buildWestFeederPortal" in content
    assert "-150" in content  # West Feeder Gate portal at x = -150m


def test_multi_signal_controller_16_poles():
    """Verify 16 physical signal poles (4 per intersection) with multi-phase controls."""
    signal_path = os.path.join(DIGITAL_TWIN_DIR, "MultiSignalController.ts")
    with open(signal_path, encoding="utf-8") as f:
        content = f.read()

    # Controller structure
    assert "MultiSignalController" in content
    assert "buildNodeSignals" in content
    assert "setNodePhase" in content

    # 4 mast poles per intersection: NE, NW, SW, SE
    assert "9.5" in content  # offset coords for mast poles
    assert "CylinderGeometry" in content  # Mast and mast arm
    assert "CircleGeometry" in content  # Signal lenses

    # Phase definitions (EW green, yellow, all-red, NS green, yellow)
    assert "nodeSignal.ewGreenLenses" in content
    assert "nodeSignal.nsGreenLenses" in content
    assert "nodeSignal.ewRedLenses" in content
    assert "nodeSignal.nsRedLenses" in content


def test_scene_controller_corridor_camera_presets():
    """Verify SceneController supports corridor-wide camera presets and expanded maxDistance."""
    ctrl_path = os.path.join(DIGITAL_TWIN_DIR, "SceneController.ts")
    with open(ctrl_path, encoding="utf-8") as f:
        content = f.read()

    # Presets include single-node and corridor presets
    for preset in [
        "iso",
        "top",
        "close",
        "chase",
        "corridor",
        "nodeA",
        "nodeB",
        "nodeC",
        "nodeD",
        "hospital",
    ]:
        assert preset in content

    # Camera max distance allows zooming out over 1,000m corridor
    match = re.search(r"maxDistance\s*=\s*(\d+)", content)
    assert match is not None
    assert int(match.group(1)) >= 800


def test_scene_environment_corridor_integration():
    """Verify SceneEnvironment instantiates and manages corridor road, city, and multi-signals."""
    env_path = os.path.join(DIGITAL_TWIN_DIR, "SceneEnvironment.ts")
    with open(env_path, encoding="utf-8") as f:
        content = f.read()

    # Corridor components
    assert "MultiIntersectionRoadNetwork" in content
    assert "CorridorCityEnvironment" in content
    assert "MultiSignalController" in content
    assert "corridorRoadNetwork" in content
    assert "corridorCity" in content
    assert "multiSignals" in content

    # Corridor mode toggle
    assert "setCorridorMode" in content
    assert "isCorridorMode" in content


def test_digital_twin_canvas_corridor_controls():
    """Verify DigitalTwinCanvas exposes corridor navigation buttons and corridor mode toggle."""
    canvas_path = os.path.join(DIGITAL_TWIN_DIR, "DigitalTwinCanvas.tsx")
    with open(canvas_path, encoding="utf-8") as f:
        content = f.read()

    # Corridor preset buttons in HUD
    assert "handleSelectPreset('corridor')" in content
    assert "handleSelectPreset('nodeA')" in content
    assert "handleSelectPreset('nodeB')" in content
    assert "handleSelectPreset('nodeC')" in content
    assert "handleSelectPreset('nodeD')" in content
    assert "handleSelectPreset('hospital')" in content

    # Corridor mode toggle in HUD
    assert "handleToggleCorridorMode" in content
    assert "CORRIDOR:" in content
