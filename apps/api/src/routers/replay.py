"""Simulation Telemetry Replay & Historical Snapshot Endpoints (`apps.api.src.routers.replay`).

Integrates `simulation.traci.replay_controller.ReplayController` with the SQLite persistence layer
and WebSocket broadcaster for deterministic historical playback, frame seeking, variable speed,
and snapshot inspection.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from apps.api.src.database import db
from apps.api.src.schemas import (
    ReplayLoadRequest,
    ReplayLoadResponse,
    ReplaySeekRequest,
    ReplaySeekResponse,
    ReplaySpeedRequest,
    ReplayStatusResponse,
    ReplayStepRequest,
    ReplayStepResponse,
    SnapshotItemSchema,
    SnapshotListResponse,
    TelemetrySnapshotSchema,
)
from apps.api.src.websocket import ws_manager
from simulation.traci.manager import SimulationManager
from simulation.traci.replay_controller import ReplayController
from simulation.traci.snapshot_exporter import SnapshotExporter

router = APIRouter(prefix="/api/v1/simulations", tags=["Replay & Snapshots"])

# In-memory ReplayController instances keyed by simulation_id
_active_replays: dict[str, ReplayController] = {}


def _get_active_replay_or_404(simulation_id: str) -> ReplayController:
    """Helper to retrieve loaded ReplayController or raise HTTP 404."""
    controller = _active_replays.get(simulation_id)
    if controller is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Replay controller not loaded for simulation '{simulation_id}'. Call /replay/load first.",
        )
    return controller


@router.post(
    "/{simulation_id}/replay/load",
    response_model=ReplayLoadResponse,
    status_code=status.HTTP_200_OK,
)
def load_replay(
    simulation_id: str,
    req: ReplayLoadRequest,
) -> ReplayLoadResponse:
    """Load recorded snapshots into the in-memory ReplayController."""
    sim_record = db.get_simulation(simulation_id)
    if not sim_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found.",
        )

    snapshots: list[TelemetrySnapshotSchema] = []

    # 1. Try loading from database snapshots table
    db_records = db.get_snapshots(
        simulation_id=simulation_id,
        start_time=req.start_time,
        end_time=req.end_time,
        limit=req.limit,
    )
    if db_records:
        for rec in db_records:
            try:
                snap_dict = json.loads(rec.snapshot_json)
                snapshots.append(TelemetrySnapshotSchema.model_validate(snap_dict))
            except Exception:
                continue

    # 2. If no DB snapshots and file path provided, load JSONL file
    if not snapshots and req.log_path:
        path = Path(req.log_path)
        if path.exists():
            snapshots = SnapshotExporter.load_jsonl(path)

    # 3. If still empty, generate synthetic demo baseline snapshots for playback testing
    if not snapshots:
        runner = SimulationManager(step_length=0.1)
        runner.start()
        for _ in range(10):
            snap = runner.step(dt=0.1)
            snapshots.append(snap)
            # Also persist generated baseline to DB
            db.save_snapshot(
                simulation_id=simulation_id,
                sim_time_sec=snap.sim_time_sec,
                timestamp=snap.timestamp.isoformat(),
                active_vehicles_count=len(snap.vehicles),
                current_phase=snap.signals.approaches[0].split_pct
                if snap.signals and snap.signals.approaches
                else 0,
                emergency_active=snap.active_mission is not None,
                snapshot_json=snap.model_dump_json(),
            )

    controller = ReplayController()
    controller.load_snapshots(snapshots)
    _active_replays[simulation_id] = controller

    start_sec = snapshots[0].sim_time_sec if snapshots else 0.0
    end_sec = snapshots[-1].sim_time_sec if snapshots else 0.0
    duration_sec = round(end_sec - start_sec, 2)

    return ReplayLoadResponse(
        simulation_id=simulation_id,
        snapshot_count=len(snapshots),
        duration_sec=duration_sec,
        start_time_sec=round(start_sec, 2),
        end_time_sec=round(end_sec, 2),
        status="LOADED",
    )


@router.post("/{simulation_id}/replay/play", response_model=ReplayStatusResponse)
def play_replay(simulation_id: str) -> ReplayStatusResponse:
    """Start continuous replay playback."""
    controller = _get_active_replay_or_404(simulation_id)
    controller.play()

    return ReplayStatusResponse(
        simulation_id=simulation_id,
        is_playing=controller.is_playing,
        playback_speed=controller.playback_speed,
        current_time_sec=round(controller.current_time, 2),
        current_index=controller.current_index,
        total_snapshots=len(controller.snapshots),
    )


@router.post("/{simulation_id}/replay/pause", response_model=ReplayStatusResponse)
def pause_replay(simulation_id: str) -> ReplayStatusResponse:
    """Pause replay playback."""
    controller = _get_active_replay_or_404(simulation_id)
    controller.pause()

    return ReplayStatusResponse(
        simulation_id=simulation_id,
        is_playing=controller.is_playing,
        playback_speed=controller.playback_speed,
        current_time_sec=round(controller.current_time, 2),
        current_index=controller.current_index,
        total_snapshots=len(controller.snapshots),
    )


@router.post("/{simulation_id}/replay/seek", response_model=ReplaySeekResponse)
def seek_replay(simulation_id: str, req: ReplaySeekRequest) -> ReplaySeekResponse:
    """Seek to target simulation timestamp in replay buffer."""
    controller = _get_active_replay_or_404(simulation_id)
    snapshot = controller.seek(req.target_time_sec)

    if snapshot:
        ws_manager.broadcast_snapshot_sync(simulation_id, snapshot)

    return ReplaySeekResponse(
        simulation_id=simulation_id,
        current_time_sec=round(controller.current_time, 2),
        current_index=controller.current_index,
        total_snapshots=len(controller.snapshots),
        snapshot=snapshot,
    )


@router.post("/{simulation_id}/replay/speed", response_model=ReplayStatusResponse)
def set_replay_speed(simulation_id: str, req: ReplaySpeedRequest) -> ReplayStatusResponse:
    """Set playback speed multiplier (e.g. 0.5x, 1.0x, 2.0x, 4.0x)."""
    controller = _get_active_replay_or_404(simulation_id)
    controller.set_speed(req.speed_multiplier)

    return ReplayStatusResponse(
        simulation_id=simulation_id,
        is_playing=controller.is_playing,
        playback_speed=controller.playback_speed,
        current_time_sec=round(controller.current_time, 2),
        current_index=controller.current_index,
        total_snapshots=len(controller.snapshots),
    )


@router.post("/{simulation_id}/replay/step", response_model=ReplayStepResponse)
def step_replay(simulation_id: str, req: ReplayStepRequest) -> ReplayStepResponse:
    """Advance replay playback by dt seconds."""
    controller = _get_active_replay_or_404(simulation_id)
    # If not playing, temporarily enable stepping
    was_playing = controller.is_playing
    controller.is_playing = True
    snapshot = controller.step(dt=req.dt)
    controller.is_playing = was_playing

    if snapshot:
        ws_manager.broadcast_snapshot_sync(simulation_id, snapshot)

    return ReplayStepResponse(
        simulation_id=simulation_id,
        current_time_sec=round(controller.current_time, 2),
        current_index=controller.current_index,
        is_playing=controller.is_playing,
        snapshot=snapshot,
    )


@router.get("/{simulation_id}/replay/status", response_model=ReplayStatusResponse)
def get_replay_status(simulation_id: str) -> ReplayStatusResponse:
    """Retrieve playback status and timeline position of replay controller."""
    controller = _get_active_replay_or_404(simulation_id)

    return ReplayStatusResponse(
        simulation_id=simulation_id,
        is_playing=controller.is_playing,
        playback_speed=controller.playback_speed,
        current_time_sec=round(controller.current_time, 2),
        current_index=controller.current_index,
        total_snapshots=len(controller.snapshots),
    )


@router.get("/{simulation_id}/snapshots", response_model=SnapshotListResponse)
def list_snapshots(
    simulation_id: str,
    start_time: float | None = None,
    end_time: float | None = None,
    limit: int = 100,
) -> SnapshotListResponse:
    """Query persisted simulation snapshots from SQLite database."""
    sim_record = db.get_simulation(simulation_id)
    if not sim_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found.",
        )

    # Sanitize parameters if called directly in pure Python or via FastAPI
    st = float(start_time) if isinstance(start_time, (int, float)) else None
    et = float(end_time) if isinstance(end_time, (int, float)) else None
    lim = int(limit) if isinstance(limit, int) and not isinstance(limit, bool) else 100

    records = db.get_snapshots(
        simulation_id=simulation_id,
        start_time=st,
        end_time=et,
        limit=lim,
    )
    total_count = db.count_snapshots(simulation_id)

    items = [
        SnapshotItemSchema(
            id=r.id,
            simulation_id=r.simulation_id,
            sim_time_sec=round(r.sim_time_sec, 2),
            timestamp=r.timestamp,
            active_vehicles_count=r.active_vehicles_count,
            current_phase=r.current_phase,
            emergency_active=r.emergency_active,
        )
        for r in records
    ]

    return SnapshotListResponse(
        simulation_id=simulation_id,
        total_count=total_count,
        returned_count=len(items),
        snapshots=items,
    )
