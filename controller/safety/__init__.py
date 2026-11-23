"""ClearWayAI Independent Signal Safety Gateway Package (`controller.safety`).

Emulates a hardware Malfunction Management Unit (MMU) / Conflict Monitor Unit (CMU)
providing an independent, zero-trust safety boundary between AI/optimization controllers
and physical/simulated traffic signals:
1. Enforces conflict-free mutual exclusion (INV-01).
2. Clamps minimum green interval (INV-02: >=10s).
3. Enforces maximum green ceiling (INV-03: <=75s).
4. Guarantees mandatory yellow change (INV-04: >=3s) and all-red clearance (INV-05: >=2s).
5. Watchdog monitoring with communication loss fallback (INV-06).
"""

from __future__ import annotations

from controller.safety.signal_safety_gateway import (
    CorridorSafetyAudit,
    GatewayOperationalMode,
    GatewayTripReason,
    SafetyGatewayConfig,
    SafetyGatewayReport,
    SafetyInterventionRecord,
    SignalColor,
    SignalSafetyGateway,
)

__all__ = [
    "CorridorSafetyAudit",
    "GatewayOperationalMode",
    "GatewayTripReason",
    "SafetyGatewayConfig",
    "SafetyGatewayReport",
    "SafetyInterventionRecord",
    "SignalColor",
    "SignalSafetyGateway",
]
