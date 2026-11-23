"""Automated Unit & Integration Test Suite for Moving-Horizon Corridor Coordinator (Task 39).

Verifies:
1. Moving-horizon spatial-temporal window gating (Nodes A & B in horizon, Nodes C & D outside).
2. Inter-node arrival offset calculations between successive intersections (A->B, B->C, C->D).
3. Queue spillback detection and pre-emptive downstream flushing activation.
4. Cascading green-wave progression as emergency vehicle transits from Node A to Node D.
5. Immediate tail clearance release (cleared nodes release hold; downstream nodes advance).
6. Corridor lifecycle states: STANDBY -> CORRIDOR_ARMED -> ACTIVE_GREEN_WAVE -> TRANSIT_IN_PROGRESS -> ALL_CLEARED.
7. Step simulation interface returning valid 4-intersection phase assignments.
8. Real-time latency benchmark (< 50.0 ms across 4 intersections).
"""

from __future__ import annotations

import time

import pytest

from ai.state.traffic_state_estimator import ApproachTrafficState
from controller.mission.emergency_mission import (
    CORRIDOR_ENTRY_X_METERS,
    EmergencyMission,
    EmergencyVehicleType,
    MissionStatus,
)
from controller.scheduler.corridor_coordinator import (
    CorridorCoordinationStatus,
    CorridorCoordinatorConfig,
    MovingHorizonCorridorCoordinator,
)
from controller.scheduler.preclearance_controller import PreclearanceState


@pytest.fixture
def coordinator_config() -> CorridorCoordinatorConfig:
    """Fixture providing standard corridor coordinator configuration."""
    return CorridorCoordinatorConfig(
        horizon_distance_m=750.0,
        horizon_time_sec=45.0,
        spillback_threshold_ratio=0.50,  # 150m on a 300m link
        max_spillback_advance_sec=12.0,
    )


@pytest.fixture
def coordinator(coordinator_config: CorridorCoordinatorConfig) -> MovingHorizonCorridorCoordinator:
    """Fixture providing initialized MovingHorizonCorridorCoordinator."""
    return MovingHorizonCorridorCoordinator(config=coordinator_config)


@pytest.fixture
def nominal_traffic_state() -> ApproachTrafficState:
    """Fixture providing nominal Eastbound approach traffic state."""
    return ApproachTrafficState(
        approach_id="EB",
        timestamp_sec=100.0,
        vehicle_count=15,
        counts_by_class={"car": 5, "motorcycle": 9, "bus": 1},
        motorcycle_ratio=9.0 / 15.0,
        queue_length_meters=30.0,
        queued_vehicle_count=10,
        approach_occupancy_ratio=0.35,
        traffic_density_vpm=15.0,
        mean_speed_kmh=14.0,
    )


@pytest.fixture
def spillback_traffic_state() -> ApproachTrafficState:
    """Fixture providing heavy queue traffic state exceeding 50% link length (180m > 150m)."""
    return ApproachTrafficState(
        approach_id="EB",
        timestamp_sec=100.0,
        vehicle_count=45,
        counts_by_class={"car": 25, "motorcycle": 15, "bus": 5},
        motorcycle_ratio=15.0 / 45.0,
        queue_length_meters=180.0,
        queued_vehicle_count=38,
        approach_occupancy_ratio=0.85,
        traffic_density_vpm=45.0,
        mean_speed_kmh=3.5,
    )


@pytest.fixture
def active_mission() -> EmergencyMission:
    """Fixture providing an active ambulance mission at corridor entry gate."""
    return EmergencyMission(
        mission_id="mission_amb_339",
        vehicle_id="AMB-339",
        vehicle_type=EmergencyVehicleType.AMBULANCE,
        status=MissionStatus.APPROACHING,
        current_position_m=CORRIDOR_ENTRY_X_METERS,  # x = -200.0m
        current_speed_mps=15.0,
        target_speed_mps=18.5,
    )


def test_standby_status_when_no_active_mission(
    coordinator: MovingHorizonCorridorCoordinator,
    nominal_traffic_state: ApproachTrafficState,
):
    """Verify coordinator remains in STANDBY with 0 active holds when no mission is running."""
    report = coordinator.update_corridor(
        mission=None,
        traffic_states={"node_a": nominal_traffic_state},
        sim_time=10.0,
    )

    assert report.corridor_status == CorridorCoordinationStatus.STANDBY
    assert report.total_active_holds == 0
    assert len(report.active_horizon_nodes) == 0
    assert len(report.cleared_nodes) == 0
    for sched in report.schedules.values():
        assert sched.state == PreclearanceState.MONITORING
        assert sched.in_moving_horizon is False


def test_moving_horizon_window_filtering(
    coordinator: MovingHorizonCorridorCoordinator,
    nominal_traffic_state: ApproachTrafficState,
    active_mission: EmergencyMission,
):
    """Verify nodes inside horizon (A: 200m, B: 500m) are coordinated, while C (800m) and D (1100m) are excluded."""
    # EV is at x = -200m. Horizon distance is 750m.
    # Node A stopline = 0m (distance = 200m <= 750m) -> IN
    # Node B stopline = 300m (distance = 500m <= 750m) -> IN
    # Node C stopline = 600m (distance = 800m > 750m) -> OUT
    # Node D stopline = 900m (distance = 1100m > 750m) -> OUT
    report = coordinator.update_corridor(
        mission=active_mission,
        traffic_states=dict.fromkeys(coordinator.intersections, nominal_traffic_state),
        sim_time=25.0,
    )

    assert "node_a" in report.active_horizon_nodes
    assert "node_b" in report.active_horizon_nodes
    assert "node_c" not in report.active_horizon_nodes
    assert "node_d" not in report.active_horizon_nodes

    # Verify Node C and D remain in nominal plan
    sched_c = report.schedules["node_c"]
    sched_d = report.schedules["node_d"]
    assert sched_c.in_moving_horizon is False
    assert sched_d.in_moving_horizon is False
    assert sched_c.state == PreclearanceState.MONITORING
    assert sched_d.state == PreclearanceState.MONITORING


def test_inter_node_offset_calculation(
    coordinator: MovingHorizonCorridorCoordinator,
    nominal_traffic_state: ApproachTrafficState,
    active_mission: EmergencyMission,
):
    """Verify calculated arrival offsets between successive corridor nodes."""
    report = coordinator.update_corridor(
        mission=active_mission,
        traffic_states=dict.fromkeys(coordinator.intersections, nominal_traffic_state),
        sim_time=10.0,
    )

    offsets = report.coordination_offsets_sec
    assert "node_a_to_node_b" in offsets
    assert "node_b_to_node_c" in offsets
    assert "node_c_to_node_d" in offsets

    # Each inter-node distance is 300m at ~18.5 m/s -> offset ~16.2 seconds
    for offset in offsets.values():
        assert 14.0 <= offset <= 20.0


def test_spillback_detection_and_preemptive_flushing(
    coordinator: MovingHorizonCorridorCoordinator,
    nominal_traffic_state: ApproachTrafficState,
    spillback_traffic_state: ApproachTrafficState,
    active_mission: EmergencyMission,
):
    """Verify spillback risk detection when downstream queue exceeds 50% link storage (180m > 150m)."""
    # Set Node B approach to heavy spillback queue
    traffic_states = {
        "node_a": nominal_traffic_state,
        "node_b": spillback_traffic_state,
        "node_c": nominal_traffic_state,
        "node_d": nominal_traffic_state,
    }

    report = coordinator.update_corridor(
        mission=active_mission,
        traffic_states=traffic_states,
        sim_time=15.0,
    )

    sched_b = report.schedules["node_b"]
    assert sched_b.spillback_risk is True
    assert sched_b.spillback_advance_sec > 0.0

    # Node A nominal queue should NOT flag spillback
    sched_a = report.schedules["node_a"]
    assert sched_a.spillback_risk is False

    # Check alert logged in report
    assert any("node_b" in alert for alert in report.spillback_alerts)


def test_cascading_wave_and_tail_clearance_progression(
    coordinator: MovingHorizonCorridorCoordinator,
    nominal_traffic_state: ApproachTrafficState,
):
    """Verify progression of EV through corridor: cleared nodes release green hold while wave advances."""
    mission = EmergencyMission(
        mission_id="mission_amb_339",
        vehicle_id="AMB-339",
        status=MissionStatus.CORRIDOR_TRANSIT,
        current_position_m=-50.0,
        current_speed_mps=18.5,
    )
    traffic_states = dict.fromkeys(coordinator.intersections, nominal_traffic_state)

    # Step 1: EV approaches Node A (x = -50m) -> Node A is in passing zone / holding green
    rep1 = coordinator.update_corridor(mission, traffic_states, sim_time=10.0)
    assert "node_a" not in rep1.cleared_nodes
    assert rep1.schedules["node_a"].state in (
        PreclearanceState.HOLDING_GREEN,
        PreclearanceState.EV_PASSING,
    )

    # Step 2: EV clears Node A and enters Link A->B (x = 25m > 0m + 15m exit)
    mission.current_position_m = 25.0
    rep2 = coordinator.update_corridor(mission, traffic_states, sim_time=14.0)
    assert "node_a" in rep2.cleared_nodes
    assert rep2.schedules["node_a"].has_cleared is True

    # Step 3: EV approaches Node B (x = 250m) -> Node B in passing zone
    mission.current_position_m = 260.0
    rep3 = coordinator.update_corridor(mission, traffic_states, sim_time=25.0)
    assert "node_b" not in rep3.cleared_nodes
    assert rep3.schedules["node_b"].state in (
        PreclearanceState.HOLDING_GREEN,
        PreclearanceState.EV_PASSING,
    )
    # Node C is now within 750m horizon (600m - 260m = 340m <= 750m)
    assert "node_c" in rep3.active_horizon_nodes

    # Step 4: EV clears all nodes (x = 925m > 900m + 15m) -> ALL_CLEARED
    mission.current_position_m = 925.0
    rep4 = coordinator.update_corridor(mission, traffic_states, sim_time=60.0)
    assert set(rep4.cleared_nodes) == {"node_a", "node_b", "node_c", "node_d"}
    assert rep4.corridor_status == CorridorCoordinationStatus.ALL_CLEARED


def test_corridor_step_runner_interface(
    coordinator: MovingHorizonCorridorCoordinator,
    nominal_traffic_state: ApproachTrafficState,
    active_mission: EmergencyMission,
):
    """Verify coordinator step() interface outputs valid phase mappings."""
    traffic_states = dict.fromkeys(coordinator.intersections, nominal_traffic_state)
    phases = coordinator.step(
        sim_time=20.0,
        mission=active_mission,
        traffic_states=traffic_states,
        dt=0.1,
    )

    assert isinstance(phases, dict)
    assert set(phases.keys()) == {"node_a", "node_b", "node_c", "node_d"}
    for phase in phases.values():
        assert 0 <= phase <= 5


def test_realtime_corridor_evaluation_latency(
    coordinator: MovingHorizonCorridorCoordinator,
    nominal_traffic_state: ApproachTrafficState,
    active_mission: EmergencyMission,
):
    """Verify sub-50ms real-time SLA for entire 4-node moving-horizon coordination loop."""
    traffic_states = dict.fromkeys(coordinator.intersections, nominal_traffic_state)

    # Warmup
    coordinator.update_corridor(active_mission, traffic_states, sim_time=10.0)

    # Benchmark 20 iterations
    latencies = []
    for i in range(20):
        t0 = time.perf_counter()
        coordinator.update_corridor(active_mission, traffic_states, sim_time=10.0 + i)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency < 50.0, (
        f"Moving-horizon corridor evaluation exceeded 50ms SLA: {avg_latency:.2f}ms"
    )
