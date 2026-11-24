"""
ClearWayAI - Variable Message Sign (VMS) Advisory System (`controller.vms.vms_manager`).

Generates real-time, safety-compliant bilingual driver advisory messages for 4 overhead
cantilever/gantry LED display boards positioned along the arterial corridor:
- VMS-A: Gantry at x = -80m (Approaching Node A, Maple St)
- VMS-B: Gantry at x = 170m (Approaching Node B, Oak St / INT-0457)
- VMS-C: Gantry at x = 420m (Approaching Node C, Pine St)
- VMS-D: Gantry at x = 670m (Approaching Node D, Elm St)

Operational Advisory Modes:
1. NOMINAL:
   VI: "CHÚC QUÝ KHÁCH BÌNH AN"
   EN: "SPEED LIMIT 50 KM/H"
2. PRE_CLEARANCE (Queue shockwave draining):
   VI: "ĐANG GIẢI TỎA DÒNG XE"
   EN: "PRIORITY CORRIDOR AHEAD"
3. EMERGENCY_CORRIDOR (Ambulance in immediate approach window):
   VI: "NHƯỜNG ĐƯỜNG XE CẤP CỨU"
   EN: "MERGE RIGHT >>> AMB-339"
4. CAUTION_RECOVERY (Post-transit phase equilibrium adjustment):
   VI: "CHÚ Ý GIAO LỘ ĐIỀU TIẾT"
   EN: "RESUMING NORMAL TRAFFIC"
"""

from __future__ import annotations

import sys
import time
from dataclasses import asdict, dataclass, field
from typing import Any

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        def __str__(self) -> str:
            return str(self.value)


class VMSAdvisoryMode(StrEnum):
    """Operational advisory display mode for arterial overhead VMS boards."""

    NOMINAL = "NOMINAL"
    PRE_CLEARANCE = "PRE_CLEARANCE"
    EMERGENCY_CORRIDOR = "EMERGENCY_CORRIDOR"
    CAUTION_RECOVERY = "CAUTION_RECOVERY"


# Standard Gantry Coordinates (Meters along Eastbound 5th Ave)
VMS_GANTRY_TOPOLOGY: dict[str, dict[str, Any]] = {
    "node_a": {
        "board_id": "VMS-A",
        "node_id": "node_a",
        "target_stopline_x": 0.0,
        "gantry_x_m": -80.0,
        "cross_street": "Maple St",
    },
    "node_b": {
        "board_id": "VMS-B",
        "node_id": "node_b",
        "target_stopline_x": 250.0,
        "gantry_x_m": 170.0,
        "cross_street": "Oak St",
    },
    "node_c": {
        "board_id": "VMS-C",
        "node_id": "node_c",
        "target_stopline_x": 500.0,
        "gantry_x_m": 420.0,
        "cross_street": "Pine St",
    },
    "node_d": {
        "board_id": "VMS-D",
        "node_id": "node_d",
        "target_stopline_x": 750.0,
        "gantry_x_m": 670.0,
        "cross_street": "Elm St",
    },
}


@dataclass
class VMSBoardStatus:
    """Real-time display status of an individual overhead VMS gantry board."""

    board_id: str
    node_id: str
    gantry_x_m: float
    target_stopline_x: float
    mode: VMSAdvisoryMode
    message_line_1_vi: str
    message_line_2_en: str
    recommended_speed_kmh: int
    flashing_strobe: bool
    chevron_direction: str  # "RIGHT", "NONE", "BOTH"
    ev_distance_m: float | None = None
    ev_eta_sec: float | None = None
    timestamp_sec: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["mode"] = str(self.mode)
        return d


@dataclass
class VMSCorridorStatus:
    """Corridor-wide collection of all 4 overhead VMS advisory displays."""

    corridor_status: str
    boards: dict[str, VMSBoardStatus]
    active_emergency: bool
    emergency_vehicle_id: str | None
    emergency_position_m: float | None
    timestamp_sec: float
    provenance: str = "CLEARWAY_VMS_ADVISORY"

    def to_dict(self) -> dict[str, Any]:
        return {
            "corridor_status": self.corridor_status,
            "boards": {k: v.to_dict() for k, v in self.boards.items()},
            "active_emergency": self.active_emergency,
            "emergency_vehicle_id": self.emergency_vehicle_id,
            "emergency_position_m": self.emergency_position_m,
            "timestamp_sec": self.timestamp_sec,
            "provenance": self.provenance,
        }


class VMSManager:
    """Evaluates mission kinematics and signal coordination state to generate VMS advisories."""

    def __init__(self) -> None:
        self.gantries = VMS_GANTRY_TOPOLOGY

    def evaluate_board(
        self,
        node_id: str,
        ev_active: bool,
        ev_x: float | None,
        ev_speed_mps: float | None = None,
        ev_id: str = "AMB-339",
        sim_time: float = 0.0,
    ) -> VMSBoardStatus:
        """Evaluate advisory display mode and text for a single intersection VMS gantry."""
        info = self.gantries.get(node_id)
        if not info:
            raise KeyError(f"Unknown node_id for VMS: {node_id}")

        gantry_x = info["gantry_x_m"]
        stopline_x = info["target_stopline_x"]

        # Case 1: No active emergency mission
        if not ev_active or ev_x is None:
            return VMSBoardStatus(
                board_id=info["board_id"],
                node_id=node_id,
                gantry_x_m=gantry_x,
                target_stopline_x=stopline_x,
                mode=VMSAdvisoryMode.NOMINAL,
                message_line_1_vi="CHÚC QUÝ KHÁCH BÌNH AN",
                message_line_2_en="SPEED LIMIT 50 KM/H",
                recommended_speed_kmh=50,
                flashing_strobe=False,
                chevron_direction="NONE",
                ev_distance_m=None,
                ev_eta_sec=None,
                timestamp_sec=sim_time,
            )

        # Distance from EV to stopline and to gantry
        dist_to_stopline = stopline_x - ev_x
        spd = max(10.0, ev_speed_mps if ev_speed_mps is not None else 18.5)
        eta_sec = max(0.0, dist_to_stopline / spd) if dist_to_stopline > 0 else 0.0

        # Case 2: EV has already cleared this intersection
        if dist_to_stopline < -15.0:
            if dist_to_stopline >= -120.0:
                # Immediate tail recovery zone
                return VMSBoardStatus(
                    board_id=info["board_id"],
                    node_id=node_id,
                    gantry_x_m=gantry_x,
                    target_stopline_x=stopline_x,
                    mode=VMSAdvisoryMode.CAUTION_RECOVERY,
                    message_line_1_vi="CHÚ Ý GIAO LỘ ĐIỀU TIẾT",
                    message_line_2_en="RESUMING NORMAL TRAFFIC",
                    recommended_speed_kmh=40,
                    flashing_strobe=False,
                    chevron_direction="NONE",
                    ev_distance_m=round(dist_to_stopline, 1),
                    ev_eta_sec=0.0,
                    timestamp_sec=sim_time,
                )
            else:
                # Completely cleared
                return VMSBoardStatus(
                    board_id=info["board_id"],
                    node_id=node_id,
                    gantry_x_m=gantry_x,
                    target_stopline_x=stopline_x,
                    mode=VMSAdvisoryMode.NOMINAL,
                    message_line_1_vi="CHÚC QUÝ KHÁCH BÌNH AN",
                    message_line_2_en="SPEED LIMIT 50 KM/H",
                    recommended_speed_kmh=50,
                    flashing_strobe=False,
                    chevron_direction="NONE",
                    ev_distance_m=round(dist_to_stopline, 1),
                    ev_eta_sec=0.0,
                    timestamp_sec=sim_time,
                )

        # Case 3: EV is in immediate approach (< 180m from stopline) -> MERGE RIGHT
        if dist_to_stopline <= 180.0:
            return VMSBoardStatus(
                board_id=info["board_id"],
                node_id=node_id,
                gantry_x_m=gantry_x,
                target_stopline_x=stopline_x,
                mode=VMSAdvisoryMode.EMERGENCY_CORRIDOR,
                message_line_1_vi="NHƯỜNG ĐƯỜNG XE CẤP CỨU",
                message_line_2_en=f"MERGE RIGHT >>> {ev_id}",
                recommended_speed_kmh=30,
                flashing_strobe=True,
                chevron_direction="RIGHT",
                ev_distance_m=round(dist_to_stopline, 1),
                ev_eta_sec=round(eta_sec, 1),
                timestamp_sec=sim_time,
            )

        # Case 4: EV is approaching in lookahead moving-horizon (180m - 450m) -> PRE-CLEARANCE
        if dist_to_stopline <= 450.0:
            return VMSBoardStatus(
                board_id=info["board_id"],
                node_id=node_id,
                gantry_x_m=gantry_x,
                target_stopline_x=stopline_x,
                mode=VMSAdvisoryMode.PRE_CLEARANCE,
                message_line_1_vi="ĐANG GIẢI TỎA DÒNG XE",
                message_line_2_en="PRIORITY CORRIDOR AHEAD",
                recommended_speed_kmh=40,
                flashing_strobe=True,
                chevron_direction="RIGHT",
                ev_distance_m=round(dist_to_stopline, 1),
                ev_eta_sec=round(eta_sec, 1),
                timestamp_sec=sim_time,
            )

        # Case 5: EV is still far upstream (> 450m)
        return VMSBoardStatus(
            board_id=info["board_id"],
            node_id=node_id,
            gantry_x_m=gantry_x,
            target_stopline_x=stopline_x,
            mode=VMSAdvisoryMode.NOMINAL,
            message_line_1_vi="CHÚC QUÝ KHÁCH BÌNH AN",
            message_line_2_en="SPEED LIMIT 50 KM/H",
            recommended_speed_kmh=50,
            flashing_strobe=False,
            chevron_direction="NONE",
            ev_distance_m=round(dist_to_stopline, 1),
            ev_eta_sec=round(eta_sec, 1),
            timestamp_sec=sim_time,
        )

    def evaluate_corridor(
        self,
        ev_active: bool,
        ev_x: float | None,
        ev_speed_mps: float | None = None,
        ev_id: str = "AMB-339",
        sim_time: float = 0.0,
    ) -> VMSCorridorStatus:
        """Evaluate and return advisory status across all 4 corridor VMS gantries."""
        boards = {}
        for nid in self.gantries:
            boards[nid] = self.evaluate_board(
                node_id=nid,
                ev_active=ev_active,
                ev_x=ev_x,
                ev_speed_mps=ev_speed_mps,
                ev_id=ev_id,
                sim_time=sim_time,
            )

        status_str = "EMERGENCY_CORRIDOR_ACTIVE" if ev_active else "NOMINAL_TRAFFIC"
        return VMSCorridorStatus(
            corridor_status=status_str,
            boards=boards,
            active_emergency=ev_active,
            emergency_vehicle_id=ev_id if ev_active else None,
            emergency_position_m=round(ev_x, 1) if ev_x is not None else None,
            timestamp_sec=sim_time,
        )


# Global singleton instance
vms_manager = VMSManager()
