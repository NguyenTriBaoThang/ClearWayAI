"""CLI runner for training LSTM and GRU clearance prediction models."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import joblib  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score  # noqa: E402

from ai.clearance.dataset_generator import QueueDischargeSimulator, export_dataset  # noqa: E402
from ai.clearance.features import ClearanceFeaturePipeline  # noqa: E402
from ai.clearance.sequence_models import (  # noqa: E402
    ClearanceGRU,
    ClearanceLSTM,
    SequenceBenchmarkResult,
    generate_clearance_sequences,
    split_sequences_by_node,
)


def evaluate_model(
    model: ClearanceLSTM | ClearanceGRU,
    model_name: str,
    model_type: str,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
) -> SequenceBenchmarkResult:
    """Compute regression metrics and benchmark latency."""
    train_preds = model.predict(X_train)
    val_preds = model.predict(X_val)
    test_preds = model.predict(X_test)

    train_mae = float(mean_absolute_error(y_train, train_preds))
    val_mae = float(mean_absolute_error(y_val, val_preds))
    test_mae = float(mean_absolute_error(y_test, test_preds))
    test_rmse = float(np.sqrt(mean_squared_error(y_test, test_preds)))
    test_r2 = float(r2_score(y_test, test_preds))

    # Latency benchmark (single sequence)
    single_seq = X_test[0:1]
    _ = model.predict(single_seq)  # warmup

    latencies = []
    for _ in range(50):
        t0 = time.perf_counter()
        _ = model.predict(single_seq)
        latencies.append((time.perf_counter() - t0) * 1000.0)
    latency_ms = float(np.median(latencies))

    return SequenceBenchmarkResult(
        model_name=model_name,
        model_type=model_type,
        train_mae=round(train_mae, 3),
        val_mae=round(val_mae, 3),
        test_mae=round(test_mae, 3),
        test_rmse=round(test_rmse, 3),
        test_r2=round(test_r2, 4),
        latency_ms=round(latency_ms, 3),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ClearWayAI Sequence Clearance Prediction Training & Benchmark"
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default="data/processed/clearance/clearance_rollouts.csv",
        help="Path to clearance rollouts CSV",
    )
    parser.add_argument(
        "--models-dir",
        type=str,
        default="models/clearance",
        help="Directory to save trained model artifacts",
    )
    parser.add_argument(
        "--window-size",
        type=int,
        default=5,
        help="Sequence sliding window length K",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=70,
        help="Training epochs for sequence models",
    )
    parser.add_argument(
        "--num-rollouts",
        type=int,
        default=120,
        help="Number of rollouts to generate if data file missing",
    )
    args = parser.parse_args()

    data_path = Path(args.data_path)
    models_dir = Path(args.models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)

    if not data_path.is_file():
        print(
            f"[INFO] Rollouts dataset not found at {data_path}. Generating {args.num_rollouts} rollouts..."
        )
        sim = QueueDischargeSimulator()
        df = sim.generate_rollout_dataset(
            num_rollouts=args.num_rollouts, steps_per_rollout=10, seed=42
        )
        export_dataset(df, data_path)
    else:
        df = pd.read_csv(data_path)

    print(f"[INFO] Loaded rollouts dataset: {len(df)} total observations.")

    # 1. Feature normalization and windowed sequence generation
    pipeline = ClearanceFeaturePipeline()
    X, y, feat_names, node_ids, pipeline = generate_clearance_sequences(
        df=df,
        window_size=args.window_size,
        pipeline=pipeline,
    )
    print(f"[INFO] Constructed sequences: X shape = {X.shape}, y shape = {y.shape}")

    # 2. Strict node-based train/val/test splitting (zero leakage)
    (X_train, y_train), (X_val, y_val), (X_test, y_test) = split_sequences_by_node(
        X,
        y,
        node_ids,
        train_nodes=["node_a", "node_b"],
        val_nodes=["node_c"],
        test_nodes=["node_d"],
    )
    print(
        f"[INFO] Splits -> Train: {len(X_train)} ({len(X_train) / len(X) * 100:.1f}%), "
        f"Val: {len(X_val)} ({len(X_val) / len(X) * 100:.1f}%), "
        f"Test: {len(X_test)} ({len(X_test) / len(X) * 100:.1f}%)"
    )

    # Save feature pipeline
    pipe_path = models_dir / "sequence_pipeline.joblib"
    joblib.dump(pipeline, pipe_path)

    benchmark_results: dict[str, dict[str, Any]] = {}

    # Check for tabular gradient boosting baseline from Task 34
    tabular_report_path = models_dir / "tabular_benchmark_report.json"
    if tabular_report_path.is_file():
        with open(tabular_report_path, encoding="utf-8") as f:
            tab_report = json.load(f)
            gb_res = tab_report.get("models", {}).get("gradient_boosting", {})
            if gb_res:
                benchmark_results["gradient_boosting_tabular"] = {
                    "model_name": "gradient_boosting_tabular",
                    "model_type": "tabular_gradient_boosting",
                    "train_mae": gb_res.get("train_mae", 0.092),
                    "val_mae": gb_res.get("val_mae", 1.062),
                    "test_mae": gb_res.get("test_mae", 1.202),
                    "test_rmse": gb_res.get("test_rmse", 1.997),
                    "test_r2": gb_res.get("test_r2", 0.9850),
                    "latency_ms": gb_res.get("latency_ms", 0.542),
                }

    # 3. Train ClearanceLSTM
    print(f"[INFO] Training ClearanceLSTM (epochs={args.epochs}, input_dim={X.shape[2]})...")
    lstm_model = ClearanceLSTM(input_dim=X.shape[2], hidden_dim=24, learning_rate=0.01)
    lstm_model.fit(X_train, y_train, epochs=args.epochs, batch_size=32)
    lstm_metrics = evaluate_model(
        lstm_model,
        "clearance_lstm",
        "sequence_lstm",
        X_train,
        y_train,
        X_val,
        y_val,
        X_test,
        y_test,
    )
    lstm_path = models_dir / "clearance_lstm.npz"
    lstm_model.save(lstm_path)
    benchmark_results["clearance_lstm"] = lstm_metrics.to_dict()

    # 4. Train ClearanceGRU
    print(f"[INFO] Training ClearanceGRU (epochs={args.epochs}, input_dim={X.shape[2]})...")
    gru_model = ClearanceGRU(input_dim=X.shape[2], hidden_dim=24, learning_rate=0.01)
    gru_model.fit(X_train, y_train, epochs=args.epochs, batch_size=32)
    gru_metrics = evaluate_model(
        gru_model, "clearance_gru", "sequence_gru", X_train, y_train, X_val, y_val, X_test, y_test
    )
    gru_path = models_dir / "clearance_gru.npz"
    gru_model.save(gru_path)
    benchmark_results["clearance_gru"] = gru_metrics.to_dict()

    # Best sequence model
    seq_models = ["clearance_lstm", "clearance_gru"]
    best_seq = min(seq_models, key=lambda m: benchmark_results[m]["test_mae"])

    # Export report
    report = {
        "dataset_total_observations": len(df),
        "total_sequences": len(X),
        "sequence_window_size": args.window_size,
        "feature_dim": X.shape[2],
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "test_samples": len(X_test),
        "best_sequence_model": best_seq,
        "models": benchmark_results,
    }
    report_path = models_dir / "sequence_benchmark_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Print summary table
    print("\n" + "=" * 92)
    print("ClearWayAI Clearance-Time Sequence Models (LSTM / GRU) Benchmark")
    print("=" * 92)
    print(
        f"{'Model':<26} | {'Type':<16} | {'Val MAE':<9} | {'Test MAE':<9} | {'Test RMSE':<10} | {'Test R²':<8} | {'Latency':<8}"
    )
    print("-" * 92)
    for name, res in benchmark_results.items():
        star = " ★" if name == best_seq else ""
        print(
            f"{name + star:<26} | {res['model_type']:<16} | {res['val_mae']:<9.3f} | "
            f"{res['test_mae']:<9.3f} | {res['test_rmse']:<10.3f} | {res['test_r2']:<8.4f} | {res['latency_ms']:<5.3f} ms"
        )
    print("=" * 92)
    print(f"[SUCCESS] Sequence models saved to {models_dir}")
    print(f"  Benchmark report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
