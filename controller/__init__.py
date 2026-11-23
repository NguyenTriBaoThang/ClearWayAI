"""ClearWayAI Coordination & Safety Controller Package (`controller`).

Implements multi-intersection corridor coordination, emergency vehicle pre-clearance,
ETA estimation, signal phase scheduling, and independent safety gating.
"""

from controller.mission.emergency_mission import (
    EmergencyMission,
    EmergencyMissionManager,
    EmergencyVehicleType,
    MissionStatus,
)
from controller.mission.eta_estimator import (
    MultiNodeETAEvaluator,
    MultiNodeETAReport,
    NodeETAResult,
)
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
    "EmergencyMission",
    "EmergencyMissionManager",
    "EmergencyVehicleType",
    "MissionStatus",
    "MovingHorizonCorridorCoordinator",
    "MultiNodeETAEvaluator",
    "MultiNodeETAReport",
    "NodeCoordinationSchedule",
    "NodeETAResult",
    "PreclearanceConfig",
    "PreclearanceController",
    "PreclearanceDecision",
    "PreclearanceState",
]
