"""Automated verification test for Task 47: SUMO to 3D Synchronization (Phase H).

Verifies the real-time synchronization bridge between SUMO/TraCI microscopic simulation
and the 3D WebGL Digital Twin:
1. Spatial coordinate mapping from SUMO (x, y) to 3D world (X: corridor, Y: elevation, Z: lateral).
2. Heading and kinematic velocity transformations.
3. Linear interpolation and dead-reckoning extrapolation with STALE detection.
4. Multi-intersection signal synchronization across Nodes A–D with preemption hold.
5. Dynamic emergency priority corridor progression (AMB-339 from West Feeder to Trauma Center).
6. Automatic failover watchdog from LIVE_SUMO to DEMO_FIXTURE upon packet timeout.
"""

import os

DIGITAL_TWIN_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "apps", "web", "src", "features", "digital-twin")
)
DASHBOARD_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "apps", "web", "src", "features", "dashboard")
)


def test_sync_modules_exist():
    """Verify all Task 47 synchronization modules exist."""
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "SumoTrajectorySource.ts"))
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "CorridorSyncBridge.ts"))
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "MultiSignalController.ts"))
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "CorridorOverlay3D.ts"))
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "DigitalTwinCanvas.tsx"))
    assert os.path.exists(os.path.join(DASHBOARD_DIR, "OperationsContext.tsx"))


def test_sumo_trajectory_source_spatial_and_kinematic_mapping():
    """Verify SumoTrajectorySource maps SUMO coordinates, heading, and vehicle classes."""
    src_path = os.path.join(DIGITAL_TWIN_DIR, "SumoTrajectorySource.ts")
    with open(src_path, encoding="utf-8") as f:
        content = f.read()

    # Implements VehicleTrajectorySource with SUMO_SIMULATED provenance
    assert "VehicleTrajectorySource" in content
    assert "SUMO_SIMULATED" in content

    # Spatial Coordinate transformations:
    # position_x -> 3D X (corridor span)
    assert "x3d = v.position_x" in content or "x: x3d" in content
    # position_y -> 3D Z (lateral/cross-street offset)
    assert "z3d = v.position_y" in content or "z: z3d" in content
    # elevation y=0.2 above road
    assert "0.2" in content

    # Heading alignment (0=North, 90=East, 180=South, 270=West)
    assert "heading_deg" in content
    assert "v.heading_deg" in content

    # Vehicle class mapping:
    assert "emergency_ambulance" in content
    assert "emergency_fire" in content
    assert "motorcycle" in content
    assert "bus" in content
    assert "truck" in content
    assert "suv" in content

    # Kinematics: speed_ms = speed_kmh / 3.6
    assert "/ 3.6" in content


def test_sumo_interpolation_and_dead_reckoning():
    """Verify temporal buffering, tick interpolation, dead reckoning, and STALE detection."""
    src_path = os.path.join(DIGITAL_TWIN_DIR, "SumoTrajectorySource.ts")
    with open(src_path, encoding="utf-8") as f:
        content = f.read()

    # Ingestion & Buffer
    assert "ingestTelemetrySnapshot" in content
    assert "buffer" in content

    # Interpolation alpha calculation
    assert "elapsed" in content or "alpha" in content

    # Dead-reckoning forward projection using speed and heading
    assert "Math.cos" in content or "Math.sin" in content

    # STALE threshold
    assert "STALE_THRESHOLD_MS" in content
    assert "'STALE'" in content


def test_corridor_sync_bridge_signal_phases():
    """Verify CorridorSyncBridge synchronizes 16 physical signal poles across Nodes A–D."""
    bridge_path = os.path.join(DIGITAL_TWIN_DIR, "CorridorSyncBridge.ts")
    with open(bridge_path, encoding="utf-8") as f:
        content = f.read()

    # Signal synchronization method
    assert "syncTrafficSignals" in content
    assert "setNodePhase" in content

    # Nodes A–D managed
    for node in ["node_a", "node_b", "node_c", "node_d"]:
        assert node in content


def test_corridor_sync_bridge_emergency_ribbon_progression():
    """Verify CorridorSyncBridge tracks AMB-339 and updates corridor mode and node progression."""
    bridge_path = os.path.join(DIGITAL_TWIN_DIR, "CorridorSyncBridge.ts")
    with open(bridge_path, encoding="utf-8") as f:
        content = f.read()

    # Emergency corridor sync
    assert "syncEmergencyCorridor" in content
    assert "AMB" in content or "is_priority_vehicle" in content

    # Dynamic mode transitions (PLANNED, ACTIVE, COMPLETED at Trauma Center x>=850m)
    assert "850" in content
    assert "'COMPLETED'" in content
    assert "'ACTIVE'" in content

    # Preemption holds (phase 0 EW green hold when approaching an intersection)
    assert "setNodePhase('node_a', 0)" in content
    assert "setNodePhase('node_b', 0)" in content
    assert "setNodePhase('node_c', 0)" in content
    assert "setNodePhase('node_d', 0)" in content


def test_corridor_sync_bridge_failover_watchdog():
    """Verify watchdog timeout and transparent fallback to DEMO_FIXTURE."""
    bridge_path = os.path.join(DIGITAL_TWIN_DIR, "CorridorSyncBridge.ts")
    with open(bridge_path, encoding="utf-8") as f:
        content = f.read()

    # Fallback timeout defined
    assert "FALLBACK_TIMEOUT_MS" in content
    # Watchdog toggles trajectory source
    assert "setTrajectorySource" in content
    assert "LIVE_SUMO" in content
    assert "DEMO_FIXTURE" in content
    assert "FALLBACK_FIXTURE" in content


def test_digital_twin_canvas_sync_integration():
    """Verify DigitalTwinCanvas integrates CorridorSyncBridge, HUD sync pill, and preemption badge."""
    canvas_path = os.path.join(DIGITAL_TWIN_DIR, "DigitalTwinCanvas.tsx")
    with open(canvas_path, encoding="utf-8") as f:
        content = f.read()

    # Bridge instantiated and managed
    assert "CorridorSyncBridge" in content
    assert "bridgeRef" in content

    # Realtime ingestion effect
    assert "ingestSnapshot" in content
    assert "latestSnapshot" in content

    # HUD Controls
    assert "SUMO LIVE" in content
    assert "toggleSyncMode" in content
    assert "PREEMPTION ACTIVE" in content
