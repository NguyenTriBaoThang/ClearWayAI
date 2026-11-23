"""ESP32 Physical Miniature Testbench API Router (`apps.api.src.routers.hardware`).

Exposes endpoints to monitor, command, and synchronize the physical ESP32 microcontroller
testbench (or virtual emulator) with the ClearWayAI corridor coordination engine.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from apps.api.src.schemas import (
    ESP32BridgeStatusResponse,
    ESP32CommandRequest,
    ESP32SyncRequest,
    ESP32TelemetryResponse,
)
from controller.hardware.esp32_bridge import (
    ESP32HardwareBridge,
    HardwareBridgeConfig,
)

router = APIRouter(prefix="/api/v1/hardware", tags=["Physical Hardware Bench"])

# Shared singleton instance of the hardware bridge
# Defaults to high-fidelity simulation mode for CI/CD and automated testing
hardware_bridge = ESP32HardwareBridge(
    HardwareBridgeConfig(simulation_mode=True)
)
hardware_bridge.connect()


@router.get("/status", response_model=ESP32BridgeStatusResponse)
def get_hardware_status() -> ESP32BridgeStatusResponse:
    """Retrieve current operational status, port, and watchdog health of the ESP32 bridge."""
    try:
        telemetry = hardware_bridge.get_telemetry()
        return ESP32BridgeStatusResponse(
            connected=hardware_bridge.is_connected(),
            mode=telemetry.get("mode", "SIMULATION"),
            port=telemetry.get("port", "COM3"),
            baudrate=telemetry.get("baudrate", 115200),
            watchdog_ok=telemetry.get("watchdog_ok", True),
            mmu_ok=not telemetry.get("mmu_tripped", False),
            active_nodes=list(telemetry.get("nodes", {}).keys()),
            watchdog_age_sec=telemetry.get("watchdog_age_sec", 0.0),
            transport=telemetry.get("transport", "EMULATOR"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query hardware status: {e}",
        ) from None


@router.post("/command")
def send_hardware_command(cmd_req: ESP32CommandRequest) -> dict[str, Any]:
    """Execute a manual control command on the physical testbench (e.g. LAMP_TEST, RESET_FAULTS)."""
    try:
        if cmd_req.command == "LAMP_TEST":
            return hardware_bridge.trigger_lamp_test()
        elif cmd_req.command == "RESET_FAULTS":
            return hardware_bridge.reset_faults()
        elif cmd_req.command == "HEARTBEAT":
            return hardware_bridge.send_heartbeat()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported hardware command: {cmd_req.command}",
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Command execution error: {e}",
        ) from None


@router.post("/sync")
def sync_corridor_to_hardware(sync_req: ESP32SyncRequest) -> dict[str, Any]:
    """Synchronize multi-intersection signal phase states to physical hardware LEDs."""
    try:
        ack = hardware_bridge.sync_corridor(
            nodes_state=sync_req.nodes,
            emergency_active=sync_req.emergency,
        )
        return ack
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Synchronization failure: {e}",
        ) from None


@router.get("/telemetry", response_model=ESP32TelemetryResponse)
def get_hardware_telemetry() -> ESP32TelemetryResponse:
    """Retrieve full low-level register states and telemetry from the ESP32 controller."""
    try:
        raw_telemetry = hardware_bridge.get_telemetry()
        return ESP32TelemetryResponse(
            mode=raw_telemetry.get("mode", "SIMULATION"),
            fault_code=raw_telemetry.get("fault_code", "NONE"),
            mmu_tripped=raw_telemetry.get("mmu_tripped", False),
            watchdog_age_sec=raw_telemetry.get("watchdog_age_sec", 0.0),
            watchdog_ok=raw_telemetry.get("watchdog_ok", True),
            emergency_strobe=raw_telemetry.get("emergency_strobe", False),
            packet_seq=raw_telemetry.get("packet_seq", 0),
            total_frames=raw_telemetry.get("total_frames", 0),
            nodes=raw_telemetry.get("nodes", {}),
            transport=raw_telemetry.get("transport", "EMULATOR"),
            port=raw_telemetry.get("port", "COM3"),
            baudrate=raw_telemetry.get("baudrate", 115200),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch hardware telemetry: {e}",
        ) from None

