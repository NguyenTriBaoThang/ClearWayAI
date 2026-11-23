"""Data schemas for ClearWayAI API adhering to shared domain contracts."""

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(UTC)


# Domain Literals
OperationalMode = Literal["SIMULATION", "OFFLINE_VIDEO", "SHADOW_ADVISORY", "AUTHORIZED_PILOT"]
DataProvenance = Literal[
    "DEMO_FIXTURE", "SUMO_SIMULATED", "OFFLINE_VIDEO", "SHADOW_ADVISORY", "LIVE_CONNECTED"
]
SignalLightColor = Literal["red", "yellow", "green"]
VehicleType = Literal["motorcycle", "car", "suv", "bus", "truck", "ambulance", "fire_engine"]


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: Literal["healthy", "degraded", "unhealthy"] = "healthy"
    service: str = "clearway-api"
    version: str = "0.1.0"
    timestamp: datetime = Field(default_factory=utc_now)
    environment: str = "development"


class ModuleStatus(BaseModel):
    """Detailed status of individual system modules."""

    simulation: Literal["PLANNED", "IN_PROGRESS", "IMPLEMENTED", "VERIFIED"] = "VERIFIED"
    ai_clearance: Literal["PLANNED", "IN_PROGRESS", "IMPLEMENTED", "VERIFIED"] = "VERIFIED"
    traffic_signals: Literal["PLANNED", "IN_PROGRESS", "IMPLEMENTED", "VERIFIED"] = "VERIFIED"
    digital_twin: Literal["PLANNED", "IN_PROGRESS", "IMPLEMENTED", "VERIFIED"] = "VERIFIED"
    v2x_telemetry: Literal["UNAVAILABLE", "SIMULATED", "CONNECTED"] = "SIMULATED"
    hardware_bridge: Literal["PLANNED", "IN_PROGRESS", "IMPLEMENTED", "VERIFIED"] = "VERIFIED"


class SystemStatusResponse(BaseModel):
    """System operational status schema adhering to safety and provenance rules."""

    status: Literal["operational", "degraded", "offline"] = "operational"
    mode: OperationalMode = "SIMULATION"
    simulation_only: bool = True
    public_signal_control_permitted: bool = False
    data_provenance: DataProvenance = "DEMO_FIXTURE"
    demo_mode_enabled: bool = True
    modules: ModuleStatus = Field(default_factory=ModuleStatus)
    active_scenario: str | None = "demo-oak-5th-intersection"
    timestamp: datetime = Field(default_factory=utc_now)
    message: str = "ClearWayAI System Operational. All live telemetry and control disabled pending verification."


class VehicleTelemetry(BaseModel):
    """Vehicle kinematics and class telemetry snapshot."""

    vehicle_id: str
    vehicle_class: VehicleType
    speed_kmh: float
    position_x: float
    position_y: float
    position_z: float
    heading_deg: float
    lane_id: str
    is_priority_vehicle: bool = False
    mission_id: str | None = None
    provenance: DataProvenance = "DEMO_FIXTURE"


class SignalApproachTimingSchema(BaseModel):
    """Timing for an individual vehicular approach."""

    approach: str
    red_s: int
    yellow_s: int
    green_s: int
    cycle_s: int
    split_pct: int
    current_phase: SignalLightColor


class SignalStateSchema(BaseModel):
    """Comprehensive signal phase timing and coordination state."""

    intersection_id: str
    intersection_name: str
    cycle_time_s: int
    current_phase_name: str
    next_phase_name: str
    approaches: list[SignalApproachTimingSchema]
    provenance: DataProvenance = "DEMO_FIXTURE"


class HardwareStatusSchema(BaseModel):
    """V2I / V2X hardware pipeline telemetry and channel diagnostics."""

    network_id: str
    obu_vehicles_online: int
    obu_pct: float
    rsu_online: int
    rsu_pct: float
    edge_controllers_online: int
    signal_controllers_online: int
    v2x_status: Literal["Active", "Degraded", "Offline", "Simulated"]
    latency_ms: float
    packet_loss_pct: float
    provenance: DataProvenance = "DEMO_FIXTURE"


class EmergencyMissionSchema(BaseModel):
    """Active emergency vehicle corridor pre-clearance mission."""

    mission_id: str
    vehicle_id: str
    vehicle_type: Literal["ambulance", "firetruck"]
    target_facility: str
    eta_hospital_min: float
    status: Literal["ACTIVE", "STANDBY", "COMPLETED", "CANCELLED"]
    corridor_intersections: list[str]
    provenance: DataProvenance = "DEMO_FIXTURE"


class TrafficAnalyticsSchema(BaseModel):
    """Aggregated traffic performance indices and delay deltas."""

    intersection_id: str
    performance_index: float
    throughput_pct_change: float
    avg_delay_pct_change: float
    stops_per_veh_pct_change: float
    occupancy_pct: float
    avg_speed_kmh: float
    avg_queue_m: float
    backlog_m: float
    provenance: DataProvenance = "DEMO_FIXTURE"


class TelemetrySnapshotSchema(BaseModel):
    """Full atomic intersection telemetry snapshot streamed over WebSocket."""

    intersection_id: str
    timestamp: datetime = Field(default_factory=utc_now)
    sim_time_sec: float
    vehicles: list[VehicleTelemetry] = Field(default_factory=list)
    signals: SignalStateSchema | None = None
    hardware: HardwareStatusSchema | None = None
    analytics: TrafficAnalyticsSchema | None = None
    active_mission: EmergencyMissionSchema | None = None
    provenance: DataProvenance = "DEMO_FIXTURE"


# --- Task 42 Extended REST API Schemas ---


# 1. Simulation Schemas
class SimulationCreateRequest(BaseModel):
    """Request payload to instantiate a simulation run."""

    name: str = "Oak-5th Synthetic Corridor"
    scenario_id: str = "normal"
    use_synthetic_engine: bool = True


class SimulationResponse(BaseModel):
    """Response payload for simulation episode metadata."""

    simulation_id: str
    name: str
    scenario_id: str
    status: str
    started_at: str
    stopped_at: str | None = None
    total_steps: int = 0
    emergency_events: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class SimulationStepRequest(BaseModel):
    """Request payload to advance a simulation episode."""

    dt: float = Field(default=0.1, ge=0.01, le=1.0)
    active_mission_id: str | None = None


class SimulationStepResponse(BaseModel):
    """Response payload following a simulation step."""

    simulation_id: str
    sim_time_sec: float
    total_steps: int
    active_vehicles_count: int
    traffic_lights: dict[str, int]
    emergency_vehicle_active: bool
    status: str = "RUNNING"


# 2. Priority Mission Schemas
class MissionCreateRequest(BaseModel):
    """Request payload to dispatch an emergency priority mission."""

    vehicle_id: str = "AMB-339"
    vehicle_type: str = "emergency_ambulance"
    origin: str = "West Feeder Gate"
    destination: str = "Metropolitan Trauma Center"
    target_speed_mps: float = 18.5
    priority_level: int = 1


class MissionResponse(BaseModel):
    """Response payload representing an emergency mission."""

    mission_id: str
    vehicle_id: str
    vehicle_type: str
    status: str
    origin: str
    destination: str
    dispatched_at: str
    arrived_at: str | None = None
    current_position_m: float
    current_speed_kmh: float
    progress_ratio: float
    is_active: bool
    route_nodes: list[str] = Field(default_factory=list)


class NodeETASchema(BaseModel):
    """Arrival ETA metrics for a specific stopline."""

    node_id: str
    stopline_x_m: float
    distance_to_stopline_m: float
    eta_seconds: float
    has_passed: bool
    confidence_score: float = 1.0


class MultiNodeETAResponse(BaseModel):
    """Corridor-wide multi-intersection kinematic arrival ETA report."""

    mission_id: str
    vehicle_id: str
    current_position_m: float
    current_speed_kmh: float
    etas_by_node: dict[str, NodeETASchema]
    hospital_eta_sec: float
    calculation_timestamp: float
    provenance: str = "KINEMATIC_CORRIDOR_ESTIMATOR"


# 3. AI Clearance Prediction Schemas
class ClearancePredictRequest(BaseModel):
    """Request payload for ML queue clearance shockwave prediction."""

    node_id: str = "node_b"
    approach_id: str = "EB"
    queue_length_meters: float = Field(default=35.0, ge=0.0)
    queued_vehicle_count: int = Field(default=12, ge=0)
    vehicle_count: int = Field(default=16, ge=0)
    motorcycle_ratio: float = Field(default=0.625, ge=0.0, le=1.0)
    approach_occupancy_ratio: float = Field(default=0.45, ge=0.0, le=1.0)
    weather: str = "clear"
    force_model: str | None = None


class ClearancePredictResponse(BaseModel):
    """Response payload with predicted clearance duration and model provenance."""

    node_id: str
    predicted_clearance_sec: float
    confidence_score: float
    model_name: str
    model_type: str
    fallback_used: bool
    fallback_tier: str
    latency_ms: float
    provenance: str


class ModelMetadataSchema(BaseModel):
    """Model registry catalog metadata."""

    name: str
    role: str
    model_type: str
    val_mae: float
    test_mae: float
    test_r2: float
    latency_ms: float
    provenance: str
    description: str


class ModelRegistryCatalogResponse(BaseModel):
    """Clearance Model Registry catalog response."""

    registry_version: str
    champion_tabular: str
    champion_sequential: str
    models: list[ModelMetadataSchema]


# 4. Corridor Coordination & Safety Schemas
class CorridorPlanResponse(BaseModel):
    """Consolidated snapshot of corridor moving-horizon coordination plan."""

    mission_id: str | None
    vehicle_id: str | None
    corridor_status: str
    current_position_m: float
    current_speed_kmh: float
    active_horizon_nodes: list[str]
    cleared_nodes: list[str]
    commanded_phases: dict[str, int]
    coordination_offsets_sec: dict[str, float]
    spillback_alerts: list[str]
    total_active_holds: int
    timestamp_sec: float
    provenance: str


class PreclearanceEvaluateRequest(BaseModel):
    """Request to evaluate JIT pre-clearance trigger for an intersection."""

    node_id: str = "node_a"
    mission_id: str | None = None
    queue_length_meters: float = 30.0
    queued_vehicle_count: int = 10
    sim_time: float = 10.0


class PreclearanceDecisionResponse(BaseModel):
    """Response for intersection pre-clearance evaluation."""

    node_id: str
    state: str
    should_actuate: bool
    commanded_phase: int
    delta_trigger_sec: float
    ev_eta_sec: float
    predicted_clearance_sec: float
    reason: str


class RecoveryInitiateRequest(BaseModel):
    """Request to initiate post-clearance recovery."""

    node_id: str = "node_a"
    preemption_duration_sec: float = 25.0
    cross_queue_meters: float = 30.0
    sim_time: float = 50.0


class RecoveryStatusResponse(BaseModel):
    """Response for post-clearance recovery state."""

    node_id: str
    state: str
    initial_green_debt_sec: float
    remaining_green_debt_sec: float
    current_recovery_cycle: int
    bonus_green_allocated_sec: float
    commanded_phase: int
    is_recovered: bool
    reason: str


class SafetyAuditResponse(BaseModel):
    """Response for independent MMU safety audit."""

    all_nodes_safe: bool
    sanitized_phases: dict[str, int]
    total_interventions_corridor: int
    timestamp_sec: float
    provenance: str = "INDEPENDENT_SIGNAL_SAFETY_GATEWAY"
