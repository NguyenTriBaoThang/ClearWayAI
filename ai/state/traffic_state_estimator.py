"""Macroscopic Traffic State Estimator from Camera Perception & Tracking.

Estimates real-world metric traffic parameters for intersection approaches:
1. Queue length (meters from stop line to queue tail).
2. Approach roadway occupancy ratio [0.0, 1.0].
3. Vietnamese mixed-traffic motorcycle ratio.
4. Traffic density (vehicles per 100 meters).
5. Emergency vehicle detection and distance to stop line.
6. Empirical queue flush time estimate for Phase E clearance models.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from ai.calibration.homography import CameraCalibrationProfile
from ai.detection.yolo_detector import CLASS_NAMES
from ai.tracking.byte_tracker import Tracklet

# Vehicle footprint areas in ground-plane square meters
VEHICLE_FOOTPRINTS_M2: dict[str, float] = {
    "motorcycle": 1.6,  # 0.8m x 2.0m
    "car": 7.5,  # 1.8m x 4.2m
    "suv": 9.5,  # 1.9m x 5.0m
    "bus": 28.0,  # 2.5m x 11.2m
    "truck": 25.0,  # 2.5m x 10.0m
    "ambulance": 10.0,  # 2.0m x 5.0m
    "fire_engine": 24.0,  # 2.5m x 9.6m
}

STARTUP_LOST_TIME_SEC = 3.0
SATURATION_DISCHARGE_SPEED_MPS = 4.5  # ~16.2 km/h
QUEUE_SPEED_THRESHOLD_KMH = 2.0  # v < 2 km/h considered queued


@dataclass
class ApproachTrafficState:
    """State metrics for a single intersection approach (e.g. Eastbound)."""

    approach_id: str
    timestamp_sec: float
    vehicle_count: int
    counts_by_class: dict[str, int]
    motorcycle_ratio: float
    queue_length_meters: float
    queued_vehicle_count: int
    approach_occupancy_ratio: float
    traffic_density_vpm: float  # vehicles per 100 meters
    mean_speed_kmh: float
    emergency_vehicle_detected: bool = False
    emergency_class: str | None = None
    emergency_distance_to_stopline_m: float | None = None
    estimated_queue_flush_time_sec: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "approach_id": self.approach_id,
            "timestamp_sec": round(self.timestamp_sec, 3),
            "vehicle_count": self.vehicle_count,
            "counts_by_class": self.counts_by_class,
            "motorcycle_ratio": round(self.motorcycle_ratio, 4),
            "queue_length_meters": round(self.queue_length_meters, 2),
            "queued_vehicle_count": self.queued_vehicle_count,
            "approach_occupancy_ratio": round(self.approach_occupancy_ratio, 4),
            "traffic_density_vpm": round(self.traffic_density_vpm, 2),
            "mean_speed_kmh": round(self.mean_speed_kmh, 2),
            "emergency_vehicle_detected": self.emergency_vehicle_detected,
            "emergency_class": self.emergency_class,
            "emergency_distance_to_stopline_m": (
                round(self.emergency_distance_to_stopline_m, 2)
                if self.emergency_distance_to_stopline_m is not None
                else None
            ),
            "estimated_queue_flush_time_sec": round(self.estimated_queue_flush_time_sec, 2),
        }


@dataclass
class IntersectionTrafficState:
    """Aggregated traffic state across all approaches of an intersection."""

    intersection_id: str
    timestamp_sec: float
    approaches: dict[str, ApproachTrafficState] = field(default_factory=dict)
    total_vehicle_count: int = 0
    total_queued_count: int = 0
    max_queue_length_meters: float = 0.0
    critical_approach: str = "EB"
    emergency_preemption_active: bool = False
    provenance: str = "OFFLINE_VIDEO"

    def to_dict(self) -> dict[str, Any]:
        return {
            "intersection_id": self.intersection_id,
            "timestamp_sec": round(self.timestamp_sec, 3),
            "total_vehicle_count": self.total_vehicle_count,
            "total_queued_count": self.total_queued_count,
            "max_queue_length_meters": round(self.max_queue_length_meters, 2),
            "critical_approach": self.critical_approach,
            "emergency_preemption_active": self.emergency_preemption_active,
            "provenance": self.provenance,
            "approaches": {k: v.to_dict() for k, v in self.approaches.items()},
        }


class TrafficStateEstimator:
    """Estimates macroscopic queue lengths and occupancies using Homography projection."""

    def __init__(self, calibration_profile: CameraCalibrationProfile) -> None:
        self.calib = calibration_profile

    def estimate_approach_state(
        self,
        tracklets: list[Tracklet],
        timestamp_sec: float = 0.0,
    ) -> ApproachTrafficState:
        """Project tracklets to ground plane and compute approach queue metrics."""
        if not tracklets:
            return ApproachTrafficState(
                approach_id=self.calib.approach_direction,
                timestamp_sec=timestamp_sec,
                vehicle_count=0,
                counts_by_class=dict.fromkeys(CLASS_NAMES, 0),
                motorcycle_ratio=0.0,
                queue_length_meters=0.0,
                queued_vehicle_count=0,
                approach_occupancy_ratio=0.0,
                traffic_density_vpm=0.0,
                mean_speed_kmh=0.0,
                emergency_vehicle_detected=False,
                estimated_queue_flush_time_sec=0.0,
            )

        counts = dict.fromkeys(CLASS_NAMES, 0)
        queued_count = 0
        max_queue_dist = 0.0
        total_footprint_m2 = 0.0
        speeds_kmh: list[float] = []

        emergency_detected = False
        emergency_cls: str | None = None
        emergency_dist: float | None = None

        # Extract bottom-center contact patch pixel coordinates for each tracklet
        pixel_points: list[tuple[float, float]] = []
        for t in tracklets:
            x_min, _, x_max, y_max = t.bbox
            xc = (x_min + x_max) / 2.0
            # Scale normalized coordinates to image resolution if normalized in [0, 1]
            if x_max <= 1.05 and y_max <= 1.05:
                w_img, h_img = self.calib.image_resolution
                pixel_points.append((xc * w_img, y_max * h_img))
            else:
                pixel_points.append((xc, y_max))

        # Project all points to ground plane meters (X, Y)
        ground_points = self.calib.project_to_meters(pixel_points)

        for idx, t in enumerate(tracklets):
            cls_name = t.class_name
            if cls_name in counts:
                counts[cls_name] += 1
            else:
                counts[cls_name] = 1

            total_footprint_m2 += VEHICLE_FOOTPRINTS_M2.get(cls_name, 7.5)

            # Ground coordinates: Y represents distance along approach towards stopline
            _, y_m = ground_points[idx]
            dist_to_stopline = max(0.0, y_m - self.calib.stopline_y_m)

            # Estimate speed from tracklet history
            speed_kmh = 0.0
            if len(t.history) >= 2:
                t_prev, xc_prev, yc_prev, _ = t.history[-2]
                t_curr, xc_curr, yc_curr, _ = t.history[-1]
                dt = t_curr - t_prev
                if dt > 1e-4:
                    # Ground distance
                    p_prev = self.calib.project_to_meters(
                        [
                            (
                                xc_prev * self.calib.image_resolution[0],
                                yc_prev * self.calib.image_resolution[1],
                            )
                        ]
                    )[0]
                    p_curr = self.calib.project_to_meters(
                        [
                            (
                                xc_curr * self.calib.image_resolution[0],
                                yc_curr * self.calib.image_resolution[1],
                            )
                        ]
                    )[0]
                    dist_m = math.hypot(p_curr[0] - p_prev[0], p_curr[1] - p_prev[1])
                    speed_mps = dist_m / dt
                    speed_kmh = speed_mps * 3.6
                    speeds_kmh.append(speed_kmh)

            is_queued = speed_kmh < QUEUE_SPEED_THRESHOLD_KMH
            if is_queued and dist_to_stopline <= self.calib.approach_length_m:
                queued_count += 1
                if dist_to_stopline > max_queue_dist:
                    max_queue_dist = dist_to_stopline

            # Check emergency vehicles
            if cls_name in ["ambulance", "fire_engine"]:
                emergency_detected = True
                emergency_cls = cls_name
                emergency_dist = dist_to_stopline

        num_vehicles = len(tracklets)
        motorcycles = counts.get("motorcycle", 0)
        moto_ratio = motorcycles / max(1, num_vehicles)

        road_area_m2 = max(1.0, self.calib.roadway_width_m * self.calib.approach_length_m)
        occupancy_ratio = min(1.0, total_footprint_m2 / road_area_m2)
        density_vpm = num_vehicles / (self.calib.approach_length_m / 100.0)
        mean_speed = float(sum(speeds_kmh) / len(speeds_kmh)) if speeds_kmh else 0.0

        # Estimated clearance time: startup lost time + queue flush time
        flush_time = (
            STARTUP_LOST_TIME_SEC + (max_queue_dist / SATURATION_DISCHARGE_SPEED_MPS)
            if max_queue_dist > 0.0
            else 0.0
        )

        return ApproachTrafficState(
            approach_id=self.calib.approach_direction,
            timestamp_sec=timestamp_sec,
            vehicle_count=num_vehicles,
            counts_by_class=counts,
            motorcycle_ratio=moto_ratio,
            queue_length_meters=max_queue_dist,
            queued_vehicle_count=queued_count,
            approach_occupancy_ratio=occupancy_ratio,
            traffic_density_vpm=density_vpm,
            mean_speed_kmh=mean_speed,
            emergency_vehicle_detected=emergency_detected,
            emergency_class=emergency_cls,
            emergency_distance_to_stopline_m=emergency_dist,
            estimated_queue_flush_time_sec=flush_time,
        )

    def estimate_intersection_state(
        self,
        approaches: dict[str, ApproachTrafficState],
        intersection_id: str = "INT_OAK_5TH",
        timestamp_sec: float = 0.0,
    ) -> IntersectionTrafficState:
        """Aggregate approach metrics into full intersection summary."""
        total_veh = sum(a.vehicle_count for a in approaches.values())
        total_q = sum(a.queued_vehicle_count for a in approaches.values())
        max_q = max((a.queue_length_meters for a in approaches.values()), default=0.0)

        # Critical approach is the one with emergency vehicle, or longest queue
        crit_app = "EB"
        emergency_active = False

        for app_id, state in approaches.items():
            if state.emergency_vehicle_detected:
                crit_app = app_id
                emergency_active = True
                break

        if not emergency_active and approaches:
            crit_app = max(approaches.keys(), key=lambda k: approaches[k].queue_length_meters)

        return IntersectionTrafficState(
            intersection_id=intersection_id,
            timestamp_sec=timestamp_sec,
            approaches=approaches,
            total_vehicle_count=total_veh,
            total_queued_count=total_q,
            max_queue_length_meters=max_q,
            critical_approach=crit_app,
            emergency_preemption_active=emergency_active,
            provenance="OFFLINE_VIDEO",
        )
