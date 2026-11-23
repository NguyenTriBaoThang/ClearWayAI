"""Kalman Filter State Estimator for Bounding Box Tracking in ByteTrack.

Tracks an 8-dimensional state vector:
    [x, y, a, h, vx, vy, va, vh]^T
where:
    (x, y) is the bounding box center,
    a = width / height is the aspect ratio,
    h is the box height,
    (vx, vy, va, vh) are the corresponding velocities.
"""

from __future__ import annotations

import numpy as np


class KalmanFilter:
    """Constant-velocity Kalman filter for 2D bounding boxes."""

    def __init__(self) -> None:
        ndim = 4
        dt = 1.0

        # State transition matrix F (8x8)
        self._motion_mat = np.eye(2 * ndim, 2 * ndim, dtype=float)
        for i in range(ndim):
            self._motion_mat[i, ndim + i] = dt

        # Measurement projection matrix H (4x8)
        self._update_mat = np.eye(ndim, 2 * ndim, dtype=float)

        # Process and measurement noise standard deviations
        self._std_weight_position = 1.0 / 20.0
        self._std_weight_velocity = 1.0 / 160.0

    def initiate(
        self, measurement: np.ndarray | tuple[float, float, float, float]
    ) -> tuple[np.ndarray, np.ndarray]:
        """Create new track state from measurement [x, y, a, h].

        Returns:
            mean: 8D state vector [x, y, a, h, 0, 0, 0, 0]
            covariance: 8x8 covariance matrix
        """
        meas = np.asarray(measurement, dtype=float)
        mean_pos = meas
        mean_vel = np.zeros_like(mean_pos)
        mean = np.r_[mean_pos, mean_vel]

        h = meas[3]
        std = [
            2 * self._std_weight_position * h,
            2 * self._std_weight_position * h,
            1e-2,
            2 * self._std_weight_position * h,
            10 * self._std_weight_velocity * h,
            10 * self._std_weight_velocity * h,
            1e-5,
            10 * self._std_weight_velocity * h,
        ]
        covariance = np.diag(np.square(std))
        return mean, covariance

    def predict(self, mean: np.ndarray, covariance: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Execute state prediction step."""
        h = mean[3]
        std_pos = [
            self._std_weight_position * h,
            self._std_weight_position * h,
            1e-2,
            self._std_weight_position * h,
        ]
        std_vel = [
            self._std_weight_velocity * h,
            self._std_weight_velocity * h,
            1e-5,
            self._std_weight_velocity * h,
        ]
        motion_cov = np.diag(np.square(np.r_[std_pos, std_vel]))

        mean_pred = np.dot(self._motion_mat, mean)
        cov_pred = (
            np.linalg.multi_dot((self._motion_mat, covariance, self._motion_mat.T)) + motion_cov
        )
        return mean_pred, cov_pred

    def project(self, mean: np.ndarray, covariance: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Project state distribution to measurement space."""
        h = mean[3]
        std = [
            self._std_weight_position * h,
            self._std_weight_position * h,
            1e-1,
            self._std_weight_position * h,
        ]
        meas_cov = np.diag(np.square(std))

        mean_proj = np.dot(self._update_mat, mean)
        cov_proj = (
            np.linalg.multi_dot((self._update_mat, covariance, self._update_mat.T)) + meas_cov
        )
        return mean_proj, cov_proj

    def update(
        self,
        mean: np.ndarray,
        covariance: np.ndarray,
        measurement: np.ndarray | tuple[float, float, float, float],
    ) -> tuple[np.ndarray, np.ndarray]:
        """Execute state update step with new measurement [x, y, a, h]."""
        projected_mean, projected_cov = self.project(mean, covariance)
        meas = np.asarray(measurement, dtype=float)

        # Kalman gain K = P * H^T * S^-1
        chol_factor = np.linalg.cholesky(projected_cov)
        kalman_gain = np.linalg.solve(
            chol_factor.T,
            np.linalg.solve(chol_factor, np.dot(covariance, self._update_mat.T).T),
        ).T

        innovation = meas - projected_mean
        new_mean = mean + np.dot(innovation, kalman_gain.T)
        new_cov = covariance - np.linalg.multi_dot((kalman_gain, projected_cov, kalman_gain.T))
        return new_mean, new_cov


def bbox_to_xyah(bbox: tuple[float, float, float, float]) -> np.ndarray:
    """Convert [x_min, y_min, x_max, y_max] to [x_center, y_center, aspect_ratio, height]."""
    x_min, y_min, x_max, y_max = bbox
    w = max(1e-4, x_max - x_min)
    h = max(1e-4, y_max - y_min)
    xc = x_min + w / 2.0
    yc = y_min + h / 2.0
    aspect = w / h
    return np.array([xc, yc, aspect, h], dtype=float)


def xyah_to_bbox(xyah: np.ndarray) -> tuple[float, float, float, float]:
    """Convert [x_center, y_center, aspect_ratio, height] back to [x_min, y_min, x_max, y_max]."""
    xc, yc, aspect, h = xyah[:4]
    w = max(1e-4, aspect * h)
    x_min = xc - w / 2.0
    y_min = yc - h / 2.0
    x_max = xc + w / 2.0
    y_max = yc + h / 2.0
    return (float(x_min), float(y_min), float(x_max), float(y_max))
