"""ClearWayAI Coordination & Safety Controller Package (`controller`).

Implements multi-intersection corridor coordination, emergency vehicle pre-clearance,
ETA estimation, signal phase scheduling, post-clearance recovery, and independent safety gating.
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
from controller.recovery.recovery_controller import (
    CorridorRecoveryReport,
    NodeRecoveryStatus,
    PostClearanceRecoveryController,
    RecoveryConfig,
    RecoveryState,
)
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
    "CorridorRecoveryReport",
    "CorridorSafetyAudit",
    "EmergencyMission",
    "EmergencyMissionManager",
    "EmergencyVehicleType",
    "ESP32HardwareBridge",
    "GatewayOperationalMode",
    "GatewayTripReason",
    "HardwareBridgeConfig",
    "HardwareFaultCode",
    "HardwareMode",
    "MissionStatus",
    "MovingHorizonCorridorCoordinator",
    "MultiNodeETAEvaluator",
    "MultiNodeETAReport",
    "NodeCoordinationSchedule",
    "NodeETAResult",
    "NodeRecoveryStatus",
    "NodeSignalHardware",
    "PostClearanceRecoveryController",
    "PreclearanceConfig",
    "PreclearanceController",
    "PreclearanceDecision",
    "PreclearanceState",
    "RecoveryConfig",
    "RecoveryState",
    "SafetyGatewayConfig",
    "SafetyGatewayReport",
    "SafetyInterventionRecord",
    "SignalColor",
    "SignalLEDColor",
    "SignalSafetyGateway",
    "VirtualESP32Emulator",
]
