"""ClearWayAI Multi-Object Tracking & Vehicle Trajectory Extraction Package."""

from ai.tracking.byte_tracker import (
    ByteTracker,
    Tracklet,
    TrackState,
    compute_iou_cost_matrix,
)
from ai.tracking.kalman_filter import (
    KalmanFilter,
    bbox_to_xyah,
    xyah_to_bbox,
)
from ai.tracking.trajectory import (
    TrajectoryPoint,
    TrajectoryTracker,
    VehicleTrajectory,
    VirtualTripwire,
    line_segments_intersect,
)

__all__ = [
    "ByteTracker",
    "Tracklet",
    "TrackState",
    "KalmanFilter",
    "bbox_to_xyah",
    "xyah_to_bbox",
    "compute_iou_cost_matrix",
    "TrajectoryPoint",
    "VehicleTrajectory",
    "VirtualTripwire",
    "TrajectoryTracker",
    "line_segments_intersect",
]

