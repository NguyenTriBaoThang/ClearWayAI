"""ClearWayAI Post-Clearance Smooth Recovery State Machine (`controller.recovery`).

Provides smooth multi-cycle equilibrium recovery for intersections after priority
preemption clearance:
1. Calculates accumulated cross-street green debt and vehicle deficit demand.
2. Amortizes green debt smoothly across multiple recovery cycles to prevent network shock.
3. Resynchronizes local cycle offsets with corridor master clock for green-wave restoration.
4. Enforces safety bounds (minimum green, safe yellow/all-red, anti-starvation limits).
"""

from __future__ import annotations

from controller.recovery.recovery_controller import (
    CorridorRecoveryReport,
    NodeRecoveryStatus,
    PostClearanceRecoveryController,
    RecoveryConfig,
    RecoveryState,
)

__all__ = [
    "CorridorRecoveryReport",
    "NodeRecoveryStatus",
    "PostClearanceRecoveryController",
    "RecoveryConfig",
    "RecoveryState",
]

