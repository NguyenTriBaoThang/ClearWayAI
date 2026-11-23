"""
Automated Test Suite for Task 27: Baseline Controllers (B0, B1, B2) & Benchmark Runner
Verifies:
1. B0 Fixed-Time controller 72s NEMA cycle timing and zero-preemption behavior.
2. B1 Reactive Local controller 100m proximity activation, safety clearance transitions, and release.
3. B2 Corridor Coordination controller green-wave preemption across all 4 corridor nodes.
4. Comparative preemption durations (B2 > B1 > B0=0).
5. BenchmarkRunner execution and formatted markdown summary generation.
"""

import os

from simulation.baselines.b0_fixed_time import B0FixedTimeController
from simulation.baselines.b1_reactive import B1ReactiveController
from simulation.baselines.b2_corridor import B2CorridorController
from simulation.baselines.benchmark_runner import BenchmarkRunner

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_b0_fixed_time_controller():
    """Verify B0 executes static 72s NEMA cycle and ignores emergency vehicles."""
    ctrl = B0FixedTimeController()

    # Check phase timing across 72s cycle
    assert ctrl.get_phase_at_time(10.0) == 0  # Arterial Green
    assert ctrl.get_phase_at_time(36.0) == 1  # Arterial Yellow
    assert ctrl.get_phase_at_time(40.0) == 2  # All-Red
    assert ctrl.get_phase_at_time(50.0) == 3  # Cross Green
    assert ctrl.get_phase_at_time(68.0) == 4  # Cross Yellow
    assert ctrl.get_phase_at_time(71.0) == 5  # All-Red
    assert ctrl.get_phase_at_time(82.0) == 0  # Back to Arterial Green (82 % 72 = 10)

    # Check approach colors
    colors_p0 = ctrl.get_approach_colors(0)
    assert colors_p0["eb"] == "green"
    assert colors_p0["nb"] == "red"

    # Emergency vehicle present: B0 should NOT preempt
    active_vehs = {
        "AMB-339": {"x": 580.0, "is_emergency": True, "route": "route_eb_through"},
    }
    phases = ctrl.step(sim_time=50.0, active_vehicles=active_vehs, dt=0.1)
    assert phases["node_c"] == 3  # Remains Cross Green (no preemption!)
    assert ctrl.metrics.preemption_events == 0
    assert ctrl.metrics.total_preemption_duration_sec == 0.0


def test_b1_reactive_local_controller():
    """Verify B1 triggers preemption only when emergency vehicle is within 100m proximity."""
    ctrl = B1ReactiveController()

    # Case 1: Ambulance far away (x = -150m, Node C stopline is 600m -> 750m away)
    active_far = {
        "AMB-339": {"x": -150.0, "is_emergency": True, "route": "route_eb_through"},
    }
    phases_far = ctrl.step(sim_time=50.0, active_vehicles=active_far, dt=0.1)
    assert phases_far["node_c"] == 3  # Node C is NOT preempted (distance > 100m)

    # Case 2: Ambulance approaches Node C (x = 550m, 50m before stopline x=600m)
    active_near = {
        "AMB-339": {"x": 550.0, "is_emergency": True, "route": "route_eb_through"},
    }
    # Initial transition: from Cross Green (phase 3) through Yellow (phase 4)
    phases_near = ctrl.step(sim_time=50.0, active_vehicles=active_near, dt=0.1)
    assert "node_c" in ctrl.preempted_nodes
    assert phases_near["node_c"] in [0, 4, 5]  # In transition or emergency green
    assert ctrl.metrics.preemption_events >= 1

    # Node A (at x=0m) should NOT be preempted because ambulance is already at x=550m
    assert "node_a" not in ctrl.preempted_nodes


def test_b2_corridor_coordination_controller():
    """Verify B2 locks all corridor intersections when ambulance enters corridor."""
    ctrl = B2CorridorController()

    # Case 1: Outside corridor (x = -200m)
    active_outside = {
        "AMB-339": {"x": -200.0, "is_emergency": True, "route": "route_eb_through"},
    }
    phases_out = ctrl.step(sim_time=50.0, active_vehicles=active_outside, dt=0.1)
    assert not ctrl.is_corridor_preempted
    assert phases_out["node_c"] == 3

    # Case 2: Ambulance enters corridor (x = -100m, past entry gate -150m)
    active_in = {
        "AMB-339": {"x": -100.0, "is_emergency": True, "route": "route_eb_through"},
    }
    ctrl.step(sim_time=50.0, active_vehicles=active_in, dt=0.1)
    assert ctrl.is_corridor_preempted

    # Run past transition timer
    for _ in range(70):  # 7.0 seconds
        phases_locked = ctrl.step(sim_time=55.0, active_vehicles=active_in, dt=0.1)

    # All corridor nodes locked to Arterial Green (Phase 0)
    for nid in ["node_a", "node_b", "node_c", "node_d"]:
        assert phases_locked[nid] == 0


def test_comparative_preemption_durations():
    """Verify preemption durations: B2 (corridor-wide) > B1 (localized) > B0 (zero)."""
    b0 = B0FixedTimeController()
    b1 = B1ReactiveController()
    b2 = B2CorridorController()

    # Simulate ambulance traveling through corridor from x=-150m to x=950m over 50s
    for step in range(500):
        t = float(step) * 0.1
        # Ambulance speed ~22 m/s -> pos = -150 + 22 * t
        pos_x = -150.0 + (22.0 * t)
        active_vehs = {
            "AMB-339": {"x": pos_x, "is_emergency": True, "route": "route_eb_through"},
        }
        b0.step(sim_time=t, active_vehicles=active_vehs, dt=0.1)
        b1.step(sim_time=t, active_vehicles=active_vehs, dt=0.1)
        b2.step(sim_time=t, active_vehicles=active_vehs, dt=0.1)

    assert b0.metrics.total_preemption_duration_sec == 0.0
    assert b1.metrics.total_preemption_duration_sec > 0.0
    assert b2.metrics.total_preemption_duration_sec > b1.metrics.total_preemption_duration_sec


def test_benchmark_runner_execution():
    """Verify BenchmarkRunner executes trials for all 3 baselines and generates markdown report."""
    runner = BenchmarkRunner(scenario="peak_emergency", duration=30.0, dt=0.1)
    results = runner.run_all_baselines()

    assert "B0_FixedTime" in results
    assert "B1_ReactiveLocal" in results
    assert "B2_CorridorCoord" in results

    b0_res = results["B0_FixedTime"]
    assert "emergency_transit_time_sec" in b0_res
    assert "emergency_avg_speed_kmh" in b0_res
    assert b0_res["preemption_duration_sec"] == 0.0

    report = runner.format_markdown_table(results)
    assert "ClearWayAI Baseline Comparison Benchmark" in report
    assert "B0_FixedTime" in report
    assert "B1_ReactiveLocal" in report
    assert "B2_CorridorCoord" in report
