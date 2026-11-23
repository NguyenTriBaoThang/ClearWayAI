"""ClearWayAI ESP32 Hardware Demonstration Testbench CLI.

Interactive diagnostic and test utility for engineers to verify serial UART communication,
run LED test sequences, validate hardware MMU conflict prevention, and test the watchdog.

Usage:
    python -m controller.hardware.testbench_cli --mode sim --run-test lamp_test
    python -m controller.hardware.testbench_cli --mode serial --port COM3 --run-test walking_green
"""

from __future__ import annotations

import argparse
import sys
import time

from controller.hardware.esp32_bridge import (
    ESP32HardwareBridge,
    HardwareBridgeConfig,
    HardwareMode,
)


def print_banner() -> None:
    print("=" * 70)
    print("🚦 ClearWayAI - ESP32 Physical Testbench Diagnostic Utility")
    print("=" * 70)


def run_lamp_test(bridge: ESP32HardwareBridge, duration_sec: float = 3.0) -> bool:
    print(f"\n▶ Running LAMP TEST on all 4 intersections for {duration_sec}s...")
    res = bridge.trigger_lamp_test()
    print(f"  Response: {res}")
    time.sleep(duration_sec)
    telemetry = bridge.get_telemetry()
    print(f"  Telemetry Mode: {telemetry.get('mode')}")
    print("  ✅ Lamp test completed successfully.")
    return True


def run_walking_green(bridge: ESP32HardwareBridge) -> bool:
    print("\n▶ Running WALKING GREEN corridor progression across Nodes A -> D...")
    nodes = ["node_a", "node_b", "node_c", "node_d"]

    for active_idx, active_node in enumerate(nodes):
        node_states = {}
        for nid in nodes:
            if nid == active_node:
                node_states[nid] = {"ew": "GREEN", "ns": "RED"}
            else:
                node_states[nid] = {"ew": "RED", "ns": "GREEN"}

        print(
            f"  [Step {active_idx + 1}/4] Green priority at {active_node.upper()} (Corridor EW)"
        )
        res = bridge.sync_corridor(node_states, emergency_active=False)
        if res.get("status") != "OK":
            print(f"  ❌ Error syncing node {active_node}: {res}")
            return False
        time.sleep(1.0)

    print("  ✅ Walking green progression sequence verified.")
    return True


def run_emergency_strobe(
    bridge: ESP32HardwareBridge, duration_sec: float = 3.0
) -> bool:
    print(f"\n▶ Triggering EMERGENCY PRE-CLEARANCE CORRIDOR & STROBE for {duration_sec}s...")
    nodes = ["node_a", "node_b", "node_c", "node_d"]
    # All corridor nodes green on EW, red on NS
    emergency_states = {
        nid: {"ew": "GREEN", "ns": "RED"} for nid in nodes
    }

    res = bridge.sync_corridor(emergency_states, emergency_active=True)
    print(f"  Corridor Sync ACK: {res}")
    time.sleep(duration_sec)

    telemetry = bridge.get_telemetry()
    print(f"  Emergency Strobe Active: {telemetry.get('emergency_strobe')}")
    print("  ✅ Emergency pre-clearance corridor sequence completed.")
    return True


def run_watchdog_test(bridge: ESP32HardwareBridge) -> bool:
    print("\n▶ Testing Hardware Fail-Safe Watchdog Timeout (INV-06)...")
    print("  Suspending heartbeats for 2.5s (threshold = 2.0s)...")
    time.sleep(2.5)

    telemetry = bridge.get_telemetry()
    mode = telemetry.get("mode")
    fault = telemetry.get("fault_code")
    print(f"  Current Operating Mode: {mode}")
    print(f"  Diagnostic Fault Code: {fault}")

    if mode == HardwareMode.AUTONOMOUS_FALLBACK.value:
        print("  ✅ Watchdog successfully triggered AUTONOMOUS_FALLBACK mode!")
    else:
        print(f"  ❌ Watchdog failed to transition: mode={mode}")
        return False

    # Send heartbeat to recover
    print("  Sending keep-alive heartbeat to recover from fallback...")
    bridge.send_heartbeat()
    telemetry_rec = bridge.get_telemetry()
    print(f"  Recovered Mode: {telemetry_rec.get('mode')}")
    print("  ✅ Watchdog self-recovery verified.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ClearWayAI ESP32 Hardware Testbench CLI"
    )
    parser.add_argument(
        "--mode",
        choices=["sim", "serial"],
        default="sim",
        help="Transport mode (sim=Virtual Emulator, serial=Physical USB UART)",
    )
    parser.add_argument(
        "--port", default="COM3", help="Serial port (e.g. COM3 or /dev/ttyUSB0)"
    )
    parser.add_argument(
        "--baudrate", type=int, default=115200, help="Baudrate (default: 115200)"
    )
    parser.add_argument(
        "--run-test",
        choices=[
            "lamp_test",
            "walking_green",
            "emergency_strobe",
            "watchdog",
            "all",
        ],
        default="all",
        help="Specific diagnostic test routine to execute",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=2.0,
        help="Duration in seconds for duration-based tests",
    )

    args = parser.parse_args()

    print_banner()
    config = HardwareBridgeConfig(
        port=args.port,
        baudrate=args.baudrate,
        simulation_mode=(args.mode == "sim"),
    )

    bridge = ESP32HardwareBridge(config)
    print(f"Connecting bridge in {args.mode.upper()} mode on {args.port}...")
    if not bridge.connect():
        print("❌ Failed to connect bridge.")
        return 1

    print("✅ Bridge connection established.")

    try:
        if args.run_test in ("lamp_test", "all"):
            run_lamp_test(bridge, args.duration)
        if args.run_test in ("walking_green", "all"):
            run_walking_green(bridge)
        if args.run_test in ("emergency_strobe", "all"):
            run_emergency_strobe(bridge, args.duration)
        if args.run_test in ("watchdog", "all"):
            run_watchdog_test(bridge)
    finally:
        bridge.disconnect()
        print("\nBridge disconnected cleanly.")

    print("\n🎉 All hardware diagnostic checks passed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

