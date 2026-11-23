"""Simulation Lifecycle & Step Execution Endpoints (`apps.api.src.routers.simulations`)."""

from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, HTTPException, status

from apps.api.src.database import SimulationRecord, db
from apps.api.src.schemas import (
    SimulationCreateRequest,
    SimulationResponse,
    SimulationStepRequest,
    SimulationStepResponse,
)
from simulation.traci.manager import SimulationManager

router = APIRouter(prefix="/api/v1/simulations", tags=["Simulations"])

# Active in-memory simulation runner instances
_active_runners: dict[str, SimulationManager] = {}


@router.post("", response_model=SimulationResponse, status_code=status.HTTP_201_CREATED)
def create_simulation(req: SimulationCreateRequest) -> SimulationResponse:
    """Instantiate and start a new corridor simulation episode."""
    sim_id = f"sim-{uuid.uuid4().hex[:8]}"
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Initialize simulation manager
    runner = SimulationManager(
        step_length=0.1,
    )
    runner.start()
    _active_runners[sim_id] = runner

    record = SimulationRecord(
        simulation_id=sim_id,
        name=req.name,
        scenario_id=req.scenario_id,
        status="RUNNING",
        started_at=now_iso,
        total_steps=0,
        emergency_events=0,
    )
    db.create_simulation(record)

    return SimulationResponse(
        simulation_id=record.simulation_id,
        name=record.name,
        scenario_id=record.scenario_id,
        status=record.status,
        started_at=record.started_at,
        stopped_at=record.stopped_at,
        total_steps=record.total_steps,
        emergency_events=record.emergency_events,
        metadata={"engine": "SyntheticCorridorEngine"},
    )


@router.get("", response_model=list[SimulationResponse])
def list_simulations() -> list[SimulationResponse]:
    """Retrieve history of all instantiated simulation episodes."""
    records = db.list_simulations()
    return [
        SimulationResponse(
            simulation_id=r.simulation_id,
            name=r.name,
            scenario_id=r.scenario_id,
            status=r.status,
            started_at=r.started_at,
            stopped_at=r.stopped_at,
            total_steps=r.total_steps,
            emergency_events=r.emergency_events,
            metadata=r.to_dict().get("metadata", {}),
        )
        for r in records
    ]


@router.get("/{simulation_id}", response_model=SimulationResponse)
def get_simulation(simulation_id: str) -> SimulationResponse:
    """Retrieve details and runtime metrics for a specific simulation episode."""
    record = db.get_simulation(simulation_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found.",
        )
    return SimulationResponse(
        simulation_id=record.simulation_id,
        name=record.name,
        scenario_id=record.scenario_id,
        status=record.status,
        started_at=record.started_at,
        stopped_at=record.stopped_at,
        total_steps=record.total_steps,
        emergency_events=record.emergency_events,
        metadata=record.to_dict().get("metadata", {}),
    )


@router.post("/{simulation_id}/step", response_model=SimulationStepResponse)
def step_simulation(
    simulation_id: str,
    req: SimulationStepRequest,
) -> SimulationStepResponse:
    """Advance simulation episode by dt seconds."""
    record = db.get_simulation(simulation_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found.",
        )

    runner = _active_runners.get(simulation_id)
    if not runner:
        # Re-attach or start runner if stopped
        runner = SimulationManager(
            step_length=req.dt,
        )
        runner.start()
        _active_runners[simulation_id] = runner

    # Advance step
    runner.step(dt=req.dt)
    sim_time = runner.get_sim_time()
    active_count = len(runner.engine.active_vehicles) if runner.engine else 0
    curr_phase = runner.engine.current_phase if runner.engine else 0
    lights: dict[str, int] = {
        nid: curr_phase for nid in ["node_a", "node_b", "node_c", "node_d"]
    }

    # Update database step counter
    new_step_count = record.total_steps + 1
    db.update_simulation_step(simulation_id, new_step_count)

    return SimulationStepResponse(
        simulation_id=simulation_id,
        sim_time_sec=round(sim_time, 2),
        total_steps=new_step_count,
        active_vehicles_count=active_count,
        traffic_lights=lights,
        emergency_vehicle_active=req.active_mission_id is not None,
        status="RUNNING",
    )


@router.post("/{simulation_id}/stop", response_model=SimulationResponse)
def stop_simulation(simulation_id: str) -> SimulationResponse:
    """Halt and finalize a simulation episode."""
    record = db.get_simulation(simulation_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{simulation_id}' not found.",
        )

    runner = _active_runners.pop(simulation_id, None)
    if runner:
        runner.stop()

    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    db.stop_simulation(simulation_id, now_iso)
    record.status = "STOPPED"
    record.stopped_at = now_iso

    return SimulationResponse(
        simulation_id=record.simulation_id,
        name=record.name,
        scenario_id=record.scenario_id,
        status=record.status,
        started_at=record.started_at,
        stopped_at=record.stopped_at,
        total_steps=record.total_steps,
        emergency_events=record.emergency_events,
    )
