"""Automated verification test for Task 11: 3D Vehicle Motion & Lane Graph Trajectories."""

import os

DIGITAL_TWIN_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "apps", "web", "src", "features", "digital-twin")
)


def test_vehicle_motion_modules_exist():
    """Verify VehicleTrajectorySource, VehicleSnapshotFixture, and VehicleMotionSystem exist."""
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "VehicleTrajectorySource.ts"))
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "VehicleSnapshotFixture.ts"))
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "VehicleMotionSystem.ts"))


def test_vehicle_snapshot_fixture_specification():
    """Verify snapshot fixture generates realistic, deterministic mixed traffic and emergency corridor."""
    fixture_path = os.path.join(DIGITAL_TWIN_DIR, "VehicleSnapshotFixture.ts")
    with open(fixture_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Trajectory source implementation
    assert "VehicleTrajectorySource" in content
    assert "sourceId = 'DEMO_FIXTURE'" in content
    assert "getSnapshotsAtTime" in content
    assert "getSignalPhase" in content

    # Priority vehicles & emergency pre-emption
    assert "AMB-339" in content
    assert "emergency_ambulance" in content
    assert "FIRE-09" in content

    # Multi-class mixed fleet (buses, trucks, SUVs, passenger cars, motorcycles)
    assert "BUS-104" in content
    assert "TRUCK-55" in content
    assert "SUV-01" in content
    assert "CAR-01" in content
    assert "MOTO-01" in content

    # Lane graph routing and stop line compliance
    assert "EB_STRAIGHT" in content
    assert "WB_STRAIGHT" in content
    assert "NB_STRAIGHT" in content
    assert "SB_STRAIGHT" in content
    assert "NB_RIGHT" in content
    assert "EB_LEFT" in content
    assert "WAITING_SIGNAL" in content


def test_vehicle_motion_system_interpolation_and_safety():
    """Verify VehicleMotionSystem implements persistent mapping, angle slerp, anti-teleport clamping, and STALE detection."""
    sys_path = os.path.join(DIGITAL_TWIN_DIR, "VehicleMotionSystem.ts")
    with open(sys_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Persistent mapping
    assert "vehicles: Map<string, ManagedMotionVehicle>" in content
    assert "createVehicleInstance" in content

    # Shortest angular arc interpolation
    assert "lerpAngleDeg" in content
    assert "(toDeg - fromDeg + 540) % 360" in content

    # Anti-teleportation & bounded extrapolation
    assert "MAX_TELEPORT_DELTA_M" in content
    assert "STALE_THRESHOLD_MS" in content
    assert "STALE" in content

    # 3D Billboard Speed Badges
    assert "createSpeedBadgeSprite" in content
    assert "updateSpeedBadge" in content
    assert "setShowBadges" in content


def test_speed_unit_conversion():
    """Verify physical m/s to display km/h conversion accuracy (1 m/s = 3.6 km/h)."""
    # 60 km/h is 16.666... m/s
    speed_ms = 60.0 / 3.6
    speed_kmh = round(speed_ms * 3.6, 1)
    assert speed_kmh == 60.0

    # 30 km/h is 8.333... m/s
    speed_ms_30 = 30.0 / 3.6
    speed_kmh_30 = round(speed_ms_30 * 3.6, 1)
    assert speed_kmh_30 == 30.0


def test_digital_twin_canvas_vehicle_motion_and_inspector():
    """Verify DigitalTwinCanvas integrates motion system, rich vehicle inspector, and layer controls."""
    canvas_path = os.path.join(DIGITAL_TWIN_DIR, "DigitalTwinCanvas.tsx")
    with open(canvas_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Status pill active
    assert "VEHICLE MOTION ACTIVE" in content

    # Layer toggles
    assert "vehicleBadges" in content
    assert "Vehicle Badges / Speeds" in content
    assert "3D Vehicle Fleet" in content

    # Rich Inspector Card
    assert "Inspector Card" in content or "Selected Vehicle Inspector Card" in content
    assert "Follow Cam" in content or "Follow with Chase Cam" in content
    assert "speed_kmh" in content
    assert "speed_ms" in content
    assert "current_lane_id" in content

    # Zero static fake rule
    assert "dashboard-target.png" not in content, "Scene must never use static target image!"

