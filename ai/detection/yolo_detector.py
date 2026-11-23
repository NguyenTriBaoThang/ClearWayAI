"""ClearWayAI YOLO Object Detection Engine for Vietnamese Mixed Traffic.

Supports 7 vehicle classes:
0: motorcycle, 1: car, 2: suv, 3: bus, 4: truck, 5: ambulance, 6: fire_engine.
Includes pure-Python / numpy Non-Maximum Suppression (NMS), IoU computation,
and a dual-engine architecture (real weights or zero-dependency mock fallback).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

CLASS_NAMES: list[str] = [
    "motorcycle",
    "car",
    "suv",
    "bus",
    "truck",
    "ambulance",
    "fire_engine",
]
NUM_CLASSES = len(CLASS_NAMES)


@dataclass
class Detection:
    """Bounding box detection result."""

    bbox: tuple[float, float, float, float]  # (x_min, y_min, x_max, y_max) normalized to [0, 1]
    confidence: float
    class_id: int
    class_name: str

    @property
    def x_min(self) -> float:
        return self.bbox[0]

    @property
    def y_min(self) -> float:
        return self.bbox[1]

    @property
    def x_max(self) -> float:
        return self.bbox[2]

    @property
    def y_max(self) -> float:
        return self.bbox[3]

    @property
    def width(self) -> float:
        return max(0.0, self.x_max - self.x_min)

    @property
    def height(self) -> float:
        return max(0.0, self.y_max - self.y_min)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x_min + self.x_max) / 2.0, (self.y_min + self.y_max) / 2.0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "bbox": list(self.bbox),
            "confidence": round(self.confidence, 4),
            "class_id": self.class_id,
            "class_name": self.class_name,
            "area": round(self.area, 6),
            "center": [round(c, 4) for c in self.center],
        }


@dataclass
class DetectionResult:
    """Detection inference output for a single frame."""

    frame_id: int | str
    timestamp_sec: float
    detections: list[Detection] = field(default_factory=list)
    inference_time_ms: float = 0.0
    provenance: str = "YOLO_INFERENCE"
    image_width: int = 1920
    image_height: int = 1080

    def count_by_class(self) -> dict[str, int]:
        """Aggregate detection count per vehicle class."""
        counts = dict.fromkeys(CLASS_NAMES, 0)
        for det in self.detections:
            if det.class_name in counts:
                counts[det.class_name] += 1
        return counts

    def filter_by_confidence(self, min_conf: float) -> list[Detection]:
        """Filter detections above a confidence threshold."""
        return [d for d in self.detections if d.confidence >= min_conf]

    @property
    def total_count(self) -> int:
        return len(self.detections)

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "timestamp_sec": round(self.timestamp_sec, 3),
            "total_count": self.total_count,
            "inference_time_ms": round(self.inference_time_ms, 2),
            "provenance": self.provenance,
            "class_counts": self.count_by_class(),
            "detections": [d.to_dict() for d in self.detections],
        }


def compute_iou(
    box_a: tuple[float, float, float, float] | list[float],
    box_b: tuple[float, float, float, float] | list[float],
) -> float:
    """Calculate Intersection over Union (IoU) between two [x_min, y_min, x_max, y_max] boxes."""
    x_min_inter = max(box_a[0], box_b[0])
    y_min_inter = max(box_a[1], box_b[1])
    x_max_inter = min(box_a[2], box_b[2])
    y_max_inter = min(box_a[3], box_b[3])

    inter_w = max(0.0, x_max_inter - x_min_inter)
    inter_h = max(0.0, y_max_inter - y_min_inter)
    intersection = inter_w * inter_h

    area_a = max(0.0, box_a[2] - box_a[0]) * max(0.0, box_a[3] - box_a[1])
    area_b = max(0.0, box_b[2] - box_b[0]) * max(0.0, box_b[3] - box_b[1])
    union = area_a + area_b - intersection

    if union <= 1e-9:
        return 0.0

    return min(1.0, max(0.0, intersection / union))


def apply_nms(
    detections: list[Detection],
    iou_threshold: float = 0.45,
    class_agnostic: bool = False,
) -> list[Detection]:
    """Perform Non-Maximum Suppression (NMS) to eliminate duplicate bounding boxes."""
    if not detections:
        return []

    # Sort detections by confidence score descending
    sorted_dets = sorted(detections, key=lambda d: d.confidence, reverse=True)
    kept: list[Detection] = []

    while sorted_dets:
        best = sorted_dets.pop(0)
        kept.append(best)

        remaining: list[Detection] = []
        for other in sorted_dets:
            # If class-aware, only suppress candidates of the same class
            if not class_agnostic and best.class_id != other.class_id:
                remaining.append(other)
                continue

            iou = compute_iou(best.bbox, other.bbox)
            if iou <= iou_threshold:
                remaining.append(other)

        sorted_dets = remaining

    return kept


class YOLOInferenceEngine:
    """Dual-engine detector supporting both live model weights and zero-dependency mock."""

    def __init__(
        self,
        weights_path: str | Path | None = None,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        device: str = "cpu",
        model_architecture: str = "yolov8s",
    ) -> None:
        self.weights_path = Path(weights_path) if weights_path else None
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        self.model_architecture = model_architecture
        self.is_real_model_loaded = False
        self._model: Any = None

        self._initialize_detector()

    def _initialize_detector(self) -> None:
        """Attempt to load real PyTorch/Ultralytics model; fallback gracefully if absent."""
        if self.weights_path and self.weights_path.is_file():
            try:
                # Try importing ultralytics if available
                from ultralytics import YOLO  # type: ignore

                self._model = YOLO(str(self.weights_path))
                self.is_real_model_loaded = True
            except ImportError:
                self.is_real_model_loaded = False
        else:
            self.is_real_model_loaded = False

    def predict(
        self,
        image: np.ndarray | str | Path | None = None,
        ground_truth_label: str | Path | None = None,
        frame_id: int | str = 1,
        timestamp_sec: float = 0.0,
    ) -> DetectionResult:
        """Execute detection inference on a frame."""
        start_t = time.perf_counter()

        # Mode 1: Real model loaded
        if self.is_real_model_loaded and self._model is not None and image is not None:
            results = self._model(image, conf=self.conf_threshold, iou=self.iou_threshold)
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            return self._parse_ultralytics_results(
                results, frame_id, timestamp_sec, elapsed_ms, "YOLO_INFERENCE"
            )

        # Mode 2: Ground-truth label file provided (e.g. from data/processed/yolo/labels/)
        if ground_truth_label:
            p = Path(ground_truth_label)
            if p.is_file():
                detections = self._load_detections_from_label_file(p)
                filtered = [d for d in detections if d.confidence >= self.conf_threshold]
                nms_dets = apply_nms(filtered, self.iou_threshold)
                elapsed_ms = (time.perf_counter() - start_t) * 1000.0
                return DetectionResult(
                    frame_id=frame_id,
                    timestamp_sec=timestamp_sec,
                    detections=nms_dets,
                    inference_time_ms=elapsed_ms,
                    provenance="OFFLINE_VIDEO",
                )

        # Mode 3: Heuristic synthetic mixed-traffic generator (Vietnamese corridor pattern)
        detections = self._generate_synthetic_mixed_traffic(frame_id)
        filtered = [d for d in detections if d.confidence >= self.conf_threshold]
        nms_dets = apply_nms(filtered, self.iou_threshold)
        elapsed_ms = (time.perf_counter() - start_t) * 1000.0

        return DetectionResult(
            frame_id=frame_id,
            timestamp_sec=timestamp_sec,
            detections=nms_dets,
            inference_time_ms=elapsed_ms,
            provenance="HEURISTIC_MOCK",
        )

    def predict_batch(
        self,
        images_or_labels: list[Any],
        start_frame: int = 1,
        fps: float = 30.0,
    ) -> list[DetectionResult]:
        """Execute batch inference across a sequence of frames."""
        results: list[DetectionResult] = []
        for idx, item in enumerate(images_or_labels):
            fid = start_frame + idx
            ts = idx / fps
            if isinstance(item, (str, Path)) and str(item).endswith(".txt"):
                res = self.predict(ground_truth_label=item, frame_id=fid, timestamp_sec=ts)
            else:
                res = self.predict(image=item, frame_id=fid, timestamp_sec=ts)
            results.append(res)
        return results

    def _load_detections_from_label_file(self, label_path: Path) -> list[Detection]:
        """Parse normalized YOLO label file: <class_id> <x_center> <y_center> <w> <h>."""
        detections: list[Detection] = []
        with open(label_path, encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    cls_id = int(parts[0])
                    xc, yc, w, h = map(float, parts[1:5])
                    conf = float(parts[5]) if len(parts) > 5 else 0.90  # default high conf for GT
                    x_min = max(0.0, xc - w / 2.0)
                    y_min = max(0.0, yc - h / 2.0)
                    x_max = min(1.0, xc + w / 2.0)
                    y_max = min(1.0, yc + h / 2.0)

                    cls_name = CLASS_NAMES[cls_id] if 0 <= cls_id < len(CLASS_NAMES) else "unknown"
                    detections.append(
                        Detection(
                            bbox=(x_min, y_min, x_max, y_max),
                            confidence=conf,
                            class_id=cls_id,
                            class_name=cls_name,
                        )
                    )
        return detections

    def _generate_synthetic_mixed_traffic(self, seed_offset: int | str) -> list[Detection]:
        """Generate deterministic Vietnamese mixed traffic detections (motorcycle swarm + cars + ambulance)."""
        rng = np.random.default_rng(abs(hash(str(seed_offset))) % (2**31))
        dets: list[Detection] = []

        # 1. Motorcycle swarm: 10 to 18 clustered motorcycles near stopline
        num_motos = rng.integers(10, 19)
        for _ in range(num_motos):
            xc = rng.uniform(0.35, 0.65)
            yc = rng.uniform(0.55, 0.75)
            w = rng.uniform(0.06, 0.09)
            h = rng.uniform(0.10, 0.14)
            conf = rng.uniform(0.75, 0.96)
            dets.append(
                Detection(
                    bbox=(xc - w / 2, yc - h / 2, xc + w / 2, yc + h / 2),
                    confidence=conf,
                    class_id=0,
                    class_name="motorcycle",
                )
            )

        # 2. Cars / Sedans: 3 to 5
        num_cars = rng.integers(3, 6)
        for _ in range(num_cars):
            xc = rng.uniform(0.20, 0.80)
            yc = rng.uniform(0.45, 0.65)
            w = rng.uniform(0.14, 0.19)
            h = rng.uniform(0.12, 0.17)
            conf = rng.uniform(0.80, 0.98)
            dets.append(
                Detection(
                    bbox=(xc - w / 2, yc - h / 2, xc + w / 2, yc + h / 2),
                    confidence=conf,
                    class_id=1,
                    class_name="car",
                )
            )

        # 3. SUV: 1 to 3
        num_suvs = rng.integers(1, 4)
        for _ in range(num_suvs):
            xc = rng.uniform(0.15, 0.85)
            yc = rng.uniform(0.40, 0.60)
            w = rng.uniform(0.16, 0.22)
            h = rng.uniform(0.14, 0.20)
            conf = rng.uniform(0.78, 0.95)
            dets.append(
                Detection(
                    bbox=(xc - w / 2, yc - h / 2, xc + w / 2, yc + h / 2),
                    confidence=conf,
                    class_id=2,
                    class_name="suv",
                )
            )

        # 4. Bus or Truck: 1 each occasionally
        if rng.random() > 0.4:
            dets.append(
                Detection(
                    bbox=(0.10, 0.40, 0.32, 0.68),
                    confidence=0.88,
                    class_id=3,
                    class_name="bus",
                )
            )
        if rng.random() > 0.5:
            dets.append(
                Detection(
                    bbox=(0.68, 0.38, 0.90, 0.66),
                    confidence=0.86,
                    class_id=4,
                    class_name="truck",
                )
            )

        # 5. AMB-339 Priority Emergency Ambulance: on corridor approach
        dets.append(
            Detection(
                bbox=(0.42, 0.70, 0.62, 0.89),
                confidence=0.94,
                class_id=5,
                class_name="ambulance",
            )
        )

        return dets

    def _parse_ultralytics_results(
        self,
        results: Any,
        frame_id: int | str,
        timestamp_sec: float,
        elapsed_ms: float,
        provenance: str,
    ) -> DetectionResult:
        """Parse Ultralytics YOLO Results object into standard DetectionResult."""
        detections: list[Detection] = []
        if results and len(results) > 0:
            boxes = results[0].boxes
            for i in range(len(boxes)):
                xyxyn = boxes.xyxyn[i].cpu().numpy()
                conf = float(boxes.conf[i].cpu().numpy())
                cls_id = int(boxes.cls[i].cpu().numpy())
                cls_name = CLASS_NAMES[cls_id] if 0 <= cls_id < len(CLASS_NAMES) else "unknown"
                detections.append(
                    Detection(
                        bbox=(float(xyxyn[0]), float(xyxyn[1]), float(xyxyn[2]), float(xyxyn[3])),
                        confidence=conf,
                        class_id=cls_id,
                        class_name=cls_name,
                    )
                )

        return DetectionResult(
            frame_id=frame_id,
            timestamp_sec=timestamp_sec,
            detections=detections,
            inference_time_ms=elapsed_ms,
            provenance=provenance,
        )

    def benchmark_latency(self, num_runs: int = 20) -> dict[str, float]:
        """Profile detector runtime latency in milliseconds."""
        times: list[float] = []
        dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)

        for i in range(num_runs):
            t0 = time.perf_counter()
            self.predict(image=dummy_img, frame_id=i)
            times.append((time.perf_counter() - t0) * 1000.0)

        return {
            "mean_latency_ms": float(np.mean(times)),
            "p95_latency_ms": float(np.percentile(times, 95)),
            "min_latency_ms": float(np.min(times)),
            "max_latency_ms": float(np.max(times)),
            "fps_equivalent": float(1000.0 / np.mean(times)) if np.mean(times) > 0 else 0.0,
        }
