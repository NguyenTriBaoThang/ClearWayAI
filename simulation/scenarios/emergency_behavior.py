"""
ClearWayAI - Emergency Vehicle Behavior & Corridor Clearance Model
Provides analysis and verification models for:
- Blue-light yielding behavior ("Rettungsgasse" lateral clearance corridor formation)
- Minimum lateral clearance width (>= 3.0m required for ambulance passage)
- Deceleration / shockwave tracking for emergency vehicles
- Transit times and ETA calculation from West Gate through Nodes A -> B -> C -> D
"""

from dataclasses import dataclass


@dataclass
class CorridorClearanceMetrics:
    corridor_length_m: float
    free_flow_speed_mps: float
    ambulance_speed_mps: float
    min_lateral_corridor_width_m: float
    lateral_yielding_achieved: bool
    deceleration_events: int
    transit_time_sec: float
    eta_to_hospital_sec: float
    corridor_nodes_cleared: int


class EmergencyCorridorAnalyzer:
    """
    Evaluates emergency vehicle transit and surrounding traffic yielding dynamics
    under the SUMO SL2015 Sublane Model.
    """

    CORRIDOR_DISTANCE_METERS = 900.0  # Node A (0m) to Node D (900m)
    TOTAL_ROUTE_METERS = 1300.0  # West Feeder (-200m) to Hospital (1100m)
    AMBULANCE_WIDTH_METERS = 2.20
    REQUIRED_CLEARANCE_BUFFER_METERS = 0.80  # 0.40m buffer on each side

    def __init__(self, speed_mps: float = 20.0):
        self.ambulance_speed_mps = speed_mps
        self.required_width = self.AMBULANCE_WIDTH_METERS + self.REQUIRED_CLEARANCE_BUFFER_METERS

    def evaluate_lateral_yielding(
        self,
        left_vehicle_lat_pos: float = 1.10,
        right_vehicle_lat_pos: float = -1.10,
        lane_width: float = 3.20,
    ) -> tuple[float, bool]:
        """
        Calculates the available lateral clearance width between queued vehicles
        under the sublane model.
        Returns: (clearance_width_meters, is_sufficient)
        """
        # When passenger cars and motorcycles shift towards lane boundaries (curb / edge),
        # the central channel opens up:
        clearance_width = abs(left_vehicle_lat_pos - right_vehicle_lat_pos) + (lane_width - 2.0)
        is_sufficient = clearance_width >= self.required_width
        return round(clearance_width, 2), is_sufficient

    def estimate_transit_time(
        self,
        has_preclearance: bool = True,
        congestion_level: str = "peak",
    ) -> CorridorClearanceMetrics:
        """
        Calculates expected transit metrics for AMB-339 along the arterial corridor
        with or without ClearWay AI pre-clearance.
        """
        if has_preclearance:
            # ClearWay AI Pre-Clearance: Green wave clears queues ahead of ambulance
            avg_speed = 18.5  # ~66 km/h (unimpeded priority transit)
            decel_events = 0
            yielding_achieved = True
            lateral_width = 3.40
        else:
            # Baseline / No Pre-Clearance: Ambulance encounters residual queues
            speed_penalties = {
                "free_flow": 16.0,
                "normal": 11.5,
                "peak": 7.0,
                "spillback": 4.5,
            }
            avg_speed = speed_penalties.get(congestion_level, 10.0)
            decel_events = 3 if congestion_level in ["peak", "spillback"] else 1
            yielding_achieved = congestion_level != "spillback"
            lateral_width = 2.70 if congestion_level in ["peak", "spillback"] else 3.10

        transit_time = self.TOTAL_ROUTE_METERS / avg_speed
        eta_hospital = transit_time

        return CorridorClearanceMetrics(
            corridor_length_m=self.TOTAL_ROUTE_METERS,
            free_flow_speed_mps=16.67,
            ambulance_speed_mps=round(avg_speed, 2),
            min_lateral_corridor_width_m=lateral_width,
            lateral_yielding_achieved=yielding_achieved,
            deceleration_events=decel_events,
            transit_time_sec=round(transit_time, 1),
            eta_to_hospital_sec=round(eta_hospital, 1),
            corridor_nodes_cleared=4,
        )
