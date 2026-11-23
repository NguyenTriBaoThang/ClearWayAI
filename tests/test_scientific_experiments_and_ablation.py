"""
ClearWayAI - Automated Test Suite for Task 51: Scientific Experiments, Sensitivity Sweeps & Ablation.

Verifies:
1. B3 ClearWayAI proposed controller state machine, JIT pre-clearance, and MMU safety interlocks.
2. MetricStatistics small-sample Student-t 95% confidence interval calculation and edge cases.
3. Multi-seed replication benchmark across B0, B1, B2, and B3 with zero stop verification.
4. Parametric sensitivity sweeps across traffic volumes, fleet composition, and weather friction.
5. Component ablation study validating the contributions of ML shockwave prediction, Moving-Horizon, and Recovery.
6. Scientific Markdown report generation and JSON persistence.
"""

import json
from pathlib import Path

from simulation.baselines.b3_clearway import B3ClearWayController
from simulation.experiments.scientific_evaluator import (
    MetricStatistics,
    ScientificBenchmarkRunner,
)


def test_b3_clearway_controller_mechanics():
    """Verify B3 controller coordinates multi-node corridor with MMU safety gateway."""
    ctrl = B3ClearWayController(cycle_time=72.0)
    assert ctrl.cycle_time == 72.0
    assert ctrl.enable_ai_prediction is True
    assert ctrl.enable_moving_horizon is True
    assert ctrl.enable_recovery is True

    # Initial state without emergency vehicle: nominal Webster phases
    phases_nominal = ctrl.step(
        sim_time=10.0,
        active_vehicles={},
        dt=0.1,
    )
    assert len(phases_nominal) == 4
    for nid in ["node_a", "node_b", "node_c", "node_d"]:
        assert phases_nominal[nid] in [0, 1, 2, 3, 4, 5]
    assert ctrl.is_corridor_preempted is False

    # Emergency vehicle approaching Node A
    active_ev = {
        "AMB-339": {
            "id": "AMB-339",
            "type": "emergency_ambulance",
            "is_emergency": True,
            "x": -50.0,
            "speed": 18.5,
            "route": "route_eb_through",
        }
    }
    phases_ev = ctrl.step(sim_time=12.0, active_vehicles=active_ev, dt=0.1)
    assert len(phases_ev) == 4
    assert ctrl.active_mission is not None
    assert ctrl.active_mission.is_active is True

    # Verify reset behavior
    ctrl.reset()
    assert ctrl.metrics.total_steps == 0
    assert ctrl.metrics.total_preemption_duration_sec == 0.0
    assert ctrl.is_corridor_preempted is False


def test_metric_statistics_and_confidence_intervals():
    """Verify small-sample Student-t 95% confidence interval computation."""
    # Empty case
    stat_empty = MetricStatistics.from_values([])
    assert stat_empty.sample_size == 0
    assert stat_empty.mean == 0.0

    # Single value case
    stat_single = MetricStatistics.from_values([42.5])
    assert stat_single.sample_size == 1
    assert stat_single.mean == 42.5
    assert stat_single.ci95_margin == 0.0

    # 10 replications case (N=10, df=9, t_crit=2.262)
    values = [37.2, 36.8, 37.5, 38.0, 36.5, 37.1, 37.4, 37.9, 36.9, 37.3]
    stat_10 = MetricStatistics.from_values(values)
    assert stat_10.sample_size == 10
    assert 37.0 <= stat_10.mean <= 37.5
    assert stat_10.std > 0.0
    assert stat_10.sem > 0.0
    assert stat_10.ci95_margin > 0.0
    assert stat_10.ci95_low < stat_10.mean < stat_10.ci95_high

    # Formatted string check
    formatted = stat_10.to_formatted_str()
    assert "±" in formatted


def test_multi_seed_scientific_benchmark_execution():
    """Verify multi-seed benchmark execution across B0, B1, B2, and B3."""
    test_seeds = [42, 101, 2024]
    runner = ScientificBenchmarkRunner(
        scenario="peak_emergency",
        duration=75.0,
        dt=0.2,
        seeds=test_seeds,
    )
    report = runner.run_multi_seed_evaluation(
        models=["B0_FixedTime", "B1_ReactiveLocal", "B2_CorridorCoord", "B3_ClearWayAI"]
    )

    assert report.scenario == "peak_emergency"
    assert report.sample_size == 3
    assert "B0_FixedTime" in report.results_by_model
    assert "B1_ReactiveLocal" in report.results_by_model
    assert "B2_CorridorCoord" in report.results_by_model
    assert "B3_ClearWayAI" in report.results_by_model

    b3_stats = report.results_by_model["B3_ClearWayAI"]
    # ClearWayAI achieves zero stops across seeds
    assert b3_stats["stops"].mean == 0.0
    assert b3_stats["transit_time"].mean > 0.0

    # Relative improvement tracking
    assert "B3_ClearWayAI" in report.relative_improvements_vs_b0


def test_traffic_volume_and_weather_sensitivity():
    """Verify parametric sweeps over demand levels and weather friction."""
    runner = ScientificBenchmarkRunner(
        scenario="peak_emergency",
        duration=70.0,
        dt=0.2,
        seeds=[42],
    )
    sens = runner.run_sensitivity_sweep(
        volumes=["normal", "peak"],
        fleet_ratios=[0.50, 0.75],
        weather_conditions=["clear", "rain"],
    )

    assert "traffic_volume_sweep" in sens
    assert "fleet_mix_sweep" in sens
    assert "weather_sweep" in sens

    assert "normal" in sens["traffic_volume_sweep"]
    assert "peak" in sens["traffic_volume_sweep"]
    assert "moto_50pct" in sens["fleet_mix_sweep"]
    assert "clear" in sens["weather_sweep"]
    assert "rain" in sens["weather_sweep"]


def test_systematic_component_ablation_study():
    """Verify systematic component ablation evaluates all 4 variants."""
    runner = ScientificBenchmarkRunner(
        scenario="peak_emergency",
        duration=70.0,
        dt=0.2,
        seeds=[42, 101],
    )
    abl = runner.run_ablation_study()

    assert "ablation_summary" in abl
    summary = abl["ablation_summary"]

    assert "Full_ClearWayAI" in summary
    assert "Ablation_No_ML_Clearance" in summary
    assert "Ablation_No_Moving_Horizon" in summary
    assert "Ablation_No_Recovery" in summary

    full = summary["Full_ClearWayAI"]
    assert full["stops_mean"] == 0.0
    assert "transit_time_ci95" in full


def test_scientific_markdown_report_and_json_export(tmp_path: Path):
    """Verify Markdown report generation and JSON dataset persistence."""
    runner = ScientificBenchmarkRunner(
        scenario="peak_emergency",
        duration=70.0,
        dt=0.2,
        seeds=[42, 101],
    )
    report = runner.run_multi_seed_evaluation(models=["B0_FixedTime", "B3_ClearWayAI"])

    md_report = runner.format_markdown_report(report)
    assert "ClearWayAI Scientific Benchmark Evaluation Report" in md_report
    assert "Table 1: Multi-Seed Baseline Comparison" in md_report
    assert "B0_FixedTime" in md_report
    assert "B3_ClearWayAI" in md_report
    assert "Zero Stop Guarantee" in md_report

    # JSON export
    export_path = tmp_path / "scientific_results.json"
    sens = runner.run_sensitivity_sweep(
        volumes=["peak"], fleet_ratios=[0.6], weather_conditions=["clear"]
    )
    abl = runner.run_ablation_study()
    runner.export_json(report, sens, abl, export_path)

    assert export_path.exists()
    with open(export_path, encoding="utf-8") as f:
        data = json.load(f)

    assert data["meta"]["scenario"] == "peak_emergency"
    assert "multi_seed_comparison" in data
    assert "sensitivity_sweeps" in data
    assert "ablation_study" in data
