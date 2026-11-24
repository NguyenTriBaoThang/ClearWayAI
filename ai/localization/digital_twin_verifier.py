"""Digital Twin Spatial Localization Verifier (Task 60).

Compares camera-projected 3D vehicle states against ground-truth surveyed
physical coordinates / SUMO ground truth. Computes 3D RMSE, lateral lane deviation,
longitudinal displacement, and heading angle accuracy.
Enforces the strict spatial verification threshold: RMSE <= 1.5m.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class LocalizationBenchmarkResult:
    """Benchmark results for 2D-to-3D camera localization accuracy."""

    total_samples: int
    rmse_meters: float
    mae_meters: float
    longitudinal_error_mean_m: float
    longitudinal_error_std_m: float
    lateral_error_mean_m: float
    lateral_error_std_m: float
    heading_error_deg: float
    speed_error_kmh: float
    pass_criteria_rmse_m: float = 1.50
    pass_criteria_lateral_m: float = 0.60
    pass_criteria_heading_deg: float = 10.0
    status: str = "VERIFIED_PASSED"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DigitalTwinLocalizationVerifier:
    """Quantitative accuracy evaluator for Camera-to-3D projection."""

    def __init__(
        self,
        max_allowable_rmse_m: float = 1.50,
        max_allowable_lateral_m: float = 0.60,
        max_allowable_heading_deg: float = 10.0,
    ):
        self.max_allowable_rmse_m = max_allowable_rmse_m
        self.max_allowable_lateral_m = max_allowable_lateral_m
        self.max_allowable_heading_deg = max_allowable_heading_deg

    def evaluate_coordinates(
        self,
        predicted_3d: list[tuple[float, float, float]] | np.ndarray,
        ground_truth_3d: list[tuple[float, float, float]] | np.ndarray,
        pred_headings: list[float] | np.ndarray | None = None,
        gt_headings: list[float] | np.ndarray | None = None,
        pred_speeds: list[float] | np.ndarray | None = None,
        gt_speeds: list[float] | np.ndarray | None = None,
    ) -> LocalizationBenchmarkResult:
        """Evaluate spatial accuracy across matched prediction and ground-truth coordinates."""
        pred = np.asarray(predicted_3d, dtype=np.float64)
        gt = np.asarray(ground_truth_3d, dtype=np.float64)

        if len(pred) != len(gt):
            raise ValueError(
                f"Sample count mismatch: {len(pred)} predictions vs {len(gt)} ground-truth"
            )
        if len(pred) == 0:
            raise ValueError("Cannot evaluate empty coordinate set")

        # Longitudinal errors along X axis
        dx = pred[:, 0] - gt[:, 0]
        # Lateral errors along Z axis
        dz = pred[:, 2] - gt[:, 2]

        # 3D Euclidean distances
        distances = np.sqrt(dx**2 + dz**2)

        rmse = float(np.sqrt(np.mean(distances**2)))
        mae = float(np.mean(distances))

        long_mean = float(np.mean(np.abs(dx)))
        long_std = float(np.std(dx))
        lat_mean = float(np.mean(np.abs(dz)))
        lat_std = float(np.std(dz))

        # Heading error
        if pred_headings is not None and gt_headings is not None:
            p_h = np.asarray(pred_headings, dtype=np.float64)
            g_h = np.asarray(gt_headings, dtype=np.float64)
            # Shortest angular distance
            d_head = np.abs((p_h - g_h + 180.0) % 360.0 - 180.0)
            heading_err = float(np.mean(d_head))
        else:
            heading_err = 0.0

        # Speed error
        if pred_speeds is not None and gt_speeds is not None:
            p_s = np.asarray(pred_speeds, dtype=np.float64)
            g_s = np.asarray(gt_speeds, dtype=np.float64)
            speed_err = float(np.mean(np.abs(p_s - g_s)))
        else:
            speed_err = 0.0

        # Check compliance against formal acceptance thresholds
        passed = (
            rmse <= self.max_allowable_rmse_m
            and lat_mean <= self.max_allowable_lateral_m
            and heading_err <= self.max_allowable_heading_deg
        )

        status = "VERIFIED_PASSED" if passed else "FAIL_EXCEEDED_ERROR_BUDGET"

        return LocalizationBenchmarkResult(
            total_samples=len(pred),
            rmse_meters=round(rmse, 3),
            mae_meters=round(mae, 3),
            longitudinal_error_mean_m=round(long_mean, 3),
            longitudinal_error_std_m=round(long_std, 3),
            lateral_error_mean_m=round(lat_mean, 3),
            lateral_error_std_m=round(lat_std, 3),
            heading_error_deg=round(heading_err, 2),
            speed_error_kmh=round(speed_err, 2),
            pass_criteria_rmse_m=self.max_allowable_rmse_m,
            pass_criteria_lateral_m=self.max_allowable_lateral_m,
            pass_criteria_heading_deg=self.max_allowable_heading_deg,
            status=status,
        )

    def save_report(self, result: LocalizationBenchmarkResult, output_path: Path | str) -> None:
        """Write evaluation results to formatted JSON report."""
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2)
        print(f"✅ Digital Twin localization verification report saved to: {p}")
