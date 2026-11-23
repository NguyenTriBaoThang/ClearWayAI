"""Automated Unit & Integration Test Suite for Signal Safety Gateway (Task 41).

Verifies the independent zero-trust Malfunction Management Unit (MMU):
1. INV-01: Conflict-free mutual exclusion (Green/Yellow EB/WB mutually exclusive with NB/SB).
2. INV-02: Minimum Green Interval clamping (>= 10.0s).
3. INV-03: Maximum Green Interval ceiling enforcement (<= 75.0s, forces Yellow).
4. INV-04: Mandatory Yellow Change enforcement (>= 3.0s, prohibits skipping or truncating Yellow).
5. INV-05: Mandatory All-Red Clearance enforcement (>= 2.0s, prohibits skipping All-Red).
6. INV-06: Communication Loss & Heartbeat Watchdog timeout (<= 2.0s, engages Webster fallback).
7. Corridor-wide multi-intersection audit (Nodes A, B, C, D).
8. Real-time sub-millisecond execution latency (< 1.0 ms).
"""

from __future__ import annotations

import time

import pytest

from controller.safety.signal_safety_gateway import (
    CorridorSafetyAudit,
    GatewayOperationalMode,
    GatewayTripReason,
    SafetyGatewayConfig,
    SignalColor,
    SignalSafetyGateway,
)


@pytest.fixture
def config() -> SafetyGatewayConfig:
    """Fixture providing standard Safety Gateway configuration."""
    return SafetyGatewayConfig(
        min_green_sec=10.0,
        max_green_sec=75.0,
        min_yellow_sec=3.0,
        min_all_red_sec=2.0,
        heartbeat_timeout_sec=2.0,
        nominal_cycle_sec=72.0,
    )


@pytest.fixture
def gateway(config: SafetyGatewayConfig) -> SignalSafetyGateway:
    """Fixture providing initialized SignalSafetyGateway."""
    return SignalSafetyGateway(
        config=config,
        node_ids=["node_a", "node_b", "node_c", "node_d"],
    )


def test_mutual_exclusion_invariant_inv_01(gateway: SignalSafetyGateway):
    """Verify INV-01: Conflict-free mutual exclusion across approach colors."""
    # All 6 standard NEMA phases must be conflict-free
    for p in range(6):
        colors = gateway.get_approach_colors(p)
        assert gateway.check_conflict_free(colors) is True

    # Conflicting green-green state must be detected as unsafe
    hazardous_colors = {
        "eb": SignalColor.GREEN,
        "wb": SignalColor.GREEN,
        "nb": SignalColor.GREEN,  # HAZARD! Both EW and NS green
        "sb": SignalColor.RED,
    }
    assert gateway.check_conflict_free(hazardous_colors) is False

    # Out of range invalid phase (-1 or 99) drops to Fail-Safe All-Red
    rep_inv = gateway.verify_and_sanitize_command(
        node_id="node_a",
        proposed_phase=99,
        sim_time=10.0,
    )
    assert rep_inv.operational_mode == GatewayOperationalMode.FAILSAFE_ALL_RED
    assert rep_inv.sanitized_phase == gateway.config.arterial_phase_all_red
    assert rep_inv.intervention is not None
    assert rep_inv.intervention.trip_reason == GatewayTripReason.INVALID_PHASE_INDEX


def test_minimum_green_enforcement_inv_02(gateway: SignalSafetyGateway):
    """Verify INV-02: Transitions from Green before 10s are clamped to Green."""
    # At t = 0s, Node A turns to Phase 0 (Arterial Green)
    gateway.verify_and_sanitize_command(
        node_id="node_a",
        proposed_phase=0,
        sim_time=0.0,
    )

    # At t = 4.0s (elapsed = 4.0s < 10.0s), an algorithm attempts to transition to Phase 1 (Yellow)
    rep_early = gateway.verify_and_sanitize_command(
        node_id="node_a",
        proposed_phase=1,
        sim_time=4.0,
    )
    assert rep_early.operational_mode == GatewayOperationalMode.CLAMPED_SAFE
    assert rep_early.sanitized_phase == 0  # Clamped to Green!
    assert rep_early.intervention is not None
    assert rep_early.intervention.trip_reason == GatewayTripReason.MIN_GREEN_VIOLATION

    # At t = 10.1s (elapsed = 10.1s >= 10.0s), transition to Yellow is permitted
    rep_ok = gateway.verify_and_sanitize_command(
        node_id="node_a",
        proposed_phase=1,
        sim_time=10.1,
    )
    assert rep_ok.operational_mode == GatewayOperationalMode.NORMAL_PASSTHROUGH
    assert rep_ok.sanitized_phase == 1
    assert rep_ok.intervention is None


def test_maximum_green_ceiling_enforcement_inv_03(gateway: SignalSafetyGateway):
    """Verify INV-03: Holding Green past 75s triggers forced transition to Yellow."""
    # Turn Green at t = 0s
    gateway.verify_and_sanitize_command("node_a", proposed_phase=0, sim_time=0.0)

    # Hold Green at t = 50s (safe)
    rep_mid = gateway.verify_and_sanitize_command("node_a", proposed_phase=0, sim_time=50.0)
    assert rep_mid.operational_mode == GatewayOperationalMode.NORMAL_PASSTHROUGH
    assert rep_mid.sanitized_phase == 0

    # At t = 76s (> 75s max green): gateway forces Yellow
    rep_max = gateway.verify_and_sanitize_command("node_a", proposed_phase=0, sim_time=76.0)
    assert rep_max.operational_mode == GatewayOperationalMode.CLAMPED_SAFE
    assert rep_max.sanitized_phase == 1  # Forced Yellow
    assert rep_max.intervention is not None
    assert rep_max.intervention.trip_reason == GatewayTripReason.MAX_GREEN_EXCEEDED


def test_mandatory_yellow_enforcement_inv_04(gateway: SignalSafetyGateway):
    """Verify INV-04: Skipping or truncating Yellow is strictly intercepted."""
    # Green at t = 0s; advance to t = 12s (> min green)
    gateway.verify_and_sanitize_command("node_a", proposed_phase=0, sim_time=0.0)

    # Subtest 1: Attempt to skip Yellow directly to All-Red (0 -> 2)
    rep_skip = gateway.verify_and_sanitize_command("node_a", proposed_phase=2, sim_time=12.0)
    assert rep_skip.operational_mode == GatewayOperationalMode.CLAMPED_SAFE
    assert rep_skip.sanitized_phase == 1  # Clamped to Yellow!
    assert rep_skip.intervention is not None
    assert rep_skip.intervention.trip_reason == GatewayTripReason.YELLOW_TRUNCATION_VIOLATION

    # Subtest 2: Attempt to truncate Yellow before 3s (at t = 13.5s, elapsed = 1.5s < 3s)
    rep_trunc = gateway.verify_and_sanitize_command("node_a", proposed_phase=2, sim_time=13.5)
    assert rep_trunc.operational_mode == GatewayOperationalMode.CLAMPED_SAFE
    assert rep_trunc.sanitized_phase == 1  # Clamped to Yellow

    # At t = 15.1s (elapsed = 3.1s >= 3.0s), transition to All-Red (phase 2) is permitted
    rep_ok = gateway.verify_and_sanitize_command("node_a", proposed_phase=2, sim_time=15.1)
    assert rep_ok.operational_mode == GatewayOperationalMode.NORMAL_PASSTHROUGH
    assert rep_ok.sanitized_phase == 2


def test_mandatory_all_red_enforcement_inv_05(gateway: SignalSafetyGateway):
    """Verify INV-05: Skipping or truncating All-Red clearance is strictly intercepted."""
    # Set Node A into Yellow at t = 10s -> All-Red at t = 13.1s
    gateway._current_phases["node_a"] = 1
    gateway._phase_start_times["node_a"] = 10.0

    # Advance to All-Red (phase 2) at t = 13.1s
    gateway.verify_and_sanitize_command("node_a", proposed_phase=2, sim_time=13.1)

    # Attempt to jump to Cross Green (phase 3) at t = 14.0s (elapsed = 0.9s < 2.0s)
    rep_early = gateway.verify_and_sanitize_command("node_a", proposed_phase=3, sim_time=14.0)
    assert rep_early.operational_mode == GatewayOperationalMode.CLAMPED_SAFE
    assert rep_early.sanitized_phase == 2  # Clamped to All-Red
    assert rep_early.intervention is not None
    assert rep_early.intervention.trip_reason == GatewayTripReason.ALL_RED_SKIPPED_VIOLATION

    # At t = 15.2s (elapsed = 2.1s >= 2.0s), transition to Cross Green is permitted
    rep_ok = gateway.verify_and_sanitize_command("node_a", proposed_phase=3, sim_time=15.2)
    assert rep_ok.operational_mode == GatewayOperationalMode.NORMAL_PASSTHROUGH
    assert rep_ok.sanitized_phase == 3


def test_heartbeat_timeout_watchdog_inv_06(gateway: SignalSafetyGateway):
    """Verify INV-06: Communication loss (> 2.0s) trips to autonomous Webster fallback."""
    # Send normal command with heartbeat at t = 10.0s
    gateway.verify_and_sanitize_command("node_a", proposed_phase=0, sim_time=10.0, heartbeat=True)

    # Time advances to t = 13.0s (gap = 3.0s > 2.0s timeout), without valid heartbeat
    rep_timeout = gateway.verify_and_sanitize_command(
        "node_a", proposed_phase=0, sim_time=13.0, heartbeat=False
    )
    assert rep_timeout.operational_mode == GatewayOperationalMode.FALLBACK_WEBSTER
    assert rep_timeout.intervention is not None
    assert rep_timeout.intervention.trip_reason == GatewayTripReason.HEARTBEAT_TIMEOUT
    # Sanitized phase defaults to Webster nominal cycle phase
    assert rep_timeout.sanitized_phase == gateway.get_nominal_phase(13.0)


def test_corridor_wide_safety_audit(gateway: SignalSafetyGateway):
    """Verify simultaneous multi-intersection corridor audit (Nodes A, B, C, D)."""
    # Nodes A, B, C nominal (0), Node D invalid (99)
    proposed = {
        "node_a": 0,
        "node_b": 0,
        "node_c": 0,
        "node_d": 99,
    }

    audit = gateway.audit_corridor_phases(proposed, sim_time=15.0)

    assert isinstance(audit, CorridorSafetyAudit)
    assert audit.all_nodes_safe is False
    assert audit.total_interventions_corridor >= 1
    assert audit.sanitized_phases["node_d"] == gateway.config.arterial_phase_all_red
    assert audit.reports_by_node["node_a"].is_safe is True
    assert audit.reports_by_node["node_d"].is_safe is False


def test_realtime_execution_latency(gateway: SignalSafetyGateway):
    """Verify sub-millisecond hardware-level execution latency (< 1.0 ms across 4 nodes)."""
    proposed = {"node_a": 0, "node_b": 0, "node_c": 0, "node_d": 0}

    # Warmup
    gateway.audit_corridor_phases(proposed, sim_time=10.0)

    # Benchmark 50 iterations
    latencies = []
    for i in range(50):
        t0 = time.perf_counter()
        gateway.audit_corridor_phases(proposed, sim_time=10.0 + i * 0.1)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency < 1.0, f"Safety gateway latency exceeded 1ms SLA: {avg_latency:.3f}ms"
