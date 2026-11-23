"""Automated test suite for Task 32: Camera Calibration & Macroscopic Traffic State Estimator.

Validates:
1. Planar Homography computation via DLT (SVD) and inverse reprojection.
2. Camera calibration profiles loading and JSON persistence.
3. Metric ground plane projection and coordinate roundtrip (pixel <-> meter).
4. Queue length estimation (meters from stopline), occupancy ratio, and density.
5. Vietnamese mixed-traffic motorcycle ratio calculation.
6. Emergency vehicle corridor pre-clearance trigger detection.
7. Verification of all official intersection camera calibration profiles.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from ai.calibration.homography import (
    CameraCalibrationProfile,
    compute_homography,
    reprojection_error,
    transform_points,
)
from ai.detection.yolo_detector import Detection
from ai.state.traffic_state_estimator import (
    ApproachTrafficState,
    TrafficStateEstimator,
)
from ai.tracking.byte_tracker import Tracklet


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def calibration_dir(repo_root: Path) -> Path:
    return repo_root / "data" / "calibration"


# =========================================================================
# 1. HOMOGRAPHY & PLANAR GEOMETRY TESTS
# =========================================================================


def test_compute_homography_exact_transform() -> None:
    """Homography between 4 known points must reproject with zero error."""
    src = [(100.0, 100.0), (500.0, 100.0), (500.0, 400.0), (100.0, 400.0)]
    # Linear scale + translation: X = 0.1 * u, Y = 0.2 * v + 5.0
    dst = [(10.0, 25.0), (50.0, 25.0), (50.0, 85.0), (10.0, 85.0)]

    H = compute_homography(src, dst)
    projected = transform_points(H, src)

    for p, d in zip(projected, dst, strict=True):
        assert pytest.approx(p[0], abs=1e-4) == d[0]
        assert pytest.approx(p[1], abs=1e-4) == d[1]

    err = reprojection_error(H, src, dst)
    assert err < 1e-4


def test_homography_perspective_warp_and_inverse() -> None:
    """Homography on perspective trapezoid must support exact inverse projection."""
    # Trapezoid in image (perspective view of road)
    src_trapezoid = [(600.0, 900.0), (1320.0, 900.0), (1060.0, 450.0), (860.0, 450.0)]
    # Metric rectangle on ground (14m wide x 80m deep)
    dst_rectangle = [(0.0, 0.0), (14.0, 0.0), (14.0, 80.0), (0.0, 80.0)]

    H = compute_homography(src_trapezoid, dst_rectangle)
    ground_pts = transform_points(H, src_trapezoid)

    for g, exp in zip(ground_pts, dst_rectangle, strict=True):
        assert pytest.approx(g[0], abs=1e-4) == exp[0]
        assert pytest.approx(g[1], abs=1e-4) == exp[1]

    # Inverse transformation: ground back to pixels
    H_inv = np.linalg.inv(H)
    restored_pixels = transform_points(H_inv, ground_pts)

    for r, orig in zip(restored_pixels, src_trapezoid, strict=True):
        assert pytest.approx(r[0], abs=1e-2) == orig[0]
        assert pytest.approx(r[1], abs=1e-2) == orig[1]


def test_compute_homography_insufficient_points() -> None:
    """Homography must raise ValueError if fewer than 4 points provided."""
    with pytest.raises(ValueError, match="At least 4 point"):
        compute_homography([(0, 0), (1, 1)], [(0, 0), (1, 1)])


# =========================================================================
# 2. CAMERA CALIBRATION PROFILE TESTS
# =========================================================================


def test_calibration_profile_create_and_json(tmp_path: Path) -> None:
    """Test CameraCalibrationProfile serialization and inverse projection helper."""
    src = [(600.0, 900.0), (1320.0, 900.0), (1060.0, 450.0), (860.0, 450.0)]
    dst = [(0.0, 0.0), (14.0, 0.0), (14.0, 80.0), (0.0, 80.0)]

    prof = CameraCalibrationProfile.create(
        camera_id="CAM_TEST_01",
        intersection_name="Test Intersection",
        approach_direction="EB",
        image_resolution=(1920, 1080),
        roadway_width_m=14.0,
        approach_length_m=80.0,
        source_points_pixel=src,
        destination_points_meters=dst,
        stopline_y_m=0.0,
    )

    assert prof.reprojection_error_m < 0.01

    # Save to JSON
    json_path = tmp_path / "test_calib.json"
    prof.save_json(json_path)
    assert json_path.is_file()

    # Load from JSON
    loaded = CameraCalibrationProfile.load_json(json_path)
    assert loaded.camera_id == "CAM_TEST_01"
    assert loaded.roadway_width_m == 14.0

    # Project to meters and back
    meters = loaded.project_to_meters([(960.0, 900.0)])  # bottom center of stopline
    assert pytest.approx(meters[0, 0], abs=0.5) == 7.0  # midpoint of 14m road
    assert pytest.approx(meters[0, 1], abs=0.5) == 0.0  # at stopline Y=0


def test_official_calibration_profiles_valid(calibration_dir: Path) -> None:
    """Assert all 4 official calibration profiles exist and have low reprojection error."""
    profiles = [
        "cam_hcmc_d1.json",
        "cam_hcmc_d5.json",
        "cam_hanoi_hk.json",
        "cam_synth_corridor.json",
    ]
    for filename in profiles:
        prof_path = calibration_dir / filename
        assert prof_path.is_file(), f"Missing calibration profile: {filename}"

        prof = CameraCalibrationProfile.load_json(prof_path)
        assert prof.reprojection_error_m < 0.10, (
            f"Excessive error in {filename}: {prof.reprojection_error_m}m"
        )
        assert len(prof.homography_matrix) == 3
        assert prof.roadway_width_m >= 10.0
        assert prof.approach_length_m >= 50.0


# =========================================================================
# 3. MACROSCOPIC TRAFFIC STATE ESTIMATION TESTS
# =========================================================================


@pytest.fixture
def dummy_profile() -> CameraCalibrationProfile:
    src = [(600.0, 900.0), (1320.0, 900.0), (1060.0, 450.0), (860.0, 450.0)]
    dst = [(0.0, 0.0), (14.0, 0.0), (14.0, 80.0), (0.0, 80.0)]
    return CameraCalibrationProfile.create(
        camera_id="CAM_TEST_01",
        intersection_name="Test Intersection",
        approach_direction="EB",
        image_resolution=(1920, 1080),
        roadway_width_m=14.0,
        approach_length_m=80.0,
        source_points_pixel=src,
        destination_points_meters=dst,
        stopline_y_m=0.0,
    )


def test_traffic_state_empty_approach(dummy_profile: CameraCalibrationProfile) -> None:
    """Empty approach should yield zero queue length and zero occupancy."""
    estimator = TrafficStateEstimator(dummy_profile)
    state = estimator.estimate_approach_state([])

    assert state.vehicle_count == 0
    assert state.queue_length_meters == 0.0
    assert state.queued_vehicle_count == 0
    assert state.approach_occupancy_ratio == 0.0
    assert state.motorcycle_ratio == 0.0
    assert state.emergency_vehicle_detected is False
    assert state.estimated_queue_flush_time_sec == 0.0


def test_traffic_state_queue_length_and_occupancy(dummy_profile: CameraCalibrationProfile) -> None:
    """Test queue length is determined by furthest stopped vehicle from stopline."""
    estimator = TrafficStateEstimator(dummy_profile)

    # Create 3 tracklets in queue (motorcycle near stopline, car behind, truck further back)
    # Stopline is at Y=0 (bottom of image ~900px, top is Y=80m ~450px)
    # Normalized coords: y=0.83 is near stopline, y=0.55 is ~40m back
    t1 = Tracklet(
        Detection(
            bbox=(0.48, 0.80, 0.52, 0.86), confidence=0.92, class_id=0, class_name="motorcycle"
        ),
        frame_id=1,
    )
    t2 = Tracklet(
        Detection(bbox=(0.45, 0.65, 0.55, 0.75), confidence=0.90, class_id=1, class_name="car"),
        frame_id=1,
    )
    t3 = Tracklet(
        Detection(bbox=(0.44, 0.50, 0.56, 0.62), confidence=0.88, class_id=4, class_name="truck"),
        frame_id=1,
    )

    tracklets = [t1, t2, t3]
    state = estimator.estimate_approach_state(tracklets, timestamp_sec=10.0)

    assert state.vehicle_count == 3
    assert state.queued_vehicle_count == 3
    # Furthest vehicle (truck at y_max~0.62) is approximately 18m back on ground plane
    assert state.queue_length_meters > 15.0
    assert state.approach_occupancy_ratio > 0.0
    assert state.motorcycle_ratio == pytest.approx(1.0 / 3.0, abs=1e-3)
    # Estimated flush time = 3.0s startup + (queue / 4.5 m/s)
    assert state.estimated_queue_flush_time_sec > 3.0


def test_traffic_state_emergency_vehicle_detection(dummy_profile: CameraCalibrationProfile) -> None:
    """Emergency vehicle presence must trigger preemption flag and report distance."""
    estimator = TrafficStateEstimator(dummy_profile)

    amb_det = Detection(
        bbox=(0.48, 0.70, 0.54, 0.82), confidence=0.95, class_id=5, class_name="ambulance"
    )
    amb_track = Tracklet(amb_det, frame_id=1)

    state = estimator.estimate_approach_state([amb_track], timestamp_sec=5.0)

    assert state.emergency_vehicle_detected is True
    assert state.emergency_class == "ambulance"
    assert state.emergency_distance_to_stopline_m is not None
    assert state.emergency_distance_to_stopline_m >= 0.0


def test_intersection_traffic_state_aggregation(dummy_profile: CameraCalibrationProfile) -> None:
    """IntersectionTrafficState should aggregate all approaches and identify critical approach."""
    estimator = TrafficStateEstimator(dummy_profile)

    # Approach EB has normal queue (20m)
    app_eb = ApproachTrafficState(
        approach_id="EB",
        timestamp_sec=1.0,
        vehicle_count=5,
        counts_by_class={"motorcycle": 4, "car": 1},
        motorcycle_ratio=0.8,
        queue_length_meters=20.0,
        queued_vehicle_count=4,
        approach_occupancy_ratio=0.15,
        traffic_density_vpm=6.25,
        mean_speed_kmh=12.0,
        emergency_vehicle_detected=False,
    )

    # Approach NB has emergency ambulance
    app_nb = ApproachTrafficState(
        approach_id="NB",
        timestamp_sec=1.0,
        vehicle_count=3,
        counts_by_class={"motorcycle": 2, "ambulance": 1},
        motorcycle_ratio=0.67,
        queue_length_meters=15.0,
        queued_vehicle_count=2,
        approach_occupancy_ratio=0.12,
        traffic_density_vpm=4.28,
        mean_speed_kmh=22.0,
        emergency_vehicle_detected=True,
        emergency_class="ambulance",
        emergency_distance_to_stopline_m=18.5,
    )

    approaches = {"EB": app_eb, "NB": app_nb}
    inter_state = estimator.estimate_intersection_state(approaches, intersection_id="INT_OAK_5TH")

    assert inter_state.total_vehicle_count == 8
    assert inter_state.total_queued_count == 6
    assert inter_state.max_queue_length_meters == 20.0
    # NB is critical because of emergency vehicle
    assert inter_state.critical_approach == "NB"
    assert inter_state.emergency_preemption_active is True
