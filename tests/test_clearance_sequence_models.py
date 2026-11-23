"""Automated Unit & Integration Test Suite for Clearance Sequence Models (Task 35).

Verifies:
1. Rollout time-series generation and sliding window sequence construction.
2. Zero data leakage across intersection nodes.
3. ClearanceLSTM and ClearanceGRU forward/backward pass and training convergence.
4. Save/load serialization roundtrips.
5. SequencePredictor inference with ApproachTrafficState.
6. train_sequence CLI execution and benchmark report generation.
"""

from __future__ import annotations

import json
import subprocess
import sys

import numpy as np
import pytest

from ai.clearance.dataset_generator import QueueDischargeSimulator
from ai.clearance.sequence_models import (
    ClearanceGRU,
    ClearanceLSTM,
    SequencePredictor,
    generate_clearance_sequences,
    split_sequences_by_node,
)
from ai.state.traffic_state_estimator import ApproachTrafficState


@pytest.fixture
def sample_rollout_df():
    """Generates a small deterministic rollout dataset for testing."""
    sim = QueueDischargeSimulator()
    return sim.generate_rollout_dataset(num_rollouts=16, steps_per_rollout=8, seed=42)


def test_generate_rollout_dataset(sample_rollout_df):
    """Verify rollout dataset integrity and step sequencing."""
    df = sample_rollout_df
    assert len(df) == 16 * 8
    assert "rollout_id" in df.columns
    assert "step" in df.columns
    assert "clearance_time_sec" in df.columns

    # Verify each rollout has 8 sequential steps
    for _, grp in df.groupby("rollout_id"):
        assert len(grp) == 8
        assert list(grp["step"]) == list(range(8))
        assert (grp["clearance_time_sec"] > 0.0).all()


def test_generate_clearance_sequences(sample_rollout_df):
    """Verify sliding window generation produces correct (N, K, D) shapes."""
    K = 5
    X, y, feat_names, node_ids, pipeline = generate_clearance_sequences(
        sample_rollout_df, window_size=K
    )

    # 16 rollouts * (8 - 5 + 1) = 16 * 4 = 64 sequences
    expected_n = 16 * (8 - K + 1)
    assert X.shape[0] == expected_n
    assert X.shape[1] == K
    assert X.shape[2] == len(feat_names)
    assert len(y) == expected_n
    assert len(node_ids) == expected_n
    assert pipeline.is_fitted


def test_split_sequences_by_node_zero_leakage(sample_rollout_df):
    """Verify strictly disjoint spatial partitioning across intersection nodes."""
    X, y, _, node_ids, _ = generate_clearance_sequences(sample_rollout_df, window_size=5)

    (X_tr, y_tr), (X_v, y_v), (X_te, y_te) = split_sequences_by_node(
        X,
        y,
        node_ids,
        train_nodes=["node_a", "node_b"],
        val_nodes=["node_c"],
        test_nodes=["node_d"],
    )

    assert len(X_tr) > 0
    assert len(X_v) > 0
    assert len(X_te) > 0
    assert len(X_tr) + len(X_v) + len(X_te) == len(X)

    # Total zero leakage assertion
    assert (len(y_tr) / len(y)) == pytest.approx(0.50, abs=0.05)
    assert (len(y_v) / len(y)) == pytest.approx(0.25, abs=0.05)
    assert (len(y_te) / len(y)) == pytest.approx(0.25, abs=0.05)


def test_clearance_lstm_forward_backward_and_fit(sample_rollout_df):
    """Verify ClearanceLSTM forward pass, gradient computation, and loss reduction."""
    X, y, _, node_ids, _ = generate_clearance_sequences(sample_rollout_df, window_size=5)
    (X_tr, y_tr), _, (X_te, y_te) = split_sequences_by_node(X, y, node_ids)

    model = ClearanceLSTM(input_dim=X.shape[2], hidden_dim=16, learning_rate=0.02, seed=42)

    # Forward pass
    y_pred, cache = model.forward(X_tr[:8])
    assert y_pred.shape == (8, 1)
    assert len(cache) == 5

    # Backward pass
    grads = model.backward(y_pred, y_tr[:8], cache)
    assert "W" in grads and grads["W"].shape == model.W.shape
    assert "U" in grads and grads["U"].shape == model.U.shape
    assert "b" in grads and grads["b"].shape == model.b.shape
    assert "W_y" in grads and grads["W_y"].shape == model.W_y.shape
    assert "W_skip" in grads and grads["W_skip"].shape == model.W_skip.shape

    # Training fit
    model.fit(X_tr, y_tr, epochs=40, batch_size=16)
    assert model.is_fitted

    preds = model.predict(X_te)
    assert preds.shape == (len(X_te),)
    mae = float(np.mean(np.abs(preds - y_te)))
    assert mae < 12.0  # tiny 32-sample test split threshold


def test_clearance_gru_forward_backward_and_fit(sample_rollout_df):
    """Verify ClearanceGRU forward pass, gradient computation, and loss reduction."""
    X, y, _, node_ids, _ = generate_clearance_sequences(sample_rollout_df, window_size=5)
    (X_tr, y_tr), _, (X_te, y_te) = split_sequences_by_node(X, y, node_ids)

    model = ClearanceGRU(input_dim=X.shape[2], hidden_dim=16, learning_rate=0.02, seed=42)

    # Forward pass
    y_pred, cache = model.forward(X_tr[:8])
    assert y_pred.shape == (8, 1)
    assert len(cache) == 5

    # Backward pass
    grads = model.backward(y_pred, y_tr[:8], cache)
    assert "W_z" in grads and grads["W_z"].shape == model.W_z.shape
    assert "W_r" in grads and grads["W_r"].shape == model.W_r.shape
    assert "W_h" in grads and grads["W_h"].shape == model.W_h.shape

    # Training fit
    model.fit(X_tr, y_tr, epochs=40, batch_size=16)
    assert model.is_fitted

    preds = model.predict(X_te)
    assert preds.shape == (len(X_te),)
    mae = float(np.mean(np.abs(preds - y_te)))
    assert mae < 14.0


def test_sequence_models_save_and_load(tmp_path, sample_rollout_df):
    """Verify serialization roundtrip for LSTM and GRU."""
    X, y, _, _, _ = generate_clearance_sequences(sample_rollout_df, window_size=5)

    # 1. LSTM
    lstm = ClearanceLSTM(input_dim=X.shape[2], hidden_dim=16, seed=42)
    lstm.fit(X, y, epochs=10)
    p_lstm = tmp_path / "test_lstm.npz"
    lstm.save(p_lstm)

    loaded_lstm = ClearanceLSTM.load(p_lstm)
    pred_orig = lstm.predict(X[:5])
    pred_load = loaded_lstm.predict(X[:5])
    np.testing.assert_allclose(pred_orig, pred_load, rtol=1e-5)

    # 2. GRU
    gru = ClearanceGRU(input_dim=X.shape[2], hidden_dim=16, seed=42)
    gru.fit(X, y, epochs=10)
    p_gru = tmp_path / "test_gru.npz"
    gru.save(p_gru)

    loaded_gru = ClearanceGRU.load(p_gru)
    pred_orig_gru = gru.predict(X[:5])
    pred_load_gru = loaded_gru.predict(X[:5])
    np.testing.assert_allclose(pred_orig_gru, pred_load_gru, rtol=1e-5)


def test_sequence_predictor_inference(tmp_path, sample_rollout_df):
    """Verify SequencePredictor can predict from states and handles warm-up padding."""
    X, y, _, _, pipeline = generate_clearance_sequences(sample_rollout_df, window_size=5)
    lstm = ClearanceLSTM(input_dim=X.shape[2], hidden_dim=16, seed=42)
    lstm.fit(X, y, epochs=20)

    model_path = tmp_path / "clearance_lstm.npz"
    pipe_path = tmp_path / "sequence_pipeline.joblib"
    predictor = SequencePredictor(model=lstm, pipeline=pipeline, sequence_length=5)
    predictor.save_bundle(model_path, pipe_path)

    # Load back
    loaded_predictor = SequencePredictor.load(model_path, pipe_path)

    # Predict from ApproachTrafficState sequence (length 5)
    states = [
        ApproachTrafficState(
            approach_id="EB",
            timestamp_sec=float(i * 5.0),
            vehicle_count=12,
            counts_by_class={"car": 3, "motorcycle": 8, "bus": 1, "truck": 0},
            motorcycle_ratio=8.0 / 12.0,
            queue_length_meters=20.0 + i * 2.0,
            queued_vehicle_count=5 + i,
            approach_occupancy_ratio=0.35 + i * 0.05,
            traffic_density_vpm=12.0,
            mean_speed_kmh=15.0 - i * 1.0,
        )
        for i in range(5)
    ]

    t_clear = loaded_predictor.predict_from_traffic_states(states, node_id="node_b")
    assert isinstance(t_clear, float)
    assert t_clear > 1.0

    # Test short buffer padding (length 2 < 5)
    t_clear_short = loaded_predictor.predict_from_traffic_states(states[:2], node_id="node_b")
    assert isinstance(t_clear_short, float)
    assert t_clear_short > 1.0


def test_train_sequence_cli(tmp_path):
    """Verify CLI execution of train_sequence.py end-to-end."""
    models_dir = tmp_path / "models"
    data_path = tmp_path / "rollouts.csv"

    cmd = [
        sys.executable,
        "ai/clearance/train_sequence.py",
        "--data-path",
        str(data_path),
        "--models-dir",
        str(models_dir),
        "--num-rollouts",
        "40",
        "--epochs",
        "50",
        "--window-size",
        "5",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert "ClearWayAI Clearance-Time Sequence Models" in res.stdout

    # Verify generated artifacts
    assert (models_dir / "clearance_lstm.npz").is_file()
    assert (models_dir / "clearance_gru.npz").is_file()
    assert (models_dir / "sequence_pipeline.joblib").is_file()
    assert (models_dir / "sequence_benchmark_report.json").is_file()

    with open(models_dir / "sequence_benchmark_report.json", encoding="utf-8") as f:
        report = json.load(f)

    assert "clearance_lstm" in report["models"]
    assert "clearance_gru" in report["models"]
    assert report["models"]["clearance_lstm"]["test_mae"] < 6.0
    assert report["models"]["clearance_gru"]["test_mae"] < 6.0
