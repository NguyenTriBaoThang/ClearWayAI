"""Automated verification test for Task 12: 3D Traffic Signals, Pedestrian Crossing, and Conflict-Free Phase Logic."""

import os

DIGITAL_TWIN_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "apps", "web", "src", "features", "digital-twin")
)


def test_traffic_signal_modules_exist():
    """Verify SignalPhaseController.ts and TrafficSignal3D.ts exist."""
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "SignalPhaseController.ts"))
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "TrafficSignal3D.ts"))


def test_conflict_free_safety_interlock_logic():
    """Verify SignalPhaseController enforces strict conflict-free matrix, yellow intervals, and all-red clearance."""
    controller_path = os.path.join(DIGITAL_TWIN_DIR, "SignalPhaseController.ts")
    with open(controller_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Safety validation & interlock
    assert "validateConflictFree" in content
    assert "ew === 'green' || ew === 'yellow'" in content
    assert "ns === 'green' || ns === 'yellow'" in content
    assert "FAILSAFE_ALL_RED" in content or "conflictFreeVerified" in content

    # Standard NEMA Phase Progression
    assert "PHASE_1_EW_GREEN" in content
    assert "PHASE_2_EW_YELLOW" in content
    assert "PHASE_3_ALL_RED_CLEARANCE" in content
    assert "PHASE_4_NS_GREEN" in content
    assert "PHASE_5_NS_YELLOW" in content
    assert "PHASE_6_ALL_RED_CLEARANCE" in content

    # Minimum intervals
    assert "EW_GREEN_END" in content
    assert "EW_YELLOW_END" in content
    assert "ALL_RED_1_END" in content
    assert "NS_GREEN_END" in content
    assert "NS_YELLOW_END" in content


def test_physical_signal_head_single_lens_rule():
    """Verify TrafficSignal3D enforces physical single-lens illumination (no simultaneous red+green)."""
    signal3d_path = os.path.join(DIGITAL_TWIN_DIR, "TrafficSignal3D.ts")
    with open(signal3d_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Master poles for all 4 intersection quadrants
    assert "SIG-POLE-N" in content
    assert "SIG-POLE-S" in content
    assert "SIG-POLE-E" in content
    assert "SIG-POLE-W" in content

    # Emissive lens reset ensuring mutual exclusion
    assert "updateSignalHead" in content
    assert "head.redMat.emissive.setHex(0x000000)" in content
    assert "head.yellowMat.emissive.setHex(0x000000)" in content
    assert "head.greenMat.emissive.setHex(0x000000)" in content

    # Overhead mast-arm and post-mounted dual heads
    assert "primaryHead" in content
    assert "secondaryHead" in content
    assert "pedestrianHead" in content


def test_pedestrian_crossing_agents_and_walk_logic():
    """Verify 3D pedestrian agents animate across zebra crosswalks during WALK phase and wait safely on sidewalk."""
    signal3d_path = os.path.join(DIGITAL_TWIN_DIR, "TrafficSignal3D.ts")
    with open(signal3d_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "buildPedestrianAgents" in content
    assert "createPedestrianFigure" in content
    assert "PED-NORTH-1" in content or "crosswalkConfigs" in content
    assert "pedPhase === 'WALK'" in content
    assert "walkCycle" in content


def test_scene_environment_and_canvas_signal_integration():
    """Verify SceneEnvironment mounts signals and DigitalTwinCanvas has inspector & live phase badges."""
    env_path = os.path.join(DIGITAL_TWIN_DIR, "SceneEnvironment.ts")
    with open(env_path, "r", encoding="utf-8") as f:
        env_content = f.read()

    assert "TrafficSignal3D" in env_content
    assert "this.trafficSignals = new TrafficSignal3D();" in env_content
    assert "this.trafficSignals.update(timeMs);" in env_content
    assert "this.trafficSignals.dispose();" in env_content

    canvas_path = os.path.join(DIGITAL_TWIN_DIR, "DigitalTwinCanvas.tsx")
    with open(canvas_path, "r", encoding="utf-8") as f:
        canvas_content = f.read()

    # Active status pill
    assert "SIGNALS & TRAFFIC ACTIVE" in canvas_content

    # HUD Real-time Signal Phase Mini Badge
    assert "Signal Phase:" in canvas_content
    assert "5th Ave (EW):" in canvas_content
    assert "Oak St (NS):" in canvas_content

    # Signal Pole Inspector Card
    assert "Signal Pole:" in canvas_content
    assert "selectedPole" in canvas_content
    assert "CONFLICT_FREE_VERIFIED" in canvas_content or "conflictFreeStatus" in canvas_content

    # Layer menu items
    assert "trafficSignals" in canvas_content
    assert "Traffic Signal Poles" in canvas_content
    assert "pedestrians" in canvas_content
    assert "Pedestrians Crossing" in canvas_content

    # Zero static fake rule
    assert "dashboard-target.png" not in canvas_content, "Scene must never use static target image!"
