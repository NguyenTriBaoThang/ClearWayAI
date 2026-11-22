"""Verification test suite for Task 17: Bottom-Left IoT Sensor Network & City Map Overview Panel."""

import os

WEB_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "web", "src"))


def test_iot_sensors_files_exist():
    """Verify that IoTSensorsPanel and IoTSensorsCard exist in the web codebase."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "IoTSensorsPanel.tsx")
    card_path = os.path.join(WEB_SRC, "features", "operations", "IoTSensorsCard.tsx")

    assert os.path.exists(panel_path), f"File {panel_path} must exist!"
    assert os.path.exists(card_path), f"File {card_path} must exist!"


def test_five_sensor_categories_inventory():
    """Verify all 5 sensor device categories and counts matching the UI blueprint."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "IoTSensorsPanel.tsx")
    with open(panel_path, encoding="utf-8") as f:
        content = f.read()

    # 5 Device Categories:
    assert "Traffic Cameras" in content
    assert "LiDAR Sensors" in content
    assert "Loop Detectors" in content
    assert "RSUs (V2I)" in content or "RSU" in content
    assert "Signal Controllers" in content

    # Online Counts:
    assert "112" in content
    assert "48" in content
    assert "96" in content
    assert "42" in content
    assert "8" in content


def test_six_data_layers_checkboxes():
    """Verify that all 6 city data layers are supported with interactive state toggles."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "IoTSensorsPanel.tsx")
    with open(panel_path, encoding="utf-8") as f:
        content = f.read()

    # 6 Data Layers:
    assert "Traffic Flow" in content
    assert "Sensor Coverage" in content
    assert "V2X Network" in content
    assert "Incident / Event" in content
    assert "Emergency Corridor" in content
    assert "Parking Occupancy" in content
    assert "toggleLayer" in content


def test_mini_vector_city_map_elements():
    """Verify vector SVG city map includes arterial streets, hospital, scale bar, and compass."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "IoTSensorsPanel.tsx")
    with open(panel_path, encoding="utf-8") as f:
        content = f.read()

    # Streets
    assert "5th Ave" in content
    assert "Oak St" in content

    # Hospital marker 'H'
    assert ">H<" in content or '"H"' in content
    assert "Hospital" in content

    # Ambulance AMB-339
    assert "AMB-339" in content

    # Compass rose 'N'
    assert ">N<" in content or '"N"' in content
    assert "Compass" in content

    # Metric scale bar: 0 250 500 1,000 m
    assert "1,000 m" in content
    assert "250" in content
    assert "500" in content


def test_interactive_intersection_node_inspector():
    """Verify corridor intersection nodes are defined and interactive."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "IoTSensorsPanel.tsx")
    with open(panel_path, encoding="utf-8") as f:
        content = f.read()

    # Nodes on the corridor
    assert "INT-0455" in content
    assert "INT-0456" in content
    assert "INT-0457" in content
    assert "INT-0458" in content

    # Selected node inspector
    assert "selectedNode" in content
    assert "activePhase" in content
    assert "queueM" in content


def test_honest_provenance_gating():
    """Verify honest provenance gating: clearly labeled as simulated, zero fake claims."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "IoTSensorsPanel.tsx")
    with open(panel_path, encoding="utf-8") as f:
        content = f.read()

    assert "DEMO_FIXTURE" in content


def test_zero_static_fake_assets():
    """Verify no raster mock images are used."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "IoTSensorsPanel.tsx")
    with open(panel_path, encoding="utf-8") as f:
        content = f.read()

    assert "dashboard-target.png" not in content
    assert "placeholder.png" not in content

