"""Vehicle Trajectory Extraction, Speed Estimation and Virtual Tripwire Counting.

Records continuous kinematic histories for ByteTrack tracklets, computes
instantaneous velocity (km/h) and heading, and counts vehicles crossing stop lines.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from ai.detection.yolo_detector import CLASS_NAMES, Detection
from ai.tracking.byte_tracker import ByteTracker, Tracklet


@dataclass
class TrajectoryPoint:
    """Discrete position and kinematic state at a point in time."""

    x: float
    y: float
    timestamp_sec: float
    speed_mps: float = 0.0
    speed_kmh: float = 0.0
    heading_deg: float = 0.0


@dataclass
class VehicleTrajectory:
    """Full trajectory and motion profile for a tracked vehicle."""

    track_id: int
    class_name: str
    points: list[TrajectoryPoint] = field(default_factory=list)
    total_distance_m: float = 0.0

    @property
    def latest_point(self) -> TrajectoryPoint | None:
        return self.points[-1] if self.points else None

    @property
    def instantaneous_speed_kmh(self) -> float:
        return self.latest_point.speed_kmh if self.latest_point else 0.0

    @property
    def mean_speed_kmh(self) -> float:
        speeds = [p.speed_kmh for p in self.points if p.speed_kmh > 0.0]
        return float(sum(speeds) / len(speeds)) if speeds else 0.0

    @property
    def is_stopped(self) -> bool:
        """Determines if vehicle is queued or stopped (v < 2.0 km/h)."""
        return self.instantaneous_speed_kmh < 2.0

    def add_point(
        self,
        x: float,
        y: float,
        timestamp_sec: float,
        pixel_to_meter_scale: float = 1.0,
    ) -> TrajectoryPoint:
        """Append new location and compute velocity and heading."""
        speed_mps = 0.0
        speed_kmh = 0.0
        heading_deg = 0.0

        if self.points:
            prev = self.points[-1]
            dt = timestamp_sec - prev.timestamp_sec
            if dt > 1e-4:
                dx = (x - prev.x) * pixel_to_meter_scale
                dy = (y - prev.y) * pixel_to_meter_scale
                dist = math.hypot(dx, dy)
                self.total_distance_m += dist
                speed_mps = dist / dt
                speed_kmh = speed_mps * 3.6
                heading_deg = math.degrees(math.atan2(dy, dx)) % 360.0

        pt = TrajectoryPoint(
            x=x,
            y=y,
            timestamp_sec=timestamp_sec,
            speed_mps=round(speed_mps, 3),
            speed_kmh=round(speed_kmh, 2),
            heading_deg=round(heading_deg, 1),
        )
        self.points.append(pt)
        if len(self.points) > 300:
            self.points.pop(0)

        return pt

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_id": self.track_id,
            "class_name": self.class_name,
            "length_points": len(self.points),
            "total_distance_m": round(self.total_distance_m, 2),
            "instantaneous_speed_kmh": self.instantaneous_speed_kmh,
            "mean_speed_kmh": round(self.mean_speed_kmh, 2),
            "is_stopped": self.is_stopped,
        }


def ccw(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> bool:
    """Counter-clockwise orientation test for 3 points."""
    return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])


def line_segments_intersect(
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    p4: tuple[float, float],
) -> bool:
    """Return True if line segment p1-p2 intersects segment p3-p4."""
    return (ccw(p1, p3, p4) != ccw(p2, p3, p4)) and (ccw(p1, p2, p3) != ccw(p1, p2, p4))


class VirtualTripwire:
    """Virtual sensor line detecting and counting vehicle crossings (e.g. stoplines)."""

    def __init__(
        self,
        name: str,
        start_pt: tuple[float, float],
        end_pt: tuple[float, float],
    ) -> None:
        self.name = name
        self.start_pt = start_pt
        self.end_pt = end_pt
        self.counts_by_class: dict[str, int] = dict.fromkeys(CLASS_NAMES, 0)
        self.crossed_track_ids: set[int] = set()

    @property
    def total_count(self) -> int:
        return sum(self.counts_by_class.values())

    def check_crossing(
        self,
        track_id: int,
        class_name: str,
        prev_pos: tuple[float, float],
        curr_pos: tuple[float, float],
    ) -> bool:
        """Check if vehicle motion vector crossed the virtual line."""
        if track_id in self.crossed_track_ids:
            return False

        if line_segments_intersect(prev_pos, curr_pos, self.start_pt, self.end_pt):
            self.crossed_track_ids.add(track_id)
            if class_name in self.counts_by_class:
                self.counts_by_class[class_name] += 1
            else:
                self.counts_by_class[class_name] = 1
            return True

        return False


class TrajectoryTracker:
    """High-level trajectory manager combining ByteTrack with kinematic profiling."""

    def __init__(
        self,
        pixel_to_meter_scale: float = 25.0,  # e.g. 1.0 normalized coord = 25m
        tripwires: list[VirtualTripwire] | None = None,
        confirm_hits: int = 1,
    ) -> None:
        self.tracker = ByteTracker(confirm_hits=confirm_hits)
        self.scale = pixel_to_meter_scale
        self.trajectories: dict[int, VehicleTrajectory] = {}
        self.tripwires: list[VirtualTripwire] = tripwires or []

    def update(
        self,
        detections: list[Detection],
        frame_id: int = 1,
        timestamp_sec: float = 0.0,
    ) -> list[Tracklet]:
        """Process frame detections, update ByteTrack and trajectory kinematic states."""
        active_tracks = self.tracker.update(detections, frame_id, timestamp_sec)

        for track in active_tracks:
            tid = track.track_id
            xc, yc = track.bbox[0] + (track.bbox[2] - track.bbox[0]) / 2.0, track.bbox[3]

            if tid not in self.trajectories:
                self.trajectories[tid] = VehicleTrajectory(
                    track_id=tid, class_name=track.class_name
                )

            traj = self.trajectories[tid]
            prev_pt = (traj.latest_point.x, traj.latest_point.y) if traj.latest_point else None

            traj.add_point(xc, yc, timestamp_sec, self.scale)

            # Check virtual tripwires
            if prev_pt is not None:
                curr_pt = (xc, yc)
                for tw in self.tripwires:
                    tw.check_crossing(tid, track.class_name, prev_pt, curr_pt)

        return active_tracks

    def get_trajectory(self, track_id: int) -> VehicleTrajectory | None:
        return self.trajectories.get(track_id)

    def count_active_queued(self) -> int:
        """Count currently stopped vehicles in active tracking pool."""
        return sum(1 for traj in self.trajectories.values() if traj.is_stopped)
