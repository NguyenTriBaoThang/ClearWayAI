"""ClearWayAI Real Camera-to-3D Localization & Digital Twin Verification Subsystem (`ai.localization`) (Task 60).

Transforms 2D traffic perception bounding boxes into calibrated 3D Cartesian coordinates
within the digital twin world space and audits spatial accuracy against ground truth.
"""

from __future__ import annotations

from ai.localization.camera_to_3d import (
    CameraTo3DProjector,
    Vehicle3DTelemetry,
    VehicleKalmanFilter3D,
)
from ai.localization.digital_twin_verifier import (
    DigitalTwinLocalizationVerifier,
    LocalizationBenchmarkResult,
)
from ai.localization.run_verification_pipeline import run_localization_verification

__all__ = [
    "CameraTo3DProjector",
    "DigitalTwinLocalizationVerifier",
    "LocalizationBenchmarkResult",
    "Vehicle3DTelemetry",
    "VehicleKalmanFilter3D",
    "run_localization_verification",
]

