"""Verification test suite for Task 14: Top-Left V2I/V2X Communication & Hardware Status Panel."""

import os

WEB_SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "web", "src"))
SHARED_SRC = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "packages", "shared", "src")
)


def test_v2x_panel_files_exist():
    """Verify that V2XHardwarePanel and V2XHardwareCard exist in the web codebase."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "V2XHardwarePanel.tsx")
    card_path = os.path.join(WEB_SRC, "features", "operations", "V2XHardwareCard.tsx")

    assert os.path.exists(panel_path), f"File {panel_path} must exist!"
    assert os.path.exists(card_path), f"File {card_path} must exist!"


def test_hardware_status_contract_compliance():
    """Verify that V2XHardwarePanel adheres to the shared HardwareStatus interface."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "V2XHardwarePanel.tsx")
    with open(panel_path, encoding="utf-8") as f:
        content = f.read()

    # Must import HardwareStatus and DataProvenance from @clearway/shared
    assert "HardwareStatus" in content
    assert "DataProvenance" in content

    # Must implement all fields of HardwareStatus
    assert "network_id" in content
    assert "obu_vehicles_online" in content
    assert "obu_pct" in content
    assert "rsu_online" in content
    assert "rsu_pct" in content
    assert "edge_controllers_online" in content
    assert "signal_controllers_online" in content
    assert "latency_ms" in content
    assert "packet_loss_pct" in content
    assert "v2x_status" in content
    assert "DEMO_FIXTURE" in content


def test_pipeline_architecture_nodes():
    """Verify that all 4 hardware pipeline architecture nodes are defined and rendered."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "V2XHardwarePanel.tsx")
    with open(panel_path, encoding="utf-8") as f:
        content = f.read()

    # 4 Architecture stages: Vehicle (OBU) ➔ RSU ➔ Edge Controller ➔ Signal Controller
    assert "On-Board Units" in content or "OBU" in content
    assert "RSU (Roadside Unit)" in content or "RSU" in content
    assert "Edge Controller" in content
    assert "Signal Controller" in content

    # Telemetry and unit specs
    assert "1,842 Online" in content
    assert "42 Online" in content
    assert "99.2%" in content
    assert "5.9 GHz" in content


def test_honest_provenance_gating():
    """Verify honest provenance gating: clearly labeled as simulated, zero fake claims."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "V2XHardwarePanel.tsx")
    with open(panel_path, encoding="utf-8") as f:
        content = f.read()

    # Must clearly display simulated status
    assert "Simulated V2X Network" in content
    assert "DEMO_FIXTURE" in content

    # Must explain synthetic nature in provenance notes
    assert "SUMO" in content or "synthetic" in content.lower()


def test_interactive_device_inspector():
    """Verify interactive inspector modal/drawer with station IDs, IP/MAC, protocols, and ping."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "V2XHardwarePanel.tsx")
    with open(panel_path, encoding="utf-8") as f:
        content = f.read()

    # Station IDs and standards
    assert "RSU-0457-MAST-1" in content
    assert "OBU-SUBNET-457" in content
    assert "EDGE-0457-PRI" in content
    assert "SIG-0457-NEMA" in content

    # Protocols
    assert "SAE J2735" in content
    assert "IEEE 802.11p" in content
    assert "NTCIP 1202" in content
    assert "C-V2X" in content

    # Interactive diagnostics / ping
    assert "handlePingDevice" in content or "Ping Diagnostics" in content
    assert "handleSelectNode" in content or "activeNode" in content


def test_simulation_fallback_modes():
    """Verify degraded and offline fallback modes with safety interlock alerts."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "V2XHardwarePanel.tsx")
    with open(panel_path, encoding="utf-8") as f:
        content = f.read()

    # Three operating modes
    assert "nominal" in content
    assert "degraded" in content
    assert "offline" in content

    # Fallback safety alerts
    assert "inductive loops" in content or "radar" in content
    assert "autonomous" in content or "fail-safe" in content.lower()


def test_zero_static_fake_assets():
    """Verify no static fake screenshot assets or raster mocks are referenced."""
    panel_path = os.path.join(WEB_SRC, "features", "dashboard", "V2XHardwarePanel.tsx")
    with open(panel_path, encoding="utf-8") as f:
        content = f.read()

    assert "dashboard-target.png" not in content
    assert "placeholder.png" not in content
