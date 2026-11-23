"""CLI runner for training tabular clearance prediction models."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import pandas as pd  # noqa: E402

from ai.clearance.tabular_models import TabularModelTrainer  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ClearWayAI Tabular Clearance Prediction Training & Benchmark"
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default="data/processed/clearance/clearance_ground_truth.csv",
        help="Path to clearance dataset CSV",
    )
    parser.add_argument(
        "--models-dir",
        type=str,
        default="models/clearance",
        help="Directory to save trained model artifacts",
    )
    args = parser.parse_args()

    data_path = Path(args.data_path)
    if not data_path.is_file():
        print(f"[ERROR] Dataset not found: {data_path}")
        return 1

    df = pd.read_csv(data_path)
    trainer = TabularModelTrainer()
    results = trainer.train_and_evaluate(df, models_dir=args.models_dir)

    print("=" * 80)
    print("ClearWayAI Clearance-Time Tabular Models Benchmark")
    print("=" * 80)
    print(
        f"{'Model':<22} | {'Train MAE':<10} | {'Val MAE':<9} | {'Test MAE':<9} | {'Test RMSE':<10} | {'Test R²':<8} | {'Latency':<8}"
    )
    print("-" * 80)

    for name, res in results.items():
        star = " ★" if name == trainer.best_model_name else ""
        print(
            f"{name + star:<22} | {res.train_mae:<10.3f} | {res.val_mae:<9.3f} | "
            f"{res.test_mae:<9.3f} | {res.test_rmse:<10.3f} | {res.test_r2:<8.4f} | {res.latency_ms:<5.3f} ms"
        )

    print("=" * 80)
    print(f"[SUCCESS] Best performing model: {trainer.best_model_name}")
    print(f"Artifacts saved to {args.models_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
