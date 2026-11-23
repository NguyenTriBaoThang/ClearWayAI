"""AI Queue Clearance Prediction & Model Registry Endpoints (`apps.api.src.routers.clearance`)."""

from __future__ import annotations

import time

from fastapi import APIRouter

from ai.clearance.model_registry import (
    ClearanceModelRegistry,
    ModelType,
    UnifiedClearancePredictor,
)
from ai.state.traffic_state_estimator import ApproachTrafficState
from apps.api.src.database import ClearancePredictionRecord, db
from apps.api.src.schemas import (
    ClearancePredictRequest,
    ClearancePredictResponse,
    ModelMetadataSchema,
    ModelRegistryCatalogResponse,
)

router = APIRouter(prefix="/api/v1/clearance", tags=["Clearance AI"])

# Global singleton predictor and registry
registry = ClearanceModelRegistry()
predictor = UnifiedClearancePredictor(registry=registry)


@router.post("/predict", response_model=ClearancePredictResponse)
def predict_queue_clearance(req: ClearancePredictRequest) -> ClearancePredictResponse:
    """Predict queue clearance duration using champion model with multi-tier fail-safe fallback."""
    now = time.time()
    state = ApproachTrafficState(
        approach_id=req.approach_id,
        timestamp_sec=now,
        vehicle_count=req.vehicle_count,
        counts_by_class={},
        motorcycle_ratio=req.motorcycle_ratio,
        queue_length_meters=req.queue_length_meters,
        queued_vehicle_count=req.queued_vehicle_count,
        approach_occupancy_ratio=req.approach_occupancy_ratio,
        traffic_density_vpm=20.0,
        mean_speed_kmh=12.0,
    )

    result = predictor.predict(
        states=state,
        node_id=req.node_id,
        weather=req.weather,
        force_model=req.force_model,
    )

    # Persist inference record in database
    db_rec = ClearancePredictionRecord(
        id=None,
        timestamp=result.timestamp_sec,
        node_id=req.node_id,
        predicted_clearance_sec=result.predicted_clearance_sec,
        confidence_score=result.confidence_score,
        model_name=result.model_name,
        fallback_used=result.fallback_used,
        fallback_tier=str(result.fallback_tier),
    )
    db.log_clearance_prediction(db_rec)

    return ClearancePredictResponse(
        node_id=req.node_id,
        predicted_clearance_sec=result.predicted_clearance_sec,
        confidence_score=result.confidence_score,
        model_name=result.model_name,
        model_type=str(result.model_type),
        fallback_used=result.fallback_used,
        fallback_tier=str(result.fallback_tier),
        latency_ms=result.latency_ms,
        provenance=result.provenance,
    )


@router.get("/registry", response_model=ModelRegistryCatalogResponse)
def get_model_registry_catalog() -> ModelRegistryCatalogResponse:
    """Retrieve catalog of registered clearance models, benchmarks, and active champions."""
    manifest = registry.export_registry_manifest()
    models_dict = manifest.get("models", {})

    model_schemas: list[ModelMetadataSchema] = []
    for _m_name, m_info in models_dict.items():
        model_schemas.append(
            ModelMetadataSchema(
                name=m_info.get("name", ""),
                role=m_info.get("role", "CANDIDATE"),
                model_type=m_info.get("model_type", "tabular"),
                val_mae=float(m_info.get("val_mae", 0.0)),
                test_mae=float(m_info.get("test_mae", 0.0)),
                test_r2=float(m_info.get("test_r2", 0.0)),
                latency_ms=float(m_info.get("latency_ms", 0.0)),
                provenance=m_info.get("provenance", "CLEARANCE_REGISTRY"),
                description=m_info.get("description", ""),
            )
        )

    champ_tab = registry.get_champion(ModelType.TABULAR).name
    champ_seq = registry.get_champion(ModelType.SEQUENTIAL).name

    return ModelRegistryCatalogResponse(
        registry_version=str(manifest.get("registry_version", "1.0.0")),
        champion_tabular=champ_tab,
        champion_sequential=champ_seq,
        models=model_schemas,
    )

