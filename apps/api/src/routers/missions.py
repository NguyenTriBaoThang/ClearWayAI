"""Emergency Mission Management & Corridor ETA Endpoints (`apps.api.src.routers.missions`)."""

from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, HTTPException, Query, status

from apps.api.src.database import MissionRecord, db
from apps.api.src.schemas import (
    MissionCreateRequest,
    MissionResponse,
    MultiNodeETAResponse,
    NodeETASchema,
)
from controller.mission.emergency_mission import (
    EmergencyMission,
    EmergencyMissionManager,
    EmergencyVehicleType,
    MissionStatus,
)
from controller.mission.eta_estimator import MultiNodeETAEvaluator

router = APIRouter(prefix="/api/v1/missions", tags=["Missions"])

# Global singleton mission manager & ETA evaluator for API lifecycle
mission_manager = EmergencyMissionManager()
eta_evaluator = MultiNodeETAEvaluator()


def _to_mission_response(m: EmergencyMission) -> MissionResponse:
    """Helper to convert EmergencyMission domain model to MissionResponse schema."""
    return MissionResponse(
        mission_id=m.mission_id,
        vehicle_id=m.vehicle_id,
        vehicle_type=str(m.vehicle_type),
        status=str(m.status),
        origin=m.origin,
        destination=m.destination,
        dispatched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(m.dispatched_timestamp)),
        arrived_at=(
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(m.arrived_timestamp))
            if m.arrived_timestamp
            else None
        ),
        current_position_m=m.current_position_m,
        current_speed_kmh=m.current_speed_kmh,
        progress_ratio=m.progress_ratio,
        is_active=m.is_active,
        route_nodes=list(m.route_nodes),
    )


def _sync_to_db(m: EmergencyMission) -> None:
    """Persist domain mission state into SQLite database."""
    record = MissionRecord(
        mission_id=m.mission_id,
        vehicle_id=m.vehicle_id,
        vehicle_type=str(m.vehicle_type),
        status=str(m.status),
        origin=m.origin,
        destination=m.destination,
        dispatched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(m.dispatched_timestamp)),
        arrived_at=(
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(m.arrived_timestamp))
            if m.arrived_timestamp
            else None
        ),
        current_position_m=m.current_position_m,
        current_speed_mps=m.current_speed_mps,
        progress_ratio=m.progress_ratio,
        target_speed_mps=m.target_speed_mps,
        priority_level=m.priority_level,
        route_nodes_json=str(m.route_nodes).replace("'", '"'),
    )
    db.save_mission(record)


@router.post("", response_model=MissionResponse, status_code=status.HTTP_201_CREATED)
def create_and_dispatch_mission(req: MissionCreateRequest) -> MissionResponse:
    """Register and dispatch a high-priority emergency transit mission."""
    mission_id = f"mission-{uuid.uuid4().hex[:8]}"

    # Map string type to enum
    v_type = EmergencyVehicleType.AMBULANCE
    if "fire" in req.vehicle_type.lower():
        v_type = EmergencyVehicleType.FIRE_ENGINE
    elif "police" in req.vehicle_type.lower():
        v_type = EmergencyVehicleType.POLICE_ESCORT

    m = mission_manager.create_mission(
        mission_id=mission_id,
        vehicle_id=req.vehicle_id,
        vehicle_type=v_type,
        target_speed_mps=req.target_speed_mps,
        priority_level=req.priority_level,
    )
    m.origin = req.origin
    m.destination = req.destination

    # Dispatch immediately
    mission_manager.dispatch_mission(mission_id)
    _sync_to_db(m)

    return _to_mission_response(m)


@router.get("", response_model=list[MissionResponse])
def list_missions() -> list[MissionResponse]:
    """Retrieve history and active emergency missions."""
    db_records = db.list_missions()
    if db_records:
        return [
            MissionResponse(
                mission_id=r.mission_id,
                vehicle_id=r.vehicle_id,
                vehicle_type=r.vehicle_type,
                status=r.status,
                origin=r.origin,
                destination=r.destination,
                dispatched_at=r.dispatched_at,
                arrived_at=r.arrived_at,
                current_position_m=r.current_position_m,
                current_speed_kmh=round(r.current_speed_mps * 3.6, 1),
                progress_ratio=r.progress_ratio,
                is_active=r.status
                in (
                    MissionStatus.DISPATCHED,
                    MissionStatus.APPROACHING,
                    MissionStatus.CORRIDOR_TRANSIT,
                ),
                route_nodes=r.to_dict().get("route_nodes", []),
            )
            for r in db_records
        ]

    # In-memory fallback
    return [_to_mission_response(m) for m in mission_manager.list_missions()]


@router.get("/{mission_id}", response_model=MissionResponse)
def get_mission(mission_id: str) -> MissionResponse:
    """Retrieve details for a specific emergency mission."""
    m = mission_manager.get_mission(mission_id)
    if m:
        return _to_mission_response(m)

    rec = db.get_mission(mission_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mission '{mission_id}' not found.",
        )
    return MissionResponse(
        mission_id=rec.mission_id,
        vehicle_id=rec.vehicle_id,
        vehicle_type=rec.vehicle_type,
        status=rec.status,
        origin=rec.origin,
        destination=rec.destination,
        dispatched_at=rec.dispatched_at,
        arrived_at=rec.arrived_at,
        current_position_m=rec.current_position_m,
        current_speed_kmh=round(rec.current_speed_mps * 3.6, 1),
        progress_ratio=rec.progress_ratio,
        is_active=rec.status
        in (
            MissionStatus.DISPATCHED,
            MissionStatus.APPROACHING,
            MissionStatus.CORRIDOR_TRANSIT,
        ),
        route_nodes=rec.to_dict().get("route_nodes", []),
    )


@router.get("/{mission_id}/eta", response_model=MultiNodeETAResponse)
def get_mission_eta(
    mission_id: str,
    weather: str = Query(default="clear", description="Weather friction condition"),
) -> MultiNodeETAResponse:
    """Calculate real-time multi-node kinematic arrival ETAs for an emergency mission."""
    m = mission_manager.get_mission(mission_id)
    if not m:
        rec = db.get_mission(mission_id)
        if not rec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Mission '{mission_id}' not found.",
            )
        # Rehydrate into in-memory manager
        m = mission_manager.create_mission(
            mission_id=rec.mission_id,
            vehicle_id=rec.vehicle_id,
            target_speed_mps=rec.target_speed_mps,
            priority_level=rec.priority_level,
        )
        m.current_position_m = rec.current_position_m
        m.current_speed_mps = rec.current_speed_mps
        m.status = MissionStatus(rec.status)

    weather_str = weather if isinstance(weather, str) else "clear"
    eta_report = eta_evaluator.compute_multi_node_eta(
        mission=m,
        weather=weather_str,
    )

    node_schemas: dict[str, NodeETASchema] = {
        nid: NodeETASchema(
            node_id=res.node_id,
            stopline_x_m=res.stopline_x_meters,
            distance_to_stopline_m=res.distance_to_stopline_m,
            eta_seconds=res.eta_seconds,
            has_passed=res.has_passed,
            confidence_score=res.confidence_score,
        )
        for nid, res in eta_report.etas_by_node.items()
    }

    return MultiNodeETAResponse(
        mission_id=m.mission_id,
        vehicle_id=m.vehicle_id,
        current_position_m=m.current_position_m,
        current_speed_kmh=m.current_speed_kmh,
        etas_by_node=node_schemas,
        hospital_eta_sec=eta_report.hospital_eta_sec,
        calculation_timestamp=eta_report.calculation_timestamp,
        provenance="KINEMATIC_CORRIDOR_ESTIMATOR",
    )


@router.post("/{mission_id}/telemetry", response_model=MissionResponse)
def update_mission_telemetry(
    mission_id: str,
    position_m: float = Query(..., description="Corridor longitudinal position (meters)"),
    speed_mps: float = Query(..., ge=0.0, description="Instantaneous velocity (m/s)"),
    current_edge: str | None = Query(default=None, description="Current corridor edge ID"),
) -> MissionResponse:
    """Update vehicle kinematics for an active mission and update database."""
    m = mission_manager.get_mission(mission_id)
    if not m:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active mission '{mission_id}' not found in runtime registry.",
        )

    updated_mission = mission_manager.update_telemetry(
        position_m=position_m,
        speed_mps=speed_mps,
        current_edge=current_edge,
        mission_id=mission_id,
    )
    _sync_to_db(updated_mission)
    return _to_mission_response(updated_mission)
