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
from controller.scheduler.preclearance_controller import (
    CorridorPreclearancePlan,
    PreclearanceConfig,
    PreclearanceController,
    PreclearanceDecision,
    PreclearanceState,
)

__all__ = [
    "CorridorPreclearancePlan",
    "EmergencyMission",
    "EmergencyMissionManager",
    "EmergencyVehicleType",
    "MissionStatus",
    "MultiNodeETAEvaluator",
    "MultiNodeETAReport",
    "NodeETAResult",
    "PreclearanceConfig",
    "PreclearanceController",
    "PreclearanceDecision",
    "PreclearanceState",
]
