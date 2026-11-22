"""Data schemas for ClearWayAI API adhering to shared domain contracts."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(UTC)


# Domain Literals
OperationalMode = Literal["SIMULATION", "OFFLINE_VIDEO", "SHADOW_ADVISORY", "AUTHORIZED_PILOT"]
DataProvenance = Literal["DEMO_FIXTURE", "SUMO_SIMULATED", "OFFLINE_VIDEO", "SHADOW_ADVISORY", "LIVE_CONNECTED"]
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
    simulation: Literal["PLANNED", "IN_PROGRESS", "IMPLEMENTED", "VERIFIED"] = "PLANNED"
    ai_clearance: Literal["PLANNED", "IN_PROGRESS", "IMPLEMENTED", "VERIFIED"] = "PLANNED"
    traffic_signals: Literal["PLANNED", "IN_PROGRESS", "IMPLEMENTED", "VERIFIED"] = "PLANNED"
    digital_twin: Literal["PLANNED", "IN_PROGRESS", "IMPLEMENTED", "VERIFIED"] = "PLANNED"
    v2x_telemetry: Literal["UNAVAILABLE", "SIMULATED", "CONNECTED"] = "UNAVAILABLE"
    hardware_bridge: Literal["PLANNED", "IN_PROGRESS", "IMPLEMENTED", "VERIFIED"] = "PLANNED"


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
    message: str = "ClearWayAI System Initialized. All live telemetry and control disabled pending verification."


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
