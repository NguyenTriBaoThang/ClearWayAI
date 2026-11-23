"""Automated Unit & Integration Test Suite for Clearance Model Registry & Fallbacks (Task 36).

Verifies:
1. Model Registry catalog discovery, SHA-256 integrity, and champion designations.
2. Dynamic champion selection (single state -> Tabular; sequence history -> Sequential).
3. Explicit model selection overrides.
4. Input validity evaluation and confidence scoring.
5. Tier 1 Kinematic Shockwave fallback upon AI anomaly or exception.
6. Tier 2 Conservative Static Default fallback upon missing/corrupted inputs.
7. Real-time latency SLA (<= 10.0 ms).
8. Registry manifest schema and roundtrip persistence.
"""

from __future__ import annotations

import time

import pytest

from ai.clearance.model_registry import (
    ClearanceModelRegistry,
    FallbackTier,
    ModelRole,
    ModelType,
    UnifiedClearancePredictor,
)
from ai.state.traffic_state_estimator import ApproachTrafficState


@pytest.fixture
def sample_traffic_state() -> ApproachTrafficState:
    """Creates a realistic nominal ApproachTrafficState."""
    return ApproachTrafficState(
        approach_id="EB",
        timestamp_sec=time.time(),
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
def sample_state_sequence() -> list[ApproachTrafficState]:
    """Creates a 5-step consecutive temporal sequence of states."""
    t0 = time.time()
    return [
        ApproachTrafficState(
            approach_id="EB",
            timestamp_sec=t0 + i * 5.0,
            vehicle_count=10 + i * 2,
            counts_by_class={"car": 3, "motorcycle": 8, "bus": 1, "truck": 0},
            motorcycle_ratio=8.0 / (12 + i),
            queue_length_meters=20.0 + i * 3.5,
            queued_vehicle_count=6 + i,
            approach_occupancy_ratio=0.30 + i * 0.04,
            traffic_density_vpm=10.0 + i,
            mean_speed_kmh=18.0 - i * 1.2,
        )
        for i in range(5)
    ]


def test_registry_discovery_and_catalog():
    """Verify that all 5 clearance models are registered with correct roles."""
    registry = ClearanceModelRegistry()
    models = registry.list_models()

    assert len(models) >= 5
    model_names = {m.name for m in models}
    expected = {
        "gradient_boosting",
        "random_forest",
        "linear_regression",
        "clearance_gru",
        "clearance_lstm",
    }
    assert expected.issubset(model_names)

    # Verify Champions
    tab_champ = registry.get_champion(ModelType.TABULAR)
    assert tab_champ.name == "gradient_boosting"
    assert tab_champ.role == ModelRole.CHAMPION

    seq_champ = registry.get_champion(ModelType.SEQUENTIAL)
    assert seq_champ.name == "clearance_gru"
    assert seq_champ.role == ModelRole.CHAMPION

    # Verify SHA-256 and sizes
    for m in models:
        assert len(m.sha256) == 64
        assert m.size_bytes > 0
        assert m.test_mae > 0.0


def test_registry_model_loading_and_caching():
    """Verify that predictors load successfully and are cached in memory."""
    registry = ClearanceModelRegistry()

    # Load Tabular
    tab_pred = registry.load_tabular_model("gradient_boosting")
    assert tab_pred is not None
    # Caching check
    assert registry.load_tabular_model("gradient_boosting") is tab_pred

    # Load Sequential
    seq_pred = registry.load_sequence_model("clearance_gru")
    assert seq_pred is not None
    assert registry.load_sequence_model("clearance_gru") is seq_pred


def test_dynamic_champion_routing(sample_traffic_state, sample_state_sequence):
    """Verify dynamic routing: single state -> Tabular; sequence -> Sequential."""
    predictor = UnifiedClearancePredictor()

    # Case 1: Single instantaneous snapshot -> Tabular Champion
    res_single = predictor.predict(sample_traffic_state)
    assert res_single.model_name == "gradient_boosting"
    assert res_single.model_type == ModelType.TABULAR
    assert res_single.fallback_used is False
    assert res_single.fallback_tier == FallbackTier.TIER_0_AI
    assert res_single.provenance == "AI_TABULAR_CHAMPION"
    assert res_single.predicted_clearance_sec > 1.0

    # Case 2: Sequence buffer of length 5 -> Sequential Champion
    res_seq = predictor.predict(sample_state_sequence)
    assert res_seq.model_name == "clearance_gru"
    assert res_seq.model_type == ModelType.SEQUENTIAL
    assert res_seq.fallback_used is False
    assert res_seq.fallback_tier == FallbackTier.TIER_0_AI
    assert res_seq.provenance == "AI_SEQUENCE_CHAMPION"
    assert res_seq.predicted_clearance_sec > 1.0


def test_explicit_model_override(sample_traffic_state):
    """Verify explicit model override parameter."""
    predictor = UnifiedClearancePredictor()

    res_rf = predictor.predict(sample_traffic_state, force_model="random_forest")
    assert res_rf.model_name == "random_forest"
    assert res_rf.fallback_used is False

    res_lr = predictor.predict(sample_traffic_state, force_model="linear_regression")
    assert res_lr.model_name == "linear_regression"
    assert res_lr.fallback_used is False


def test_input_validity_evaluation():
    """Verify input domain checks and confidence degradation."""
    predictor = UnifiedClearancePredictor()

    # Nominal
    valid, conf, _ = predictor.evaluate_input_validity(30.0, 10, 0.4, 0.3)
    assert valid is True
    assert conf >= 0.85

    # Out of physical bounds (negative queue)
    valid_neg, conf_neg, reason = predictor.evaluate_input_validity(-5.0, 10, 0.4, 0.3)
    assert valid_neg is False
    assert conf_neg == 0.0
    assert "Negative queue length" in str(reason)

    # Out of physical bounds (occupancy > 1.0)
    valid_occ, _, reason_occ = predictor.evaluate_input_validity(30.0, 10, 1.4, 0.3)
    assert valid_occ is False
    assert "out of range" in str(reason_occ)


def test_tier_1_kinematic_fallback_on_corrupted_domain():
    """Verify graceful Tier 1 physical fallback when input violates domain."""
    predictor = UnifiedClearancePredictor()

    bad_state = ApproachTrafficState(
        approach_id="EB",
        timestamp_sec=time.time(),
        vehicle_count=5,
        counts_by_class={"car": 2, "motorcycle": 3},
        motorcycle_ratio=0.6,
        queue_length_meters=-12.0,  # Negative queue from noisy sensor
        queued_vehicle_count=5,
        approach_occupancy_ratio=0.2,
        traffic_density_vpm=5.0,
        mean_speed_kmh=15.0,
    )

    res = predictor.predict(bad_state)
    assert res.fallback_used is True
    assert res.fallback_tier == FallbackTier.TIER_1_KINEMATIC_PHYSICS
    assert res.provenance == "FALLBACK_PHYSICAL_SHOCKWAVE"
    assert "Negative queue length" in str(res.fallback_reason)
    assert res.predicted_clearance_sec >= 0.0


def test_tier_2_conservative_default_fallback():
    """Verify Tier 2 default safe fallback when input is None or empty."""
    predictor = UnifiedClearancePredictor()

    # None input
    res_none = predictor.predict(None)  # type: ignore[arg-type]
    assert res_none.fallback_used is True
    assert res_none.fallback_tier == FallbackTier.TIER_2_CONSERVATIVE_DEFAULT
    assert res_none.predicted_clearance_sec == 25.0
    assert res_none.confidence_score == 0.50
    assert res_none.provenance == "FALLBACK_CONSERVATIVE_DEFAULT"

    # Empty list input
    res_empty = predictor.predict([])
    assert res_empty.fallback_used is True
    assert res_empty.fallback_tier == FallbackTier.TIER_2_CONSERVATIVE_DEFAULT
    assert res_empty.predicted_clearance_sec == 25.0


def test_real_time_latency_sla(sample_traffic_state):
    """Verify that predictor completes inference within the real-time SLA (<= 10ms)."""
    predictor = UnifiedClearancePredictor()

    # Warm-up
    _ = predictor.predict(sample_traffic_state)

    latencies = []
    for _ in range(50):
        res = predictor.predict(sample_traffic_state)
        latencies.append(res.latency_ms)

    median_latency = float(sorted(latencies)[len(latencies) // 2])
    assert median_latency < 10.0, f"Median latency {median_latency}ms exceeds 10ms SLA"


def test_export_registry_manifest(tmp_path):
    """Verify export of official registry manifest JSON."""
    registry = ClearanceModelRegistry()
    out_file = tmp_path / "registry_manifest.json"

    manifest = registry.export_registry_manifest(out_file)
    assert out_file.is_file()

    assert manifest["registry_version"] == "1.0.0"
    assert manifest["champion_models"]["tabular"] == "gradient_boosting"
    assert manifest["champion_models"]["sequential"] == "clearance_gru"
    assert len(manifest["models"]) >= 5
    assert len(manifest["fallback_hierarchy"]) == 3
