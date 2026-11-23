"""Comprehensive Test Suite for ClearWayAI Real-time WebSocket Stream, Snapshots & Replay (Task 43).

Verifies:
1. WebSocketManager connection tracking, channel segregation, and graceful disconnect.
2. Subscription filtering by node_id and vehicle_id.
3. Bidirectional client message dispatch (ping, subscribe, control actions, errors).
4. Snapshot and event broadcasting to multiple subscribers and global channels.
5. Snapshot persistence in SQLite database and query endpoints with time window filters.
6. ReplayController lifecycle API (load, play, pause, seek, speed, step, status).
7. Error and boundary handling (404 for uninstantiated simulations or uninitialized replay buffers).
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import HTTPException

from apps.api.src.database import DatabaseManager
from apps.api.src.routers import replay, simulations
from apps.api.src.schemas import (
    ReplayLoadRequest,
    ReplaySeekRequest,
    ReplaySpeedRequest,
    ReplayStepRequest,
    SimulationCreateRequest,
    SimulationStepRequest,
)
from apps.api.src.websocket import WebSocketManager


class MockWebSocket:
    """Mock FastAPI/Starlette WebSocket for fast in-memory testing."""

    def __init__(self) -> None:
        self.accepted = False
        self.sent_messages: list[dict[str, Any]] = []
        self.closed = False
        self.fail_on_send = False

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, data: dict[str, Any]) -> None:
        if self.fail_on_send:
            raise RuntimeError("Connection broken")
        self.sent_messages.append(data)

    async def close(self) -> None:
        self.closed = True


def run_coro_sync(coro: Any) -> Any:
    """Drive a coroutine to completion synchronously without creating socket pairs."""
    stack = [coro]
    result = None
    exc = None
    while stack:
        curr = stack[-1]
        try:
            if exc is not None:
                err = exc
                exc = None
                val = curr.throw(err)
            else:
                val = curr.send(result)
            if hasattr(val, "send"):
                stack.append(val)
                result = None
            else:
                result = val
        except StopIteration as e:
            stack.pop()
            result = e.value
        except BaseException as e:
            stack.pop()
            exc = e
            if not stack:
                raise
    return result


@pytest.fixture(autouse=True)
def setup_isolated_db(tmp_path):
    """Provide isolated SQLite database for each test run."""
    from apps.api.src import database

    temp_db_path = tmp_path / "test_websocket_replay.db"
    test_db = DatabaseManager(db_path=temp_db_path)

    orig_db = database.db
    database.db = test_db
    simulations.db = test_db
    replay.db = test_db

    # Clean active runners & replay controllers
    simulations._active_runners.clear()
    replay._active_replays.clear()

    yield test_db

    database.db = orig_db
    simulations.db = orig_db
    replay.db = orig_db


# --- WebSocket Manager Unit Tests ---


def test_websocket_manager_connect_and_disconnect() -> None:
    """Verify WebSocket connection registration, channel counts, and cleanup."""

    async def _run():
        mgr = WebSocketManager()
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()

        assert mgr.total_connections == 0

        # Connect ws1 to channel "sim-001" and ws2 to channel "global"
        await mgr.connect(ws1, channel="sim-001")
        await mgr.connect(ws2, channel="global")

        assert ws1.accepted
        assert ws2.accepted
        assert mgr.total_connections == 2
        assert mgr.get_channel_count("sim-001") == 1
        assert mgr.get_channel_count("global") == 1

        # Disconnect ws1
        await mgr.disconnect(ws1, channel="sim-001")
        assert mgr.total_connections == 1
        assert mgr.get_channel_count("sim-001") == 0

        # Disconnect ws2
        await mgr.disconnect(ws2, channel="global")
        assert mgr.total_connections == 0

    run_coro_sync(_run())


def test_websocket_manager_subscription_filtering() -> None:
    """Verify subscription filtering by node_id and vehicle_id."""

    async def _run():
        mgr = WebSocketManager()
        ws_all = MockWebSocket()
        ws_node_b = MockWebSocket()
        ws_amb = MockWebSocket()

        await mgr.connect(ws_all, channel="sim-test")
        await mgr.connect(ws_node_b, channel="sim-test")
        await mgr.connect(ws_amb, channel="sim-test")

        # Set client filters
        mgr.set_filter(ws_node_b, {"node_id": "node_b"})
        mgr.set_filter(ws_amb, {"vehicle_id": "AMB-339"})

        # Message matching node_a and regular car
        msg_a = {
            "event": "snapshot",
            "data": {
                "intersection_id": "node_a",
                "vehicles": [{"vehicle_id": "car-1", "speed_kmh": 35.0}],
            },
        }
        sent = await mgr.broadcast_json("sim-test", msg_a)
        assert sent == 1  # only ws_all
        assert len(ws_all.sent_messages) == 1
        assert len(ws_node_b.sent_messages) == 0
        assert len(ws_amb.sent_messages) == 0

        # Message matching node_b and AMB-339
        msg_b = {
            "event": "snapshot",
            "data": {
                "intersection_id": "node_b",
                "vehicles": [{"vehicle_id": "AMB-339", "speed_kmh": 65.0}],
            },
        }
        sent = await mgr.broadcast_json("sim-test", msg_b)
        assert sent == 3  # ws_all, ws_node_b, ws_amb
        assert len(ws_all.sent_messages) == 2
        assert len(ws_node_b.sent_messages) == 1
        assert len(ws_amb.sent_messages) == 1

    run_coro_sync(_run())


def test_websocket_manager_client_command_dispatch() -> None:
    """Verify dispatching of incoming client commands (ping, subscribe, actions, errors)."""

    async def _run():
        mgr = WebSocketManager()
        ws = MockWebSocket()
        await mgr.connect(ws, channel="sim-cmd")

        # 1. Ping
        pong = await mgr.handle_client_message(ws, "sim-cmd", {"action": "ping"})
        assert pong["event"] == "pong"
        assert pong["simulation_id"] == "sim-cmd"
        assert "timestamp" in pong

        # 2. Subscribe filter
        sub_reply = await mgr.handle_client_message(
            ws, "sim-cmd", {"action": "subscribe", "filter": {"node_id": "node_c"}}
        )
        assert sub_reply["event"] == "subscribed"
        assert sub_reply["filter"] == {"node_id": "node_c"}
        assert mgr.get_filter(ws) == {"node_id": "node_c"}

        # 3. Control commands
        for action in ("pause", "resume", "play", "step", "seek", "speed"):
            ack = await mgr.handle_client_message(ws, "sim-cmd", {"action": action, "dt": 0.2})
            assert ack["event"] == f"command_ack_{action}"

        # 4. Unknown action
        err = await mgr.handle_client_message(ws, "sim-cmd", {"action": "invalid_command"})
        assert err["event"] == "error"
        assert "Unsupported action" in err["message"]

    run_coro_sync(_run())


def test_websocket_broadcast_and_dead_connection_cleanup() -> None:
    """Verify snapshot and event broadcast to multiple subscribers, including dead socket pruning."""

    async def _run():
        mgr = WebSocketManager()
        ws_healthy = MockWebSocket()
        ws_broken = MockWebSocket()
        ws_broken.fail_on_send = True

        await mgr.connect(ws_healthy, channel="sim-multi")
        await mgr.connect(ws_broken, channel="sim-multi")
        assert mgr.get_channel_count("sim-multi") == 2

        # Broadcast event
        sent = await mgr.broadcast_event(
            simulation_id="sim-multi",
            event_name="PREEMPTION_TRIGGERED",
            payload={"node_id": "node_b", "green_hold_sec": 12.0},
        )

        # ws_healthy receives event, ws_broken fails and is pruned
        assert sent == 1
        assert len(ws_healthy.sent_messages) == 1
        assert ws_healthy.sent_messages[0]["event"] == "PREEMPTION_TRIGGERED"
        assert mgr.get_channel_count("sim-multi") == 1

    run_coro_sync(_run())


# --- Historical Snapshots & Database Persistence Tests ---


def test_simulation_step_persists_snapshots_and_queries() -> None:
    """Verify that stepping a simulation persists snapshots to SQLite and can be queried."""
    # 1. Create Simulation
    create_req = SimulationCreateRequest(
        name="Snapshot Stream Verification",
        scenario_id="normal",
        use_synthetic_engine=True,
    )
    sim = simulations.create_simulation(create_req)
    sim_id = sim.simulation_id

    # 2. Advance several steps
    step_req = SimulationStepRequest(dt=0.1)
    for _ in range(5):
        simulations.step_simulation(sim_id, step_req)

    # 3. Query snapshots via replay router
    snapshot_resp = replay.list_snapshots(simulation_id=sim_id, limit=50)
    assert snapshot_resp.simulation_id == sim_id
    assert snapshot_resp.total_count == 5
    assert snapshot_resp.returned_count == 5
    assert len(snapshot_resp.snapshots) == 5

    # Check order and fields
    first_snap = snapshot_resp.snapshots[0]
    last_snap = snapshot_resp.snapshots[-1]
    assert first_snap.sim_time_sec <= last_snap.sim_time_sec
    assert first_snap.simulation_id == sim_id

    # 4. Test query with time window filter
    filtered = replay.list_snapshots(
        simulation_id=sim_id,
        start_time=first_snap.sim_time_sec,
        end_time=first_snap.sim_time_sec + 0.15,
        limit=2,
    )
    assert filtered.returned_count <= 2


def test_snapshots_query_non_existent_simulation() -> None:
    """Verify 404 error when querying snapshots for non-existent simulation."""
    with pytest.raises(HTTPException) as exc_info:
        replay.list_snapshots(simulation_id="sim-does-not-exist")
    assert exc_info.value.status_code == 404


# --- Replay Controller REST Endpoints Tests ---


def test_replay_controller_lifecycle() -> None:
    """Verify loading, play, pause, seek, set_speed, step, and status in ReplayController."""
    # 1. Create Simulation
    create_req = SimulationCreateRequest(
        name="Replay Test Scenario",
        scenario_id="normal",
        use_synthetic_engine=True,
    )
    sim = simulations.create_simulation(create_req)
    sim_id = sim.simulation_id

    # 2. Stepping to generate initial snapshots
    step_req = SimulationStepRequest(dt=0.1)
    for _ in range(6):
        simulations.step_simulation(sim_id, step_req)

    # 3. Load Replay Controller
    load_req = ReplayLoadRequest(limit=100)
    load_resp = replay.load_replay(sim_id, load_req)
    assert load_resp.simulation_id == sim_id
    assert load_resp.snapshot_count == 6
    assert load_resp.status == "LOADED"
    assert load_resp.duration_sec >= 0.0

    # 4. Check initial Replay Status
    status_resp = replay.get_replay_status(sim_id)
    assert status_resp.simulation_id == sim_id
    assert status_resp.is_playing is False
    assert status_resp.playback_speed == 1.0
    assert status_resp.current_index == 0
    assert status_resp.total_snapshots == 6

    # 5. Play Replay
    play_resp = replay.play_replay(sim_id)
    assert play_resp.is_playing is True

    # 6. Set Playback Speed (2.0x)
    speed_req = ReplaySpeedRequest(speed_multiplier=2.0)
    speed_resp = replay.set_replay_speed(sim_id, speed_req)
    assert speed_resp.playback_speed == 2.0

    # 7. Step Replay Forward
    step_r_req = ReplayStepRequest(dt=0.2)
    step_r_resp = replay.step_replay(sim_id, step_r_req)
    assert step_r_resp.simulation_id == sim_id
    assert step_r_resp.snapshot is not None
    assert step_r_resp.current_time_sec >= 0.2

    # 8. Pause Replay
    pause_resp = replay.pause_replay(sim_id)
    assert pause_resp.is_playing is False

    # 9. Seek Replay
    seek_req = ReplaySeekRequest(target_time_sec=0.1)
    seek_resp = replay.seek_replay(sim_id, seek_req)
    assert seek_resp.simulation_id == sim_id
    assert seek_resp.snapshot is not None
    assert seek_resp.current_time_sec == pytest.approx(0.1, abs=0.05)


def test_replay_unloaded_controller_raises_404() -> None:
    """Verify 404 when calling replay control endpoints before loading snapshots."""
    # Create simulation but do not call /replay/load
    sim = simulations.create_simulation(SimulationCreateRequest(name="Unloaded Test"))
    sim_id = sim.simulation_id

    with pytest.raises(HTTPException) as exc_info:
        replay.play_replay(sim_id)
    assert exc_info.value.status_code == 404
    assert "Call /replay/load first" in exc_info.value.detail

    with pytest.raises(HTTPException):
        replay.pause_replay(sim_id)

    with pytest.raises(HTTPException):
        replay.get_replay_status(sim_id)

    with pytest.raises(HTTPException):
        replay.seek_replay(sim_id, ReplaySeekRequest(target_time_sec=1.0))
