"""Data schemas for ClearWayAI API."""

from datetime import datetime, timezone
from typing import Optional, Literal
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


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
    mode: Literal["SIMULATION", "OFFLINE_VIDEO", "SHADOW_ADVISORY", "AUTHORIZED_PILOT"] = "SIMULATION"
    simulation_only: bool = True
    public_signal_control_permitted: bool = False
    data_provenance: Literal["DEMO_FIXTURE", "SUMO_SIMULATED", "OFFLINE_VIDEO", "SHADOW_ADVISORY", "LIVE_CONNECTED"] = "DEMO_FIXTURE"
    demo_mode_enabled: bool = True
    modules: ModuleStatus = Field(default_factory=ModuleStatus)
    active_scenario: Optional[str] = "demo-oak-5th-intersection"
    timestamp: datetime = Field(default_factory=utc_now)
    message: str = "ClearWayAI System Initialized. All live telemetry and control disabled pending verification."
