"""Automated test suite for Task 29: Annotation Guide & Zero-Leakage Dataset Splitting.

Validates:
1. Annotation guidelines, 7-class taxonomy, and boundary rules.
2. YOLO dataset configuration (dataset.yaml).
3. Zero temporal and spatial data leakage (disjoint scenes, cameras, image hashes).
4. YOLO label syntax, coordinate normalization in [0, 1], and box integrity.
5. Dataset splitting utility and CLI commands.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from data.scripts.check_dataset_leakage import (
    EXPECTED_CLASSES,
    NUM_CLASSES,
    audit_dataset_integrity,
    check_disjoint_cameras,
    check_disjoint_scenes,
    check_image_hashes_disjoint,
    validate_yolo_labels,
)
from data.scripts.split_dataset import (
    export_splits_json,
    partition_scenes_disjoint,
)


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def data_root(repo_root: Path) -> Path:
    return repo_root / "data"


# =========================================================================
# 1. ANNOTATION GUIDE & TAXONOMY TESTS
# =========================================================================


def test_annotation_guide_exists_and_complete(repo_root: Path) -> None:
    """Verify docs/ANNOTATION_GUIDE.md exists and covers all required guidelines."""
    guide_path = repo_root / "docs" / "ANNOTATION_GUIDE.md"
    assert guide_path.is_file(), f"Missing {guide_path}"

    content = guide_path.read_text(encoding="utf-8")

    # Verify all 7 classes
    for cls_name in EXPECTED_CLASSES:
        assert cls_name in content, f"Annotation guide missing class: {cls_name}"

    # Verify Vietnamese traffic terms
    assert "xe máy" in content.lower() or "xe hai bánh" in content.lower()
    assert "cứu thương" in content.lower()
    assert "cứu hỏa" in content.lower()

    # Verify boundary and occlusion rules
    assert "20%" in content or "20\\%" in content
    assert "occlusion" in content.lower()
    assert "truncation" in content.lower()
    assert "rider" in content.lower()

    # Verify zero-leakage invariant
    assert "zero" in content.lower()
    assert "leakage" in content.lower()
    assert "scene" in content.lower()


# =========================================================================
# 2. YOLO DATASET YAML SPECIFICATION TESTS
# =========================================================================


def test_yolo_dataset_yaml_structure(data_root: Path) -> None:
    """Verify data/processed/yolo/dataset.yaml has valid YOLO format and 7 classes."""
    yaml_path = data_root / "processed" / "yolo" / "dataset.yaml"
    assert yaml_path.is_file(), f"Missing {yaml_path}"

    with open(yaml_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    assert cfg["nc"] == NUM_CLASSES
    assert isinstance(cfg["names"], (list, dict))

    if isinstance(cfg["names"], dict):
        for idx in range(NUM_CLASSES):
            assert idx in cfg["names"]
            assert cfg["names"][idx] == EXPECTED_CLASSES[idx]
    else:
        assert cfg["names"] == EXPECTED_CLASSES

    assert "train" in cfg
    assert "val" in cfg
    assert "test" in cfg


# =========================================================================
# 3. ZERO-LEAKAGE AUDIT TESTS
# =========================================================================


def test_splits_json_zero_leakage(data_root: Path) -> None:
    """Verify data/splits/splits.json is fully disjoint with zero spatial/temporal leakage."""
    splits_path = data_root / "splits" / "splits.json"
    assert splits_path.is_file(), f"Missing {splits_path}"

    with open(splits_path, encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("zero_leakage_verified") is True
    assert data.get("classes") == EXPECTED_CLASSES

    # Scene disjointness
    scene_errs = check_disjoint_scenes(data)
    assert len(scene_errs) == 0, f"Scene leakage: {scene_errs}"

    # Camera disjointness
    cam_errs = check_disjoint_cameras(data)
    assert len(cam_errs) == 0, f"Camera leakage: {cam_errs}"


def test_audit_dataset_integrity_end_to_end(data_root: Path) -> None:
    """Run full dataset audit asserting zero leakage, valid labels, and hashes."""
    splits_path = data_root / "splits" / "splits.json"
    passed, report = audit_dataset_integrity(splits_path)

    assert passed is True
    assert report["status"] == "PASS"
    assert report["leakage_free"] is True
    assert report["labels_valid"] is True
    assert report.get("total_bounding_boxes", 0) > 0


def test_leak_detector_flags_shared_scenes() -> None:
    """Verify that check_disjoint_scenes detects synthetic scene overlap."""
    bad_splits = {
        "splits": {
            "train": {"scene_ids": ["SCENE_A", "SCENE_B"]},
            "val": {"scene_ids": ["SCENE_B", "SCENE_C"]},
            "test": {"scene_ids": ["SCENE_D"]},
        }
    }
    errors = check_disjoint_scenes(bad_splits)
    assert len(errors) == 1
    assert "SCENE_B" in errors[0]


def test_leak_detector_flags_shared_cameras() -> None:
    """Verify that check_disjoint_cameras detects camera overlap between splits."""
    bad_splits = {
        "splits": {
            "train": {"camera_ids": ["CAM_01"]},
            "val": {"camera_ids": ["CAM_02"]},
            "test": {"camera_ids": ["CAM_01"]},
        }
    }
    errors = check_disjoint_cameras(bad_splits)
    assert len(errors) == 1
    assert "CAM_01" in errors[0]


def test_image_hash_disjointness(data_root: Path) -> None:
    """Verify all images across train, val, and test have unique SHA-256 hashes."""
    yolo_dir = data_root / "processed" / "yolo"
    ok, errors = check_image_hashes_disjoint(yolo_dir)
    assert ok is True
    assert len(errors) == 0


# =========================================================================
# 4. YOLO LABEL FORMAT & INTEGRITY TESTS
# =========================================================================


def test_yolo_labels_validity_real_data(data_root: Path) -> None:
    """Assert all repository YOLO label files comply with normalized box specifications."""
    labels_dir = data_root / "processed" / "yolo" / "labels"
    n_lbls, n_boxes, errors = validate_yolo_labels(labels_dir)

    assert n_lbls >= 9
    assert n_boxes >= 50
    assert len(errors) == 0, f"Label validation errors: {errors}"


def test_validate_yolo_labels_flags_malformed(tmp_path: Path) -> None:
    """Verify validator flags invalid tokens, out-of-range class IDs, and negative boxes."""
    labels_dir = tmp_path / "labels"
    train_dir = labels_dir / "train"
    train_dir.mkdir(parents=True)

    # Malformed file
    bad_file = train_dir / "bad.txt"
    bad_file.write_text(
        "7 0.5 0.5 0.2 0.2\n"  # class 7 out of bounds [0, 6]
        "0 0.5 0.5 -0.1 0.2\n"  # negative width
        "0 1.5 0.5 0.2 0.2\n"  # xc > 1.0
        "0 0.5 0.5\n",  # incomplete line (3 tokens)
        encoding="utf-8",
    )

    n_lbls, n_boxes, errors = validate_yolo_labels(labels_dir)
    assert n_lbls == 1
    assert n_boxes == 4
    assert len(errors) >= 4


# =========================================================================
# 5. DATASET SPLITTER UTILITY TESTS
# =========================================================================


def test_partition_scenes_disjoint() -> None:
    """Test scene partitioner produces non-overlapping splits."""
    scenes = [
        {
            "scene_id": f"SCENE_{i:02d}",
            "camera_id": f"CAM_{i:02d}",
            "samples": [f"img_{i}_{j}" for j in range(5)],
        }
        for i in range(10)
    ]

    splits = partition_scenes_disjoint(
        scenes, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15, seed=42
    )

    train_ids = set(splits["train"]["scene_ids"])
    val_ids = set(splits["val"]["scene_ids"])
    test_ids = set(splits["test"]["scene_ids"])

    assert len(train_ids) > 0
    assert len(val_ids) > 0
    assert len(test_ids) > 0

    assert train_ids.isdisjoint(val_ids)
    assert train_ids.isdisjoint(test_ids)
    assert val_ids.isdisjoint(test_ids)

    # All scenes allocated
    assert train_ids | val_ids | test_ids == {s["scene_id"] for s in scenes}


def test_partition_scenes_invalid_ratios() -> None:
    """Test partitioner raises ValueError on ratios not summing to 1.0."""
    scenes = [{"scene_id": "SCENE_01", "camera_id": "CAM_01"}]
    with pytest.raises(ValueError, match="Ratios must sum to 1.0"):
        partition_scenes_disjoint(scenes, train_ratio=0.5, val_ratio=0.2, test_ratio=0.1)


def test_export_splits_json(tmp_path: Path) -> None:
    """Test exporting splits to JSON file."""
    splits = {
        "train": {"scene_ids": ["S1"], "samples": ["img1"]},
        "val": {"scene_ids": ["S2"], "samples": ["img2"]},
        "test": {"scene_ids": ["S3"], "samples": ["img3"]},
    }
    out_file = tmp_path / "splits_test.json"
    export_splits_json(splits, out_file)

    assert out_file.is_file()
    with open(out_file, encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["partition_strategy"] == "scene_and_camera_disjoint"
    assert loaded["splits"]["train"]["scene_ids"] == ["S1"]


# =========================================================================
# 6. CLI TOOLS EXECUTION TESTS
# =========================================================================


def test_cli_check_dataset_leakage(data_root: Path) -> None:
    """Test CLI execution of check_dataset_leakage.py."""
    splits_json = data_root / "splits" / "splits.json"
    dataset_yaml = data_root / "processed" / "yolo" / "dataset.yaml"

    res = subprocess.run(
        [
            sys.executable,
            "data/scripts/check_dataset_leakage.py",
            "--splits-json",
            str(splits_json),
            "--dataset-yaml",
            str(dataset_yaml),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "SUCCESS" in res.stdout
    assert "Zero temporal/spatial leakage verified" in res.stdout


def test_cli_split_dataset(tmp_path: Path) -> None:
    """Test CLI execution of split_dataset.py."""
    out_json = tmp_path / "cli_splits.json"
    res = subprocess.run(
        [
            sys.executable,
            "data/scripts/split_dataset.py",
            "--output-splits",
            str(out_json),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert out_json.is_file()
