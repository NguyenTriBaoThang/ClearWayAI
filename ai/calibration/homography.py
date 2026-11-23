"""Planar Homography Calibration for Traffic Cameras.

Transforms roadside camera image pixels (u, v) into metric ground-plane
coordinates (X, Y) in meters, correcting for perspective foreshortening.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np


def compute_homography(
    src_points: np.ndarray | list[tuple[float, float]],
    dst_points: np.ndarray | list[tuple[float, float]],
) -> np.ndarray:
    """Compute 3x3 Homography matrix H using Direct Linear Transformation (DLT) via SVD.

    Maps: dst ~ H * src
    Where src_points are (u, v) pixel coordinates,
    and dst_points are (X, Y) metric ground-plane coordinates.
    """
    src = np.asarray(src_points, dtype=float)
    dst = np.asarray(dst_points, dtype=float)

    if len(src) < 4 or len(dst) < 4:
        raise ValueError(f"At least 4 point correspondences required, got {len(src)}")
    if len(src) != len(dst):
        raise ValueError(f"Mismatch: {len(src)} source points vs {len(dst)} destination points")

    num_pts = len(src)
    A = np.zeros((2 * num_pts, 9), dtype=float)

    for i in range(num_pts):
        u, v = src[i]
        X, Y = dst[i]
        A[2 * i] = [-u, -v, -1.0, 0.0, 0.0, 0.0, u * X, v * X, X]
        A[2 * i + 1] = [0.0, 0.0, 0.0, -u, -v, -1.0, u * Y, v * Y, Y]

    # Singular Value Decomposition (SVD)
    _, _, Vt = np.linalg.svd(A)
    H = Vt[-1].reshape((3, 3))

    # Normalize so H[2, 2] == 1.0 if non-zero
    if abs(H[2, 2]) > 1e-9:
        H /= H[2, 2]

    return H


def transform_points(
    H: np.ndarray,
    points: np.ndarray | list[tuple[float, float]],
) -> np.ndarray:
    """Apply homography transformation H to 2D points.

    Returns:
        Transformed 2D points of shape (N, 2).
    """
    pts = np.asarray(points, dtype=float)
    if pts.ndim == 1:
        pts = pts.reshape(1, 2)

    num_pts = len(pts)
    # Homogeneous coordinates (N, 3)
    homo = np.hstack([pts, np.ones((num_pts, 1), dtype=float)])
    transformed = np.dot(H, homo.T).T

    # Perspective division
    w = transformed[:, 2:3]
    # Guard against division by near-zero
    w = np.where(np.abs(w) < 1e-9, 1e-9, w)
    result = transformed[:, :2] / w
    return result


def reprojection_error(
    H: np.ndarray,
    src_points: np.ndarray | list[tuple[float, float]],
    dst_points: np.ndarray | list[tuple[float, float]],
) -> float:
    """Calculate Root Mean Square Error (RMSE) between projected points and ground truth."""
    projected = transform_points(H, src_points)
    dst = np.asarray(dst_points, dtype=float)
    error = np.sqrt(np.mean(np.sum((projected - dst) ** 2, axis=1)))
    return float(error)


@dataclass
class CameraCalibrationProfile:
    """Camera intrinsic/extrinsic metric calibration profile."""

    camera_id: str
    intersection_name: str
    approach_direction: str  # "EB", "WB", "NB", "SB"
    image_resolution: tuple[int, int]  # (width, height)
    roadway_width_m: float  # e.g. 14.0 m
    approach_length_m: float  # e.g. 80.0 m
    stopline_y_m: float  # Y coordinate of stop line in ground plane
    source_points_pixel: list[list[float]]  # 4 image coordinates [[u, v], ...]
    destination_points_meters: list[list[float]]  # 4 ground coordinates [[X, Y], ...]
    homography_matrix: list[list[float]]
    reprojection_error_m: float

    @classmethod
    def create(
        cls,
        camera_id: str,
        intersection_name: str,
        approach_direction: str,
        image_resolution: tuple[int, int],
        roadway_width_m: float,
        approach_length_m: float,
        source_points_pixel: list[tuple[float, float]] | list[list[float]],
        destination_points_meters: list[tuple[float, float]] | list[list[float]],
        stopline_y_m: float = 0.0,
    ) -> CameraCalibrationProfile:
        """Construct profile and compute DLT homography matrix automatically."""
        src = np.array(source_points_pixel, dtype=float)
        dst = np.array(destination_points_meters, dtype=float)
        H = compute_homography(src, dst)
        err = reprojection_error(H, src, dst)

        return cls(
            camera_id=camera_id,
            intersection_name=intersection_name,
            approach_direction=approach_direction,
            image_resolution=image_resolution,
            roadway_width_m=roadway_width_m,
            approach_length_m=approach_length_m,
            stopline_y_m=stopline_y_m,
            source_points_pixel=src.tolist(),
            destination_points_meters=dst.tolist(),
            homography_matrix=H.tolist(),
            reprojection_error_m=round(err, 4),
        )

    def project_to_meters(self, pixel_points: np.ndarray | list[tuple[float, float]]) -> np.ndarray:
        """Transform image coordinates to ground plane meters."""
        H = np.array(self.homography_matrix, dtype=float)
        return transform_points(H, pixel_points)

    def project_to_pixels(
        self, ground_points: np.ndarray | list[tuple[float, float]]
    ) -> np.ndarray:
        """Transform ground plane meters back to image pixels using inverse homography."""
        H = np.array(self.homography_matrix, dtype=float)
        H_inv = np.linalg.inv(H)
        return transform_points(H_inv, ground_points)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def save_json(self, path: Path | str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_json(cls, path: Path | str) -> CameraCalibrationProfile:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)
