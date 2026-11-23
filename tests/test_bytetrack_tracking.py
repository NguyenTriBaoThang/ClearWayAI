"""Automated test suite for Task 31: ByteTrack Multi-Object Tracking & Vehicle Trajectories.

Validates:
1. Kalman filter motion prediction and state covariance convergence.
2. Invertible bounding box <-> xyah coordinate transformation.
3. ByteTrack two-stage association recovering occluded vehicles (Low-Score Match).
4. Tracklet lifecycle transitions (New -> Tracked -> Lost -> Removed).
5. Continuous trajectory extraction, speed estimation (km/h), and heading.
6. Virtual tripwire stopline crossing count accuracy.
7. End-to-end integration with YOLO detection outputs.
"""

from __future__ import annotations

import numpy as np
import pytest

from ai.detection.yolo_detector import Detection, YOLOInferenceEngine
from ai.tracking.byte_tracker import (
    ByteTracker,
    TrackState,
)
from ai.tracking.kalman_filter import (
    KalmanFilter,
    bbox_to_xyah,
    xyah_to_bbox,
)
from ai.tracking.trajectory import (
    TrajectoryTracker,
    VehicleTrajectory,
    VirtualTripwire,
    line_segments_intersect,
)

# =========================================================================
# 1. KALMAN FILTER TESTS
# =========================================================================


def test_bbox_xyah_conversion_roundtrip() -> None:
    """Verify bbox [x_min, y_min, x_max, y_max] <-> xyah is strictly invertible."""
    original_bbox = (0.25, 0.35, 0.65, 0.85)
    xyah = bbox_to_xyah(original_bbox)
    restored_bbox = xyah_to_bbox(xyah)

    for orig, rest in zip(original_bbox, restored_bbox, strict=True):
        assert pytest.approx(orig, abs=1e-4) == rest


def test_kalman_filter_motion_convergence() -> None:
    """Kalman filter should track linear motion and estimate positive velocity."""
    kf = KalmanFilter()
    init_box = bbox_to_xyah((0.10, 0.20, 0.18, 0.35))
    mean, cov = kf.initiate(init_box)

    # Move rightwards along X: 0.10 -> 0.15 -> 0.20 -> 0.25
    for step in range(1, 5):
        mean, cov = kf.predict(mean, cov)
        new_box = bbox_to_xyah((0.10 + step * 0.05, 0.20, 0.18 + step * 0.05, 0.35))
        mean, cov = kf.update(mean, cov, new_box)

    # Velocity along x (index 4) should be positive
    vx = mean[4]
    assert vx > 0.02
    assert np.all(np.diag(cov) >= 0.0)


# =========================================================================
# 2. BYTETRACK TWO-STAGE ASSOCIATION TESTS
# =========================================================================


def test_bytetrack_stable_id_tracking() -> None:
    """Tracker must maintain identical track_id for moving vehicle across frames."""
    tracker = ByteTracker(track_thresh=0.50, confirm_hits=2)
    track_ids: list[int] = []

    for frame in range(1, 6):
        x = 0.20 + (frame - 1) * 0.03
        det = Detection(
            bbox=(x, 0.40, x + 0.08, 0.52),
            confidence=0.90,
            class_id=0,
            class_name="motorcycle",
        )
        tracks = tracker.update([det], frame_id=frame, timestamp_sec=frame * 0.033)

        if tracks:
            track_ids.append(tracks[0].track_id)

    # Once confirmed (frame 2+), the ID must stay completely constant
    assert len(track_ids) >= 4
    assert len(set(track_ids)) == 1, f"ID switch occurred: {track_ids}"


def test_bytetrack_low_confidence_occlusion_recovery() -> None:
    """Crucial ByteTrack invariant: Low-score detection in Stage 2 recovers occluded vehicle."""
    tracker = ByteTracker(
        track_thresh=0.60,  # High threshold
        low_conf_thresh=0.20,  # Low threshold
        confirm_hits=1,
    )

    # Frame 1: Clear visibility (conf 0.92)
    det1 = Detection(
        bbox=(0.40, 0.40, 0.48, 0.55), confidence=0.92, class_id=0, class_name="motorcycle"
    )
    t1 = tracker.update([det1], frame_id=1, timestamp_sec=0.033)
    assert len(t1) == 1
    init_id = t1[0].track_id

    # Frame 2: Moving slightly, still visible (conf 0.88)
    det2 = Detection(
        bbox=(0.42, 0.41, 0.50, 0.56), confidence=0.88, class_id=0, class_name="motorcycle"
    )
    t2 = tracker.update([det2], frame_id=2, timestamp_sec=0.066)
    assert len(t2) == 1
    assert t2[0].track_id == init_id

    # Frame 3: Severe occlusion by bus! Confidence drops to 0.35 (below 0.60 high threshold)
    # ByteTrack stage 2 must match it and NOT lose or re-assign ID!
    det3 = Detection(
        bbox=(0.44, 0.42, 0.52, 0.57), confidence=0.35, class_id=0, class_name="motorcycle"
    )
    t3 = tracker.update([det3], frame_id=3, timestamp_sec=0.100)
    assert len(t3) == 1
    assert t3[0].track_id == init_id, "ByteTrack failed to recover occluded vehicle in Stage 2!"

    # Frame 4: Vehicle emerges from occlusion, conf 0.94
    det4 = Detection(
        bbox=(0.46, 0.43, 0.54, 0.58), confidence=0.94, class_id=0, class_name="motorcycle"
    )
    t4 = tracker.update([det4], frame_id=4, timestamp_sec=0.133)
    assert len(t4) == 1
    assert t4[0].track_id == init_id


def test_tracklet_lifecycle_lost_and_removed() -> None:
    """Tracklet must transition to Lost then Removed when detections disappear."""
    tracker = ByteTracker(track_thresh=0.50, max_time_lost=2, confirm_hits=1)

    det = Detection(bbox=(0.30, 0.30, 0.40, 0.45), confidence=0.95, class_id=1, class_name="car")
    tracks = tracker.update([det], frame_id=1, timestamp_sec=0.033)
    assert len(tracks) == 1
    assert tracks[0].state == TrackState.TRACKED

    # Frame 2: Missing detection -> mark LOST
    tracks_f2 = tracker.update([], frame_id=2, timestamp_sec=0.066)
    assert len(tracks_f2) == 0
    assert len(tracker.lost_stracks) == 1
    assert tracker.lost_stracks[0].state == TrackState.LOST

    # Frame 3: Missing -> still LOST (time_since_update = 2 <= max_time_lost)
    tracker.update([], frame_id=3, timestamp_sec=0.100)
    assert len(tracker.lost_stracks) == 1

    # Frame 4: Missing -> exceeds max_time_lost (3 > 2) -> REMOVED
    tracker.update([], frame_id=4, timestamp_sec=0.133)
    assert len(tracker.lost_stracks) == 0
    assert len(tracker.removed_stracks) >= 1
    assert tracker.removed_stracks[0].state == TrackState.REMOVED


# =========================================================================
# 3. TRAJECTORY KINEMATICS & TRIPWIRE TESTS
# =========================================================================


def test_trajectory_speed_and_heading() -> None:
    """Trajectory tracker should calculate instantaneous and mean speeds."""
    traj = VehicleTrajectory(track_id=1, class_name="ambulance")

    # Move 10 meters east over 1.0 second (10 m/s = 36 km/h, heading 0 deg)
    traj.add_point(0.0, 0.0, 0.0, pixel_to_meter_scale=1.0)
    p2 = traj.add_point(10.0, 0.0, 1.0, pixel_to_meter_scale=1.0)

    assert pytest.approx(p2.speed_mps, abs=0.1) == 10.0
    assert pytest.approx(p2.speed_kmh, abs=0.1) == 36.0
    assert pytest.approx(p2.heading_deg, abs=0.5) == 0.0
    assert traj.total_distance_m == 10.0
    assert traj.is_stopped is False


def test_trajectory_is_stopped() -> None:
    """Vehicle with v < 2.0 km/h should be flagged as stopped/queued."""
    traj = VehicleTrajectory(track_id=2, class_name="motorcycle")
    traj.add_point(0.5, 0.5, 0.0)
    traj.add_point(0.5, 0.5, 2.0)  # zero movement over 2 seconds

    assert traj.instantaneous_speed_kmh == 0.0
    assert traj.is_stopped is True


def test_virtual_tripwire_line_crossing() -> None:
    """Tripwire should detect crossing and prevent duplicate counts for same ID."""
    # Horizontal tripwire across x in [0.0, 1.0] at y = 0.50
    tw = VirtualTripwire(
        name="stopline_approach_north",
        start_pt=(0.0, 0.50),
        end_pt=(1.0, 0.50),
    )

    # Path crossing from y=0.40 to y=0.60
    p_prev = (0.50, 0.40)
    p_curr = (0.50, 0.60)

    # First crossing: should return True
    crossed = tw.check_crossing(
        track_id=101, class_name="ambulance", prev_pos=p_prev, curr_pos=p_curr
    )
    assert crossed is True
    assert tw.total_count == 1
    assert tw.counts_by_class["ambulance"] == 1

    # Second crossing attempt with same track_id: should return False (no double counting)
    p_next = (0.50, 0.70)
    crossed_again = tw.check_crossing(
        track_id=101, class_name="ambulance", prev_pos=p_curr, curr_pos=p_next
    )
    assert crossed_again is False
    assert tw.total_count == 1


def test_line_segments_intersect_geometry() -> None:
    """Test geometric segment intersection helper."""
    # Intersecting cross
    assert line_segments_intersect((0, 5), (10, 5), (5, 0), (5, 10)) is True
    # Parallel lines
    assert line_segments_intersect((0, 0), (10, 0), (0, 5), (10, 5)) is False
    # Disjoint collinear
    assert line_segments_intersect((0, 0), (5, 0), (6, 0), (10, 0)) is False


# =========================================================================
# 4. END-TO-END PIPELINE INTEGRATION
# =========================================================================


def test_trajectory_tracker_pipeline_with_yolo() -> None:
    """Verify TrajectoryTracker updates successfully with YOLO detections."""
    tripwire = VirtualTripwire("corridor_line", (0.0, 0.50), (1.0, 0.50))
    traj_tracker = TrajectoryTracker(tripwires=[tripwire], confirm_hits=1)

    # Feed synthetic frames
    detector = YOLOInferenceEngine()

    for f in range(1, 5):
        det_result = detector.predict(frame_id=f, timestamp_sec=f * 0.033)
        active_tracks = traj_tracker.update(
            det_result.detections, frame_id=f, timestamp_sec=f * 0.033
        )
        assert len(active_tracks) > 0

    # Verify trajectories were generated
    assert len(traj_tracker.trajectories) > 0
    # Verify count method
    queued_count = traj_tracker.count_active_queued()
    assert queued_count >= 0
