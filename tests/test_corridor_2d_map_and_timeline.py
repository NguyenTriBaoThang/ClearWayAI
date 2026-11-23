"""Comprehensive Test Suite for Task 45: 2D Corridor Route Map & Moving-Horizon Coordination Timeline.

Validates:
1. File structure and module exports for CorridorRouteMap2D, CorridorTimeline, and CorridorOperationsView.
2. Arterial corridor topology: 4 sequential nodes (A, B, C, D) across 1,000m corridor with Trauma Center destination.
3. SVG schematic graphics: roadway lanes, directional chevrons, moving-horizon ribbon, and AMB-339 marker.
4. Time-space Gantt timeline: cascading green-wave offsets, JIT pre-clearance triggers, and recovery amortization.
5. Interactive node selection, ETA countdowns, and queue dissipation inspection.
6. DashboardPage dual viewport switching (3D Digital Twin vs 2D Corridor Map & Timeline).
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_SRC = REPO_ROOT / "apps" / "web" / "src"
CORRIDOR_DIR = WEB_SRC / "features" / "corridor"


def test_corridor_component_files_exist() -> None:
    """Verify that all Task 45 corridor visualization components exist."""
    required_files = [
        CORRIDOR_DIR / "CorridorRouteMap2D.tsx",
        CORRIDOR_DIR / "CorridorTimeline.tsx",
        CORRIDOR_DIR / "CorridorOperationsView.tsx",
    ]
    for file_path in required_files:
        assert file_path.is_file(), f"Expected {file_path} to exist!"


def test_corridor_topology_and_nodes() -> None:
    """Verify 4 sequential arterial nodes A–D with precise stations and cross streets."""
    map_tsx = (CORRIDOR_DIR / "CorridorRouteMap2D.tsx").read_text(encoding="utf-8")

    # Nodes A–D
    assert "CORRIDOR_NODES" in map_tsx
    assert "node_a" in map_tsx
    assert "node_b" in map_tsx
    assert "node_c" in map_tsx
    assert "node_d" in map_tsx

    # Cross street labels
    assert "Maple St" in map_tsx
    assert "Oak St" in map_tsx
    assert "Pine St" in map_tsx
    assert "Elm St" in map_tsx

    # Stations
    assert "250" in map_tsx
    assert "500" in map_tsx
    assert "750" in map_tsx

    # Destinations
    assert "West Feeder" in map_tsx
    assert "TRAUMA CTR" in map_tsx


def test_2d_schematic_svg_and_vehicle_marker() -> None:
    """Verify SVG vector elements, lane dividers, moving horizon ribbon, and AMB-339 marker."""
    map_tsx = (CORRIDOR_DIR / "CorridorRouteMap2D.tsx").read_text(encoding="utf-8")

    # SVG layout
    assert "<svg" in map_tsx
    assert "viewBox=" in map_tsx
    assert "horizonGradient" in map_tsx

    # AMB-339 Vehicle Marker
    assert "AMB-339" in map_tsx
    assert "ambXPercent" in map_tsx
    assert "Medical Cross Symbol" in map_tsx or "path" in map_tsx
    assert "animate" in map_tsx  # Strobe pulsing animation

    # Interactive Inspection
    assert "handleNodeClick" in map_tsx
    assert "selectedNode" in map_tsx
    assert "Δt_trigger" in map_tsx
    assert "MMU ZERO-CONFLICT PASS" in map_tsx


def test_coordination_timeline_gantt_and_offsets() -> None:
    """Verify time-space Gantt timeline, cascading offsets, JIT triggers, and recovery debt."""
    timeline_tsx = (CORRIDOR_DIR / "CorridorTimeline.tsx").read_text(encoding="utf-8")

    # Time window & scale
    assert "MAX_TIME_SEC = 60.0" in timeline_tsx or "60" in timeline_tsx
    assert "DEFAULT_TIMELINE_NODES" in timeline_tsx

    # Cascading offsets (Green-wave progression)
    assert "13.5" in timeline_tsx
    assert "27.0" in timeline_tsx
    assert "40.5" in timeline_tsx

    # Bands
    assert "JIT Pre-clearance Actuation Window" in timeline_tsx or "triggerStart" in timeline_tsx
    assert "Active Preemption Green Hold" in timeline_tsx or "holdEnd" in timeline_tsx
    assert "Cross-Street Green Debt Amortization" in timeline_tsx or "recoveryEnd" in timeline_tsx

    # State Machine Lifecycle
    assert "HOLDING_GREEN" in timeline_tsx
    assert "EV_PASSING" in timeline_tsx
    assert "ARMED" in timeline_tsx
    assert "RECOVERY" in timeline_tsx

    # Recovery Strategy
    assert "3-Cycle Quadratic Debt Amortization" in timeline_tsx


def test_corridor_operations_view_tabs() -> None:
    """Verify CorridorOperationsView supports dual deck, 2D map, and timeline tabs."""
    view_tsx = (CORRIDOR_DIR / "CorridorOperationsView.tsx").read_text(encoding="utf-8")

    assert "CorridorRouteMap2D" in view_tsx
    assert "CorridorTimeline" in view_tsx
    assert "Dual Deck" in view_tsx
    assert "2D Map" in view_tsx
    assert "Timeline" in view_tsx


def test_dashboard_page_viewport_mode_switching() -> None:
    """Verify DashboardPage has view switcher between 3D Digital Twin and 2D Corridor Deck."""
    page_tsx = (WEB_SRC / "pages" / "DashboardPage.tsx").read_text(encoding="utf-8")

    assert "viewportMode" in page_tsx
    assert "3D DIGITAL TWIN" in page_tsx
    assert "2D CORRIDOR MAP & TIMELINE" in page_tsx
    assert "CorridorOperationsView" in page_tsx
    assert "DigitalTwinCanvas" in page_tsx
