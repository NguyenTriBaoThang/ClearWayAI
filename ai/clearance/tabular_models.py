"""Tabular Machine Learning Models for Corridor Clearance-Time Prediction.

Trains and evaluates:
1. Linear Regression (Ridge L2-regularized baseline)
2. Random Forest Regressor
3. Gradient Boosting Regressor (XGBoost / LightGBM style boosting)

Enforces zero spatial/temporal leakage via node-based splitting.
"""

from __future__ import annotations

import contextlib
import importlib
import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from ai.clearance.features import ClearanceFeaturePipeline
from ai.state.traffic_state_estimator import ApproachTrafficState


def _ensure_unpickle_compat() -> None:
    """Register module aliases in sys.modules for cross-platform scikit-learn unpickling."""
    aliases = {
        "_loss": "sklearn._loss._loss",
        "_tree": "sklearn.tree._tree",
    }
    for alias, target in aliases.items():
        if alias not in sys.modules:
            with contextlib.suppress(ImportError, AttributeError):
                sys.modules[alias] = importlib.import_module(target)


@dataclass
class ModelBenchmarkResult:
    """Evaluation metrics for a trained clearance model."""

    model_name: str
    train_mae: float
    val_mae: float
    test_mae: float
    test_rmse: float
    test_r2: float
    latency_ms: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TabularModelTrainer:
    """Manages training, hyperparameter configuration, and evaluation of tabular models."""

    def __init__(self, pipeline: ClearanceFeaturePipeline | None = None) -> None:
        self.pipeline = pipeline or ClearanceFeaturePipeline()
        self.trained_models: dict[str, Any] = {}
        self.benchmark_results: dict[str, ModelBenchmarkResult] = {}
        self.best_model_name: str = "gradient_boosting"

    def train_and_evaluate(
        self,
        df: pd.DataFrame,
        models_dir: Path | str | None = None,
    ) -> dict[str, ModelBenchmarkResult]:
        """Train all 3 models on node-based split and evaluate generalization."""
        # Node-based zero-leakage split: Train (A, B), Val (C), Test (D)
        train_df, val_df, test_df = ClearanceFeaturePipeline.split_by_node(df)

        # Fit feature pipeline strictly on train set
        X_train, y_train, _ = self.pipeline.fit_transform(train_df)
        X_val, y_val, _ = self.pipeline.transform(val_df)
        X_test, y_test, _ = self.pipeline.transform(test_df)

        assert y_val is not None
        assert y_test is not None

        candidate_models = {
            "linear_regression": Ridge(alpha=1.0, random_state=42),
            "random_forest": RandomForestRegressor(
                n_estimators=100,
                max_depth=12,
                min_samples_split=4,
                random_state=42,
            ),
            "gradient_boosting": GradientBoostingRegressor(
                n_estimators=120,
                learning_rate=0.08,
                max_depth=5,
                subsample=0.85,
                random_state=42,
            ),
        }

        results: dict[str, ModelBenchmarkResult] = {}
        best_mae = float("inf")

        for name, model in candidate_models.items():
            # 1. Fit model
            model.fit(X_train, y_train)
            self.trained_models[name] = model

            # 2. Predict on splits
            pred_train = model.predict(X_train)
            pred_val = model.predict(X_val)
            pred_test = model.predict(X_test)

            # 3. Calculate metrics
            tr_mae = float(mean_absolute_error(y_train, pred_train))
            v_mae = float(mean_absolute_error(y_val, pred_val))
            te_mae = float(mean_absolute_error(y_test, pred_test))
            te_rmse = float(np.sqrt(mean_squared_error(y_test, pred_test)))
            te_r2 = float(r2_score(y_test, pred_test))

            # 4. Measure inference latency per single sample
            single_sample = X_test[:1]
            t0 = time.perf_counter()
            for _ in range(50):
                model.predict(single_sample)
            latency_ms = ((time.perf_counter() - t0) / 50.0) * 1000.0

            res = ModelBenchmarkResult(
                model_name=name,
                train_mae=round(tr_mae, 3),
                val_mae=round(v_mae, 3),
                test_mae=round(te_mae, 3),
                test_rmse=round(te_rmse, 3),
                test_r2=round(te_r2, 4),
                latency_ms=round(latency_ms, 3),
            )
            results[name] = res

            if v_mae < best_mae:
                best_mae = v_mae
                self.best_model_name = name

            # 5. Persist artifacts if directory specified
            if models_dir:
                m_dir = Path(models_dir)
                m_dir.mkdir(parents=True, exist_ok=True)
                model_path = m_dir / f"{name}.joblib"
                joblib.dump({"model": model, "pipeline": self.pipeline}, model_path)

        self.benchmark_results = results

        # Persist summary report
        if models_dir:
            m_dir = Path(models_dir)
            report_path = m_dir / "tabular_benchmark_report.json"
            report_data = {
                "best_model": self.best_model_name,
                "dataset_samples": len(df),
                "train_samples": len(train_df),
                "val_samples": len(val_df),
                "test_samples": len(test_df),
                "models": {k: v.to_dict() for k, v in results.items()},
            }
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2)

        return results


class ClearancePredictor:
    """Production inference wrapper predicting clearance duration."""

    def __init__(
        self,
        model: Any,
        pipeline: ClearanceFeaturePipeline,
        model_name: str = "gradient_boosting",
    ) -> None:
        self.model = model
        self.pipeline = pipeline
        self.model_name = model_name

    @classmethod
    def load(cls, model_path: Path | str) -> ClearancePredictor:
        """Load bundled model and feature pipeline from disk."""
        _ensure_unpickle_compat()
        data = joblib.load(model_path)
        p = Path(model_path)
        return cls(
            model=data["model"],
            pipeline=data["pipeline"],
            model_name=p.stem,
        )

    def predict_features_dict(self, features: dict[str, Any]) -> float:
        """Predict clearance time given raw feature dictionary."""
        df = pd.DataFrame([features])
        X, _, _ = self.pipeline.transform(df)
        pred = float(self.model.predict(X)[0])
        return max(0.0, round(pred, 2))

    def predict_from_traffic_state(
        self,
        state: ApproachTrafficState,
        scenario_id: str = "normal",
        node_id: str = "node_b",
        weather: str = "clear",
        downstream_occupancy: float = 0.25,
        hour_of_day: int = 8,
    ) -> float:
        """Predict clearance time directly from perception TrafficState."""
        feat = {
            "scenario_id": scenario_id,
            "node_id": node_id,
            "approach_id": state.approach_id,
            "queue_length_m": state.queue_length_meters,
            "queued_vehicle_count": state.queued_vehicle_count,
            "motorcycle_ratio": state.motorcycle_ratio,
            "heavy_vehicle_count": state.counts_by_class.get("bus", 0)
            + state.counts_by_class.get("truck", 0),
            "approach_occupancy": state.approach_occupancy_ratio,
            "downstream_occupancy": downstream_occupancy,
            "weather": weather,
            "hour_of_day": hour_of_day,
        }
        return self.predict_features_dict(feat)
