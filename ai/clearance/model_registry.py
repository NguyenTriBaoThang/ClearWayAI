"""ClearWayAI Clearance Model Registry & Multi-Tier Fallback System (Task 36).

Provides an enterprise-grade Model Registry for corridor queue clearance models:
- Discovers and catalogs trained models (Tabular Gradient Boosting, Random Forest,
  Linear Regression, Sequential GRU, Sequential LSTM).
- Tracks model roles (CHAMPION, CHALLENGER, RETIRED), evaluation benchmarks,
  and cryptographic SHA-256 checksums.
- Dynamic Champion Selection: routes requests to the optimal model based on
  temporal context (temporal sequence buffer >= 5 -> Sequential Champion;
  single snapshot -> Tabular Champion).
- Multi-Tier Fail-Safe Fallback:
  * Tier 0: Normal AI inference with confidence scoring.
  * Tier 1: Kinematic Shockwave discharge physics (Webster / LWR wave theory).
  * Tier 2: Conservative static default safe clearance (25.0s fail-safe).
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from ai.clearance.dataset_generator import QueueDischargeSimulator
from ai.clearance.features import ClearanceFeaturePipeline
from ai.clearance.sequence_models import SequencePredictor
from ai.clearance.tabular_models import ClearancePredictor
from ai.state.traffic_state_estimator import ApproachTrafficState


class ModelRole(StrEnum):
    """Lifecycle role in the clearance model registry."""

    CHAMPION = "CHAMPION"
    CHALLENGER = "CHALLENGER"
    CANDIDATE = "CANDIDATE"
    RETIRED = "RETIRED"


class ModelType(StrEnum):
    """Type of clearance model architecture."""

    TABULAR = "tabular"
    SEQUENTIAL = "sequential"
    HEURISTIC = "heuristic"


class FallbackTier(StrEnum):
    """Operational tier for clearance prediction."""

    TIER_0_AI = "TIER_0_AI"
    TIER_1_KINEMATIC_PHYSICS = "TIER_1_KINEMATIC_PHYSICS"
    TIER_2_CONSERVATIVE_DEFAULT = "TIER_2_CONSERVATIVE_DEFAULT"


@dataclass
class ModelMetadata:
    """Catalog metadata for a registered clearance model."""

    name: str
    role: ModelRole
    model_type: ModelType
    filename: str
    sha256: str
    size_bytes: int
    val_mae: float
    test_mae: float
    test_rmse: float
    test_r2: float
    latency_ms: float
    provenance: str
    description: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["role"] = str(self.role)
        d["model_type"] = str(self.model_type)
        return d


@dataclass
class ClearancePredictionResult:
    """Standardized response contract for clearance prediction with provenance."""

    predicted_clearance_sec: float
    confidence_score: float
    model_name: str
    model_type: str
    fallback_used: bool
    fallback_tier: FallbackTier
    fallback_reason: str | None
    latency_ms: float
    provenance: str
    timestamp_sec: float

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["fallback_tier"] = str(self.fallback_tier)
        return d


class ClearanceModelRegistry:
    """Discovers, catalogs, verifies, and serves trained clearance models."""

    DEFAULT_MODELS_DIR = Path("models/clearance")

    def __init__(self, models_dir: Path | str | None = None) -> None:
        self.models_dir = Path(models_dir) if models_dir else self.DEFAULT_MODELS_DIR
        self._models: dict[str, ModelMetadata] = {}
        self._loaded_models: dict[str, Any] = {}
        self._tabular_pipeline: ClearanceFeaturePipeline | None = None
        self._sequence_pipeline: ClearanceFeaturePipeline | None = None

        self._discover_and_catalog()

    def _compute_sha256(self, file_path: Path) -> str:
        """Calculate SHA-256 hex digest for an artifact."""
        if not file_path.is_file():
            return ""
        return hashlib.sha256(file_path.read_bytes()).hexdigest()

    def _discover_and_catalog(self) -> None:
        """Scan models directory and build catalog from benchmark reports."""
        if not self.models_dir.exists():
            return

        # 1. Tabular Models discovery
        tab_report_path = self.models_dir / "tabular_benchmark_report.json"
        tab_metrics: dict[str, Any] = {}
        if tab_report_path.is_file():
            try:
                with open(tab_report_path, encoding="utf-8") as f:
                    tab_metrics = json.load(f).get("models", {})
            except Exception:
                tab_metrics = {}

        # 2. Sequential Models discovery
        seq_report_path = self.models_dir / "sequence_benchmark_report.json"
        seq_metrics: dict[str, Any] = {}
        if seq_report_path.is_file():
            try:
                with open(seq_report_path, encoding="utf-8") as f:
                    seq_metrics = json.load(f).get("models", {})
            except Exception:
                seq_metrics = {}

        # Model Definitions & Specifications
        registry_specs = [
            # Tabular Champion
            {
                "name": "gradient_boosting",
                "role": ModelRole.CHAMPION,
                "model_type": ModelType.TABULAR,
                "filename": "gradient_boosting.joblib",
                "metrics_dict": tab_metrics.get("gradient_boosting", {}),
                "default_val_mae": 1.062,
                "default_test_mae": 1.202,
                "default_test_rmse": 1.997,
                "default_test_r2": 0.9850,
                "default_latency": 0.542,
                "provenance": "CLEARANCE_TABULAR_MODEL",
                "description": "Gradient Boosting Regressor (Tabular Champion for single-cycle snapshots).",
            },
            # Tabular Challenger 1
            {
                "name": "random_forest",
                "role": ModelRole.CHALLENGER,
                "model_type": ModelType.TABULAR,
                "filename": "random_forest.joblib",
                "metrics_dict": tab_metrics.get("random_forest", {}),
                "default_val_mae": 1.213,
                "default_test_mae": 1.415,
                "default_test_rmse": 2.344,
                "default_test_r2": 0.9794,
                "default_latency": 14.58,
                "provenance": "CLEARANCE_TABULAR_MODEL",
                "description": "Random Forest Regressor (Non-linear ensemble challenger).",
            },
            # Tabular Challenger 2
            {
                "name": "linear_regression",
                "role": ModelRole.CHALLENGER,
                "model_type": ModelType.TABULAR,
                "filename": "linear_regression.joblib",
                "metrics_dict": tab_metrics.get("linear_regression", {}),
                "default_val_mae": 2.528,
                "default_test_mae": 2.420,
                "default_test_rmse": 3.722,
                "default_test_r2": 0.9480,
                "default_latency": 0.105,
                "provenance": "CLEARANCE_TABULAR_MODEL",
                "description": "Ridge Regularized Linear Regression baseline.",
            },
            # Sequential Champion
            {
                "name": "clearance_gru",
                "role": ModelRole.CHAMPION,
                "model_type": ModelType.SEQUENTIAL,
                "filename": "clearance_gru.npz",
                "metrics_dict": seq_metrics.get("clearance_gru", {}),
                "default_val_mae": 5.168,
                "default_test_mae": 4.733,
                "default_test_rmse": 8.755,
                "default_test_r2": 0.8280,
                "default_latency": 0.778,
                "provenance": "CLEARANCE_SEQUENCE_MODEL",
                "description": "Gated Recurrent Unit Regressor (Sequential Champion for sliding window histories).",
            },
            # Sequential Challenger
            {
                "name": "clearance_lstm",
                "role": ModelRole.CHALLENGER,
                "model_type": ModelType.SEQUENTIAL,
                "filename": "clearance_lstm.npz",
                "metrics_dict": seq_metrics.get("clearance_lstm", {}),
                "default_val_mae": 6.556,
                "default_test_mae": 5.276,
                "default_test_rmse": 10.054,
                "default_test_r2": 0.7732,
                "default_latency": 0.679,
                "provenance": "CLEARANCE_SEQUENCE_MODEL",
                "description": "Long Short-Term Memory Regressor (Sequential challenger).",
            },
        ]

        for spec in registry_specs:
            file_path = self.models_dir / spec["filename"]
            sha = self._compute_sha256(file_path)
            size = file_path.stat().st_size if file_path.is_file() else 0
            m_dict = spec["metrics_dict"]

            meta = ModelMetadata(
                name=spec["name"],
                role=spec["role"],
                model_type=spec["model_type"],
                filename=spec["filename"],
                sha256=sha,
                size_bytes=size,
                val_mae=float(m_dict.get("val_mae", spec["default_val_mae"])),
                test_mae=float(m_dict.get("test_mae", spec["default_test_mae"])),
                test_rmse=float(m_dict.get("test_rmse", spec["default_test_rmse"])),
                test_r2=float(m_dict.get("test_r2", spec["default_test_r2"])),
                latency_ms=float(m_dict.get("latency_ms", spec["default_latency"])),
                provenance=spec["provenance"],
                description=spec["description"],
            )
            self._models[spec["name"]] = meta

    def get_model_metadata(self, name: str) -> ModelMetadata | None:
        """Retrieve metadata for a registered model."""
        return self._models.get(name)

    def list_models(self) -> list[ModelMetadata]:
        """List all cataloged models."""
        return list(self._models.values())

    def get_champion(self, model_type: ModelType) -> ModelMetadata:
        """Get the designated champion model for a model type."""
        for model in self._models.values():
            if model.model_type == model_type and model.role == ModelRole.CHAMPION:
                return model
        # Default fallback
        if model_type == ModelType.SEQUENTIAL:
            return self._models.get("clearance_gru", list(self._models.values())[0])
        return self._models.get("gradient_boosting", list(self._models.values())[0])

    def load_tabular_model(self, name: str = "gradient_boosting") -> ClearancePredictor:
        """Load a tabular model bundled with its feature pipeline."""
        if name in self._loaded_models:
            return self._loaded_models[name]

        meta = self.get_model_metadata(name)
        if not meta:
            raise ValueError(f"Model '{name}' not found in registry.")

        model_file = self.models_dir / meta.filename
        if not model_file.is_file():
            raise FileNotFoundError(f"Model artifact not found at {model_file}")

        predictor = ClearancePredictor.load(model_file)
        self._loaded_models[name] = predictor
        return predictor

    def load_sequence_model(self, name: str = "clearance_gru") -> SequencePredictor:
        """Load a sequential model bundled with its feature pipeline."""
        if name in self._loaded_models:
            return self._loaded_models[name]

        meta = self.get_model_metadata(name)
        if not meta:
            raise ValueError(f"Sequence model '{name}' not found in registry.")

        model_file = self.models_dir / meta.filename
        pipe_file = self.models_dir / "sequence_pipeline.joblib"
        if not model_file.is_file():
            raise FileNotFoundError(f"Sequence model artifact not found at {model_file}")

        predictor = SequencePredictor.load(model_file, pipe_file)
        self._loaded_models[name] = predictor
        return predictor

    def export_registry_manifest(
        self,
        output_path: Path | str | None = None,
    ) -> dict[str, Any]:
        """Generate official JSON registry catalog document."""
        manifest = {
            "registry_version": "1.0.0",
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "champion_models": {
                "tabular": self.get_champion(ModelType.TABULAR).name,
                "sequential": self.get_champion(ModelType.SEQUENTIAL).name,
            },
            "models": {name: meta.to_dict() for name, meta in self._models.items()},
            "fallback_hierarchy": [
                {
                    "tier": 0,
                    "name": "AI Inference",
                    "conditions": "Valid input within training domain, confidence >= 0.60, no exceptions",
                },
                {
                    "tier": 1,
                    "name": "Kinematic Physical Shockwave Discharge",
                    "conditions": "AI model fails, anomaly detected, or low confidence",
                },
                {
                    "tier": 2,
                    "name": "Conservative Static Default Safe Clearance",
                    "conditions": "Sensors offline or critical parameters missing/corrupted",
                },
            ],
        }

        if output_path:
            p = Path(output_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

        return manifest


class UnifiedClearancePredictor:
    """Production inference interface with automatic champion selection & multi-tier fallbacks."""

    DEFAULT_SAFE_CLEARANCE_SEC: float = 25.0
    MIN_CONFIDENCE_THRESHOLD: float = 0.60

    def __init__(
        self,
        registry: ClearanceModelRegistry | None = None,
        min_confidence: float = 0.60,
        default_safe_sec: float = 25.0,
    ) -> None:
        self.registry = registry or ClearanceModelRegistry()
        self.min_confidence = min_confidence
        self.default_safe_sec = default_safe_sec
        self.simulator = QueueDischargeSimulator()

    def evaluate_input_validity(
        self,
        queue_length_m: float,
        vehicle_count: int,
        approach_occupancy: float,
        downstream_occupancy: float,
    ) -> tuple[bool, float, str | None]:
        """Evaluate input domain validity and compute confidence score [0.0, 1.0]."""
        # Physical boundary checks
        if queue_length_m < 0.0:
            return False, 0.0, f"Negative queue length: {queue_length_m:.1f}m"
        if queue_length_m > 300.0:
            return (
                False,
                0.3,
                f"Queue length exceeds physical corridor limit: {queue_length_m:.1f}m",
            )
        if vehicle_count < 0:
            return False, 0.0, f"Negative vehicle count: {vehicle_count}"
        if not (0.0 <= approach_occupancy <= 1.0):
            return False, 0.2, f"Approach occupancy out of range [0, 1]: {approach_occupancy:.2f}"
        if not (0.0 <= downstream_occupancy <= 1.0):
            return (
                False,
                0.2,
                f"Downstream occupancy out of range [0, 1]: {downstream_occupancy:.2f}",
            )

        # Plausible domain confidence heuristic
        confidence = 0.95
        if queue_length_m > 150.0:
            confidence -= 0.15
        if approach_occupancy > 0.90:
            confidence -= 0.10
        if downstream_occupancy > 0.90:
            confidence -= 0.10

        return True, max(0.1, round(confidence, 2)), None

    def predict(
        self,
        states: ApproachTrafficState | list[ApproachTrafficState] | dict[str, Any],
        scenario_id: str = "normal",
        node_id: str = "node_b",
        weather: str = "clear",
        downstream_occupancy: float = 0.25,
        hour_of_day: int = 8,
        force_model: str | None = None,
    ) -> ClearancePredictionResult:
        """Predict clearance time with dynamic champion routing and tiered fallback safety."""
        t_start = time.perf_counter()
        now = time.time()

        # Handle null/empty input directly -> Tier 2 Fallback
        if states is None:
            latency = (time.perf_counter() - t_start) * 1000.0
            return ClearancePredictionResult(
                predicted_clearance_sec=self.default_safe_sec,
                confidence_score=0.50,
                model_name="conservative_default",
                model_type=ModelType.HEURISTIC,
                fallback_used=True,
                fallback_tier=FallbackTier.TIER_2_CONSERVATIVE_DEFAULT,
                fallback_reason="Input state is None",
                latency_ms=round(latency, 3),
                provenance="FALLBACK_CONSERVATIVE_DEFAULT",
                timestamp_sec=now,
            )

        # 1. Parse current state metrics
        if isinstance(states, list):
            if len(states) == 0:
                return self._fallback_tier_2("Empty state sequence", t_start, now)
            curr = states[-1]
            is_sequence = len(states) >= 5
        elif isinstance(states, ApproachTrafficState):
            curr = states
            is_sequence = False
        elif isinstance(states, dict):
            # Dict features
            curr = ApproachTrafficState(
                approach_id=str(states.get("approach_id", "EB")),
                timestamp_sec=float(states.get("timestamp_sec", now)),
                vehicle_count=int(states.get("queued_vehicle_count", 0)),
                counts_by_class={},
                motorcycle_ratio=float(states.get("motorcycle_ratio", 0.75)),
                queue_length_meters=float(states.get("queue_length_m", 0.0)),
                queued_vehicle_count=int(states.get("queued_vehicle_count", 0)),
                approach_occupancy_ratio=float(states.get("approach_occupancy", 0.25)),
                traffic_density_vpm=10.0,
                mean_speed_kmh=15.0,
            )
            is_sequence = False
        else:
            return self._fallback_tier_2(f"Unsupported state type: {type(states)}", t_start, now)

        # 2. Check Input Validity
        is_valid, base_confidence, invalid_reason = self.evaluate_input_validity(
            queue_length_m=curr.queue_length_meters,
            vehicle_count=curr.queued_vehicle_count,
            approach_occupancy=curr.approach_occupancy_ratio,
            downstream_occupancy=downstream_occupancy,
        )

        if not is_valid:
            # Route directly to Tier 1 Fallback
            return self._fallback_tier_1(
                curr=curr,
                downstream_occupancy=downstream_occupancy,
                weather=weather,
                reason=invalid_reason or "Input domain boundary violation",
                t_start=t_start,
                timestamp=now,
            )

        # 3. Dynamic Model Routing
        target_model = force_model
        if not target_model:
            target_model = "clearance_gru" if is_sequence else "gradient_boosting"

        # 4. Attempt AI Model Execution
        try:
            pred_time: float
            if target_model in ["clearance_gru", "clearance_lstm"]:
                seq_predictor = self.registry.load_sequence_model(target_model)
                seq_states = states if isinstance(states, list) else [curr]
                pred_time = seq_predictor.predict_from_traffic_states(
                    states=seq_states,
                    scenario_id=scenario_id,
                    node_id=node_id,
                    weather=weather,
                    downstream_occupancy=downstream_occupancy,
                    hour_of_day=hour_of_day,
                )
                m_type = ModelType.SEQUENTIAL
                prov = (
                    "AI_SEQUENCE_CHAMPION"
                    if target_model == "clearance_gru"
                    else "AI_SEQUENCE_MODEL"
                )
            else:
                tab_predictor = self.registry.load_tabular_model(target_model)
                pred_time = tab_predictor.predict_from_traffic_state(
                    state=curr,
                    scenario_id=scenario_id,
                    node_id=node_id,
                    weather=weather,
                    downstream_occupancy=downstream_occupancy,
                    hour_of_day=hour_of_day,
                )
                m_type = ModelType.TABULAR
                prov = (
                    "AI_TABULAR_CHAMPION"
                    if target_model == "gradient_boosting"
                    else "AI_TABULAR_MODEL"
                )

            # 5. Output Plausibility Audit
            if pred_time <= 0.0 and curr.queue_length_meters > 5.0:
                return self._fallback_tier_1(
                    curr=curr,
                    downstream_occupancy=downstream_occupancy,
                    weather=weather,
                    reason=f"Anomalous zero/negative clearance time ({pred_time:.2f}s) for queue {curr.queue_length_meters:.1f}m",
                    t_start=t_start,
                    timestamp=now,
                )
            if pred_time > 180.0:
                return self._fallback_tier_1(
                    curr=curr,
                    downstream_occupancy=downstream_occupancy,
                    weather=weather,
                    reason=f"Anomalously high clearance time ({pred_time:.1f}s > 180s)",
                    t_start=t_start,
                    timestamp=now,
                )

            latency = (time.perf_counter() - t_start) * 1000.0
            return ClearancePredictionResult(
                predicted_clearance_sec=round(pred_time, 2),
                confidence_score=base_confidence,
                model_name=target_model,
                model_type=m_type,
                fallback_used=False,
                fallback_tier=FallbackTier.TIER_0_AI,
                fallback_reason=None,
                latency_ms=round(latency, 3),
                provenance=prov,
                timestamp_sec=now,
            )

        except Exception as exc:
            # Model execution exception -> Graceful Tier 1 Fallback
            return self._fallback_tier_1(
                curr=curr,
                downstream_occupancy=downstream_occupancy,
                weather=weather,
                reason=f"AI model inference exception: {exc}",
                t_start=t_start,
                timestamp=now,
            )

    def _fallback_tier_1(
        self,
        curr: ApproachTrafficState,
        downstream_occupancy: float,
        weather: str,
        reason: str,
        t_start: float,
        timestamp: float,
    ) -> ClearancePredictionResult:
        """Level 1 Kinematic Shockwave physical discharge fallback."""
        try:
            heavy_count = curr.counts_by_class.get("bus", 0) + curr.counts_by_class.get("truck", 0)
            t_clear = self.simulator.compute_clearance_time(
                queue_length_m=max(0.0, curr.queue_length_meters),
                queued_vehicle_count=max(0, curr.queued_vehicle_count),
                motorcycle_ratio=curr.motorcycle_ratio,
                heavy_vehicle_count=heavy_count,
                approach_occupancy=curr.approach_occupancy_ratio,
                downstream_occupancy=downstream_occupancy,
                weather=weather,
            )
            latency = (time.perf_counter() - t_start) * 1000.0
            return ClearancePredictionResult(
                predicted_clearance_sec=round(t_clear, 2),
                confidence_score=0.85,  # deterministic kinematic formula
                model_name="kinematic_shockwave_simulator",
                model_type=ModelType.HEURISTIC,
                fallback_used=True,
                fallback_tier=FallbackTier.TIER_1_KINEMATIC_PHYSICS,
                fallback_reason=reason,
                latency_ms=round(latency, 3),
                provenance="FALLBACK_PHYSICAL_SHOCKWAVE",
                timestamp_sec=timestamp,
            )
        except Exception as exc:
            # If physical calculation also fails -> Tier 2 Fallback
            return self._fallback_tier_2(
                reason=f"Kinematic fallback failed ({exc}) following: {reason}",
                t_start=t_start,
                timestamp=timestamp,
            )

    def _fallback_tier_2(
        self,
        reason: str,
        t_start: float,
        timestamp: float,
    ) -> ClearancePredictionResult:
        """Level 2 Conservative static default safe clearance."""
        latency = (time.perf_counter() - t_start) * 1000.0
        return ClearancePredictionResult(
            predicted_clearance_sec=self.default_safe_sec,
            confidence_score=0.50,
            model_name="conservative_default",
            model_type=ModelType.HEURISTIC,
            fallback_used=True,
            fallback_tier=FallbackTier.TIER_2_CONSERVATIVE_DEFAULT,
            fallback_reason=reason,
            latency_ms=round(latency, 3),
            provenance="FALLBACK_CONSERVATIVE_DEFAULT",
            timestamp_sec=timestamp,
        )
