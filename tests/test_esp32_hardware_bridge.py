"""Automated Verification Suite for ESP32 Physical Testbench & Hardware Bridge (Task 54).

Tests:
1. ESP32 firmware source code, pinouts, and circuit documentation existence.
2. Bridge initialization and connection state.
3. UART JSON serial framing and command parsing.
4. Hardware MMU (Malfunction Management Unit) conflict interlock (INV-03).
5. Hardware Fail-Safe Watchdog timeout and autonomous fallback recovery (INV-06).
6. Corridor signal phase synchronization across Nodes A–D.
7. Emergency corridor strobe activation.
8. FastAPI hardware REST endpoints.
9. Diagnostic CLI testbench subroutines.
"""

from __future__ import annotations

from pathlib import Path

from apps.api.src.routers.hardware import (
    get_hardware_status,
    get_hardware_telemetry,
    send_hardware_command,
    sync_corridor_to_hardware,
)
from apps.api.src.schemas import ESP32CommandRequest, ESP32SyncRequest
from controller.hardware.esp32_bridge import (
    ESP32HardwareBridge,
    HardwareBridgeConfig,
    HardwareFaultCode,
    HardwareMode,
    SignalLEDColor,
    VirtualESP32Emulator,
)
from controller.hardware.testbench_cli import (
    run_emergency_strobe,
    run_lamp_test,
    run_walking_green,
)


def test_firmware_source_and_circuit_documentation():
    """Verify that ESP32 firmware, schematic diagrams, and BOM files exist and are well-formed."""
    firmware_path = Path("hardware/firmware/clearway_esp32_firmware.ino")
    schematic_path = Path("hardware/schematics/breadboard_wiring.md")
    bom_path = Path("hardware/bom/BILL_OF_MATERIALS.md")

    assert firmware_path.exists(), "ESP32 Arduino sketch must exist"
    assert schematic_path.exists(), "Circuit schematic documentation must exist"
    assert bom_path.exists(), "Bill of Materials documentation must exist"

    fw_content = firmware_path.read_text(encoding="utf-8")
    assert "verifyHardwareMMU" in fw_content
    assert "WATCHDOG_TIMEOUT_MS" in fw_content
    assert "USE_SHIFT_REGISTERS" in fw_content
    assert "handleAutonomousFallback" in fw_content
    assert "PIN_EMERGENCY_STROBE" in fw_content

    schematic_content = schematic_path.read_text(encoding="utf-8")
    assert "74HC595" in schematic_content
    assert "PIN_SR_DATA" in schematic_content
    assert "Node A" in schematic_content and "Node D" in schematic_content

    bom_content = bom_path.read_text(encoding="utf-8")
    assert "ESP32 DevKit" in bom_content
    assert "Traffic Light LED" in bom_content


def test_esp32_bridge_initialization_and_connection():
    """Verify bridge connects in simulation mode and instantiates 4 corridor nodes."""
    config = HardwareBridgeConfig(simulation_mode=True)
    bridge = ESP32HardwareBridge(config)

    assert not bridge.is_connected()
    connected = bridge.connect()
    assert connected
    assert bridge.is_connected()
    assert bridge.emulator is not None
    assert len(bridge.emulator.nodes) == 4
    assert "node_a" in bridge.emulator.nodes
    assert "node_d" in bridge.emulator.nodes

    bridge.disconnect()
    assert not bridge.is_connected()


def test_serial_protocol_json_framing():
    """Test UART JSON packet processing and sequence number tracking."""
    bridge = ESP32HardwareBridge(HardwareBridgeConfig(simulation_mode=True))
    bridge.connect()

    # 1. Heartbeat packet
    hb_ack = bridge.send_heartbeat()
    assert hb_ack["ack"] == "HEARTBEAT"
    assert hb_ack["status"] == "OK"
    assert hb_ack["seq"] == 1

    # 2. Lamp test packet
    lt_ack = bridge.trigger_lamp_test()
    assert lt_ack["ack"] == "LAMP_TEST"
    assert lt_ack["status"] == "OK"

    # Verify emulator mode changed to LAMP_TEST
    telemetry = bridge.get_telemetry()
    assert telemetry["mode"] == HardwareMode.LAMP_TEST.value

    bridge.disconnect()


def test_hardware_mmu_conflict_interlock():
    """Verify hardware MMU rejects conflicting simultaneous green signals (INV-03)."""
    bridge = ESP32HardwareBridge(HardwareBridgeConfig(simulation_mode=True))
    bridge.connect()

    # Attempt illegal conflict state: Node B has both EW Green and NS Green
    conflicting_state = {
        "node_a": {"ew": "GREEN", "ns": "RED"},
        "node_b": {"ew": "GREEN", "ns": "GREEN"},  # CONFLICT!
        "node_c": {"ew": "RED", "ns": "GREEN"},
        "node_d": {"ew": "RED", "ns": "RED"},
    }

    res = bridge.sync_corridor(conflicting_state)
    assert res["status"] == "MMU_CONFLICT_TRIP"
    assert res["fault"] == HardwareFaultCode.ERR_HW_MMU_CONFLICT.value
    assert res["conflict_node"] == "node_b"

    telemetry = bridge.get_telemetry()
    assert telemetry["mmu_tripped"] is True
    assert telemetry["mode"] == HardwareMode.MMU_TRIP_LATCHED.value

    # Reset faults
    reset_res = bridge.reset_faults()
    assert reset_res["status"] == "OK"

    telemetry_after = bridge.get_telemetry()
    assert telemetry_after["mmu_tripped"] is False
    assert telemetry_after["fault_code"] == HardwareFaultCode.NONE.value

    bridge.disconnect()


def test_hardware_watchdog_timeout_failsafe():
    """Verify hardware watchdog timeout triggers autonomous fallback (INV-06)."""
    emulator = VirtualESP32Emulator(watchdog_threshold_sec=0.1)
    emulator.last_heartbeat_timestamp = 100.0

    # Initial state is healthy
    emulator.tick(now=100.0)
    assert emulator.mode == HardwareMode.SIMULATION
    assert emulator.fault_code == HardwareFaultCode.NONE

    # Fast forward beyond watchdog threshold (0.15s > 0.10s)
    emulator.tick(now=100.15)
    assert emulator.mode == HardwareMode.AUTONOMOUS_FALLBACK
    assert emulator.fault_code == HardwareFaultCode.ERR_HW_WATCHDOG_TIMEOUT

    # Autonomous fallback cycles through safe phases
    emulator.tick(now=105.0)
    assert emulator.nodes["node_a"].ew_color in (
        SignalLEDColor.GREEN,
        SignalLEDColor.YELLOW,
        SignalLEDColor.RED,
    )

    # Sending a packet restores normal mode
    ack_str = emulator.process_incoming_frame('{"cmd":"HEARTBEAT","seq":99}\n')
    assert "HEARTBEAT" in ack_str
    assert emulator.mode == HardwareMode.SIMULATION
    assert emulator.fault_code == HardwareFaultCode.NONE


def test_corridor_phase_synchronization_and_emergency():
    """Verify phase sync across all 4 intersections and emergency strobe beacon."""
    bridge = ESP32HardwareBridge(HardwareBridgeConfig(simulation_mode=True))
    bridge.connect()

    corridor_state = {
        "node_a": {"ew": "G", "ns": "R"},
        "node_b": {"ew": "G", "ns": "R"},
        "node_c": {"ew": "Y", "ns": "R"},
        "node_d": {"ew": "R", "ns": "G"},
    }

    res = bridge.sync_corridor(corridor_state, emergency_active=True)
    assert res["status"] == "OK"
    assert res["mmu_ok"] is True

    telemetry = bridge.get_telemetry()
    assert telemetry["emergency_strobe"] is True
    nodes = telemetry["nodes"]

    assert nodes["node_a"]["ew_color"] == SignalLEDColor.GREEN.value
    assert nodes["node_a"]["ns_color"] == SignalLEDColor.RED.value
    assert nodes["node_c"]["ew_color"] == SignalLEDColor.YELLOW.value
    assert nodes["node_d"]["ns_color"] == SignalLEDColor.GREEN.value

    bridge.disconnect()


def test_fastapi_hardware_endpoints():
    """Verify REST API hardware status, command, sync, and telemetry endpoints."""
    # Refresh heartbeat to ensure watchdog is healthy
    hb_init = send_hardware_command(ESP32CommandRequest(command="HEARTBEAT"))
    assert hb_init.get("status") == "OK"

    # 1. Status endpoint
    status_resp = get_hardware_status()
    assert status_resp.connected is True
    assert status_resp.watchdog_ok is True
    assert status_resp.mmu_ok is True
    assert "node_a" in status_resp.active_nodes

    # 2. Command endpoint - Lamp Test
    cmd_resp = send_hardware_command(ESP32CommandRequest(command="LAMP_TEST"))
    assert cmd_resp.get("status") == "OK"

    # 3. Command endpoint - Heartbeat
    hb_resp = send_hardware_command(ESP32CommandRequest(command="HEARTBEAT"))
    assert hb_resp.get("status") == "OK"

    # 4. Sync endpoint
    sync_req = ESP32SyncRequest(
        emergency=False,
        nodes={
            "node_a": {"ew": "GREEN", "ns": "RED"},
            "node_b": {"ew": "RED", "ns": "GREEN"},
            "node_c": {"ew": "GREEN", "ns": "RED"},
            "node_d": {"ew": "RED", "ns": "GREEN"},
        },
    )
    sync_resp = sync_corridor_to_hardware(sync_req)
    assert sync_resp.get("status") == "OK"

    # 5. Telemetry endpoint
    telemetry_resp = get_hardware_telemetry()
    assert telemetry_resp.mmu_tripped is False
    assert telemetry_resp.provenance == "REALTIME_HARDWARE"
    assert len(telemetry_resp.nodes) == 4


def test_diagnostic_testbench_subroutines():
    """Verify testbench CLI subroutines (lamp test, walking green, emergency, watchdog)."""
    bridge = ESP32HardwareBridge(
        HardwareBridgeConfig(simulation_mode=True, watchdog_threshold_sec=0.2)
    )
    bridge.connect()

    assert run_lamp_test(bridge, duration_sec=0.05) is True
    assert run_walking_green(bridge) is True
    assert run_emergency_strobe(bridge, duration_sec=0.05) is True

    bridge.disconnect()
