"""Camera-to-3D Digital Twin Projection and Metric Localization Engine (Task 60).

Projects 2D video bounding boxes from roadside traffic cameras onto the 3D WebGL
Cartesian coordinate plane using Planar Homography and temporal Kalman filtering.
Estimates vehicle ground contact positions, instantaneous velocity vectors,
and 3D heading angles along the 1,300m corridor.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from ai.calibration.homography import CameraCalibrationProfile, transform_points


@dataclass
class Vehicle3DTelemetry:
    """Standardized 3D spatial state for a vehicle in the digital twin."""

    vehicle_id: str
    vehicle_class: str
    position_x: float  # Longitudinal coordinate along 5th Ave (-150m to 1100m)
    position_y: float  # Vertical elevation (0.0 on road plane)
    position_z: float  # Lateral cross-street offset (-7.0m to +7.0m on arterial)
    speed_kmh: float
    heading_deg: float  # Yaw angle (0 deg = Eastbound along +X)
    confidence: float
    provenance: str = "OFFLINE_VIDEO"
    timestamp_sec: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["position_x"] = round(self.position_x, 3)
        d["position_y"] = round(self.position_y, 3)
        d["position_z"] = round(self.position_z, 3)
        d["speed_kmh"] = round(self.speed_kmh, 2)
        d["heading_deg"] = round(self.heading_deg, 2)
        d["confidence"] = round(self.confidence, 4)
        return d


class VehicleKalmanFilter3D:
    """Constant-velocity 2D ground-plane Kalman filter for smoothing 3D coordinates."""

    def __init__(self, init_x: float, init_z: float, q_var: float = 0.5, r_var: float = 0.25):
        # State: [X, Z, v_X, v_Z]
        self.state = np.array([init_x, init_z, 0.0, 0.0], dtype=np.float64)
        self.P = np.diag([1.0, 1.0, 4.0, 4.0]).astype(np.float64)
        self.q_var = q_var
        self.r_var = r_var
        self.last_timestamp: float | None = None

    def predict(self, dt: float) -> np.ndarray:
        """Predict forward by dt seconds."""
        F = np.array(
            [
                [1.0, 0.0, dt, 0.0],
                [0.0, 1.0, 0.0, dt],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        )

        # Discrete-time process noise covariance
        q_dt = self.q_var * dt
        Q = np.diag([0.25 * q_dt * dt**2, 0.25 * q_dt * dt**2, q_dt, q_dt])

        self.state = F @ self.state
        self.P = F @ self.P @ F.T + Q
        return self.state[:2]

    def update(self, meas_x: float, meas_z: float) -> np.ndarray:
        """Update state with observed measurement [meas_x, meas_z]."""
        H = np.array(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
            ],
            dtype=np.float64,
        )
        R = np.diag([self.r_var, self.r_var])

        z = np.array([meas_x, meas_z], dtype=np.float64)
        y = z - H @ self.state
        S = H @ self.P @ H.T + R
        K = self.P @ H.T @ np.linalg.inv(S)

        self.state += K @ y
        I_mat = np.eye(4, dtype=np.float64)
        self.P = (I_mat - K @ H) @ self.P
        return self.state[:2]


class CameraTo3DProjector:
    """Projects 2D detections into Digital Twin 3D Cartesian world space."""

    def __init__(
        self,
        calibration_profile: CameraCalibrationProfile,
        node_offset_x: float = 0.0,
        provenance: str = "OFFLINE_VIDEO",
    ):
        self.profile = calibration_profile
        self.node_offset_x = node_offset_x
        self.provenance = provenance
        self.homography = np.array(calibration_profile.homography_matrix, dtype=np.float64)

        # Track filters: vehicle_id -> VehicleKalmanFilter3D
        self.track_filters: dict[str, VehicleKalmanFilter3D] = {}

    @classmethod
    def from_calibration_file(
        cls,
        calibration_path: Path | str,
        node_offset_x: float = 0.0,
        provenance: str = "OFFLINE_VIDEO",
    ) -> CameraTo3DProjector:
        """Factory constructor loading calibration JSON."""
        profile = CameraCalibrationProfile.load_json(calibration_path)
        return cls(profile, node_offset_x=node_offset_x, provenance=provenance)

    def extract_ground_contact_point(
        self, bbox: list[float] | tuple[float, float, float, float]
    ) -> tuple[float, float]:
        """Extract bottom-center tire contact pixel from bounding box [x1, y1, x2, y2]."""
        x1, _y1, x2, y2 = bbox
        u = float((x1 + x2) / 2.0)
        v = float(y2)
        return u, v

    def project_contact_to_metric(self, u: float, v: float) -> tuple[float, float]:
        """Apply homography matrix H to convert image pixels to ground meters [x_m, y_m]."""
        pts = np.array([[u, v]], dtype=np.float64)
        transformed = transform_points(self.homography, pts)[0]
        return float(transformed[0]), float(transformed[1])

    def map_to_corridor_world_3d(
        self, x_metric: float, y_metric: float
    ) -> tuple[float, float, float]:
        """Map local approach metric coordinates into global Digital Twin 3D Cartesian coordinates.

        Corridor convention:
          - Arterial axis: X (Eastbound: towards stopline at node_offset_x).
          - Ground elevation: Y = 0.0.
          - Lateral offset: Z (across cross-street lanes, centered at 0.0).
        """
        approach_len = self.profile.approach_length_m
        roadway_w = self.profile.roadway_width_m

        if self.profile.approach_direction == "EB":
            # Eastbound approach: y_metric = 0 is stopline, y_metric = 80 is upstream
            # Vehicle approaches from (node_offset_x - approach_len) towards node_offset_x
            world_x = self.node_offset_x - (approach_len - y_metric)
            world_z = x_metric - (roadway_w / 2.0)
        elif self.profile.approach_direction == "WB":
            # Westbound approach: travels opposite direction
            world_x = self.node_offset_x + (approach_len - y_metric)
            world_z = (roadway_w / 2.0) - x_metric
        else:
            # Northbound / Southbound cross streets
            world_x = self.node_offset_x + (x_metric - roadway_w / 2.0)
            world_z = y_metric - (approach_len / 2.0)

        world_y = 0.0
        return world_x, world_y, world_z

    def project_detection(
        self,
        vehicle_id: str,
        vehicle_class: str,
        bbox: list[float] | tuple[float, float, float, float],
        confidence: float = 0.90,
        timestamp_sec: float = 0.0,
    ) -> Vehicle3DTelemetry:
        """Project a single 2D detection bounding box into a 3D VehicleTelemetry state."""
        # 1. Contact point in image plane
        u, v = self.extract_ground_contact_point(bbox)

        # 2. Local ground metric coordinates
        x_m, y_m = self.project_contact_to_metric(u, v)

        # 3. Global Digital Twin coordinates
        raw_wx, wy, raw_wz = self.map_to_corridor_world_3d(x_m, y_m)

        # 4. Temporal Kalman filtering
        if vehicle_id not in self.track_filters:
            self.track_filters[vehicle_id] = VehicleKalmanFilter3D(raw_wx, raw_wz)
            filter_obj = self.track_filters[vehicle_id]
            filter_obj.last_timestamp = timestamp_sec
            smooth_wx, smooth_wz = raw_wx, raw_wz
            speed_kmh = 0.0
            heading_deg = 0.0 if self.profile.approach_direction == "EB" else 180.0
        else:
            filter_obj = self.track_filters[vehicle_id]
            dt = (
                0.1
                if filter_obj.last_timestamp is None
                else max(0.01, timestamp_sec - filter_obj.last_timestamp)
            )
            filter_obj.predict(dt)
            smooth_pos = filter_obj.update(raw_wx, raw_wz)
            smooth_wx, smooth_wz = float(smooth_pos[0]), float(smooth_pos[1])

            vx, vz = float(filter_obj.state[2]), float(filter_obj.state[3])
            speed_mps = math.sqrt(vx**2 + vz**2)
            speed_kmh = speed_mps * 3.6

            # Heading angle derived from velocity vector
            if speed_mps > 0.5:
                heading_rad = math.atan2(vz, vx)
                heading_deg = math.degrees(heading_rad)
            else:
                heading_deg = 0.0 if self.profile.approach_direction == "EB" else 180.0

            filter_obj.last_timestamp = timestamp_sec

        return Vehicle3DTelemetry(
            vehicle_id=vehicle_id,
            vehicle_class=vehicle_class,
            position_x=smooth_wx,
            position_y=wy,
            position_z=smooth_wz,
            speed_kmh=speed_kmh,
            heading_deg=heading_deg,
            confidence=confidence,
            provenance=self.provenance,
            timestamp_sec=timestamp_sec,
        )

    def reset_tracks(self) -> None:
        """Reset internal Kalman filter trackers."""
        self.track_filters.clear()
