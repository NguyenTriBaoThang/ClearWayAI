"""Verification test suite for Task 18: Bottom-Right Traffic Analytics, Radial Gauge & Alerts Panel."""

import os

WEB_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "web", "src"))
SHARED_SRC = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "packages", "shared", "src")
)


def test_analytics_files_exist():
    """Verify that OperationsAnalyticsPanel and AnalyticsCard exist in the web codebase."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "OperationsAnalyticsPanel.tsx")
    card_path = os.path.join(WEB_SRC, "features", "operations", "AnalyticsCard.tsx")

    assert os.path.exists(panel_path), f"File {panel_path} must exist!"
    assert os.path.exists(card_path), f"File {card_path} must exist!"


def test_traffic_analytics_contract_compliance():
    """Verify that OperationsAnalyticsPanel adheres to the shared TrafficAnalytics interface."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "OperationsAnalyticsPanel.tsx")
    with open(panel_path, encoding="utf-8") as f:
        content = f.read()

    # Must import TrafficAnalytics and DataProvenance from @clearway/shared
    assert "TrafficAnalytics" in content
    assert "DataProvenance" in content

    # Must implement all key fields
    assert "intersection_id" in content
    assert "performance_index" in content
    assert "throughput_pct_change" in content
    assert "avg_delay_pct_change" in content
    assert "stops_per_veh_pct_change" in content
    assert "DEMO_FIXTURE" in content


def test_real_time_volume_bars():
    """Verify the 4 real-time hourly volume values matching the UI blueprint."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "OperationsAnalyticsPanel.tsx")
    with open(panel_path, encoding="utf-8") as f:
        content = f.read()

    # Approaches and values
    assert "NB" in content
    assert "SB" in content
    assert "EB" in content
    assert "WB" in content
    assert "1210" in content or "1,210" in content
    assert "1438" in content or "1,438" in content
    assert "2185" in content or "2,185" in content
    assert "2061" in content or "2,061" in content


def test_average_travel_time_horizontal_bars():
    """Verify zone travel times and baseline comparison percentages."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "OperationsAnalyticsPanel.tsx")
    with open(panel_path, encoding="utf-8") as f:
        content = f.read()

    # 4 corridor pairs
    assert "N → S" in content
    assert "S → N" in content
    assert "E → W" in content
    assert "W → E" in content

    # Times and deltas
    assert "2.6" in content
    assert "2.8" in content
    assert "3.9" in content
    assert "3.7" in content
    assert "-18" in content
    assert "-17" in content


def test_radial_performance_gauge_and_kpis():
    """Verify circular progress gauge with 82/100 score and key KPI deltas."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "OperationsAnalyticsPanel.tsx")
    with open(panel_path, encoding="utf-8") as f:
        content = f.read()

    # Circular gauge score
    assert "82" in content
    assert "/100" in content or "100" in content
    assert "strokeDasharray" in content

    # Key deltas
    assert "+15%" in content
    assert "-19%" in content
    assert "-22%" in content
    assert "Throughput" in content
    assert "Avg. Delay" in content
    assert "Stops" in content


def test_anomaly_alerts_feed_and_filtering():
    """Verify anomaly alerts feed with critical corridor, queue warning, and radio info."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "OperationsAnalyticsPanel.tsx")
    with open(panel_path, encoding="utf-8") as f:
        content = f.read()

    # Key alerts
    assert "AMB-339" in content
    assert "80m" in content or "87m" in content
    assert "RSU" in content

    # Severity and actions
    assert "critical" in content
    assert "warning" in content
    assert "dismissAlert" in content or "setAlertFilter" in content


def test_zero_static_fake_assets():
    """Verify no raster mock images are used in the component."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "OperationsAnalyticsPanel.tsx")
    with open(panel_path, encoding="utf-8") as f:
        content = f.read()

    assert "dashboard-target.png" not in content
    assert "placeholder.png" not in content
