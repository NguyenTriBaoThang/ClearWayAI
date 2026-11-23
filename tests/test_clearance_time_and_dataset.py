"""Automated test suite for Task 33: Clearance Time Definition & Empirical Ground Truth Dataset.

Validates:
1. Clearance time mathematical specification and shockwave physics.
2. QueueDischargeSimulator: zero queue base case, monotonicity, heavy vehicle delay,
   weather discount factor, and downstream bottleneck back-pressure.
3. Quality and schema of data/processed/clearance/clearance_ground_truth.csv.
4. ClearanceFeaturePipeline: normalization, one-hot encoding, and zero-leakage node split.
5. CLI generator execution and metadata logging.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ai.clearance.dataset_generator import (
    QueueDischargeSimulator,
)
from ai.clearance.features import (
    NUMERICAL_FEATURES,
    TARGET_COLUMN,
    ClearanceFeaturePipeline,
)


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def clearance_dir(repo_root: Path) -> Path:
    return repo_root / "data" / "processed" / "clearance"


# =========================================================================
# 1. SPECIFICATION DOCUMENT COMPLIANCE TESTS
# =========================================================================


def test_clearance_spec_document_exists(repo_root: Path) -> None:
    """Verify docs/CLEARANCE_TIME_SPEC.md exists and covers physical principles."""
    spec_path = repo_root / "docs" / "CLEARANCE_TIME_SPEC.md"
    assert spec_path.is_file(), f"Missing spec: {spec_path}"

    content = spec_path.read_text(encoding="utf-8")
    assert "T_{\\text{clear}}" in content or "T_{clear}" in content or "Clearance Time" in content
    assert "shockwave" in content.lower() or "kinematic wave" in content.lower()
    assert "motorcycle" in content.lower()
    assert "heavy" in content.lower()
    assert "downstream" in content.lower()
    assert "leakage" in content.lower()


# =========================================================================
# 2. QUEUE DISCHARGE SIMULATOR PHYSICS TESTS
# =========================================================================


def test_queue_discharge_empty_queue() -> None:
    """Empty queue must have clearance time of exactly 0.0 seconds."""
    sim = QueueDischargeSimulator()
    t_clear = sim.compute_clearance_time(
        queue_length_m=0.0,
        queued_vehicle_count=0,
        motorcycle_ratio=0.75,
        heavy_vehicle_count=0,
        approach_occupancy=0.0,
        downstream_occupancy=0.1,
    )
    assert t_clear == 0.0


def test_queue_discharge_monotonicity() -> None:
    """Longer queues must strictly require longer clearance time."""
    sim = QueueDischargeSimulator()

    t_short = sim.compute_clearance_time(
        queue_length_m=20.0,
        queued_vehicle_count=8,
        motorcycle_ratio=0.75,
        heavy_vehicle_count=0,
        approach_occupancy=0.30,
        downstream_occupancy=0.20,
    )

    t_medium = sim.compute_clearance_time(
        queue_length_m=50.0,
        queued_vehicle_count=20,
        motorcycle_ratio=0.75,
        heavy_vehicle_count=0,
        approach_occupancy=0.55,
        downstream_occupancy=0.20,
    )

    t_long = sim.compute_clearance_time(
        queue_length_m=90.0,
        queued_vehicle_count=35,
        motorcycle_ratio=0.75,
        heavy_vehicle_count=0,
        approach_occupancy=0.80,
        downstream_occupancy=0.20,
    )

    assert 0.0 < t_short < t_medium < t_long


def test_queue_discharge_heavy_vehicle_impact() -> None:
    """Heavy vehicles (buses/trucks) must add significant lost time to clearance."""
    sim = QueueDischargeSimulator()

    t_no_heavy = sim.compute_clearance_time(
        queue_length_m=40.0,
        queued_vehicle_count=15,
        motorcycle_ratio=0.75,
        heavy_vehicle_count=0,
        approach_occupancy=0.45,
        downstream_occupancy=0.25,
    )

    t_with_heavy = sim.compute_clearance_time(
        queue_length_m=40.0,
        queued_vehicle_count=15,
        motorcycle_ratio=0.75,
        heavy_vehicle_count=3,
        approach_occupancy=0.45,
        downstream_occupancy=0.25,
    )

    assert t_with_heavy > t_no_heavy
    # At least ~2 seconds penalty per heavy vehicle
    assert t_with_heavy - t_no_heavy >= 4.0


def test_queue_discharge_weather_rain_penalty() -> None:
    """Rainy weather reduces discharge velocity, extending clearance time."""
    sim = QueueDischargeSimulator()

    t_clear = sim.compute_clearance_time(
        queue_length_m=50.0,
        queued_vehicle_count=20,
        motorcycle_ratio=0.75,
        heavy_vehicle_count=1,
        approach_occupancy=0.50,
        downstream_occupancy=0.20,
        weather="clear",
    )

    t_rain = sim.compute_clearance_time(
        queue_length_m=50.0,
        queued_vehicle_count=20,
        motorcycle_ratio=0.75,
        heavy_vehicle_count=1,
        approach_occupancy=0.50,
        downstream_occupancy=0.20,
        weather="rain",
    )

    assert t_rain > t_clear


def test_queue_discharge_downstream_bottleneck() -> None:
    """High downstream occupancy (>0.70) must induce spillback delay."""
    sim = QueueDischargeSimulator()

    t_free = sim.compute_clearance_time(
        queue_length_m=45.0,
        queued_vehicle_count=18,
        motorcycle_ratio=0.75,
        heavy_vehicle_count=1,
        approach_occupancy=0.50,
        downstream_occupancy=0.30,
    )

    t_bottleneck = sim.compute_clearance_time(
        queue_length_m=45.0,
        queued_vehicle_count=18,
        motorcycle_ratio=0.75,
        heavy_vehicle_count=1,
        approach_occupancy=0.50,
        downstream_occupancy=0.85,
    )

    assert t_bottleneck > t_free + 5.0


# =========================================================================
# 3. CSV DATASET INTEGRITY & SCHEMA TESTS
# =========================================================================


def test_clearance_csv_file_exists_and_valid(clearance_dir: Path) -> None:
    """Verify data/processed/clearance/clearance_ground_truth.csv exists and is well-formed."""
    csv_path = clearance_dir / "clearance_ground_truth.csv"
    assert csv_path.is_file(), f"Missing dataset file: {csv_path}"

    df = pd.read_csv(csv_path)
    assert len(df) >= 500

    expected_cols = (
        ["scenario_id", "node_id", "approach_id"]
        + NUMERICAL_FEATURES
        + ["weather", "provenance", TARGET_COLUMN]
    )
    for col in expected_cols:
        assert col in df.columns, f"Missing expected column: {col}"

    # Zero missing values
    assert df.isnull().sum().sum() == 0, "Dataset contains NaN or null values"

    # Numerical range bounds
    assert (df["queue_length_m"] >= 0.0).all()
    assert (df["queued_vehicle_count"] >= 0).all()
    assert ((df["motorcycle_ratio"] >= 0.0) & (df["motorcycle_ratio"] <= 1.0)).all()
    assert ((df["approach_occupancy"] >= 0.0) & (df["approach_occupancy"] <= 1.0)).all()
    assert ((df["downstream_occupancy"] >= 0.0) & (df["downstream_occupancy"] <= 1.0)).all()
    assert (df[TARGET_COLUMN] >= 0.0).all()

    # All 4 scenarios and nodes represented
    assert set(df["scenario_id"].unique()) == {"free_flow", "normal", "peak", "spillback"}
    assert set(df["node_id"].unique()) == {"node_a", "node_b", "node_c", "node_d"}


def test_clearance_metadata_json(clearance_dir: Path) -> None:
    """Verify data/processed/clearance/clearance_metadata.json exists and is valid."""
    meta_path = clearance_dir / "clearance_metadata.json"
    assert meta_path.is_file(), f"Missing metadata: {meta_path}"

    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["target_variable"] == TARGET_COLUMN
    assert meta["total_samples"] >= 500
    assert "mean_clearance_sec" in meta["target_summary"]
    assert meta["target_summary"]["min_clearance_sec"] >= 0.0


# =========================================================================
# 4. FEATURE PIPELINE & ZERO-LEAKAGE SPLIT TESTS
# =========================================================================


def test_clearance_feature_pipeline_fit_transform(clearance_dir: Path) -> None:
    """Test feature pipeline scaling, one-hot encoding, and feature dimensions."""
    csv_path = clearance_dir / "clearance_ground_truth.csv"
    df = pd.read_csv(csv_path)

    pipe = ClearanceFeaturePipeline()
    X, y, feat_names = pipe.fit_transform(df)

    assert isinstance(X, np.ndarray)
    assert isinstance(y, np.ndarray)
    assert len(X) == len(df)
    assert len(y) == len(df)
    assert X.shape[1] == len(feat_names)

    # Check scaled numerical features have approximately zero mean and unit variance
    num_cols_count = len(NUMERICAL_FEATURES)
    means = np.mean(X[:, :num_cols_count], axis=0)
    stds = np.std(X[:, :num_cols_count], axis=0)

    for m in means:
        assert pytest.approx(m, abs=0.1) == 0.0
    for s in stds:
        assert pytest.approx(s, abs=0.1) == 1.0


def test_clearance_feature_pipeline_split_by_node(clearance_dir: Path) -> None:
    """Verify split_by_node enforces complete spatial isolation across train/val/test."""
    csv_path = clearance_dir / "clearance_ground_truth.csv"
    df = pd.read_csv(csv_path)

    tr_df, val_df, te_df = ClearanceFeaturePipeline.split_by_node(df)

    assert len(tr_df) > 0
    assert len(val_df) > 0
    assert len(te_df) > 0

    tr_nodes = set(tr_df["node_id"].unique())
    val_nodes = set(val_df["node_id"].unique())
    te_nodes = set(te_df["node_id"].unique())

    # Assert mutual disjointness (Zero Data Leakage)
    assert tr_nodes.isdisjoint(val_nodes)
    assert tr_nodes.isdisjoint(te_nodes)
    assert val_nodes.isdisjoint(te_nodes)


# =========================================================================
# 5. CLI EXECUTION TESTS
# =========================================================================


def test_cli_dataset_generator(tmp_path: Path) -> None:
    """Test CLI execution of dataset_generator.py."""
    out_csv = tmp_path / "test_clearance.csv"
    out_meta = tmp_path / "test_meta.json"

    res = subprocess.run(
        [
            sys.executable,
            "ai/clearance/dataset_generator.py",
            "--samples",
            "50",
            "--output-csv",
            str(out_csv),
            "--output-meta",
            str(out_meta),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "SUCCESS" in res.stdout
    assert out_csv.is_file()
    assert out_meta.is_file()
