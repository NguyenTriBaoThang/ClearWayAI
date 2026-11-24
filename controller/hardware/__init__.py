"""Hardware Integration Package for ClearWayAI (`controller.hardware`).

Provides physical microcontroller bridges (ESP32), serial/UART framing protocols,
virtual hardware emulators for CI/CD, and hardware safety monitors (MMU & Watchdog).
"""

from controller.hardware.esp32_bridge import (
    ESP32HardwareBridge,
    HardwareBridgeConfig,
    HardwareFaultCode,
    HardwareMode,
    NodeSignalHardware,
    SignalLEDColor,
    VirtualESP32Emulator,
)

__all__ = [
    "ESP32HardwareBridge",
    "HardwareBridgeConfig",
    "HardwareFaultCode",
    "HardwareMode",
    "NodeSignalHardware",
    "SignalLEDColor",
    "VirtualESP32Emulator",
]
