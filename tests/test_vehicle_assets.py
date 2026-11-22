"""Automated verification test for Task 10: 3D Vehicle Assets (Motorcycles, Cars, Buses, Ambulances)."""

import os

DIGITAL_TWIN_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "apps", "web", "src", "features", "digital-twin")
)


def test_vehicle_factory_and_manager_exist():
    """Verify VehicleAssetFactory.ts and TrafficVehicleManager.ts exist."""
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "VehicleAssetFactory.ts"))
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "TrafficVehicleManager.ts"))


def test_vehicle_asset_factory_classes():
    """Verify factory implements all 7 vehicle classes matching Vietnamese traffic & emergency services."""
    factory_path = os.path.join(DIGITAL_TWIN_DIR, "VehicleAssetFactory.ts")
    with open(factory_path, "r", encoding="utf-8") as f:
        content = f.read()

    # High-density urban motorcycle
    assert "createMotorcycle" in content

    # Passenger Car & SUV
    assert "createPassengerCar" in content
    assert "createSUV" in content

    # Urban Transit Bus
    assert "createBus" in content

    # Delivery Truck
    assert "createTruck" in content

    # Emergency Ambulance AMB-339 with dual strobes
    assert "createEmergencyAmbulance" in content
    assert "strobeLeft" in content or "strobeLeftMat" in content
    assert "strobeRight" in content or "strobeRightMat" in content

    # Emergency Fire Engine
    assert "createEmergencyFireEngine" in content
    assert "ladder" in content or "Ladder" in content


def test_traffic_vehicle_manager_fleet_and_raycasting():
    """Verify TrafficVehicleManager manages initial fleet, AMB-339 corridor motion, and click raycasting."""
    mgr_path = os.path.join(DIGITAL_TWIN_DIR, "TrafficVehicleManager.ts")
    with open(mgr_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "spawnInitialFleet" in content
    assert "AMB-339" in content
    assert "BUS-104" in content
    assert "MOTO-01" in content
    assert "findVehicleByIntersection" in content
    assert "setVehiclesVisibility" in content
    assert "update(timeMs" in content
    assert "dispose()" in content


def test_scene_environment_integrates_vehicle_manager():
    """Verify SceneEnvironment mounts vehicle manager and feeds ambulance coordinates to chase cam."""
    env_path = os.path.join(DIGITAL_TWIN_DIR, "SceneEnvironment.ts")
    with open(env_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "TrafficVehicleManager" in content
    assert "this.vehicleManager = new TrafficVehicleManager();" in content
    assert "this.scene.add(this.vehicleManager.group);" in content
    assert "this.vehicleManager.update(timeMs);" in content
    assert "this.vehicleManager.dispose();" in content


def test_canvas_has_vehicle_inspector_and_layer_controls():
    """Verify DigitalTwinCanvas integrates raycast click handler, inspector chip, and layer toggles."""
    canvas_path = os.path.join(DIGITAL_TWIN_DIR, "DigitalTwinCanvas.tsx")
    with open(canvas_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "handleCanvasClick" in content
    assert "selectedVehicle" in content
    assert "Inspector:" in content
    assert "VEHICLE FLEET ACTIVE" in content or "VEHICLE MOTION ACTIVE" in content
    assert "vehicles" in content
    assert "3D Vehicle Fleet" in content

    # No static fakes
    assert "dashboard-target.png" not in content, "Scene must never use static target image!"

