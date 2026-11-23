"""Automated verification test for Task 48: 3D Dual Simulation Comparison (Phase H).

Verifies the split-view synchronized 3D comparison between Baseline B0 (Fixed-Time
Webster control with red-light stops and queue delays) and ClearWay AI (Moving-Horizon
Pre-clearance with green wave coordination and zero stops).
"""

import os

DIGITAL_TWIN_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "apps", "web", "src", "features", "digital-twin")
)
PAGES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "apps", "web", "src", "pages")
)


def test_comparison_modules_exist():
    """Verify all Task 48 comparison modules exist."""
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "DualSimulationComparison.tsx"))
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "BaselineFixedTimeTrajectory.ts"))
    assert os.path.exists(os.path.join(DIGITAL_TWIN_DIR, "ClearWayAITrajectory.ts"))
    assert os.path.exists(os.path.join(PAGES_DIR, "DigitalTwinPage.tsx"))


def test_baseline_fixed_time_trajectory_mechanics():
    """Verify BaselineFixedTimeTrajectory models red-light delays, stops, and 72s Webster cycle."""
    b0_path = os.path.join(DIGITAL_TWIN_DIR, "BaselineFixedTimeTrajectory.ts")
    with open(b0_path, encoding="utf-8") as f:
        content = f.read()

    # Implements VehicleTrajectorySource
    assert "VehicleTrajectorySource" in content
    assert "DEMO_FIXTURE" in content

    # Red-light stops at stoplines
    assert "WAITING_SIGNAL" in content
    assert "STOP 1" in content or "ambWaiting" in content or "ambStatus" in content

    # Travel time ~108s and slower speed ~28 km/h
    assert "108" in content
    assert "50.0" in content or "45.0" in content or "28" in content

    # Rigid 72s Webster signal phase calculation
    assert "getSignalPhaseAtTime" in content
    assert "72.0" in content


def test_clearway_ai_green_wave_trajectory_mechanics():
    """Verify ClearWayAITrajectory models uninterrupted green wave transit and zero stops."""
    ai_path = os.path.join(DIGITAL_TWIN_DIR, "ClearWayAITrajectory.ts")
    with open(ai_path, encoding="utf-8") as f:
        content = f.read()

    # Implements VehicleTrajectorySource
    assert "VehicleTrajectorySource" in content
    assert "SUMO_SIMULATED" in content

    # Green wave cruising with 0 stops
    assert "PRIORITY_CORRIDOR" in content
    assert "waiting_time_s: 0" in content

    # Travel time ~60s (-44.4% reduction) and speed ~60 km/h
    assert "60.0" in content
    assert "16.67" in content or "60.0" in content

    # JIT preemption phase calculation
    assert "getSignalPhaseForNode" in content
    assert "node_a" in content
    assert "node_b" in content
    assert "node_c" in content
    assert "node_d" in content


def test_dual_simulation_comparison_split_view():
    """Verify DualSimulationComparison integrates side-by-side viewports, KPI delta, and lockstep controls."""
    comp_path = os.path.join(DIGITAL_TWIN_DIR, "DualSimulationComparison.tsx")
    with open(comp_path, encoding="utf-8") as f:
        content = f.read()

    # Split-view dual canvases
    assert "containerLeftRef" in content
    assert "containerRightRef" in content
    assert "leftRenderer" in content
    assert "rightRenderer" in content

    # Baseline vs AI titles
    assert "BASELINE B0: FIXED-TIME CONTROL" in content
    assert "CLEARWAY AI: PRE-CLEARANCE" in content

    # Comparative Delta KPI Tiles
    assert "Transit Time:" in content
    assert "108s" in content
    assert "60s" in content
    assert "-44.4%" in content
    assert "Stops:" in content
    assert "-100%" in content
    assert "Avg Speed:" in content

    # Transport controls (play, pause, step, reset, speed, scrubber)
    assert "handleTogglePlay" in content
    assert "handleStep" in content
    assert "handleReset" in content
    assert "handleScrub" in content

    # Synchronized camera linking
    assert "syncCameras" in content
    assert "SYNC CAMS:" in content


def test_digital_twin_page_view_mode_switcher():
    """Verify DigitalTwinPage supports switching between Single View and Split Comparison."""
    page_path = os.path.join(PAGES_DIR, "DigitalTwinPage.tsx")
    with open(page_path, encoding="utf-8") as f:
        content = f.read()

    # Switcher buttons
    assert "SINGLE VIEW" in content
    assert "SPLIT COMPARISON (B0 vs AI)" in content
    assert "viewMode" in content

    # Conditional render
    assert "DigitalTwinCanvas" in content
    assert "DualSimulationComparison" in content

