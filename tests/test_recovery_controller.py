"""Automated Unit & Integration Test Suite for Post-Clearance Recovery Controller (Task 40).

Verifies:
1. Green debt calculation based on preemption duration, nominal splits, and queue dissipation demand:
   $$G_{\\text{debt}} = T_{\\text{preempt}} \\times \\frac{G_{\\text{cross}}}{C} + \\frac{L_{\\text{queue}}}{v_{\\text{sat}}}$$
2. Immediate handoff from preclearance CLEARED state to start recovery.
3. Multi-cycle gradual amortization of cross-street green debt without arterial starvation.
4. Bounded split allocation respecting minimum arterial green (>=15s) and maximum cross green (<=45s).
5. State transitions: INACTIVE -> COMPENSATING -> (RESYNCHRONIZING) -> EQUILIBRIUM_RESTORED.
6. Watchdog timeout enforcement (ceiling: 180s).
7. Corridor-wide recovery report covering all 4 intersections (Nodes A, B, C, D).
8. Real-time latency benchmark (< 5.0 ms).
"""

from __future__ import annotations

import time

import pytest

from controller.recovery.recovery_controller import (
    CorridorRecoveryReport,
    PostClearanceRecoveryController,
    RecoveryConfig,
    RecoveryState,
)


@pytest.fixture
def config() -> RecoveryConfig:
    """Fixture providing standard recovery configuration."""
    return RecoveryConfig(
        nominal_cycle_sec=72.0,
        nominal_arterial_green_sec=35.0,
        nominal_cross_green_sec=25.0,
        yellow_duration_sec=3.0,
        all_red_duration_sec=2.0,
        min_arterial_green_sec=15.0,
        min_cross_green_sec=10.0,
        max_cross_green_sec=45.0,
        max_bonus_per_cycle_sec=12.0,
        recovery_cycles_budget=3,
        max_recovery_timeout_sec=180.0,
        resync_tolerance_sec=1.5,
    )


@pytest.fixture
def controller(config: RecoveryConfig) -> PostClearanceRecoveryController:
    """Fixture providing initialized PostClearanceRecoveryController."""
    return PostClearanceRecoveryController(
        config=config,
        intersections=["node_a", "node_b", "node_c", "node_d"],
    )


def test_green_debt_calculation(controller: PostClearanceRecoveryController):
    """Verify exact formula for cross-street accumulated green debt."""
    # Preemption duration = 30.0s. Nominal cross green = 25s / 72s ~ 0.3472
    # Lost nominal cross time = 30.0 * (25.0 / 72.0) = 10.42s
    # Cross queue = 45.0m. Dissipation speed = 4.5 m/s -> queue discharge = 10.0s
    # Total debt = 10.42 + 10.0 = 20.42s
    debt = controller.calculate_green_debt(
        preemption_duration_sec=30.0,
        cross_queue_meters=45.0,
    )
    assert debt == pytest.approx(20.42, abs=0.05)

    # Zero preemption and zero queue -> 0 debt
    debt_zero = controller.calculate_green_debt(
        preemption_duration_sec=0.0,
        cross_queue_meters=0.0,
    )
    assert debt_zero == 0.0

    # Upper bound test: massive preemption & queue capped at 36.0s (half cycle)
    debt_capped = controller.calculate_green_debt(
        preemption_duration_sec=120.0,
        cross_queue_meters=200.0,
    )
    assert debt_capped == 36.0


def test_inactive_node_status(controller: PostClearanceRecoveryController):
    """Verify inactive nodes return EQUILIBRIUM_RESTORED with nominal phase."""
    assert controller.is_recovering("node_a") is False

    status = controller.evaluate_node("node_a", sim_time=10.0)
    assert status.state == RecoveryState.EQUILIBRIUM_RESTORED
    assert status.is_recovered is True
    assert status.remaining_green_debt_sec == 0.0
    assert status.commanded_phase == controller.get_nominal_phase(10.0)


def test_recovery_initiation_and_split_allocation(
    controller: PostClearanceRecoveryController,
):
    """Verify recovery initiation sets COMPENSATING state and allocates cycle 1 bonus split."""
    # Initiate recovery at Node A with 30s preemption duration and 45m queue (debt ~20.42s)
    status = controller.initiate_recovery(
        node_id="node_a",
        preemption_duration_sec=30.0,
        cross_queue_meters=45.0,
        sim_time=100.0,
    )

    assert controller.is_recovering("node_a") is True
    assert status.state == RecoveryState.COMPENSATING
    assert status.initial_green_debt_sec == pytest.approx(20.42, abs=0.05)
    assert status.remaining_green_debt_sec == pytest.approx(20.42, abs=0.05)
    assert status.current_recovery_cycle == 1
    assert status.is_recovered is False

    # Bonus in cycle 1: debt / 3 = 20.42 / 3 ~ 6.81s (capped at 12.0s)
    assert status.bonus_green_allocated_sec == pytest.approx(6.81, abs=0.05)

    # Initial phase should transition to Arterial Yellow (phase 1)
    assert status.commanded_phase == controller.config.arterial_phase_yellow


def test_multi_cycle_debt_amortization_and_safety_bounds(
    controller: PostClearanceRecoveryController,
):
    """Verify monotonic debt amortization over multiple cycles respecting safety split bounds."""
    sim_t = 100.0
    controller.initiate_recovery(
        node_id="node_a",
        preemption_duration_sec=30.0,
        cross_queue_meters=45.0,
        sim_time=sim_t,
    )

    # Cycle 1: Arterial Yellow (3s) -> All-Red (2s) -> Cross Green (~31.8s) -> Yellow (3s) -> All-Red (2s) -> Arterial (~28.2s)
    # Total cycle duration = 72s. Advance sim_time through cycle 1
    sim_t += 3.1
    s_ar = controller.evaluate_node("node_a", sim_time=sim_t)
    assert s_ar.commanded_phase == controller.config.arterial_phase_all_red

    sim_t += 2.1
    s_cg = controller.evaluate_node("node_a", sim_time=sim_t)
    assert s_cg.commanded_phase == controller.config.cross_phase_green

    # Advance to end of cycle 1 (approx 72s from start)
    sim_t = 172.5
    s_c2 = controller.evaluate_node("node_a", sim_time=sim_t)

    # Should have advanced to Cycle 2
    assert s_c2.current_recovery_cycle == 2
    # Debt should have decremented monotonically: 20.42 - 6.81 ~ 13.61s
    assert s_c2.remaining_green_debt_sec < s_c2.initial_green_debt_sec
    assert s_c2.remaining_green_debt_sec == pytest.approx(13.61, abs=0.1)

    # Verify safety bounds on split:
    art_split, cross_split = controller._current_cycle_splits["node_a"]
    assert art_split >= controller.config.min_arterial_green_sec  # >= 15.0s
    assert cross_split <= controller.config.max_cross_green_sec  # <= 45.0s
    assert art_split + cross_split == pytest.approx(
        controller.config.nominal_arterial_green_sec + controller.config.nominal_cross_green_sec,
        abs=0.1,
    )


def test_full_equilibrium_restoration(controller: PostClearanceRecoveryController):
    """Verify completion of 3-cycle budget restores EQUILIBRIUM_RESTORED state."""
    sim_t = 100.0
    controller.initiate_recovery(
        node_id="node_a",
        preemption_duration_sec=15.0,  # Small preemption: debt ~10.4s
        cross_queue_meters=20.0,
        sim_time=sim_t,
    )

    # Fast forward through Cycle 1 (72s), Cycle 2 (72s), Cycle 3 (72s)
    # Step at small increments through transitions
    sim_t += 73.0  # End of Cycle 1
    controller.evaluate_node("node_a", sim_time=sim_t)

    sim_t += 73.0  # End of Cycle 2
    controller.evaluate_node("node_a", sim_time=sim_t)

    sim_t += 73.0  # End of Cycle 3
    final_status = controller.evaluate_node("node_a", sim_time=sim_t)

    assert final_status.state == RecoveryState.EQUILIBRIUM_RESTORED
    assert final_status.is_recovered is True
    assert final_status.remaining_green_debt_sec == 0.0
    assert controller.is_recovering("node_a") is False


def test_watchdog_timeout_enforcement(controller: PostClearanceRecoveryController):
    """Verify recovery timeout forces equilibrium restoration if recovery exceeds 180s ceiling."""
    sim_t = 100.0
    controller.initiate_recovery(
        node_id="node_a",
        preemption_duration_sec=36.0,
        cross_queue_meters=100.0,
        sim_time=sim_t,
    )

    # Jump past timeout ceiling (180.0s + 10.0s = 190.0s)
    timeout_status = controller.evaluate_node("node_a", sim_time=sim_t + 190.0)

    assert timeout_status.state == RecoveryState.EQUILIBRIUM_RESTORED
    assert timeout_status.is_recovered is True
    assert "timeout" in timeout_status.reason.lower()
    assert controller.is_recovering("node_a") is False


def test_corridor_wide_recovery_coordination(controller: PostClearanceRecoveryController):
    """Verify corridor-wide recovery report accurately tracks concurrent recovering intersections."""
    # Staggered clearance: Node A cleared at t = 50s, Node B cleared at t = 70s
    controller.initiate_recovery("node_a", preemption_duration_sec=25.0, sim_time=50.0)
    controller.initiate_recovery("node_b", preemption_duration_sec=20.0, sim_time=70.0)

    report = controller.evaluate_corridor(sim_time=75.0)

    assert isinstance(report, CorridorRecoveryReport)
    assert report.corridor_recovering_count == 2
    assert report.all_nodes_equilibrium is False
    assert report.node_reports["node_a"].is_recovered is False
    assert report.node_reports["node_b"].is_recovered is False
    # Node C and Node D were not preempted -> already in equilibrium
    assert report.node_reports["node_c"].is_recovered is True
    assert report.node_reports["node_d"].is_recovered is True

    # Step simulation runner interface
    phases = controller.step(sim_time=75.0)
    assert set(phases.keys()) == {"node_a", "node_b", "node_c", "node_d"}
    for p in phases.values():
        assert 0 <= p <= 5


def test_realtime_execution_latency(controller: PostClearanceRecoveryController):
    """Verify sub-5ms real-time SLA for corridor recovery evaluation across 4 intersections."""
    for nid in ["node_a", "node_b", "node_c", "node_d"]:
        controller.initiate_recovery(nid, preemption_duration_sec=20.0, sim_time=10.0)

    # Warmup
    controller.evaluate_corridor(sim_time=15.0)

    # Benchmark 20 iterations
    latencies = []
    for i in range(20):
        t0 = time.perf_counter()
        controller.evaluate_corridor(sim_time=15.0 + i * 0.1)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency < 5.0, f"Recovery evaluation exceeded 5ms SLA: {avg_latency:.2f}ms"
