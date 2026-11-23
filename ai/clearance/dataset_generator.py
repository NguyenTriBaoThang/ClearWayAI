"""ClearWayAI Queue Discharge Simulator and Clearance Ground Truth Generator.

Implements the kinematic wave & shockwave discharge physics defined in
docs/CLEARANCE_TIME_SPEC.md for Vietnamese mixed traffic queues.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

WEATHER_FACTORS = {
    "clear": 1.00,
    "overcast": 0.95,
    "rain": 0.82,  # Wet asphalt reduces discharge speed
    "haze": 0.90,
}

SCENARIOS = ["free_flow", "normal", "peak", "spillback"]
NODES = ["node_a", "node_b", "node_c", "node_d"]
APPROACHES = ["EB", "WB", "NB", "SB"]


@dataclass
class QueueDischargeConfig:
    """Physics parameters for Vietnamese urban mixed-traffic discharge."""

    base_startup_lost_time_sec: float = 2.0
    heavy_vehicle_penalty_sec: float = 2.2
    motorcycle_startup_bonus_sec: float = 1.2
    base_discharge_speed_mps: float = 4.5  # ~16.2 km/h
    noise_std_sec: float = 0.50


class QueueDischargeSimulator:
    """Simulates clearance duration from standing queues to clear corridor."""

    def __init__(self, config: QueueDischargeConfig | None = None) -> None:
        self.cfg = config or QueueDischargeConfig()

    def compute_clearance_time(
        self,
        queue_length_m: float,
        queued_vehicle_count: int,
        motorcycle_ratio: float,
        heavy_vehicle_count: int,
        approach_occupancy: float,
        downstream_occupancy: float,
        weather: str = "clear",
        rng: np.random.Generator | None = None,
    ) -> float:
        """Compute empirical clearance time T_clear according to physical shockwave formulation.

        T_clear = t_startup + Q_len / (v_discharge * eta_weather) + Delta_downstream
        """
        if queue_length_m <= 0.0 or queued_vehicle_count <= 0:
            return 0.0

        # 1. Startup lost time
        t_startup = (
            self.cfg.base_startup_lost_time_sec
            + (self.cfg.heavy_vehicle_penalty_sec * heavy_vehicle_count)
            - (self.cfg.motorcycle_startup_bonus_sec * motorcycle_ratio)
        )
        t_startup = max(0.8, t_startup)

        # 2. Wave discharge duration
        weather_factor = WEATHER_FACTORS.get(weather.lower(), 1.0)
        eff_speed = self.cfg.base_discharge_speed_mps * weather_factor
        t_discharge = queue_length_m / max(0.5, eff_speed)

        # 3. Downstream bottleneck / spillback delay penalty
        downstream_delay = 0.0
        if downstream_occupancy > 0.70:
            excess = downstream_occupancy - 0.70
            denom = max(0.05, 1.0 - downstream_occupancy)
            downstream_delay = (excess / denom) * 12.0

        # 4. Dense approach congestion compression factor
        congestion_drag = 1.0 + (0.15 * max(0.0, approach_occupancy - 0.60))

        raw_time = (t_startup + t_discharge * congestion_drag) + downstream_delay

        # Stochastic noise
        if rng is not None:
            noise = rng.normal(0.0, self.cfg.noise_std_sec)
            raw_time += noise

        return round(float(max(1.0, raw_time)), 2)

    def generate_episode(
        self,
        scenario_id: str,
        node_id: str,
        approach_id: str,
        rng: np.random.Generator,
    ) -> dict[str, Any]:
        """Generate a single traffic state and ground-truth clearance time pair."""
        # Scale parameters according to scenario profile
        if scenario_id == "free_flow":
            q_len = rng.uniform(0.0, 15.0)
            veh_count = int(rng.integers(0, 8)) if q_len > 0 else 0
            moto_ratio = float(rng.uniform(0.65, 0.85))
            heavy_count = int(rng.choice([0, 1], p=[0.9, 0.1]))
            app_occ = float(rng.uniform(0.05, 0.25))
            down_occ = float(rng.uniform(0.05, 0.20))
            hour = int(rng.choice([1, 2, 3, 4, 11, 14, 22, 23]))
        elif scenario_id == "normal":
            q_len = rng.uniform(15.0, 45.0)
            veh_count = int(rng.integers(6, 22))
            moto_ratio = float(rng.uniform(0.70, 0.85))
            heavy_count = int(rng.choice([0, 1, 2], p=[0.6, 0.3, 0.1]))
            app_occ = float(rng.uniform(0.25, 0.55))
            down_occ = float(rng.uniform(0.20, 0.45))
            hour = int(rng.choice([9, 10, 13, 15, 16, 20]))
        elif scenario_id == "peak":
            q_len = rng.uniform(40.0, 85.0)
            veh_count = int(rng.integers(18, 42))
            moto_ratio = float(rng.uniform(0.75, 0.90))
            heavy_count = int(rng.choice([1, 2, 3, 4], p=[0.3, 0.4, 0.2, 0.1]))
            app_occ = float(rng.uniform(0.50, 0.80))
            down_occ = float(rng.uniform(0.40, 0.70))
            hour = int(rng.choice([7, 8, 17, 18, 19]))
        else:  # spillback
            q_len = rng.uniform(70.0, 120.0)
            veh_count = int(rng.integers(30, 58))
            moto_ratio = float(rng.uniform(0.68, 0.88))
            heavy_count = int(rng.choice([2, 3, 4, 5], p=[0.2, 0.4, 0.3, 0.1]))
            app_occ = float(rng.uniform(0.75, 0.95))
            down_occ = float(rng.uniform(0.72, 0.92))
            hour = int(rng.choice([8, 18]))

        weather = str(rng.choice(["clear", "overcast", "rain", "haze"], p=[0.55, 0.20, 0.15, 0.10]))

        clearance_time = self.compute_clearance_time(
            queue_length_m=q_len,
            queued_vehicle_count=veh_count,
            motorcycle_ratio=moto_ratio,
            heavy_vehicle_count=heavy_count,
            approach_occupancy=app_occ,
            downstream_occupancy=down_occ,
            weather=weather,
            rng=rng,
        )

        return {
            "scenario_id": scenario_id,
            "node_id": node_id,
            "approach_id": approach_id,
            "queue_length_m": round(q_len, 2),
            "queued_vehicle_count": veh_count,
            "motorcycle_ratio": round(moto_ratio, 4),
            "heavy_vehicle_count": heavy_count,
            "approach_occupancy": round(app_occ, 4),
            "downstream_occupancy": round(down_occ, 4),
            "weather": weather,
            "hour_of_day": hour,
            "provenance": "SYNTHETIC_SHOCKWAVE",
            "clearance_time_sec": clearance_time,
        }

    def generate_dataset(
        self,
        num_samples: int = 500,
        seed: int = 42,
    ) -> pd.DataFrame:
        """Generate balanced clearance dataset across all nodes and scenarios."""
        rng = np.random.default_rng(seed)
        records: list[dict[str, Any]] = []

        samples_per_scenario = max(1, num_samples // len(SCENARIOS))

        for sc in SCENARIOS:
            for _ in range(samples_per_scenario):
                node = str(rng.choice(NODES))
                app = str(rng.choice(APPROACHES))
                rec = self.generate_episode(sc, node, app, rng)
                records.append(rec)

        # Fill remaining up to num_samples
        while len(records) < num_samples:
            sc = str(rng.choice(SCENARIOS))
            node = str(rng.choice(NODES))
            app = str(rng.choice(APPROACHES))
            records.append(self.generate_episode(sc, node, app, rng))

        df = pd.DataFrame(records)
        return df


def export_dataset(
    df: pd.DataFrame,
    csv_path: Path | str,
    metadata_path: Path | str | None = None,
) -> None:
    """Export dataset to CSV with accompanying JSON schema metadata."""
    out_csv = Path(csv_path)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)

    if metadata_path:
        out_meta = Path(metadata_path)
        out_meta.parent.mkdir(parents=True, exist_ok=True)
        meta = {
            "dataset_version": "1.0.0",
            "total_samples": len(df),
            "target_variable": "clearance_time_sec",
            "features": list(df.columns),
            "target_summary": {
                "mean_clearance_sec": round(float(df["clearance_time_sec"].mean()), 2),
                "min_clearance_sec": round(float(df["clearance_time_sec"].min()), 2),
                "max_clearance_sec": round(float(df["clearance_time_sec"].max()), 2),
                "std_clearance_sec": round(float(df["clearance_time_sec"].std()), 2),
            },
            "scenarios_represented": list(df["scenario_id"].unique()),
            "nodes_represented": list(df["node_id"].unique()),
            "weather_distribution": df["weather"].value_counts().to_dict(),
        }
        with open(out_meta, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)


def main() -> int:
    """CLI runner to generate clearance dataset."""
    parser = argparse.ArgumentParser(description="ClearWayAI Clearance Time Ground Truth Generator")
    parser.add_argument("--samples", type=int, default=500, help="Number of episodes to generate")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")
    parser.add_argument(
        "--output-csv",
        type=str,
        default="data/processed/clearance/clearance_ground_truth.csv",
        help="Path to output CSV file",
    )
    parser.add_argument(
        "--output-meta",
        type=str,
        default="data/processed/clearance/clearance_metadata.json",
        help="Path to output metadata JSON",
    )
    args = parser.parse_args()

    sim = QueueDischargeSimulator()
    df = sim.generate_dataset(num_samples=args.samples, seed=args.seed)
    export_dataset(df, args.output_csv, args.output_meta)

    print(f"[SUCCESS] Generated {len(df)} clearance episodes.")
    print(f"  CSV: {args.output_csv}")
    print(f"  Meta: {args.output_meta}")
    print(f"  Mean Clearance Time: {df['clearance_time_sec'].mean():.2f} seconds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
