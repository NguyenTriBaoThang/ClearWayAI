"""Automated Unit & Integration Test Suite for Emergency Mission & Multi-Node ETA (Task 37).

Verifies:
1. Emergency mission creation, parameters, and defaults.
2. Lifecycle state machine transitions (PENDING -> DISPATCHED -> APPROACHING -> CORRIDOR_TRANSIT -> ARRIVED).
3. Deterministic kinematic progression along the arterial corridor.
4. Multi-node ETA calculations to Nodes A, B, C, D, and Hospital.
5. Monotonic ETA reduction and traversed node detection (has_passed=True, ETA=0.0s).
6. Congestion drag and weather impact on travel durations.
7. Mission abort and completion operations.
8. Real-time sub-millisecond calculation latency (<= 2.0 ms).
"""

from __future__ import annotations

import time

import pytest

from controller.mission.emergency_mission import (
    CORRIDOR_ENTRY_X_METERS,
    HOSPITAL_X_METERS,
    EmergencyMissionManager,
    EmergencyVehicleType,
    MissionStatus,
)
from controller.mission.eta_estimator import (
    MultiNodeETAEvaluator,
    MultiNodeETAReport,
)


@pytest.fixture
def manager() -> EmergencyMissionManager:
    """Fixture providing a clean mission manager."""
    return EmergencyMissionManager()


@pytest.fixture
def evaluator() -> MultiNodeETAEvaluator:
    """Fixture providing a multi-node ETA evaluator."""
    return MultiNodeETAEvaluator()


def test_emergency_mission_creation(manager: EmergencyMissionManager):
    """Verify mission creation with default ambulance parameters."""
    mission = manager.create_mission(
        mission_id="mission_amb_339_test",
        vehicle_id="AMB-339",
        vehicle_type=EmergencyVehicleType.AMBULANCE,
        target_speed_mps=18.5,
    )

    assert mission.mission_id == "mission_amb_339_test"
    assert mission.vehicle_id == "AMB-339"
    assert mission.status == MissionStatus.PENDING
    assert mission.current_position_m == CORRIDOR_ENTRY_X_METERS
    assert mission.current_speed_mps == 0.0
    assert mission.is_active is False
    assert mission.progress_ratio == 0.0
    assert len(mission.route_nodes) == 4


def test_emergency_mission_lifecycle_and_telemetry(manager: EmergencyMissionManager):
    """Verify state machine progression from DISPATCHED to ARRIVED."""
    mission = manager.create_mission(mission_id="mission_amb_339_life")

    # 1. Dispatch
    manager.dispatch_mission(mission.mission_id)
    assert mission.status == MissionStatus.DISPATCHED
    assert mission.is_active is True
    assert manager.get_active_mission() is mission

    # 2. In Feeder Approach
    manager.update_telemetry(position_m=-120.0, speed_mps=15.0)
    assert mission.status == MissionStatus.DISPATCHED
    assert mission.current_position_m == -120.0
    assert mission.current_speed_kmh == 54.0

    # 3. Approaching Node A (within 60m)
    manager.update_telemetry(position_m=-45.0, speed_mps=18.0)
    assert mission.status == MissionStatus.APPROACHING

    # 4. Corridor Transit (past Node A)
    manager.update_telemetry(position_m=150.0, speed_mps=18.5, current_edge="edge_a_to_b")
    assert mission.status == MissionStatus.CORRIDOR_TRANSIT
    assert mission.current_edge == "edge_a_to_b"
    assert 0.20 < mission.progress_ratio < 0.35

    # 5. Arrived at Metropolitan Hospital
    manager.update_telemetry(position_m=HOSPITAL_X_METERS, speed_mps=0.0)
    assert mission.status == MissionStatus.ARRIVED
    assert mission.is_active is False
    assert mission.arrived_timestamp is not None
    assert manager.get_active_mission() is None


def test_emergency_mission_kinematic_progression(manager: EmergencyMissionManager):
    """Verify deterministic kinematic vehicle advancement along corridor."""
    mission = manager.create_mission(mission_id="mission_kinematics")
    manager.dispatch_mission(mission.mission_id)

    initial_pos = mission.current_position_m
    initial_v = mission.current_speed_mps

    # Step forward 10 seconds with 2.5 m/s^2 acceleration
    for _ in range(10):
        manager.advance_kinematics(dt_sec=1.0, acceleration_mps2=2.5)

    assert mission.current_position_m > initial_pos
    assert mission.current_speed_mps > initial_v
    assert mission.current_speed_mps <= mission.target_speed_mps
    assert mission.is_active is True


def test_emergency_mission_abort_and_complete(manager: EmergencyMissionManager):
    """Verify mission cancellation and manual completion."""
    # Abort test
    m_abort = manager.create_mission(mission_id="mission_to_abort")
    manager.dispatch_mission(m_abort.mission_id)
    assert manager.get_active_mission() is m_abort

    manager.abort_mission(m_abort.mission_id, reason="Corridor blocked by incident")
    assert m_abort.status == MissionStatus.ABORTED
    assert m_abort.abort_reason == "Corridor blocked by incident"
    assert m_abort.is_active is False
    assert manager.get_active_mission() is None

    # Complete test
    m_comp = manager.create_mission(mission_id="mission_to_complete")
    manager.dispatch_mission(m_comp.mission_id)
    manager.complete_mission(m_comp.mission_id)
    assert m_comp.status == MissionStatus.COMPLETED


def test_multi_node_eta_calculation_from_entry(
    evaluator: MultiNodeETAEvaluator,
    manager: EmergencyMissionManager,
):
    """Verify ETA values from West entry across Nodes A, B, C, D, and Hospital."""
    mission = manager.create_mission(mission_id="mission_eta_entry")
    manager.dispatch_mission(mission.mission_id)

    report: MultiNodeETAReport = evaluator.compute_multi_node_eta(mission)

    assert report.mission_id == mission.mission_id
    assert report.vehicle_id == mission.vehicle_id
    assert len(report.etas_by_node) == 5  # Node A, B, C, D, Hospital

    eta_a = report.etas_by_node["node_a"]
    eta_b = report.etas_by_node["node_b"]
    eta_c = report.etas_by_node["node_c"]
    eta_d = report.etas_by_node["node_d"]
    eta_hosp = report.etas_by_node["hospital"]

    # Distance ordering: Entry(-200) -> A(0: 200m) -> B(300: 500m) -> C(600: 800m) -> D(900: 1100m) -> Hosp(1100: 1300m)
    assert eta_a.distance_to_stopline_m == 200.0
    assert eta_b.distance_to_stopline_m == 500.0
    assert eta_c.distance_to_stopline_m == 800.0
    assert eta_d.distance_to_stopline_m == 1100.0
    assert eta_hosp.distance_to_stopline_m == 1300.0

    # Monotonic ETA progression
    assert 0.0 < eta_a.eta_seconds < eta_b.eta_seconds
    assert eta_b.eta_seconds < eta_c.eta_seconds
    assert eta_c.eta_seconds < eta_d.eta_seconds
    assert eta_d.eta_seconds < eta_hosp.eta_seconds

    # All nodes ahead
    for node_res in report.etas_by_node.values():
        assert node_res.has_passed is False
        assert node_res.confidence_score >= 0.60


def test_multi_node_eta_with_traversed_nodes(
    evaluator: MultiNodeETAEvaluator,
    manager: EmergencyMissionManager,
):
    """Verify that traversed nodes report has_passed=True and eta=0.0s."""
    mission = manager.create_mission(mission_id="mission_mid_corridor")
    manager.dispatch_mission(mission.mission_id)

    # Position vehicle at x = 450m (between Node B at 300m and Node C at 600m)
    manager.update_telemetry(position_m=450.0, speed_mps=18.5)

    report = evaluator.compute_multi_node_eta(mission)

    eta_a = report.etas_by_node["node_a"]
    eta_b = report.etas_by_node["node_b"]
    eta_c = report.etas_by_node["node_c"]
    eta_d = report.etas_by_node["node_d"]

    # Traversed nodes
    assert eta_a.has_passed is True
    assert eta_a.distance_to_stopline_m == 0.0
    assert eta_a.eta_seconds == 0.0

    assert eta_b.has_passed is True
    assert eta_b.distance_to_stopline_m == 0.0
    assert eta_b.eta_seconds == 0.0

    # Downstream nodes still ahead
    assert eta_c.has_passed is False
    assert eta_c.distance_to_stopline_m == 150.0  # 600 - 450
    assert eta_c.eta_seconds > 0.0

    assert eta_d.has_passed is False
    assert eta_d.distance_to_stopline_m == 450.0  # 900 - 450
    assert eta_d.eta_seconds > eta_c.eta_seconds


def test_traffic_congestion_drag_impact(
    evaluator: MultiNodeETAEvaluator,
    manager: EmergencyMissionManager,
):
    """Verify that high cross-street traffic occupancy adds drag to corridor ETA."""
    mission = manager.create_mission(mission_id="mission_drag_test")
    manager.dispatch_mission(mission.mission_id)
    manager.update_telemetry(position_m=-100.0, speed_mps=15.0)

    # Case 1: Low occupancy (pre-cleared green wave)
    report_low = evaluator.compute_multi_node_eta(
        mission,
        approach_occupancies={"node_a": 0.15, "node_b": 0.15, "node_c": 0.15, "node_d": 0.15},
    )

    # Case 2: Severe queue congestion (un-cleared traffic)
    report_high = evaluator.compute_multi_node_eta(
        mission,
        approach_occupancies={"node_a": 0.85, "node_b": 0.85, "node_c": 0.85, "node_d": 0.85},
    )

    eta_d_low = report_low.etas_by_node["node_d"].eta_seconds
    eta_d_high = report_high.etas_by_node["node_d"].eta_seconds

    assert eta_d_high > eta_d_low
    assert report_high.hospital_eta_sec > report_low.hospital_eta_sec


def test_weather_friction_impact(
    evaluator: MultiNodeETAEvaluator,
    manager: EmergencyMissionManager,
):
    """Verify that inclement weather (rain) increases transit ETA."""
    mission = manager.create_mission(mission_id="mission_weather_test")
    manager.dispatch_mission(mission.mission_id)

    report_clear = evaluator.compute_multi_node_eta(mission, weather="clear")
    report_rain = evaluator.compute_multi_node_eta(mission, weather="rain")

    assert report_rain.hospital_eta_sec > report_clear.hospital_eta_sec


def test_eta_estimator_real_time_latency(
    evaluator: MultiNodeETAEvaluator,
    manager: EmergencyMissionManager,
):
    """Verify that computing multi-node ETA executes in under 2.0 ms."""
    mission = manager.create_mission(mission_id="mission_perf_test")
    manager.dispatch_mission(mission.mission_id)

    # Warm-up
    _ = evaluator.compute_multi_node_eta(mission)

    latencies: list[float] = []
    for _ in range(100):
        t0 = time.perf_counter()
        _ = evaluator.compute_multi_node_eta(mission)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    median_lat = float(sorted(latencies)[len(latencies) // 2])
    assert median_lat < 2.0, f"Median ETA latency {median_lat:.3f}ms exceeds 2.0ms budget"


def test_mission_and_eta_dict_serialization(
    evaluator: MultiNodeETAEvaluator,
    manager: EmergencyMissionManager,
):
    """Verify JSON dictionary export contract."""
    mission = manager.create_mission(mission_id="mission_serial_test")
    manager.dispatch_mission(mission.mission_id)
    manager.update_telemetry(position_m=100.0, speed_mps=18.5)

    m_dict = mission.to_dict()
    assert m_dict["mission_id"] == "mission_serial_test"
    assert m_dict["status"] == "CORRIDOR_TRANSIT"
    assert m_dict["is_active"] is True
    assert "current_speed_kmh" in m_dict

    report = evaluator.compute_multi_node_eta(mission)
    r_dict = report.to_dict()
    assert r_dict["mission_id"] == "mission_serial_test"
    assert "etas_by_node" in r_dict
    assert "node_a" in r_dict["etas_by_node"]
    assert r_dict["etas_by_node"]["node_a"]["has_passed"] is True
    assert r_dict["etas_by_node"]["node_d"]["has_passed"] is False
