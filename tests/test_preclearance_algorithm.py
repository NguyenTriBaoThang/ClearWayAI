"""Automated Unit & Integration Test Suite for Pre-Clearance Algorithm (Task 38).

Verifies:
1. Exact mathematical formulation of JIT pre-clearance trigger:
   $$\\Delta t_{\\text{trigger}} = \\text{ETA}_{\\text{EV}} - \\hat{T}_{\\text{clear}} - T_{\\text{transition}} - T_{\\text{buffer}}$$
2. Deterministic phase transition overhead calculation across all 6 NEMA phases.
3. State machine transitions:
   MONITORING -> ARMED -> TRANSITIONING -> HOLDING_GREEN -> EV_PASSING -> CLEARED.
4. Just-in-Time (JIT) non-premature actuation:
   Upstream node (Node A) actuates while downstream node (Node D) remains ARMED without holding green prematurely.
5. Anti-starvation watchdog:
   Enforces maximum green hold ceiling (60.0s) against stuck/broken down vehicles.
6. Multi-tier clearance model fallback integration (Tier 0 AI -> Tier 1 Kinematic -> Tier 2 Safe Default).
7. Corridor-wide plan evaluation and step simulation interface.
8. Real-time latency benchmark (< 50.0 ms across all 4 intersections).
"""

from __future__ import annotations

import time

import pytest

from ai.clearance.model_registry import (
    ClearanceModelRegistry,
    UnifiedClearancePredictor,
)
from ai.state.traffic_state_estimator import ApproachTrafficState
from controller.mission.emergency_mission import (
    EmergencyMission,
    EmergencyVehicleType,
    MissionStatus,
)
from controller.mission.eta_estimator import MultiNodeETAEvaluator
from controller.scheduler.preclearance_controller import (
    PreclearanceConfig,
    PreclearanceController,
    PreclearanceState,
)


@pytest.fixture
def config() -> PreclearanceConfig:
    """Fixture providing standard pre-clearance configuration."""
    return PreclearanceConfig(
        yellow_duration_sec=3.0,
        all_red_duration_sec=2.0,
        safety_buffer_sec=2.0,
        min_green_duration_sec=10.0,
        max_green_hold_sec=60.0,
        passing_zone_distance_m=50.0,
        exit_clearance_distance_m=15.0,
    )


@pytest.fixture
def controller(config: PreclearanceConfig) -> PreclearanceController:
    """Fixture providing initialized PreclearanceController."""
    eta_eval = MultiNodeETAEvaluator()
    registry = ClearanceModelRegistry()
    pred = UnifiedClearancePredictor(registry=registry)
    return PreclearanceController(
        config=config,
        eta_evaluator=eta_eval,
        clearance_predictor=pred,
        intersections=["node_a", "node_b", "node_c", "node_d"],
    )


@pytest.fixture
def nominal_traffic_state() -> ApproachTrafficState:
    """Fixture providing a standard Eastbound traffic state with 35m queue."""
    return ApproachTrafficState(
        approach_id="EB",
        timestamp_sec=100.0,
        vehicle_count=16,
        counts_by_class={"car": 4, "motorcycle": 10, "bus": 1, "truck": 1},
        motorcycle_ratio=10.0 / 16.0,
        queue_length_meters=35.0,
        queued_vehicle_count=12,
        approach_occupancy_ratio=0.45,
        traffic_density_vpm=16.0,
        mean_speed_kmh=12.5,
    )


@pytest.fixture
def active_mission() -> EmergencyMission:
    """Fixture providing an approaching ambulance mission."""
    mission = EmergencyMission(
        mission_id="mission_amb_339",
        vehicle_id="AMB-339",
        vehicle_type=EmergencyVehicleType.AMBULANCE,
        status=MissionStatus.APPROACHING,
        current_position_m=-200.0,  # At corridor entry gate
        current_speed_mps=15.0,  # 54 km/h
        target_speed_mps=18.5,  # 66.6 km/h
    )
    return mission


def test_trigger_delta_formula(controller: PreclearanceController):
    """Verify exact mathematical formulation of delta_trigger."""
    # Case 1: EV is far away (ETA = 30.0s, T_clear = 8.0s, T_trans = 5.0s, T_buffer = 2.0s)
    delta1 = controller.compute_trigger_delta(
        ev_eta_sec=30.0,
        predicted_clearance_sec=8.0,
        transition_time_sec=5.0,
        safety_buffer_sec=2.0,
    )
    assert delta1 == pytest.approx(15.0, abs=1e-3)
    assert delta1 > 0  # Should NOT actuate

    # Case 2: Exact boundary trigger condition
    delta2 = controller.compute_trigger_delta(
        ev_eta_sec=15.0,
        predicted_clearance_sec=8.0,
        transition_time_sec=5.0,
        safety_buffer_sec=2.0,
    )
    assert delta2 == pytest.approx(0.0, abs=1e-3)
    assert delta2 <= 0  # Boundary -> Must actuate

    # Case 3: Imminent arrival condition
    delta3 = controller.compute_trigger_delta(
        ev_eta_sec=10.0,
        predicted_clearance_sec=8.0,
        transition_time_sec=5.0,
        safety_buffer_sec=2.0,
    )
    assert delta3 == pytest.approx(-5.0, abs=1e-3)
    assert delta3 <= 0  # Urgent actuation


def test_transition_overhead_calculation(controller: PreclearanceController):
    """Verify phase transition overhead for all NEMA phases."""
    # Phase 0 (Arterial Green): 0.0s transition required
    assert controller.compute_transition_overhead(0) == 0.0

    # Phase 1 (Arterial Yellow, 1s elapsed out of 3s): (3 - 1) + 2 = 4.0s
    assert controller.compute_transition_overhead(1, phase_elapsed_sec=1.0) == pytest.approx(4.0)

    # Phase 2 (Arterial All-Red, 0.5s elapsed out of 2s): 2 - 0.5 = 1.5s
    assert controller.compute_transition_overhead(2, phase_elapsed_sec=0.5) == pytest.approx(1.5)

    # Phase 3 (Cross Green, just started with 2s elapsed):
    # Min green = 10s -> remaining min green = 8s + 3s yellow + 2s all-red = 13.0s
    assert controller.compute_transition_overhead(3, phase_elapsed_sec=2.0) == pytest.approx(13.0)

    # Phase 3 (Cross Green, well past min green with 15s elapsed):
    # Remaining min green = 0s -> 3s yellow + 2s all-red = 5.0s
    assert controller.compute_transition_overhead(3, phase_elapsed_sec=15.0) == pytest.approx(5.0)

    # Phase 4 (Cross Yellow, 1s elapsed): (3 - 1) + 2 = 4.0s
    assert controller.compute_transition_overhead(4, phase_elapsed_sec=1.0) == pytest.approx(4.0)

    # Phase 5 (Cross All-Red, 0.5s elapsed): 2 - 0.5 = 1.5s
    assert controller.compute_transition_overhead(5, phase_elapsed_sec=0.5) == pytest.approx(1.5)


def test_monitoring_state_when_mission_inactive(
    controller: PreclearanceController,
    nominal_traffic_state: ApproachTrafficState,
):
    """Verify controller stays in MONITORING and outputs nominal plan when no active mission."""
    # Subtest 1: None mission
    dec1 = controller.evaluate_node(
        node_id="node_a",
        mission=None,
        approach_state=nominal_traffic_state,
        sim_time=10.0,
    )
    assert dec1.state == PreclearanceState.MONITORING
    assert dec1.should_actuate is False
    assert dec1.commanded_phase == controller.get_nominal_phase(10.0)

    # Subtest 2: Inactive mission (COMPLETED)
    inactive_mission = EmergencyMission(
        mission_id="mission_done",
        vehicle_id="AMB-339",
        status=MissionStatus.COMPLETED,
    )
    dec2 = controller.evaluate_node(
        node_id="node_a",
        mission=inactive_mission,
        approach_state=nominal_traffic_state,
        sim_time=10.0,
    )
    assert dec2.state == PreclearanceState.MONITORING
    assert dec2.should_actuate is False


def test_jit_non_premature_actuation(
    controller: PreclearanceController,
    nominal_traffic_state: ApproachTrafficState,
    active_mission: EmergencyMission,
):
    """Verify JIT actuation: Node A triggers while Node D remains ARMED without premature green hold."""
    # Active mission at corridor entry x = -200.0m
    # Stopline A is at x = 0.0m (dist = 200m)
    # Stopline D is at x = 900.0m (dist = 1100m)
    sim_time = 45.0  # Nominally Cross Green (Phase 3)

    corridor_plan = controller.evaluate_corridor(
        mission=active_mission,
        traffic_states={
            "node_a": nominal_traffic_state,
            "node_b": nominal_traffic_state,
            "node_c": nominal_traffic_state,
            "node_d": nominal_traffic_state,
        },
        sim_time=sim_time,
    )

    dec_a = corridor_plan.decisions["node_a"]
    dec_d = corridor_plan.decisions["node_d"]

    # Node A is 200m away -> ETA ~11s. With queue clearance ~8s + trans ~5s + buf ~2s = 15s.
    # Delta trigger = 11 - 15 = -4s <= 0 -> Node A MUST actuate!
    assert dec_a.should_actuate is True
    assert dec_a.state in (PreclearanceState.TRANSITIONING, PreclearanceState.HOLDING_GREEN)

    # Node D is 1100m away -> ETA ~60s.
    # Delta trigger = 60 - 15 = +45s > 0 -> Node D must NOT actuate prematurely!
    assert dec_d.should_actuate is False
    assert dec_d.state == PreclearanceState.ARMED
    assert dec_d.delta_trigger_sec > 30.0


def test_full_lifecycle_progression(
    controller: PreclearanceController,
    nominal_traffic_state: ApproachTrafficState,
):
    """Verify complete chronological progression through all state machine phases."""
    mission = EmergencyMission(
        mission_id="mission_amb_339",
        vehicle_id="AMB-339",
        status=MissionStatus.APPROACHING,
        current_position_m=-600.0,  # 600m before Node A stopline
        current_speed_mps=15.0,
        target_speed_mps=18.5,
    )

    # Stage 1: EV far away -> ARMED
    dec1 = controller.evaluate_node(
        node_id="node_a",
        mission=mission,
        approach_state=nominal_traffic_state,
        sim_time=0.0,
        current_signal_phase=3,
        phase_elapsed_sec=15.0,
    )
    assert dec1.state == PreclearanceState.ARMED
    assert dec1.should_actuate is False
    assert dec1.delta_trigger_sec > 0.0

    # Stage 2: EV advances closer (x = -150m) -> Triggers TRANSITIONING
    mission.current_position_m = -150.0
    dec2 = controller.evaluate_node(
        node_id="node_a",
        mission=mission,
        approach_state=nominal_traffic_state,
        sim_time=10.0,
        current_signal_phase=3,
        phase_elapsed_sec=25.0,
    )
    assert dec2.state == PreclearanceState.TRANSITIONING
    assert dec2.should_actuate is True
    assert dec2.commanded_phase == 4  # Cross Yellow

    # Stage 3: Step through yellow and all-red transition -> HOLDING_GREEN
    # 3.1s into transition: switches to all-red (phase 5)
    dec3 = controller.evaluate_node(
        node_id="node_a",
        mission=mission,
        approach_state=nominal_traffic_state,
        sim_time=13.5,
        current_signal_phase=4,
    )
    assert dec3.commanded_phase == 5  # Cross All-Red

    # 5.5s into transition: switches to Priority Arterial Green (phase 0)
    dec4 = controller.evaluate_node(
        node_id="node_a",
        mission=mission,
        approach_state=nominal_traffic_state,
        sim_time=16.0,
        current_signal_phase=5,
    )
    assert dec4.state == PreclearanceState.HOLDING_GREEN
    assert dec4.commanded_phase == 0  # Arterial Priority Green

    # Stage 4: EV enters passing zone (x = -30m, within 50m of stopline) -> EV_PASSING
    mission.current_position_m = -30.0
    dec5 = controller.evaluate_node(
        node_id="node_a",
        mission=mission,
        approach_state=nominal_traffic_state,
        sim_time=20.0,
    )
    assert dec5.state == PreclearanceState.EV_PASSING
    assert dec5.commanded_phase == 0

    # Stage 5: EV clears intersection (x = +20m, past stopline 0m + 15m exit) -> CLEARED
    mission.current_position_m = 20.0
    dec6 = controller.evaluate_node(
        node_id="node_a",
        mission=mission,
        approach_state=nominal_traffic_state,
        sim_time=23.0,
    )
    assert dec6.state == PreclearanceState.CLEARED
    assert dec6.should_actuate is False


def test_anti_starvation_watchdog_timeout(
    controller: PreclearanceController,
    nominal_traffic_state: ApproachTrafficState,
):
    """Verify maximum green hold watchdog trips if green hold exceeds ceiling (60s)."""
    mission = EmergencyMission(
        mission_id="mission_stalled",
        vehicle_id="AMB-339",
        status=MissionStatus.CORRIDOR_TRANSIT,
        current_position_m=-100.0,
        current_speed_mps=0.0,  # Vehicle stalled / stopped!
    )

    # Force controller into HOLDING_GREEN at sim_time = 0.0
    controller._node_states["node_a"] = PreclearanceState.HOLDING_GREEN
    controller._green_hold_start_time["node_a"] = 0.0

    # At sim_time = 30.0s (under 60s ceiling): still holding green
    dec_mid = controller.evaluate_node(
        node_id="node_a",
        mission=mission,
        approach_state=nominal_traffic_state,
        sim_time=30.0,
    )
    assert dec_mid.state == PreclearanceState.HOLDING_GREEN
    assert dec_mid.should_actuate is True

    # At sim_time = 65.0s (> 60s max hold): watchdog must trip and abort green hold!
    dec_timeout = controller.evaluate_node(
        node_id="node_a",
        mission=mission,
        approach_state=nominal_traffic_state,
        sim_time=65.0,
    )
    assert dec_timeout.state == PreclearanceState.MONITORING
    assert dec_timeout.should_actuate is False
    assert "Watchdog Tripped" in dec_timeout.reason


def test_multi_tier_clearance_fallback_integration(controller: PreclearanceController):
    """Verify controller gracefully handles None or corrupted traffic state using fallback."""
    mission = EmergencyMission(
        mission_id="mission_amb_339",
        vehicle_id="AMB-339",
        status=MissionStatus.APPROACHING,
        current_position_m=-100.0,
        current_speed_mps=15.0,
    )

    # Evaluate with approach_state = None -> Triggers Tier 2 Conservative Safe Default
    dec = controller.evaluate_node(
        node_id="node_a",
        mission=mission,
        approach_state=None,
        sim_time=50.0,
    )

    assert dec.fallback_used is True
    # Tier 2 safe default is 25.0s
    assert dec.predicted_clearance_sec == pytest.approx(25.0, abs=0.1)


def test_corridor_step_interface(
    controller: PreclearanceController,
    nominal_traffic_state: ApproachTrafficState,
    active_mission: EmergencyMission,
):
    """Verify simulation runner step() interface returns valid phase mapping for all nodes."""
    phases = controller.step(
        sim_time=25.0,
        mission=active_mission,
        traffic_states={"node_a": nominal_traffic_state},
        dt=0.1,
    )

    assert isinstance(phases, dict)
    assert set(phases.keys()) == {"node_a", "node_b", "node_c", "node_d"}
    for _nid, phase in phases.items():
        assert 0 <= phase <= 5


def test_realtime_execution_latency(
    controller: PreclearanceController,
    nominal_traffic_state: ApproachTrafficState,
    active_mission: EmergencyMission,
):
    """Verify sub-50ms SLA for full corridor coordination evaluation."""
    traffic_states = dict.fromkeys(["node_a", "node_b", "node_c", "node_d"], nominal_traffic_state)

    # Warmup
    controller.evaluate_corridor(active_mission, traffic_states, sim_time=10.0)

    # Benchmark 20 iterations
    latencies = []
    for i in range(20):
        t0 = time.perf_counter()
        controller.evaluate_corridor(active_mission, traffic_states, sim_time=10.0 + i)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency < 50.0, f"Corridor evaluation exceeded 50ms SLA: {avg_latency:.2f}ms"
