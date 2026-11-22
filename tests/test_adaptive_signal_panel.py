"""Verification test suite for Task 16: Top-Right Adaptive Signal Control & Queue Chart Panel."""

import os
import re

WEB_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "web", "src"))
SHARED_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages", "shared", "src"))


def test_adaptive_signal_files_exist():
    """Verify that AdaptiveSignalPanel and AdaptiveSignalCard exist in the web codebase."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "AdaptiveSignalPanel.tsx")
    card_path = os.path.join(WEB_SRC, "features", "operations", "AdaptiveSignalCard.tsx")

    assert os.path.exists(panel_path), f"File {panel_path} must exist!"
    assert os.path.exists(card_path), f"File {card_path} must exist!"


def test_traffic_analytics_contract_compliance():
    """Verify that AdaptiveSignalPanel adheres to the shared TrafficAnalytics interface."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "AdaptiveSignalPanel.tsx")
    with open(panel_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Must import TrafficAnalytics and DataProvenance from @clearway/shared
    assert "TrafficAnalytics" in content
    assert "DataProvenance" in content

    # Must implement core analytics fields
    assert "intersection_id" in content
    assert "avg_delay_pct_change" in content
    assert "occupancy_pct" in content
    assert "avg_queue_m" in content
    assert "backlog_m" in content
    assert "DEMO_FIXTURE" in content


def test_top_kpis_and_phases():
    """Verify cycle time (120s), current phase (P3 E-W Thru), and next phase (P4 E-W Left)."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "AdaptiveSignalPanel.tsx")
    with open(panel_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "120s" in content
    assert "P3 (E-W Thru)" in content
    assert "P4 (E-W Left)" in content
    assert "Cycle Time" in content
    assert "Current Phase" in content
    assert "Next Phase" in content


def test_queue_vs_capacity_vector_chart():
    """Verify the Queue vs Capacity SVG chart has curves, gridlines, axis ticks, and occupancy badge."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "AdaptiveSignalPanel.tsx")
    with open(panel_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Cyan Queue curve and Red dashed Capacity line
    assert "#00e5ff" in content
    assert "#ef476f" in content
    assert "strokeDasharray" in content

    # Axis tick labels: 0, 30, 60, 90, 120s and 40, 80, 120 veh
    assert ">120<" in content or '"120"' in content
    assert ">80<" in content or '"80"' in content
    assert ">40<" in content or '"40"' in content
    assert ">30<" in content or '"30"' in content
    assert ">60<" in content or '"60"' in content
    assert ">90<" in content or '"90"' in content

    # Occupancy badge: 76%
    assert "76%" in content or "76" in content


def test_optimization_metrics_kpi():
    """Verify -19% Delay, 87m Avg Queue, and 45m Backlog are rendered."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "AdaptiveSignalPanel.tsx")
    with open(panel_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "-19%" in content
    assert "Delay" in content
    assert "87 m" in content or "87" in content
    assert "45 m" in content or "45" in content
    assert "Avg. Queue" in content
    assert "Backlog" in content


def test_interactive_control_modes_and_diagnostics():
    """Verify multi-mode policy switcher (RL PPO, Actuated, Fixed) and diagnostics drawer."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "AdaptiveSignalPanel.tsx")
    with open(panel_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Control modes
    assert "rl_adaptive" in content
    assert "actuated" in content
    assert "fixed_time" in content

    # Diagnostics drawer and safety limits
    assert "PPO" in content
    assert "Min Green" in content or "10.0s" in content
    assert "Max Green" in content or "75.0s" in content
    assert "showDiagnostics" in content


def test_zero_static_fake_assets():
    """Verify no raster mock images are used in the component."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "AdaptiveSignalPanel.tsx")
    with open(panel_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "dashboard-target.png" not in content
    assert "placeholder.png" not in content

