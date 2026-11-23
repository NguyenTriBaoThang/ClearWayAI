"""Automated test suite for Task 30: YOLO Fine-Tuning & Vietnamese Traffic Perception.

Validates:
1. YOLOInferenceEngine dual-mode inference and graceful fallback.
2. IoU calculation and Non-Maximum Suppression (NMS) algorithms.
3. mAP@0.5 and mAP@0.5:0.95 evaluation metric accuracy.
4. Latency performance benchmarks (<= 25 ms / frame target).
5. Weights manifest schema integrity and SHA-256 digests.
6. Training pipeline plan generator and dry-run CLI execution.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from ai.detection.metrics import (
    compute_ap,
    evaluate_detections,
    evaluate_map_range,
)
from ai.detection.train_yolo import (
    Hyperparameters,
    generate_training_plan,
    validate_dataset_yaml,
)
from ai.detection.yolo_detector import (
    CLASS_NAMES,
    Detection,
    DetectionResult,
    YOLOInferenceEngine,
    apply_nms,
    compute_iou,
)


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def data_root(repo_root: Path) -> Path:
    return repo_root / "data"


# =========================================================================
# 1. INFERENCE ENGINE & FALLBACK TESTS
# =========================================================================


def test_inference_engine_initialization() -> None:
    """Verify inference engine initializes in mock fallback mode when no weights exist."""
    engine = YOLOInferenceEngine()
    assert engine.is_real_model_loaded is False
    assert engine.conf_threshold == 0.25
    assert engine.iou_threshold == 0.45


def test_inference_synthetic_mixed_traffic() -> None:
    """Verify synthetic prediction returns realistic Vietnamese mixed traffic."""
    engine = YOLOInferenceEngine()
    dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)

    result = engine.predict(image=dummy_img, frame_id=42, timestamp_sec=1.4)

    assert isinstance(result, DetectionResult)
    assert result.frame_id == 42
    assert result.timestamp_sec == 1.4
    assert result.provenance == "HEURISTIC_MOCK"
    assert result.total_count >= 10  # Vietnamese high density

    # Must contain motorcycles and emergency ambulance
    class_counts = result.count_by_class()
    assert class_counts["motorcycle"] >= 5
    assert class_counts["ambulance"] >= 1
    assert "car" in class_counts


def test_inference_from_label_file(data_root: Path) -> None:
    """Verify inference parses real ground truth label files correctly."""
    engine = YOLOInferenceEngine()
    label_path = data_root / "processed" / "yolo" / "labels" / "train" / "hcmc_d1_0001.txt"
    assert label_path.is_file(), f"Missing test label {label_path}"

    result = engine.predict(ground_truth_label=label_path, frame_id="hcmc_d1_0001")
    assert result.provenance == "OFFLINE_VIDEO"
    assert result.total_count == 10

    # Assert valid box coordinates and class names
    for det in result.detections:
        assert 0 <= det.class_id < len(CLASS_NAMES)
        assert det.class_name == CLASS_NAMES[det.class_id]
        assert 0.0 <= det.x_min <= det.x_max <= 1.0
        assert 0.0 <= det.y_min <= det.y_max <= 1.0
        assert det.confidence >= 0.25


def test_batch_inference(data_root: Path) -> None:
    """Verify batch prediction processes multiple frames sequentially."""
    engine = YOLOInferenceEngine()
    labels = [
        data_root / "processed" / "yolo" / "labels" / "train" / "hcmc_d1_0001.txt",
        data_root / "processed" / "yolo" / "labels" / "train" / "hcmc_d1_0002.txt",
    ]
    batch_results = engine.predict_batch(labels)
    assert len(batch_results) == 2
    assert batch_results[0].frame_id == 1
    assert batch_results[1].frame_id == 2


# =========================================================================
# 2. IOU & NMS ALGORITHM TESTS
# =========================================================================


def test_compute_iou_identical_boxes() -> None:
    """IoU between identical boxes must be exactly 1.0."""
    box = (0.2, 0.2, 0.6, 0.6)
    assert pytest.approx(compute_iou(box, box), rel=1e-5) == 1.0


def test_compute_iou_disjoint_boxes() -> None:
    """IoU between non-overlapping boxes must be 0.0."""
    box_a = (0.0, 0.0, 0.2, 0.2)
    box_b = (0.3, 0.3, 0.5, 0.5)
    assert compute_iou(box_a, box_b) == 0.0


def test_compute_iou_partial_overlap() -> None:
    """IoU calculation for known 50% overlap case."""
    # Box A: [0, 0, 10, 10] -> area 100
    # Box B: [5, 0, 15, 10] -> area 100
    # Intersection: [5, 0, 10, 10] -> area 50
    # Union: 100 + 100 - 50 = 150
    # IoU: 50 / 150 = 1/3 ~ 0.3333
    box_a = (0.0, 0.0, 10.0, 10.0)
    box_b = (5.0, 0.0, 15.0, 10.0)
    expected_iou = 50.0 / 150.0
    assert pytest.approx(compute_iou(box_a, box_b), rel=1e-4) == expected_iou


def test_nms_suppression_same_class() -> None:
    """NMS must suppress lower-confidence duplicate boxes of the same class."""
    dets = [
        Detection(
            bbox=(0.10, 0.10, 0.30, 0.30), confidence=0.92, class_id=0, class_name="motorcycle"
        ),
        Detection(
            bbox=(0.11, 0.10, 0.31, 0.30), confidence=0.75, class_id=0, class_name="motorcycle"
        ),
    ]
    kept = apply_nms(dets, iou_threshold=0.45)
    assert len(kept) == 1
    assert kept[0].confidence == 0.92


def test_nms_preserves_different_classes() -> None:
    """Class-aware NMS must retain overlapping boxes of different classes."""
    dets = [
        Detection(
            bbox=(0.10, 0.10, 0.30, 0.30), confidence=0.92, class_id=0, class_name="motorcycle"
        ),
        Detection(bbox=(0.11, 0.10, 0.31, 0.30), confidence=0.88, class_id=1, class_name="car"),
    ]
    kept = apply_nms(dets, iou_threshold=0.45, class_agnostic=False)
    assert len(kept) == 2


# =========================================================================
# 3. MAP EVALUATION METRIC TESTS
# =========================================================================


def test_compute_ap_perfect_score() -> None:
    """AP for constant 100% precision across all recalls must be 1.0."""
    recalls = [0.0, 0.5, 1.0]
    precisions = [1.0, 1.0, 1.0]
    assert compute_ap(recalls, precisions) == 1.0


def test_compute_ap_zero_score() -> None:
    """AP for empty or zero precision must be 0.0."""
    assert compute_ap([], []) == 0.0
    assert compute_ap([0.0, 1.0], [0.0, 0.0]) == 0.0


def test_evaluate_detections_perfect_match() -> None:
    """evaluate_detections must yield mAP=1.0 for perfect predictions."""
    gt = [
        [
            Detection(
                bbox=(0.1, 0.1, 0.3, 0.3), confidence=1.0, class_id=0, class_name="motorcycle"
            ),
            Detection(bbox=(0.5, 0.5, 0.8, 0.8), confidence=1.0, class_id=1, class_name="car"),
        ]
    ]
    pred = [
        [
            Detection(
                bbox=(0.1, 0.1, 0.3, 0.3), confidence=0.95, class_id=0, class_name="motorcycle"
            ),
            Detection(bbox=(0.5, 0.5, 0.8, 0.8), confidence=0.90, class_id=1, class_name="car"),
        ]
    ]

    metrics = evaluate_detections(gt, pred, iou_threshold=0.5)
    assert metrics["map_50"] == 1.0
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["total_tp"] == 2
    assert metrics["total_fp"] == 0


def test_evaluate_map_range() -> None:
    """evaluate_map_range should calculate average across thresholds [0.50:0.95]."""
    gt = [
        [Detection(bbox=(0.1, 0.1, 0.3, 0.3), confidence=1.0, class_id=0, class_name="motorcycle")]
    ]
    pred = [
        [Detection(bbox=(0.1, 0.1, 0.3, 0.3), confidence=0.95, class_id=0, class_name="motorcycle")]
    ]
    map_range = evaluate_map_range(gt, pred)
    assert map_range == 1.0


# =========================================================================
# 4. LATENCY PERFORMANCE BENCHMARK
# =========================================================================


def test_inference_latency_benchmark() -> None:
    """Inference latency on synthetic/mock engine must be <= 25.0 ms (real-time >= 40 FPS)."""
    engine = YOLOInferenceEngine()
    perf = engine.benchmark_latency(num_runs=15)

    assert perf["mean_latency_ms"] <= 25.0
    assert perf["fps_equivalent"] >= 40.0
    assert perf["p95_latency_ms"] < 35.0


# =========================================================================
# 5. WEIGHTS MANIFEST INTEGRITY TESTS
# =========================================================================


def test_weights_manifest_schema_and_performance(repo_root: Path) -> None:
    """Verify models/weights_manifest.json conforms to engineering specifications."""
    manifest_path = repo_root / "models" / "weights_manifest.json"
    assert manifest_path.is_file(), f"Missing {manifest_path}"

    with open(manifest_path, encoding="utf-8") as f:
        data = json.load(f)

    # Required metadata
    assert data["num_classes"] == 7
    assert data["classes"] == CLASS_NAMES
    assert data["provenance"] == "OFFLINE_VIDEO_FINE_TUNED"

    # Performance benchmarks
    metrics = data["metrics"]
    assert metrics["map_50"] >= 0.85, f"Expected mAP@0.5 >= 0.85, got {metrics['map_50']}"
    assert metrics["map_50_95"] >= 0.60, (
        f"Expected mAP@0.5:0.95 >= 0.60, got {metrics['map_50_95']}"
    )
    assert metrics["latency_ms_edge"] <= 25.0, (
        f"Edge latency exceeds 25 ms: {metrics['latency_ms_edge']}"
    )
    assert metrics["fps_edge"] >= 40.0

    # Cryptographic integrity
    artifacts = data["artifacts"]
    for format_key in ["pytorch", "onnx"]:
        art = artifacts[format_key]
        sha = art["sha256"]
        assert len(sha) == 64, f"Invalid SHA-256 length for {format_key}"
        assert all(c in "0123456789abcdefABCDEF" for c in sha)
        assert art["size_bytes"] > 0


# =========================================================================
# 6. TRAINING PIPELINE TESTS
# =========================================================================


def test_validate_dataset_yaml_helper(data_root: Path) -> None:
    """Verify training pipeline accurately validates dataset.yaml."""
    yaml_path = data_root / "processed" / "yolo" / "dataset.yaml"
    valid, cfg, errors = validate_dataset_yaml(yaml_path)
    assert valid is True
    assert cfg["nc"] == 7
    assert len(errors) == 0


def test_generate_training_plan_helper(tmp_path: Path, data_root: Path) -> None:
    """Test generating training configuration plan."""
    yaml_path = data_root / "processed" / "yolo" / "dataset.yaml"
    hparams = Hyperparameters(epochs=50, batch_size=8)
    out_plan = tmp_path / "plan.json"

    plan = generate_training_plan(yaml_path, hparams, out_plan)
    assert plan["hyperparameters"]["epochs"] == 50
    assert plan["hyperparameters"]["batch_size"] == 8
    assert out_plan.is_file()


def test_cli_train_yolo_dry_run(data_root: Path) -> None:
    """Test train_yolo.py CLI execution in dry-run mode."""
    yaml_path = data_root / "processed" / "yolo" / "dataset.yaml"
    res = subprocess.run(
        [
            sys.executable,
            "ai/detection/train_yolo.py",
            "--dataset-yaml",
            str(yaml_path),
            "--dry-run",
            "--epochs",
            "10",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "DRY RUN SUCCESS" in res.stdout
