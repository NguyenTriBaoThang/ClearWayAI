"""Automated test suite for Task 34: Baseline Tabular Clearance Prediction Models.

Validates:
1. Training and evaluation of Linear Regression, Random Forest, and Gradient Boosting.
2. Prediction accuracy on unseen test set (MAE <= 3.5s, RMSE <= 5.0s, R2 >= 0.85).
3. Real-time inference latency (<= 5.0 ms per prediction).
4. Model serialization and deserialization via joblib.
5. End-to-end integration between ApproachTrafficState and ClearancePredictor.
6. CLI training execution and tabular benchmark reporting.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from ai.clearance.tabular_models import (
    ClearancePredictor,
    TabularModelTrainer,
)
from ai.state.traffic_state_estimator import ApproachTrafficState


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def dataset_df(repo_root: Path) -> pd.DataFrame:
    csv_path = repo_root / "data" / "processed" / "clearance" / "clearance_ground_truth.csv"
    assert csv_path.is_file(), f"Missing ground truth dataset: {csv_path}"
    return pd.read_csv(csv_path)


@pytest.fixture
def models_dir(repo_root: Path) -> Path:
    return repo_root / "models" / "clearance"


# =========================================================================
# 1. MODEL TRAINING & ACCURACY TARGET TESTS
# =========================================================================


def test_train_all_tabular_models(dataset_df: pd.DataFrame) -> None:
    """Train all 3 tabular models and assert performance meets engineering targets."""
    trainer = TabularModelTrainer()
    results = trainer.train_and_evaluate(dataset_df)

    assert len(results) == 3
    assert "linear_regression" in results
    assert "random_forest" in results
    assert "gradient_boosting" in results

    # Gradient Boosting / Random Forest benchmarks on unseen Test Node (Node D)
    gb_res = results["gradient_boosting"]
    assert gb_res.test_mae <= 3.5, f"Gradient Boosting MAE exceeds 3.5s: {gb_res.test_mae}"
    assert gb_res.test_rmse <= 5.0, f"Gradient Boosting RMSE exceeds 5.0s: {gb_res.test_rmse}"
    assert gb_res.test_r2 >= 0.85, f"Gradient Boosting R2 below 0.85: {gb_res.test_r2}"
    assert gb_res.latency_ms <= 5.0, f"Inference latency exceeds 5ms: {gb_res.latency_ms}"

    rf_res = results["random_forest"]
    assert rf_res.test_mae <= 3.5
    assert rf_res.test_r2 >= 0.85

    # Non-linear ensemble models must outperform linear regression
    lin_res = results["linear_regression"]
    assert gb_res.test_mae < lin_res.test_mae


# =========================================================================
# 2. MODEL PERSISTENCE & INFERENCE TESTS
# =========================================================================


def test_model_persistence_and_loading(tmp_path: Path, dataset_df: pd.DataFrame) -> None:
    """Test saving models and loading via ClearancePredictor."""
    trainer = TabularModelTrainer()
    trainer.train_and_evaluate(dataset_df, models_dir=tmp_path)

    expected_files = [
        "linear_regression.joblib",
        "random_forest.joblib",
        "gradient_boosting.joblib",
        "tabular_benchmark_report.json",
    ]
    for filename in expected_files:
        assert (tmp_path / filename).is_file(), f"Missing output artifact {filename}"

    # Load predictor
    predictor = ClearancePredictor.load(tmp_path / "gradient_boosting.joblib")
    assert predictor.model_name == "gradient_boosting"

    # Predict test sample
    sample = {
        "scenario_id": "normal",
        "node_id": "node_b",
        "approach_id": "EB",
        "queue_length_m": 35.0,
        "queued_vehicle_count": 14,
        "motorcycle_ratio": 0.78,
        "heavy_vehicle_count": 1,
        "approach_occupancy": 0.40,
        "downstream_occupancy": 0.25,
        "weather": "clear",
        "hour_of_day": 8,
    }
    pred_time = predictor.predict_features_dict(sample)
    assert 5.0 <= pred_time <= 25.0


def test_clearance_predictor_from_traffic_state(tmp_path: Path, dataset_df: pd.DataFrame) -> None:
    """Test inference directly from ApproachTrafficState perception dataclass."""
    trainer = TabularModelTrainer()
    trainer.train_and_evaluate(dataset_df, models_dir=tmp_path)
    predictor = ClearancePredictor.load(tmp_path / "gradient_boosting.joblib")

    state = ApproachTrafficState(
        approach_id="EB",
        timestamp_sec=12.0,
        vehicle_count=16,
        counts_by_class={"motorcycle": 12, "car": 3, "bus": 1},
        motorcycle_ratio=0.75,
        queue_length_meters=42.0,
        queued_vehicle_count=14,
        approach_occupancy_ratio=0.45,
        traffic_density_vpm=5.25,
        mean_speed_kmh=4.0,
    )

    pred = predictor.predict_from_traffic_state(state, scenario_id="peak", weather="clear")
    assert pred > 5.0

    # Test empty queue: should predict minimal clearance time
    empty_state = ApproachTrafficState(
        approach_id="EB",
        timestamp_sec=12.0,
        vehicle_count=0,
        counts_by_class={},
        motorcycle_ratio=0.0,
        queue_length_meters=0.0,
        queued_vehicle_count=0,
        approach_occupancy_ratio=0.0,
        traffic_density_vpm=0.0,
        mean_speed_kmh=0.0,
    )
    empty_pred = predictor.predict_from_traffic_state(empty_state, scenario_id="free_flow")
    assert empty_pred <= 3.5


# =========================================================================
# 3. OFFICIAL ARTIFACTS & REPORT INTEGRITY TESTS
# =========================================================================


def test_official_models_and_report_exist(models_dir: Path) -> None:
    """Verify official models and tabular_benchmark_report.json exist in models/clearance/."""
    report_file = models_dir / "tabular_benchmark_report.json"
    assert report_file.is_file(), f"Missing benchmark report: {report_file}"

    with open(report_file, encoding="utf-8") as f:
        report = json.load(f)

    assert "models" in report
    assert "gradient_boosting" in report["models"]
    gb_metrics = report["models"]["gradient_boosting"]
    assert gb_metrics["test_r2"] >= 0.85
    assert gb_metrics["test_mae"] <= 3.5

    # Check joblib model files exist
    assert (models_dir / "gradient_boosting.joblib").is_file()
    assert (models_dir / "random_forest.joblib").is_file()
    assert (models_dir / "linear_regression.joblib").is_file()


# =========================================================================
# 4. CLI EXECUTION TESTS
# =========================================================================


def test_cli_train_tabular_execution(dataset_df: pd.DataFrame, tmp_path: Path) -> None:
    """Test CLI runner execution and console output."""
    csv_path = tmp_path / "data.csv"
    dataset_df.to_csv(csv_path, index=False)
    out_dir = tmp_path / "models"

    res = subprocess.run(
        [
            sys.executable,
            "ai/clearance/train_tabular.py",
            "--data-path",
            str(csv_path),
            "--models-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "SUCCESS" in res.stdout
    assert "Clearance-Time Tabular Models Benchmark" in res.stdout
