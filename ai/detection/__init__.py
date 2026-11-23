"""ClearWayAI Vehicle Detection Package for Vietnamese Mixed Traffic."""

from ai.detection.metrics import (
    compute_ap,
    evaluate_detections,
    evaluate_map_range,
)
from ai.detection.yolo_detector import (
    CLASS_NAMES,
    Detection,
    DetectionResult,
    YOLOInferenceEngine,
    apply_nms,
    compute_iou,
)

__all__ = [
    "CLASS_NAMES",
    "Detection",
    "DetectionResult",
    "YOLOInferenceEngine",
    "apply_nms",
    "compute_iou",
    "compute_ap",
    "evaluate_detections",
    "evaluate_map_range",
]
