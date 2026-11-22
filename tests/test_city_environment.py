"""Automated verification test for Task 09: 3D City Context, Hospital, Towers, and Street Furniture."""

import os

DIGITAL_TWIN_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "apps", "web", "src", "features", "digital-twin")
)


def test_city_environment_mesh_module_exists():
    """Verify CityEnvironmentMesh.ts exists and is cleanly organized."""
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "CityEnvironmentMesh.ts"))


def test_city_quadrants_and_hospital_facility():
    """Verify procedural generation of 4 city quadrants, towers, and metropolitan hospital."""
    city_path = os.path.join(DIGITAL_TWIN_DIR, "CityEnvironmentMesh.ts")
    with open(city_path, "r", encoding="utf-8") as f:
        content = f.read()

    # NW Commercial Towers
    assert "buildBuildingsNW" in content
    assert "Tower_NW1" in content
    assert "createOfficeTower" in content

    # NE Metropolitan General Hospital (tied to AMB-339 mission)
    assert "buildHospitalFacilityNE" in content
    assert "helipad" in content or "Helipad" in content
    assert "beaconMaterial" in content

    # SW Smart City Hub & Communications Spire
    assert "buildSmartCityHubSW" in content
    assert "spire" in content or "Spire" in content

    # SE Residential Towers
    assert "buildResidentialTowersSE" in content
    assert "Tower_SE1" in content


def test_street_furniture_and_rsu_nodes():
    """Verify streetlights, low-poly urban trees, and V2X RSU nodes are generated."""
    city_path = os.path.join(DIGITAL_TWIN_DIR, "CityEnvironmentMesh.ts")
    with open(city_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Streetlights
    assert "buildStreetlights" in content
    assert "lampMat" in content

    # Urban trees
    assert "buildUrbanTrees" in content
    assert "foliageMat" in content

    # V2X RSU Nodes
    assert "buildV2XRSUPoles" in content
    assert "rsuCorners" in content
    assert "RSU_NW" in content
    assert "rsuLedMaterial" in content


def test_layer_controls_and_animation_lifecycle():
    """Verify layer toggle methods, dynamic strobe updates, and resource disposal."""
    city_path = os.path.join(DIGITAL_TWIN_DIR, "CityEnvironmentMesh.ts")
    with open(city_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "setBuildingsVisibility" in content
    assert "setStreetFurnitureVisibility" in content
    assert "setTreesVisibility" in content
    assert "update(timeMs" in content
    assert "dispose()" in content


def test_scene_environment_and_canvas_integration():
    """Verify SceneEnvironment mounts CityEnvironmentMesh and DigitalTwinCanvas has HUD toggles."""
    env_path = os.path.join(DIGITAL_TWIN_DIR, "SceneEnvironment.ts")
    with open(env_path, "r", encoding="utf-8") as f:
        env_content = f.read()

    assert "CityEnvironmentMesh" in env_content
    assert "this.cityEnvironment = new CityEnvironmentMesh();" in env_content
    assert "this.cityEnvironment.update(timeMs);" in env_content
    assert "this.cityEnvironment.dispose();" in env_content

    canvas_path = os.path.join(DIGITAL_TWIN_DIR, "DigitalTwinCanvas.tsx")
    with open(canvas_path, "r", encoding="utf-8") as f:
        canvas_content = f.read()

    assert (
        "CITY TWIN ACTIVE" in canvas_content
        or "VEHICLE FLEET ACTIVE" in canvas_content
        or "VEHICLE MOTION ACTIVE" in canvas_content
        or "SIGNALS & TRAFFIC ACTIVE" in canvas_content
    )
    assert "buildings" in canvas_content
    assert "streetFurniture" in canvas_content
    assert "trees" in canvas_content
    assert "dashboard-target.png" not in canvas_content, "Scene must never use static target image!"

