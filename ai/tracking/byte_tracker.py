"""ByteTrack Multi-Object Tracking (MOT) Implementation.

Paper: "ByteTrack: Multi-Object Tracking by Associating Every Detection Box"
(Zhang et al., ECCV 2022).

Key Innovation for Vietnamese Mixed Traffic:
Associates BOTH high-confidence and low-confidence detection boxes in a two-stage
Hungarian matching process, preventing lost tracks during dense motorcycle occlusion.
"""

from __future__ import annotations

import sys
from typing import Any

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        """Python 3.10 compatibility backport for StrEnum."""

        def __str__(self) -> str:
            return str(self.value)


import numpy as np
from scipy.optimize import linear_sum_assignment

from ai.detection.yolo_detector import Detection, compute_iou
from ai.tracking.kalman_filter import (
    KalmanFilter,
    bbox_to_xyah,
    xyah_to_bbox,
)


class TrackState(StrEnum):
    """Lifecycle states of a tracked vehicle."""

    NEW = "New"
    TRACKED = "Tracked"
    LOST = "Lost"
    REMOVED = "Removed"


class Tracklet:
    """Individual vehicle track state machine and motion history."""

    _count = 0

    def __init__(
        self,
        detection: Detection,
        frame_id: int = 1,
        timestamp_sec: float = 0.0,
    ) -> None:
        Tracklet._count += 1
        self.track_id = Tracklet._count

        self.class_id = detection.class_id
        self.class_name = detection.class_name
        self.confidence = detection.confidence
        self.state = TrackState.NEW

        self.kalman_filter = KalmanFilter()
        measurement = bbox_to_xyah(detection.bbox)
        self.mean, self.covariance = self.kalman_filter.initiate(measurement)

        self.bbox: tuple[float, float, float, float] = detection.bbox
        self.hits = 1
        self.age = 0
        self.time_since_update = 0
        self.start_frame = frame_id
        self.last_frame = frame_id

        # History of (timestamp_sec, center_x, center_y, bbox)
        xc, yc = detection.center
        self.history: list[tuple[float, float, float, tuple[float, float, float, float]]] = [
            (timestamp_sec, xc, yc, detection.bbox)
        ]

    @property
    def is_confirmed(self) -> bool:
        return self.state == TrackState.TRACKED

    def predict(self) -> None:
        """Advance track state using Kalman motion model."""
        if self.state != TrackState.TRACKED:
            self.mean[7] = 0.0
        self.mean, self.covariance = self.kalman_filter.predict(self.mean, self.covariance)
        self.bbox = xyah_to_bbox(self.mean[:4])
        self.age += 1
        self.time_since_update += 1

    def update(
        self,
        detection: Detection,
        frame_id: int,
        timestamp_sec: float,
    ) -> None:
        """Update track with a newly matched detection."""
        meas = bbox_to_xyah(detection.bbox)
        self.mean, self.covariance = self.kalman_filter.update(self.mean, self.covariance, meas)
        self.bbox = xyah_to_bbox(self.mean[:4])

        self.confidence = detection.confidence
        # Update class if high confidence
        if detection.confidence > 0.60:
            self.class_id = detection.class_id
            self.class_name = detection.class_name

        self.hits += 1
        self.time_since_update = 0
        self.last_frame = frame_id

        xc, yc = detection.center
        self.history.append((timestamp_sec, xc, yc, detection.bbox))
        if len(self.history) > 120:
            self.history.pop(0)

    def mark_tracked(self) -> None:
        self.state = TrackState.TRACKED

    def mark_lost(self) -> None:
        self.state = TrackState.LOST

    def mark_removed(self) -> None:
        self.state = TrackState.REMOVED

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_id": self.track_id,
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": round(float(self.confidence), 4),
            "state": self.state.value,
            "bbox": [round(float(c), 4) for c in self.bbox],
            "hits": self.hits,
            "age": self.age,
        }


def compute_iou_cost_matrix(
    tracks: list[Tracklet],
    detections: list[Detection],
) -> np.ndarray:
    """Compute (1 - IoU) cost matrix between predicted tracks and candidate detections."""
    if not tracks or not detections:
        return np.empty((len(tracks), len(detections)), dtype=float)

    cost_mat = np.zeros((len(tracks), len(detections)), dtype=float)
    for i, trk in enumerate(tracks):
        for j, det in enumerate(detections):
            iou = compute_iou(trk.bbox, det.bbox)
            cost_mat[i, j] = 1.0 - iou
    return cost_mat


class ByteTracker:
    """ByteTrack Multi-Object Tracking Engine for Vietnamese Mixed Traffic."""

    def __init__(
        self,
        track_thresh: float = 0.50,
        low_conf_thresh: float = 0.10,
        match_thresh: float = 0.80,
        match_thresh_low: float = 0.50,
        max_time_lost: int = 30,
        confirm_hits: int = 2,
    ) -> None:
        self.track_thresh = track_thresh
        self.low_conf_thresh = low_conf_thresh
        self.match_thresh = match_thresh
        self.match_thresh_low = match_thresh_low
        self.max_time_lost = max_time_lost
        self.confirm_hits = confirm_hits

        self.tracked_stracks: list[Tracklet] = []
        self.lost_stracks: list[Tracklet] = []
        self.removed_stracks: list[Tracklet] = []
        self.frame_count = 0

    def update(
        self,
        detections: list[Detection],
        frame_id: int = 1,
        timestamp_sec: float = 0.0,
    ) -> list[Tracklet]:
        """Update tracker state with a new frame's detections.

        Returns:
            List of actively tracked confirmed vehicles.
        """
        self.frame_count = frame_id

        # 1. Partition detections into high-score and low-score pools
        dets_high: list[Detection] = []
        dets_low: list[Detection] = []

        for d in detections:
            if d.confidence >= self.track_thresh:
                dets_high.append(d)
            elif d.confidence >= self.low_conf_thresh:
                dets_low.append(d)

        # 2. Kalman motion prediction on existing tracks
        for t in self.tracked_stracks:
            t.predict()
        for t in self.lost_stracks:
            t.predict()

        # -------------------------------------------------------------
        # 3. FIRST ASSOCIATION: Match tracked tracks with high-score detections
        # -------------------------------------------------------------
        cost_mat = compute_iou_cost_matrix(self.tracked_stracks, dets_high)
        matched_a, unmatched_tracks_a, unmatched_dets_high = self._linear_assignment(
            cost_mat, self.match_thresh
        )

        for trk_idx, det_idx in matched_a:
            track = self.tracked_stracks[trk_idx]
            det = dets_high[det_idx]
            track.update(det, frame_id, timestamp_sec)
            if track.hits >= self.confirm_hits:
                track.mark_tracked()

        # -------------------------------------------------------------
        # 4. SECOND ASSOCIATION: Match unmatched tracks with low-score detections
        # (Crucial: recovers occluded motorcycles in dense clusters)
        # -------------------------------------------------------------
        remain_tracks = [self.tracked_stracks[i] for i in unmatched_tracks_a]
        cost_mat_low = compute_iou_cost_matrix(remain_tracks, dets_low)
        matched_b, unmatched_tracks_b, _ = self._linear_assignment(
            cost_mat_low, self.match_thresh_low
        )

        for r_idx, d_idx in matched_b:
            track = remain_tracks[r_idx]
            det = dets_low[d_idx]
            track.update(det, frame_id, timestamp_sec)
            if track.hits >= self.confirm_hits:
                track.mark_tracked()

        # Remaining unmatched tracks from pass 2 become LOST
        for r_idx in unmatched_tracks_b:
            track = remain_tracks[r_idx]
            track.mark_lost()

        # -------------------------------------------------------------
        # 5. ASSOCIATE REMAINING HIGH-SCORE DETECTIONS WITH LOST TRACKS
        # -------------------------------------------------------------
        unmatched_high = [dets_high[i] for i in unmatched_dets_high]
        cost_mat_lost = compute_iou_cost_matrix(self.lost_stracks, unmatched_high)
        matched_c, unmatched_lost, unmatched_new_dets = self._linear_assignment(
            cost_mat_lost, self.match_thresh
        )

        for l_idx, nh_idx in matched_c:
            track = self.lost_stracks[l_idx]
            det = unmatched_high[nh_idx]
            track.update(det, frame_id, timestamp_sec)
            track.mark_tracked()

        # -------------------------------------------------------------
        # 6. INITIALIZE NEW TRACKS FOR UNMATCHED HIGH-SCORE DETECTIONS
        # -------------------------------------------------------------
        new_tracks: list[Tracklet] = []
        for d_idx in unmatched_new_dets:
            det = unmatched_high[d_idx]
            new_trk = Tracklet(det, frame_id, timestamp_sec)
            if self.confirm_hits <= 1:
                new_trk.mark_tracked()
            new_tracks.append(new_trk)

        # -------------------------------------------------------------
        # 7. UPDATE TRACK POOLS & PURGE EXPIRED
        # -------------------------------------------------------------
        all_tracked: list[Tracklet] = []
        all_lost: list[Tracklet] = []

        # Process previous tracked pool
        for t in self.tracked_stracks:
            if t.state == TrackState.TRACKED or t.state == TrackState.NEW:
                all_tracked.append(t)
            elif t.state == TrackState.LOST:
                all_lost.append(t)
            elif t.state == TrackState.REMOVED:
                self.removed_stracks.append(t)

        # Process lost pool
        for t in self.lost_stracks:
            if t.state == TrackState.TRACKED:
                all_tracked.append(t)
            elif t.state == TrackState.LOST:
                if t.time_since_update <= self.max_time_lost:
                    all_lost.append(t)
                else:
                    t.mark_removed()
                    self.removed_stracks.append(t)

        # Add new tracks
        all_tracked.extend(new_tracks)

        self.tracked_stracks = all_tracked
        self.lost_stracks = all_lost

        # Return only confirmed tracked tracks
        return [t for t in self.tracked_stracks if t.is_confirmed]

    def _linear_assignment(
        self,
        cost_matrix: np.ndarray,
        threshold: float,
    ) -> tuple[list[tuple[int, int]], list[int], list[int]]:
        """Hungarian matching with distance gating."""
        if cost_matrix.size == 0:
            return [], list(range(cost_matrix.shape[0])), list(range(cost_matrix.shape[1]))

        row_indices, col_indices = linear_sum_assignment(cost_matrix)

        matches: list[tuple[int, int]] = []
        unmatched_rows = list(set(range(cost_matrix.shape[0])) - set(row_indices))
        unmatched_cols = list(set(range(cost_matrix.shape[1])) - set(col_indices))

        for r, c in zip(row_indices, col_indices, strict=True):
            if cost_matrix[r, c] <= threshold:
                matches.append((int(r), int(c)))
            else:
                unmatched_rows.append(int(r))
                unmatched_cols.append(int(c))

        return matches, sorted(unmatched_rows), sorted(unmatched_cols)
