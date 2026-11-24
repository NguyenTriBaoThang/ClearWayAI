"""Automated Test Suite for Real Camera-to-3D Localization and Digital Twin Verification (Task 60).

Validates bottom-center tire contact point extraction, planar homography projection,
Kalman filter smoothing, heading angle derivation, spatial accuracy metrics, and benchmark thresholds.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np

from ai.calibration.homography import CameraCalibrationProfile
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

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_contact_point_and_homography_projection():
    """Verify bottom-center contact point extraction and coordinate transformation."""
    calib_path = REPO_ROOT / "data" / "calibration" / "cam_synth_corridor.json"
    profile = CameraCalibrationProfile.load_json(calib_path)
    projector = CameraTo3DProjector(calibration_profile=profile, node_offset_x=0.0)

    # Box with center (1000, 800), bottom y2 = 800
    bbox = [960.0, 750.0, 1040.0, 800.0]
    u, v = projector.extract_ground_contact_point(bbox)
    assert u == 1000.0
    assert v == 800.0

    # Project to metric ground
    x_m, y_m = projector.project_contact_to_metric(u, v)
    assert 0.0 <= x_m <= profile.roadway_width_m
    assert 0.0 <= y_m <= profile.approach_length_m


def test_corridor_world_coordinate_mapping():
    """Verify mapping into 3D Digital Twin global coordinates across approaches."""
    calib_path = REPO_ROOT / "data" / "calibration" / "cam_synth_corridor.json"
    profile = CameraCalibrationProfile.load_json(calib_path)
    projector = CameraTo3DProjector(calibration_profile=profile, node_offset_x=300.0)

    # Eastbound approach: y_metric = 80m (upstream), y_metric = 0m (stopline)
    # x_metric = 7.0m (centerline of 14m roadway)
    wx, wy, wz = projector.map_to_corridor_world_3d(x_metric=7.0, y_metric=80.0)
    assert wy == 0.0  # Ground elevation
    assert wz == 0.0  # Roadway centerline
    assert wx == 300.0  # Stopline coordinate at Node B

    wx_upstream, _, wz_upstream = projector.map_to_corridor_world_3d(x_metric=7.0, y_metric=0.0)
    assert wx_upstream == 300.0 - 80.0  # 80m upstream of Node B


def test_kalman_filter_smoothing():
    """Verify 3D coordinate smoothing and velocity convergence."""
    kf = VehicleKalmanFilter3D(init_x=0.0, init_z=0.0)

    # Simulate vehicle moving along X at 10.0 m/s with 0.1s dt
    true_vx = 10.0
    dt = 0.1
    for i in range(1, 20):
        t = i * dt
        true_x = true_vx * t
        noisy_x = true_x + np.random.normal(0.0, 0.2)

        kf.predict(dt)
        pos = kf.update(noisy_x, 0.0)

    # Position should track closely and estimated velocity should approximate 10 m/s
    assert abs(pos[0] - true_x) < 0.5
    assert abs(kf.state[2] - true_vx) < 1.5


def test_project_detection_end_to_end():
    """Verify project_detection emits complete Vehicle3DTelemetry."""
    calib_path = REPO_ROOT / "data" / "calibration" / "cam_synth_corridor.json"
    profile = CameraCalibrationProfile.load_json(calib_path)
    projector = CameraTo3DProjector(calibration_profile=profile, node_offset_x=0.0)

    bbox1 = [940.0, 750.0, 1020.0, 800.0]
    bbox2 = [950.0, 740.0, 1030.0, 790.0]

    t1 = projector.project_detection("veh_01", "car", bbox1, timestamp_sec=0.0)
    t2 = projector.project_detection("veh_01", "car", bbox2, timestamp_sec=0.1)

    assert isinstance(t1, Vehicle3DTelemetry)
    assert isinstance(t2, Vehicle3DTelemetry)
    assert t1.vehicle_id == "veh_01"
    assert t1.position_y == 0.0
    assert t2.speed_kmh >= 0.0
    assert -7.0 <= t2.position_z <= 7.0

    projector.reset_tracks()
    assert len(projector.track_filters) == 0


def test_digital_twin_verifier_metrics():
    """Verify localization accuracy evaluator and pass/fail thresholds."""
    verifier = DigitalTwinLocalizationVerifier(
        max_allowable_rmse_m=1.50,
        max_allowable_lateral_m=0.60,
        max_allowable_heading_deg=10.0,
    )

    pred_3d = [(0.2, 0.0, 0.1), (1.1, 0.0, -0.2), (2.0, 0.0, 0.0)]
    gt_3d = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)]
    pred_h = [0.0, 1.0, -1.0]
    gt_h = [0.0, 0.0, 0.0]

    result = verifier.evaluate_coordinates(
        predicted_3d=pred_3d,
        ground_truth_3d=gt_3d,
        pred_headings=pred_h,
        gt_headings=gt_h,
    )

    assert isinstance(result, LocalizationBenchmarkResult)
    assert result.total_samples == 3
    assert result.rmse_meters < 0.50
    assert result.lateral_error_mean_m < 0.20
    assert result.heading_error_deg < 2.0
    assert result.status == "VERIFIED_PASSED"

    # Test saving report
    with tempfile.TemporaryDirectory() as tmp_dir:
        report_file = Path(tmp_dir) / "test_report.json"
        verifier.save_report(result, report_file)
        assert report_file.exists()


def test_full_verification_pipeline_run():
    """Verify run_localization_verification pipeline completes and satisfies error bounds."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        report_file = Path(tmp_dir) / "bench_report.json"
        report = run_localization_verification(
            report_output_path=report_file,
            num_vehicles=3,
            timesteps=15,
            pixel_noise_sigma=1.0,
            seed=42,
        )

        assert report["status"] == "VERIFIED_PASSED"
        assert report["rmse_meters"] <= 1.50
        assert report["lateral_error_mean_m"] <= 0.60
        assert report["heading_error_deg"] <= 10.0
        assert report_file.exists()

