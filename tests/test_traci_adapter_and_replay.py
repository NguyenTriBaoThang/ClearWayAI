"""
Automated Test Suite for Task 26: SUMO/TraCI Simulation Adapter, Telemetry Extraction & Replay
Verifies:
1. SimulationManager lifecycle operations (start, step, pause, resume, stop).
2. TelemetrySnapshotSchema compliance and provenance ("SUMO_SIMULATED").
3. Vehicle telemetry kinematics extraction (coordinates, heading, speed, class).
4. Signal phase state and approach timing extraction across intersections.
5. V2X hardware status and traffic analytics aggregation.
6. Emergency vehicle (AMB-339) mission tracking and pre-emption detection.
7. SnapshotExporter JSONL export and lossless round-trip deserialization.
8. ReplayController playback controls (play, pause, seek, step forward/backward, speed).
"""

import os

from apps.api.src.schemas import TelemetrySnapshotSchema
from simulation.traci.manager import SimulationManager
from simulation.traci.replay_controller import ReplayController
from simulation.traci.snapshot_exporter import SnapshotExporter
from simulation.traci.telemetry_collector import TelemetryCollector

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENARIOS_DIR = os.path.join(REPO_ROOT, "simulation", "scenarios")


def test_simulation_manager_lifecycle():
    """Verify SimulationManager start, step, pause, resume, and stop operations."""
    cfg_path = os.path.join(SCENARIOS_DIR, "corridor_peak_emergency.sumocfg")
    mgr = SimulationManager(config_path=cfg_path, step_length=0.1)

    assert not mgr.is_running()
    assert mgr.start() is True
    assert mgr.is_running()

    # Step forward 20 steps (2.0 seconds)
    for _ in range(20):
        snap = mgr.step(dt=0.1)

    assert abs(mgr.get_sim_time() - 2.0) < 0.05
    assert snap.sim_time_sec == round(mgr.get_sim_time(), 2)

    # Pause testing
    mgr.pause()
    assert mgr.is_paused()
    snap_paused = mgr.step(dt=0.1)
    assert snap_paused.sim_time_sec == snap.sim_time_sec

    # Resume testing
    mgr.resume()
    assert not mgr.is_paused()
    snap_resumed = mgr.step(dt=0.1)
    assert snap_resumed.sim_time_sec > snap_paused.sim_time_sec

    # Stop testing
    mgr.stop()
    assert not mgr.is_running()


def test_telemetry_snapshot_schema_compliance():
    """Verify that generated snapshots adhere strictly to TelemetrySnapshotSchema."""
    collector = TelemetryCollector(intersection_id="node_c")
    snap = collector.create_snapshot(
        sim_time_sec=15.5,
        vehicles=[],
        current_phase=0,
        avg_speed_kmh=45.0,
        avg_queue_m=12.0,
        occupancy_pct=28.0,
        is_preemption_active=False,
    )

    assert isinstance(snap, TelemetrySnapshotSchema)
    assert snap.provenance == "SUMO_SIMULATED"
    assert snap.sim_time_sec == 15.5
    assert snap.intersection_id == "node_c"

    # Signals validation
    assert snap.signals is not None
    assert snap.signals.provenance == "SUMO_SIMULATED"
    assert len(snap.signals.approaches) == 4
    assert snap.signals.current_phase_name == "Arterial EB/WB Green"

    # Hardware validation
    assert snap.hardware is not None
    assert snap.hardware.v2x_status == "Simulated"
    assert snap.hardware.rsu_online == 4

    # Analytics validation
    assert snap.analytics is not None
    assert snap.analytics.avg_speed_kmh == 45.0
    assert snap.analytics.occupancy_pct == 28.0


def test_vehicle_and_emergency_mission_extraction():
    """Verify vehicle telemetry kinematics and AMB-339 mission tracking."""
    collector = TelemetryCollector(intersection_id="node_c")

    # Regular motorcycle
    moto = collector.build_vehicle_telemetry(
        veh_id="moto_01",
        veh_type="motorcycle",
        x=250.0,
        y=0.0,
        speed_mps=12.5,
        heading_deg=90.0,
        lane_id="edge_a_to_b_0",
        is_emergency=False,
    )
    assert moto.vehicle_class == "motorcycle"
    assert moto.speed_kmh == 45.0
    assert moto.position_x == 250.0
    assert moto.heading_deg == 90.0
    assert moto.is_priority_vehicle is False

    # Emergency ambulance (AMB-339)
    amb = collector.build_vehicle_telemetry(
        veh_id="AMB-339",
        veh_type="emergency_ambulance",
        x=600.0,
        y=0.0,
        speed_mps=20.0,
        heading_deg=90.0,
        lane_id="edge_b_to_c_1",
        is_emergency=True,
        mission_id="mission-amb-339",
    )
    assert amb.vehicle_class == "ambulance"
    assert amb.is_priority_vehicle is True
    assert amb.mission_id == "mission-amb-339"

    # Snapshot with emergency ambulance
    snap = collector.create_snapshot(
        sim_time_sec=65.0,
        vehicles=[moto, amb],
        current_phase=0,
        amb_telemetry=amb,
        is_preemption_active=True,
    )
    assert snap.active_mission is not None
    assert snap.active_mission.vehicle_id == "AMB-339"
    assert snap.active_mission.status == "ACTIVE"
    assert snap.active_mission.eta_hospital_min > 0.0
    assert snap.signals.current_phase_name == "EMERGENCY PREEMPTION GREEN"


def test_snapshot_exporter_jsonl_roundtrip(tmp_path):
    """Verify SnapshotExporter exports to JSONL and deserializes losslessly."""
    collector = TelemetryCollector(intersection_id="node_c")
    snapshots = []
    for i in range(10):
        snap = collector.create_snapshot(
            sim_time_sec=float(i),
            vehicles=[],
            current_phase=i % 6,
        )
        snapshots.append(snap)

    out_file = tmp_path / "test_snapshots.jsonl"
    SnapshotExporter.export_jsonl(snapshots, out_file)
    assert out_file.is_file()

    # Load back
    loaded = SnapshotExporter.load_jsonl(out_file)
    assert len(loaded) == 10
    assert loaded[0].sim_time_sec == 0.0
    assert loaded[-1].sim_time_sec == 9.0
    assert loaded[5].signals.current_phase_name == snapshots[5].signals.current_phase_name

    # Summary
    summary = SnapshotExporter.compute_run_summary(loaded)
    assert summary["total_snapshots"] == 10
    assert summary["duration_seconds"] == 9.0


def test_replay_controller_playback_and_seeking(tmp_path):
    """Verify ReplayController seek, step, playback, and speed controls."""
    collector = TelemetryCollector(intersection_id="node_c")
    snapshots = [
        collector.create_snapshot(sim_time_sec=float(i) * 0.5, vehicles=[])
        for i in range(20)  # 0.0s to 9.5s
    ]

    out_file = tmp_path / "replay_test.jsonl"
    SnapshotExporter.export_jsonl(snapshots, out_file)

    controller = ReplayController(log_path=out_file)
    assert len(controller.snapshots) == 20
    assert controller.get_total_duration() == 9.5

    # Test seek
    s_seek = controller.seek(target_time_sec=4.0)
    assert s_seek is not None
    assert s_seek.sim_time_sec == 4.0

    # Test step forward and backward
    s_next = controller.step_forward()
    assert s_next.sim_time_sec == 4.5
    s_prev = controller.step_backward()
    assert s_prev.sim_time_sec == 4.0

    # Test playback
    controller.seek(0.0)
    controller.play()
    assert controller.is_playing
    controller.set_speed(2.0)  # 2.0x playback speed

    # Step with dt=0.5 -> advances by 0.5 * 2.0 = 1.0s
    s_played = controller.step(dt=0.5)
    assert s_played.sim_time_sec == 1.0
    assert controller.get_progress_pct() > 0.0

    controller.pause()
    assert not controller.is_playing
