"""ClearWayAI Moving-Horizon Multi-Node Pre-Clearance Scheduler (`controller.scheduler`).

Contains real-time pre-clearance algorithms based on kinematic ETA estimation
and machine-learning clearance time predictions.
"""

from __future__ import annotations

from controller.scheduler.corridor_coordinator import (
    CorridorCoordinationReport,
    CorridorCoordinationStatus,
    CorridorCoordinatorConfig,
    MovingHorizonCorridorCoordinator,
    NodeCoordinationSchedule,
)
from controller.scheduler.preclearance_controller import (
    CorridorPreclearancePlan,
    PreclearanceConfig,
    PreclearanceController,
    PreclearanceDecision,
    PreclearanceState,
)

__all__ = [
    "CorridorCoordinationReport",
    "CorridorCoordinationStatus",
    "CorridorCoordinatorConfig",
    "CorridorPreclearancePlan",
    "MovingHorizonCorridorCoordinator",
    "NodeCoordinationSchedule",
    "PreclearanceConfig",
    "PreclearanceController",
    "PreclearanceDecision",
    "PreclearanceState",
]
