"""ClearWayAI Multi-Node ETA Estimator (`controller.mission`).

Computes dynamic Estimated Time of Arrival (ETA) for emergency vehicles
across multi-intersection arterial corridors (Nodes A -> B -> C -> D -> Hospital).

Integrates:
- Non-linear kinematic acceleration curves from current velocity to cruise speed.
- Spatial stopline positions from official corridor network specification.
- Traffic congestion drag and weather-induced deceleration resistance.
- Real-time sub-millisecond calculation for closed-loop signal pre-clearance.
"""

from __future__ import annotations

import math
import time
from dataclasses import asdict, dataclass
from typing import Any

from controller.mission.emergency_mission import (
    EmergencyMission,
)

# Spatial Stopline Coordinate Reference (Meters along corridor)
CORRIDOR_NODE_STOPLINES: dict[str, float] = {
    "node_a": 0.0,
    "node_b": 300.0,
    "node_c": 600.0,
    "node_d": 900.0,
    "hospital": 1100.0,
}

WEATHER_FRICTION_FACTORS: dict[str, float] = {
    "clear": 1.00,
    "overcast": 1.02,
    "rain": 1.10,  # Wet asphalt slightly reduces acceleration & cornering
    "haze": 1.04,
}


@dataclass
class NodeETAResult:
    """Estimated arrival time metrics for a specific intersection stopline."""

    node_id: str
    stopline_x_meters: float
    distance_to_stopline_m: float
    eta_seconds: float
    estimated_arrival_timestamp: float
    has_passed: bool
    confidence_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MultiNodeETAReport:
    """Consolidated corridor-wide ETA report covering all downstream intersections."""

    mission_id: str
    vehicle_id: str
    current_position_m: float
    current_speed_kmh: float
    etas_by_node: dict[str, NodeETAResult]
    hospital_eta_sec: float
    calculation_timestamp: float
    provenance: str = "KINEMATIC_CORRIDOR_ESTIMATOR"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["etas_by_node"] = {k: v.to_dict() for k, v in self.etas_by_node.items()}
        return d


class MultiNodeETAEvaluator:
    """Estimates travel durations from emergency vehicle position to corridor stoplines."""

    DEFAULT_ACCELERATION_MPS2: float = 3.5  # Typical high-performance ambulance acceleration

    def __init__(
        self,
        node_stoplines: dict[str, float] | None = None,
        max_accel_mps2: float = 3.5,
    ) -> None:
        self.stoplines = node_stoplines or CORRIDOR_NODE_STOPLINES
        self.max_accel = max_accel_mps2

    def compute_single_node_eta(
        self,
        current_x_m: float,
        current_v_mps: float,
        target_v_mps: float,
        max_v_mps: float,
        stopline_x_m: float,
        traffic_occupancy: float = 0.20,
        weather: str = "clear",
    ) -> tuple[float, float, bool, float]:
        """Compute ETA to a single stopline considering kinematics and traffic drag.

        Returns:
            (eta_seconds, distance_remaining_m, has_passed, confidence)
        """
        dist_rem = stopline_x_m - current_x_m

        # If vehicle is already past stopline
        if dist_rem <= 0.0:
            return 0.0, 0.0, True, 1.00

        # Kinematic Phase 1: Acceleration from current_v to target_v
        v0 = max(0.0, current_v_mps)
        vt = max(5.0, target_v_mps)
        vmax = max(vt, max_v_mps)
        a = self.max_accel

        if v0 < vt:
            t_acc = (vt - v0) / a
            d_acc = v0 * t_acc + 0.5 * a * (t_acc**2)
            if dist_rem <= d_acc:
                # Arrives during acceleration phase
                # 0.5 * a * t^2 + v0 * t - dist_rem = 0
                discriminant = (v0**2) + (2.0 * a * dist_rem)
                t_free = (-v0 + math.sqrt(max(0.0, discriminant))) / a
            else:
                d_cruise = dist_rem - d_acc
                t_cruise = d_cruise / vt
                t_free = t_acc + t_cruise
        else:
            # Already at or exceeding target speed
            t_free = dist_rem / max(v0, vt)

        # Traffic Drag & Weather Resistance Multiplier
        weather_factor = WEATHER_FRICTION_FACTORS.get(weather.lower(), 1.0)
        # Moderate traffic friction (pre-clearance minimizes this, but queued bottlenecks create drag)
        congestion_drag = 1.0 + (0.18 * max(0.0, traffic_occupancy - 0.40))
        effective_drag = weather_factor * congestion_drag

        eta_raw = t_free * effective_drag

        # Clamp against physical absolute maximum speed limit (speed of light check)
        min_physical_time = dist_rem / vmax
        eta = max(min_physical_time, eta_raw)

        # Confidence heuristic (degrades with distance and high occupancy uncertainty)
        confidence = 0.96 - (dist_rem / 4000.0) - (0.10 * max(0.0, traffic_occupancy - 0.60))
        confidence = max(0.50, min(0.99, round(confidence, 2)))

        return round(eta, 1), round(dist_rem, 1), False, confidence

    def compute_multi_node_eta(
        self,
        mission: EmergencyMission,
        approach_occupancies: dict[str, float] | None = None,
        weather: str = "clear",
    ) -> MultiNodeETAReport:
        """Calculate dynamic ETAs across all 4 intersections and the hospital stopline."""
        t_now = time.time()
        occupancies = approach_occupancies or {}
        avg_corridor_occ = sum(occupancies.values()) / len(occupancies) if occupancies else 0.25

        etas: dict[str, NodeETAResult] = {}
        for node_id, stopline_x in self.stoplines.items():
            occ = occupancies.get(node_id, avg_corridor_occ)
            eta_sec, dist_m, passed, conf = self.compute_single_node_eta(
                current_x_m=mission.current_position_m,
                current_v_mps=mission.current_speed_mps,
                target_v_mps=mission.target_speed_mps,
                max_v_mps=mission.max_speed_mps,
                stopline_x_m=stopline_x,
                traffic_occupancy=occ,
                weather=weather,
            )
            arrival_ts = round(t_now + eta_sec, 2) if not passed else round(t_now, 2)
            etas[node_id] = NodeETAResult(
                node_id=node_id,
                stopline_x_meters=stopline_x,
                distance_to_stopline_m=dist_m,
                eta_seconds=eta_sec,
                estimated_arrival_timestamp=arrival_ts,
                has_passed=passed,
                confidence_score=conf,
            )

        hospital_res = etas.get("hospital")
        hospital_eta = hospital_res.eta_seconds if hospital_res else 0.0

        return MultiNodeETAReport(
            mission_id=mission.mission_id,
            vehicle_id=mission.vehicle_id,
            current_position_m=mission.current_position_m,
            current_speed_kmh=mission.current_speed_kmh,
            etas_by_node=etas,
            hospital_eta_sec=hospital_eta,
            calculation_timestamp=t_now,
        )
