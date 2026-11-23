"""ClearWayAI Emergency Mission Lifecycle & Dispatch Manager (`controller.mission`).

Models emergency response vehicle missions (e.g. AMB-339 Ambulance, Fire Brigade),
tracking lifecycle state transitions, spatial-temporal corridor routing, and telemetry updates.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class MissionStatus(StrEnum):
    """Lifecycle status of an emergency response mission."""

    PENDING = "PENDING"
    DISPATCHED = "DISPATCHED"
    APPROACHING = "APPROACHING"
    CORRIDOR_TRANSIT = "CORRIDOR_TRANSIT"
    ARRIVED = "ARRIVED"
    ABORTED = "ABORTED"
    COMPLETED = "COMPLETED"


class EmergencyVehicleType(StrEnum):
    """Classification of priority emergency response vehicles."""

    AMBULANCE = "emergency_ambulance"
    FIRE_ENGINE = "emergency_fire"
    POLICE_ESCORT = "emergency_police"


# Corridor Reference Milestones
CORRIDOR_ENTRY_X_METERS: float = -200.0  # West feeder entry
NODE_A_X_METERS: float = 0.0  # First intersection stopline
NODE_D_X_METERS: float = 900.0  # Final intersection stopline
HOSPITAL_X_METERS: float = 1100.0  # Metropolitan Hospital egress stopline
TOTAL_CORRIDOR_DISTANCE_METERS: float = HOSPITAL_X_METERS - CORRIDOR_ENTRY_X_METERS  # 1300.0m


@dataclass
class EmergencyMission:
    """Represents an active or historic priority corridor transit mission."""

    mission_id: str
    vehicle_id: str
    vehicle_type: EmergencyVehicleType = EmergencyVehicleType.AMBULANCE
    origin: str = "West Feeder Gate"
    destination: str = "Metropolitan Trauma Center"
    status: MissionStatus = MissionStatus.PENDING
    depart_time_sec: float = 0.0
    route_nodes: list[str] = field(default_factory=lambda: ["node_a", "node_b", "node_c", "node_d"])
    route_edges: list[str] = field(
        default_factory=lambda: [
            "edge_west_to_a",
            "edge_a_to_b",
            "edge_b_to_c",
            "edge_c_to_d",
            "edge_d_to_east",
        ]
    )
    target_speed_mps: float = 18.5  # ~66.6 km/h priority transit cruise
    max_speed_mps: float = 22.22  # ~80.0 km/h emergency ceiling
    current_position_m: float = CORRIDOR_ENTRY_X_METERS
    current_speed_mps: float = 0.0
    current_edge: str = "edge_west_to_a"
    priority_level: int = 1
    provenance: str = "SIMULATED_DISPATCH"
    dispatched_timestamp: float = field(default_factory=time.time)
    arrived_timestamp: float | None = None
    abort_reason: str | None = None

    @property
    def is_active(self) -> bool:
        """True if the mission is currently executing in the corridor."""
        return self.status in (
            MissionStatus.DISPATCHED,
            MissionStatus.APPROACHING,
            MissionStatus.CORRIDOR_TRANSIT,
        )

    @property
    def current_speed_kmh(self) -> float:
        """Vehicle velocity in kilometers per hour."""
        return round(self.current_speed_mps * 3.6, 1)

    @property
    def progress_ratio(self) -> float:
        """Normalized spatial progress along the arterial route [0.0, 1.0]."""
        distance_covered = self.current_position_m - CORRIDOR_ENTRY_X_METERS
        return max(0.0, min(1.0, round(distance_covered / TOTAL_CORRIDOR_DISTANCE_METERS, 4)))

    def to_dict(self) -> dict[str, Any]:
        """Serialize mission state to JSON-compatible dictionary."""
        d = asdict(self)
        d["status"] = str(self.status)
        d["vehicle_type"] = str(self.vehicle_type)
        d["current_speed_kmh"] = self.current_speed_kmh
        d["progress_ratio"] = self.progress_ratio
        d["is_active"] = self.is_active
        return d


class EmergencyMissionManager:
    """Manages lifecycle, state progression, and telemetry for corridor missions."""

    def __init__(self) -> None:
        self._missions: dict[str, EmergencyMission] = {}
        self._active_mission_id: str | None = None

    def create_mission(
        self,
        mission_id: str = "mission-amb-339",
        vehicle_id: str = "AMB-339",
        vehicle_type: EmergencyVehicleType = EmergencyVehicleType.AMBULANCE,
        target_speed_mps: float = 18.5,
        priority_level: int = 1,
        depart_time_sec: float = 0.0,
    ) -> EmergencyMission:
        """Initialize and register a new emergency mission."""
        mission = EmergencyMission(
            mission_id=mission_id,
            vehicle_id=vehicle_id,
            vehicle_type=vehicle_type,
            target_speed_mps=target_speed_mps,
            priority_level=priority_level,
            depart_time_sec=depart_time_sec,
            status=MissionStatus.PENDING,
            current_position_m=CORRIDOR_ENTRY_X_METERS,
            current_speed_mps=0.0,
        )
        self._missions[mission_id] = mission
        return mission

    def dispatch_mission(self, mission_id: str) -> EmergencyMission:
        """Dispatch a pending mission onto the arterial corridor."""
        mission = self.get_mission(mission_id)
        if not mission:
            raise KeyError(f"Mission '{mission_id}' not found.")

        if mission.status not in (MissionStatus.PENDING, MissionStatus.DISPATCHED):
            raise ValueError(f"Cannot dispatch mission in status '{mission.status}'.")

        mission.status = MissionStatus.DISPATCHED
        mission.dispatched_timestamp = time.time()
        self._active_mission_id = mission_id
        return mission

    def update_telemetry(
        self,
        position_m: float,
        speed_mps: float,
        current_edge: str | None = None,
        mission_id: str | None = None,
    ) -> EmergencyMission:
        """Update vehicle telemetry and automatically transition lifecycle status."""
        m_id = mission_id or self._active_mission_id
        if not m_id:
            raise ValueError("No active mission to update telemetry for.")

        mission = self.get_mission(m_id)
        if not mission:
            raise KeyError(f"Mission '{m_id}' not found.")

        mission.current_position_m = round(position_m, 2)
        mission.current_speed_mps = max(0.0, round(speed_mps, 2))
        if current_edge:
            mission.current_edge = current_edge

        # Dynamic state progression based on spatial landmarks
        if mission.status in (
            MissionStatus.DISPATCHED,
            MissionStatus.APPROACHING,
            MissionStatus.CORRIDOR_TRANSIT,
        ):
            if mission.current_position_m >= HOSPITAL_X_METERS:
                mission.status = MissionStatus.ARRIVED
                mission.arrived_timestamp = time.time()
                if self._active_mission_id == m_id:
                    self._active_mission_id = None
            elif mission.current_position_m >= NODE_A_X_METERS:
                mission.status = MissionStatus.CORRIDOR_TRANSIT
            elif mission.current_position_m >= -60.0:  # Within 60m of Node A
                mission.status = MissionStatus.APPROACHING
            else:
                mission.status = MissionStatus.DISPATCHED

        return mission

    def advance_kinematics(
        self,
        dt_sec: float,
        acceleration_mps2: float = 2.5,
        mission_id: str | None = None,
    ) -> EmergencyMission:
        """Simulate deterministic vehicle motion forward by dt_sec seconds."""
        m_id = mission_id or self._active_mission_id
        if not m_id:
            raise ValueError("No active mission to advance kinematics for.")

        mission = self.get_mission(m_id)
        if not mission or not mission.is_active:
            raise ValueError(f"Mission '{m_id}' is not currently active.")

        v_curr = mission.current_speed_mps
        v_target = mission.target_speed_mps

        # Smooth acceleration towards target speed
        if v_curr < v_target:
            v_next = min(v_target, v_curr + acceleration_mps2 * dt_sec)
        else:
            v_next = max(v_target, v_curr - acceleration_mps2 * dt_sec)

        avg_v = (v_curr + v_next) / 2.0
        delta_x = avg_v * dt_sec
        new_pos = mission.current_position_m + delta_x

        # Resolve edge according to x position
        if new_pos < 0.0:
            edge = "edge_west_to_a"
        elif new_pos < 300.0:
            edge = "edge_a_to_b"
        elif new_pos < 600.0:
            edge = "edge_b_to_c"
        elif new_pos < 900.0:
            edge = "edge_c_to_d"
        else:
            edge = "edge_d_to_east"

        return self.update_telemetry(
            position_m=new_pos,
            speed_mps=v_next,
            current_edge=edge,
            mission_id=m_id,
        )

    def abort_mission(
        self, mission_id: str, reason: str = "Operator cancelled"
    ) -> EmergencyMission:
        """Abort an active or pending mission."""
        mission = self.get_mission(mission_id)
        if not mission:
            raise KeyError(f"Mission '{mission_id}' not found.")

        mission.status = MissionStatus.ABORTED
        mission.abort_reason = reason
        if self._active_mission_id == mission_id:
            self._active_mission_id = None
        return mission

    def complete_mission(self, mission_id: str) -> EmergencyMission:
        """Mark mission as fully completed after hospital handoff."""
        mission = self.get_mission(mission_id)
        if not mission:
            raise KeyError(f"Mission '{mission_id}' not found.")

        mission.status = MissionStatus.COMPLETED
        if not mission.arrived_timestamp:
            mission.arrived_timestamp = time.time()
        if self._active_mission_id == mission_id:
            self._active_mission_id = None
        return mission

    def get_mission(self, mission_id: str) -> EmergencyMission | None:
        """Retrieve mission by ID."""
        return self._missions.get(mission_id)

    def get_active_mission(self) -> EmergencyMission | None:
        """Retrieve the currently active corridor mission, if any."""
        if self._active_mission_id:
            return self._missions.get(self._active_mission_id)
        for m in self._missions.values():
            if m.is_active:
                return m
        return None

    def list_missions(self) -> list[EmergencyMission]:
        """Return list of all registered missions."""
        return list(self._missions.values())
