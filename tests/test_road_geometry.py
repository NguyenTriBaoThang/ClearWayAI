"""Automated verification test for Task 08: 3D Road Geometry, Lanes, Markings, and Crosswalks."""

import os

DIGITAL_TWIN_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "apps", "web", "src", "features", "digital-twin")
)


def test_road_network_data_and_mesh_exist():
    """Verify roadNetworkData.ts and RoadNetworkMesh.ts exist."""
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "roadNetworkData.ts"))
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "RoadNetworkMesh.ts"))


def test_road_network_configuration_parameters():
    """Verify intersection topology configures standard 3.5m lanes and 4 orthogonal approaches."""
    config_path = os.path.join(DIGITAL_TWIN_DIR, "roadNetworkData.ts")
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "INT-0457" in content
    assert "Oak St. & 5th Ave" in content
    assert "laneWidthMeters: 3.5" in content
    assert "totalRoadWidthMeters: 14.0" in content
    assert "NORTH:" in content
    assert "SOUTH:" in content
    assert "EAST:" in content
    assert "WEST:" in content


def test_road_network_mesh_geometry_elements():
    """Verify RoadNetworkMesh implements asphalt, sidewalks, center lines, dashed dividers, stop lines, crosswalks, and arrows."""
    mesh_path = os.path.join(DIGITAL_TWIN_DIR, "RoadNetworkMesh.ts")
    with open(mesh_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Asphalt surfaces
    assert "buildAsphaltSurfaces" in content
    assert "0x141d36" in content  # Dark asphalt

    # Sidewalks & Curbs
    assert "buildSidewalks" in content
    assert "0x1b284a" in content  # Cyber concrete
    assert "0x00e5ff" in content  # Cyan curb glow

    # Center double yellow dividers
    assert "buildCenterDividers" in content
    assert "0xffd166" in content  # Yellow dividing line

    # Dashed lane lines & stop lines
    assert "buildLaneDividers" in content
    assert "buildStopLines" in content

    # Zebra crosswalks
    assert "buildCrosswalks" in content
    assert "0xffffff" in content  # Pure white crosswalk stripes
    assert "numStripes = 10" in content or "numStripes" in content

    # Directional lane arrows
    assert "buildDirectionalArrows" in content
    assert "createThruArrow" in content
    assert "createRightTurnArrow" in content

    # Conflict box
    assert "buildConflictBox" in content

    # Layer visibility controls
    assert "setMarkingsVisibility" in content
    assert "setCrosswalksVisibility" in content
    assert "setSidewalksVisibility" in content


def test_scene_environment_integrates_road_network():
    """Verify SceneEnvironment mounts RoadNetworkMesh and exposes clean disposal."""
    env_path = os.path.join(DIGITAL_TWIN_DIR, "SceneEnvironment.ts")
    with open(env_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "RoadNetworkMesh" in content
    assert "this.roadNetwork = new RoadNetworkMesh();" in content
    assert "this.scene.add(this.roadNetwork.group);" in content
    assert "this.roadNetwork.dispose();" in content

    # Ensure no static fake images are used
    assert "dashboard-target.png" not in content


def test_digital_twin_canvas_status_updated():
    """Verify DigitalTwinCanvas reflects active road network status and layer toggle menus."""
    canvas_path = os.path.join(DIGITAL_TWIN_DIR, "DigitalTwinCanvas.tsx")
    with open(canvas_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert (
        "ROAD NETWORK ACTIVE" in content
        or "CITY TWIN ACTIVE" in content
        or "VEHICLE FLEET ACTIVE" in content
        or "VEHICLE MOTION ACTIVE" in content
        or "SIGNALS & TRAFFIC ACTIVE" in content
    )
    assert "LAYERS" in content
    assert "roadMarkings" in content
    assert "crosswalks" in content
    assert "sidewalks" in content

