#!/usr/bin/env python3
"""
ClearWayAI - TraCI Simulation CLI Runner
Runs headless corridor simulations, logs telemetry, and exports replay files.
"""

import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from simulation.traci.manager import SimulationManager  # noqa: E402
from simulation.traci.snapshot_exporter import SnapshotExporter  # noqa: E402

SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "scenarios"
LOGS_DIR = Path(__file__).resolve().parent / "logs"


def run_headless_simulation(
    scenario: str = "peak_emergency",
    duration: float = 30.0,
    dt: float = 0.1,
    export_path: Path | None = None,
) -> list:
    """Runs a simulation session and optionally exports telemetry snapshots."""
    cfg_path = SCENARIOS_DIR / f"corridor_{scenario}.sumocfg"
    if not cfg_path.exists():
        cfg_path = SCENARIOS_DIR / "corridor_peak_emergency.sumocfg"

    print("=" * 70)
    print("🚦 ClearWayAI - Running Simulation Session")
    print(f"   Scenario: {scenario} ({cfg_path.name})")
    print(f"   Duration: {duration:.1f}s (step: {dt:.2f}s)")
    print("=" * 70)

    mgr = SimulationManager(config_path=cfg_path, step_length=dt)
    mgr.start()

    snapshots = []
    start_wall = time.time()
    steps_total = int(duration / dt)

    for i in range(steps_total):
        snap = mgr.step(dt=dt)
        snapshots.append(snap)
        if i % 100 == 0:
            active_cnt = len(snap.vehicles)
            amb_str = "🚑 [AMB-339 ON SCENE]" if snap.active_mission else "Normal"
            print(
                f"   [t={snap.sim_time_sec:6.1f}s] Active Veh: {active_cnt:3d} | "
                f"Phase: {snap.signals.current_phase_name if snap.signals else 'N/A'} | Status: {amb_str}"
            )

    wall_duration = time.time() - start_wall
    mgr.stop()

    summary = SnapshotExporter.compute_run_summary(snapshots)
    print("-" * 70)
    print("📋 Simulation Run Complete:")
    print(f"   Simulated Time: {summary['duration_seconds']}s")
    print(
        f"   Wall-Clock Time: {wall_duration:.2f}s ({(summary['duration_seconds'] / max(0.001, wall_duration)):.1f}x real-time)"
    )
    print(f"   Total Snapshots: {summary['total_snapshots']}")
    print(f"   Peak Vehicles: {summary['peak_vehicle_count']}")
    print(f"   Average Speed: {summary['avg_speed_kmh']} km/h")
    print(f"   Emergency Mission: {summary['emergency_mission_detected']}")
    print("-" * 70)

    if export_path:
        SnapshotExporter.export_jsonl(snapshots, export_path)

    return snapshots


def main():
    parser = argparse.ArgumentParser(description="Run ClearWayAI simulation and export telemetry.")
    parser.add_argument("--scenario", default="peak_emergency", help="Scenario configuration name")
    parser.add_argument(
        "--duration", type=float, default=30.0, help="Duration to simulate in seconds"
    )
    parser.add_argument("--dt", type=float, default=0.1, help="Simulation step size in seconds")
    parser.add_argument("--export", type=str, default=None, help="Output path for JSONL export")
    args = parser.parse_args()

    out_path = (
        Path(args.export)
        if args.export
        else LOGS_DIR / f"{args.scenario}_{int(args.duration)}s.jsonl"
    )
    run_headless_simulation(
        scenario=args.scenario,
        duration=args.duration,
        dt=args.dt,
        export_path=out_path,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
