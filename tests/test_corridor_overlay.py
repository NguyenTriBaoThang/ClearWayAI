"""Automated verification test for Task 13: 3D Dynamic Corridor Ribbon, Flow Arrows, and In-Scene HUD."""

import os

DIGITAL_TWIN_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "apps", "web", "src", "features", "digital-twin")
)


def test_corridor_overlay_modules_exist():
    """Verify CorridorOverlay3D.ts and FlowArrows3D.ts exist."""
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "CorridorOverlay3D.ts"))
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "FlowArrows3D.ts"))


def test_corridor_modes_and_styling():
    """Verify CorridorOverlay3D supports PLANNED, ACTIVE, COMPLETED, and BLOCKED modes."""
    corridor_path = os.path.join(DIGITAL_TWIN_DIR, "CorridorOverlay3D.ts")
    with open(corridor_path, encoding="utf-8") as f:
        content = f.read()

    # Corridor modes
    assert "PLANNED" in content
    assert "ACTIVE" in content
    assert "COMPLETED" in content
    assert "BLOCKED" in content

    # Animated Chevrons
    assert "buildChevronArrows" in content
    assert "chevronsGroup" in content
    assert "scrollOffset" in content

    # Infeasible / Blocked safety visualization
    assert "BLOCKED" in content
    assert "0xef4444" in content or "0xff1744" in content


def test_vehicle_callout_and_telemetry():
    """Verify in-scene 3D vehicle callout displays Mission ID, ETA, and priority status."""
    corridor_path = os.path.join(DIGITAL_TWIN_DIR, "CorridorOverlay3D.ts")
    with open(corridor_path, encoding="utf-8") as f:
        content = f.read()

    # Callout billboard
    assert "createCalloutSprite" in content
    assert "renderCalloutCanvas" in content
    assert "PREEMPTION ACTIVE" in content
    assert "ETA to INT-0457" in content

    # Node chain A–D telemetry
    assert "getCorridorTelemetry" in content
    assert "INT-0456" in content
    assert "INT-0457" in content
    assert "INT-0458" in content
    assert "INT-0459" in content
    assert "clearanceDistanceM" in content
    assert "preemptionLeadSec" in content


def test_flow_arrows_and_conflict_zone():
    """Verify FlowArrows3D builds flow arrows, yellow box conflict zone, hotspots, and sensor footprints."""
    arrows_path = os.path.join(DIGITAL_TWIN_DIR, "FlowArrows3D.ts")
    with open(arrows_path, encoding="utf-8") as f:
        content = f.read()

    # Flow arrows
    assert "buildFlowArrows" in content
    assert "flowArrowsGroup" in content

    # Conflict zone yellow box junction
    assert "buildConflictZoneBox" in content
    assert "conflictZoneGroup" in content
    assert "0xffd166" in content

    # Queue Hotspots & Sensor Footprints
    assert "buildQueueHotspots" in content
    assert "buildSensorFootprints" in content
    assert "sensorFootprintsGroup" in content


def test_scene_and_canvas_corridor_integration():
    """Verify SceneEnvironment mounts corridor/flow overlays and Canvas has HUD toggles & inspector."""
    env_path = os.path.join(DIGITAL_TWIN_DIR, "SceneEnvironment.ts")
    with open(env_path, encoding="utf-8") as f:
        env_content = f.read()

    assert "CorridorOverlay3D" in env_content
    assert "FlowArrows3D" in env_content
    assert "this.corridorOverlay = new CorridorOverlay3D();" in env_content
    assert "this.flowArrows = new FlowArrows3D();" in env_content
    assert "this.corridorOverlay.update(" in env_content
    assert "this.flowArrows.update(" in env_content
    assert "this.corridorOverlay.dispose();" in env_content
    assert "this.flowArrows.dispose();" in env_content

    canvas_path = os.path.join(DIGITAL_TWIN_DIR, "DigitalTwinCanvas.tsx")
    with open(canvas_path, encoding="utf-8") as f:
        canvas_content = f.read()

    # Active status pill
    assert "CORRIDOR & HUD ACTIVE" in canvas_content

    # Corridor Inspector Card
    assert "Selected Emergency Corridor Inspector Card" in canvas_content
    assert "selectedCorridor" in canvas_content
    assert "Corridor Intersections (A–D Chain)" in canvas_content

    # Layer toggles
    assert "Emergency Corridor Ribbon" in canvas_content
    assert "Traffic Flow Arrows" in canvas_content
    assert "Conflict Zone Box" in canvas_content
    assert "Sensor Footprints (RSU)" in canvas_content
    assert "Queue Hotspots" in canvas_content
    assert "Vehicle 3D Callouts" in canvas_content

    # Zero static fake rule
    assert "dashboard-target.png" not in canvas_content, "Scene must never use static target image!"
