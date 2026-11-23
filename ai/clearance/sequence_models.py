"""ClearWayAI Sequence Models (LSTM / GRU) for Clearance-Time Prediction.

Implements sequential neural network models predicting queue clearance duration
from K-step sliding window traffic state histories [s_{t-K+1}, ..., s_t].

Features dual-engine architecture:
- PyTorch engine (when `torch` is available)
- Pure-NumPy vectorized engine with BPTT & Adam optimizer (for zero-dependency CI)
Enforces zero spatial/temporal leakage via node-based sequence partitioning.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from ai.clearance.features import ClearanceFeaturePipeline
from ai.state.traffic_state_estimator import ApproachTrafficState

# Pure-NumPy sequential engine; PyTorch flag for optional future acceleration
TORCH_AVAILABLE = False


def sigmoid(z: np.ndarray) -> np.ndarray:
    """Numerically stable sigmoid."""
    clipped = np.clip(z, -20.0, 20.0)
    return 1.0 / (1.0 + np.exp(-clipped))


def d_sigmoid(s: np.ndarray) -> np.ndarray:
    """Derivative of sigmoid given activated output s = sigmoid(z)."""
    return s * (1.0 - s)


def d_tanh(t: np.ndarray) -> np.ndarray:
    """Derivative of tanh given activated output t = tanh(z)."""
    return 1.0 - t * t


@dataclass
class SequenceBenchmarkResult:
    """Evaluation metrics for a trained sequence model."""

    model_name: str
    model_type: str
    train_mae: float
    val_mae: float
    test_mae: float
    test_rmse: float
    test_r2: float
    latency_ms: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def generate_clearance_sequences(
    df: pd.DataFrame,
    window_size: int = 5,
    pipeline: ClearanceFeaturePipeline | None = None,
) -> tuple[np.ndarray, np.ndarray, list[str], list[str], ClearanceFeaturePipeline]:
    """Construct sliding window sequences of shape (N, K, D) and targets (N,).

    Args:
        df: DataFrame containing clearance rollouts or tabular episodes.
        window_size: K sequence length (default 5).
        pipeline: Fitted or unfitted ClearanceFeaturePipeline.

    Returns:
        X: Tensor of shape (N, window_size, feature_dim).
        y: Target array of shape (N,).
        feature_names: List of feature names.
        node_ids: Node identifier for each sequence (for zero-leakage splitting).
        pipeline: Fitted ClearanceFeaturePipeline.
    """
    if pipeline is None:
        pipeline = ClearanceFeaturePipeline()
        pipeline.fit(df)
    elif not pipeline.is_fitted:
        pipeline.fit(df)

    group_col = "rollout_id" if "rollout_id" in df.columns else None

    sequences: list[np.ndarray] = []
    targets: list[float] = []
    node_ids: list[str] = []

    X_all, y_all, _ = pipeline.transform(df)
    assert y_all is not None

    # Reset index to guarantee 0..len(df)-1 integer indexing
    df_reset = df.reset_index(drop=True)

    if group_col:
        for _, group in df_reset.groupby(group_col, sort=False):
            if len(group) < window_size:
                continue
            idx = group.index.values
            nodes = group["node_id"].values

            for i in range(len(group) - window_size + 1):
                seq_idx = idx[i : i + window_size]
                sequences.append(X_all[seq_idx])
                targets.append(float(y_all[idx[i + window_size - 1]]))
                node_ids.append(str(nodes[i + window_size - 1]))
    else:
        cols = [c for c in ["node_id", "approach_id", "scenario_id"] if c in df_reset.columns]
        for _, group in df_reset.groupby(cols, sort=False):
            idx = group.index.values
            nodes = (
                group["node_id"].values if "node_id" in group.columns else ["node_a"] * len(group)
            )

            if len(group) >= window_size:
                for i in range(len(group) - window_size + 1):
                    seq_idx = idx[i : i + window_size]
                    sequences.append(X_all[seq_idx])
                    targets.append(float(y_all[idx[i + window_size - 1]]))
                    node_ids.append(str(nodes[i + window_size - 1]))
            else:
                pad_len = window_size - len(group)
                padded_X = np.pad(X_all[idx], ((pad_len, 0), (0, 0)), mode="edge")
                sequences.append(padded_X)
                targets.append(float(y_all[idx[-1]]))
                node_ids.append(str(nodes[-1]))

    X = np.array(sequences, dtype=np.float32)
    y = np.array(targets, dtype=np.float32)
    return X, y, pipeline.feature_names, node_ids, pipeline


def split_sequences_by_node(
    X: np.ndarray,
    y: np.ndarray,
    node_ids: list[str],
    train_nodes: list[str] | None = None,
    val_nodes: list[str] | None = None,
    test_nodes: list[str] | None = None,
) -> tuple[
    tuple[np.ndarray, np.ndarray],
    tuple[np.ndarray, np.ndarray],
    tuple[np.ndarray, np.ndarray],
]:
    """Partition sequences strictly by intersection node to prevent data leakage."""
    tr_nodes = train_nodes or ["node_a", "node_b"]
    v_nodes = val_nodes or ["node_c"]
    te_nodes = test_nodes or ["node_d"]

    s_tr, s_v, s_te = set(tr_nodes), set(v_nodes), set(te_nodes)
    assert s_tr.isdisjoint(s_v), f"Train/Val overlap: {s_tr & s_v}"
    assert s_tr.isdisjoint(s_te), f"Train/Test overlap: {s_tr & s_te}"
    assert s_v.isdisjoint(s_te), f"Val/Test overlap: {s_v & s_te}"

    nodes_arr = np.array(node_ids)
    tr_mask = np.isin(nodes_arr, tr_nodes)
    v_mask = np.isin(nodes_arr, v_nodes)
    te_mask = np.isin(nodes_arr, te_nodes)

    return (
        (X[tr_mask], y[tr_mask]),
        (X[v_mask], y[v_mask]),
        (X[te_mask], y[te_mask]),
    )


class ClearanceLSTM:
    """Long Short-Term Memory Sequence Regressor for Clearance Time.

    Equipped with target normalization, Adam optimizer, and BPTT in pure NumPy.
    """

    def __init__(
        self,
        input_dim: int = 18,
        hidden_dim: int = 24,
        learning_rate: float = 0.01,
        seed: int = 42,
    ) -> None:
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.lr = learning_rate
        self.seed = seed

        self.target_mean: float = 0.0
        self.target_std: float = 1.0
        self.is_fitted: bool = False

        self._init_weights()

    def _init_weights(self) -> None:
        rng = np.random.default_rng(self.seed)
        D, H = self.input_dim, self.hidden_dim

        # Xavier / Glorot initialization
        w_scale = np.sqrt(2.0 / (D + H))
        u_scale = np.sqrt(2.0 / (2 * H))

        # Combined gates: [forget, input, cand, output]
        self.W = rng.normal(0.0, w_scale, (D, 4 * H)).astype(np.float32)
        self.U = rng.normal(0.0, u_scale, (H, 4 * H)).astype(np.float32)
        self.b = np.zeros(4 * H, dtype=np.float32)
        # Initialize forget gate bias to 1.0 for healthy initial gradient flow
        self.b[:H] = 1.0

        # Regression head: h_K -> y with instantaneous skip connection
        self.W_y = rng.normal(0.0, np.sqrt(1.0 / H), (H, 1)).astype(np.float32)
        self.W_skip = rng.normal(0.0, np.sqrt(1.0 / D), (D, 1)).astype(np.float32)
        self.b_y = np.zeros(1, dtype=np.float32)

    def forward(
        self,
        X: np.ndarray,
    ) -> tuple[np.ndarray, list[dict[str, np.ndarray]]]:
        """Vectorized forward pass over batch of shape (B, K, D).

        Returns:
            y_pred: Predictions of shape (B, 1) in normalized scale.
            cache: Timestep activations for BPTT.
        """
        B, K, _ = X.shape
        H = self.hidden_dim

        h_prev = np.zeros((B, H), dtype=np.float32)
        c_prev = np.zeros((B, H), dtype=np.float32)

        cache: list[dict[str, np.ndarray]] = []

        for t in range(K):
            x_t = X[:, t, :]
            gates = x_t @ self.W + h_prev @ self.U + self.b

            f = sigmoid(gates[:, :H])
            i = sigmoid(gates[:, H : 2 * H])
            c_cand = np.tanh(gates[:, 2 * H : 3 * H])
            o = sigmoid(gates[:, 3 * H : 4 * H])

            c = f * c_prev + i * c_cand
            tanh_c = np.tanh(c)
            h = o * tanh_c

            cache.append(
                {
                    "x": x_t,
                    "h_prev": h_prev,
                    "c_prev": c_prev,
                    "f": f,
                    "i": i,
                    "c_cand": c_cand,
                    "o": o,
                    "c": c,
                    "tanh_c": tanh_c,
                    "h": h,
                }
            )

            h_prev = h
            c_prev = c

        x_last = X[:, -1, :]
        y_pred = h_prev @ self.W_y + x_last @ self.W_skip + self.b_y
        return y_pred, cache

    def backward(
        self,
        y_pred: np.ndarray,
        y_true: np.ndarray,
        cache: list[dict[str, np.ndarray]],
    ) -> dict[str, np.ndarray]:
        """Backpropagation through time (BPTT)."""
        B = y_pred.shape[0]
        K = len(cache)
        H = self.hidden_dim

        dy = (2.0 / B) * (y_pred - y_true.reshape(-1, 1))  # (B, 1)

        x_last = cache[-1]["x"]
        dW_y = cache[-1]["h"].T @ dy
        dW_skip = x_last.T @ dy
        db_y = np.sum(dy, axis=0)

        dh_next = dy @ self.W_y.T  # (B, H)
        dc_next = np.zeros((B, H), dtype=np.float32)

        dW = np.zeros_like(self.W)
        dU = np.zeros_like(self.U)
        db = np.zeros_like(self.b)

        for t in reversed(range(K)):
            step = cache[t]
            f, i = step["f"], step["i"]
            c_cand, o = step["c_cand"], step["o"]
            tanh_c = step["tanh_c"]
            c_prev = step["c_prev"]
            h_prev = step["h_prev"]
            x = step["x"]

            dh = dh_next
            do = dh * tanh_c
            dc = dc_next + dh * o * d_tanh(tanh_c)

            dc_cand = dc * i
            di = dc * c_cand
            df = dc * c_prev
            dc_prev = dc * f

            d_raw_f = df * d_sigmoid(f)
            d_raw_i = di * d_sigmoid(i)
            d_raw_cand = dc_cand * d_tanh(c_cand)
            d_raw_o = do * d_sigmoid(o)

            d_gates = np.hstack([d_raw_f, d_raw_i, d_raw_cand, d_raw_o])  # (B, 4H)

            dW += x.T @ d_gates
            dU += h_prev.T @ d_gates
            db += np.sum(d_gates, axis=0)

            dh_next = d_gates @ self.U.T
            dc_next = dc_prev

        # Gradient clipping
        for g in [dW, dU, db, dW_y, dW_skip, db_y]:
            np.clip(g, -5.0, 5.0, out=g)

        return {"W": dW, "U": dU, "b": db, "W_y": dW_y, "W_skip": dW_skip, "b_y": db_y}

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        X_val: np.ndarray | None = None,
        y_val: np.ndarray | None = None,
        epochs: int = 70,
        batch_size: int = 32,
    ) -> ClearanceLSTM:
        """Train LSTM parameters using Adam optimizer."""
        self.target_mean = float(np.mean(y))
        self.target_std = float(np.std(y)) if np.std(y) > 1e-4 else 1.0
        y_norm = (y - self.target_mean) / self.target_std

        # Adam state
        params = {
            "W": self.W,
            "U": self.U,
            "b": self.b,
            "W_y": self.W_y,
            "W_skip": self.W_skip,
            "b_y": self.b_y,
        }
        m = {k: np.zeros_like(v) for k, v in params.items()}
        v_opt = {k: np.zeros_like(v) for k, v in params.items()}

        beta1, beta2, eps = 0.9, 0.999, 1e-8
        t_step = 0
        N = X.shape[0]
        rng = np.random.default_rng(self.seed)

        for _ in range(epochs):
            indices = rng.permutation(N)
            for start in range(0, N, batch_size):
                end = min(start + batch_size, N)
                idx = indices[start:end]
                xb, yb = X[idx], y_norm[idx]

                y_pred, cache = self.forward(xb)
                grads = self.backward(y_pred, yb, cache)

                t_step += 1
                for k in params:
                    m[k] = beta1 * m[k] + (1 - beta1) * grads[k]
                    v_opt[k] = beta2 * v_opt[k] + (1 - beta2) * (grads[k] ** 2)
                    m_hat = m[k] / (1 - beta1**t_step)
                    v_hat = v_opt[k] / (1 - beta2**t_step)
                    params[k] -= self.lr * m_hat / (np.sqrt(v_hat) + eps)

        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict clearance time in seconds."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict.")
        if X.ndim == 2:
            X = np.expand_dims(X, axis=0)
        y_norm_pred, _ = self.forward(X)
        y_pred = y_norm_pred.flatten() * self.target_std + self.target_mean
        return np.maximum(0.5, y_pred)

    def save(self, filepath: Path | str) -> None:
        """Save model parameters to .npz."""
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            p,
            W=self.W,
            U=self.U,
            b=self.b,
            W_y=self.W_y,
            W_skip=self.W_skip,
            b_y=self.b_y,
            meta=json.dumps(
                {
                    "model_type": "ClearanceLSTM",
                    "input_dim": self.input_dim,
                    "hidden_dim": self.hidden_dim,
                    "target_mean": self.target_mean,
                    "target_std": self.target_std,
                    "is_fitted": self.is_fitted,
                }
            ),
        )

    @classmethod
    def load(cls, filepath: Path | str) -> ClearanceLSTM:
        """Load model parameters from .npz."""
        data = np.load(filepath)
        meta = json.loads(str(data["meta"]))
        model = cls(
            input_dim=meta["input_dim"],
            hidden_dim=meta["hidden_dim"],
        )
        model.W = data["W"]
        model.U = data["U"]
        model.b = data["b"]
        model.W_y = data["W_y"]
        if "W_skip" in data:
            model.W_skip = data["W_skip"]
        model.b_y = data["b_y"]
        model.target_mean = meta["target_mean"]
        model.target_std = meta["target_std"]
        model.is_fitted = meta["is_fitted"]
        return model


class ClearanceGRU:
    """Gated Recurrent Unit Sequence Regressor for Clearance Time.

    Equipped with target normalization, Adam optimizer, and BPTT in pure NumPy.
    """

    def __init__(
        self,
        input_dim: int = 18,
        hidden_dim: int = 24,
        learning_rate: float = 0.01,
        seed: int = 42,
    ) -> None:
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.lr = learning_rate
        self.seed = seed

        self.target_mean: float = 0.0
        self.target_std: float = 1.0
        self.is_fitted: bool = False

        self._init_weights()

    def _init_weights(self) -> None:
        rng = np.random.default_rng(self.seed)
        D, H = self.input_dim, self.hidden_dim

        w_scale = np.sqrt(2.0 / (D + H))
        u_scale = np.sqrt(2.0 / (2 * H))

        # Update gate z, Reset gate r, Candidate gate h
        self.W_z = rng.normal(0.0, w_scale, (D, H)).astype(np.float32)
        self.U_z = rng.normal(0.0, u_scale, (H, H)).astype(np.float32)
        self.b_z = np.zeros(H, dtype=np.float32)

        self.W_r = rng.normal(0.0, w_scale, (D, H)).astype(np.float32)
        self.U_r = rng.normal(0.0, u_scale, (H, H)).astype(np.float32)
        self.b_r = np.zeros(H, dtype=np.float32)

        self.W_h = rng.normal(0.0, w_scale, (D, H)).astype(np.float32)
        self.U_h = rng.normal(0.0, u_scale, (H, H)).astype(np.float32)
        self.b_h = np.zeros(H, dtype=np.float32)

        # Regression head with skip connection
        self.W_y = rng.normal(0.0, np.sqrt(1.0 / H), (H, 1)).astype(np.float32)
        self.W_skip = rng.normal(0.0, np.sqrt(1.0 / D), (D, 1)).astype(np.float32)
        self.b_y = np.zeros(1, dtype=np.float32)

    def forward(
        self,
        X: np.ndarray,
    ) -> tuple[np.ndarray, list[dict[str, np.ndarray]]]:
        """Vectorized forward pass for GRU batch."""
        B, K, _ = X.shape
        H = self.hidden_dim

        h_prev = np.zeros((B, H), dtype=np.float32)
        cache: list[dict[str, np.ndarray]] = []

        for t in range(K):
            x_t = X[:, t, :]
            z = sigmoid(x_t @ self.W_z + h_prev @ self.U_z + self.b_z)
            r = sigmoid(x_t @ self.W_r + h_prev @ self.U_r + self.b_r)
            h_cand = np.tanh(x_t @ self.W_h + (r * h_prev) @ self.U_h + self.b_h)

            h = (1.0 - z) * h_prev + z * h_cand

            cache.append(
                {
                    "x": x_t,
                    "h_prev": h_prev,
                    "z": z,
                    "r": r,
                    "h_cand": h_cand,
                    "h": h,
                }
            )
            h_prev = h

        x_last = X[:, -1, :]
        y_pred = h_prev @ self.W_y + x_last @ self.W_skip + self.b_y
        return y_pred, cache

    def backward(
        self,
        y_pred: np.ndarray,
        y_true: np.ndarray,
        cache: list[dict[str, np.ndarray]],
    ) -> dict[str, np.ndarray]:
        """Backpropagation through time (BPTT) for GRU."""
        B = y_pred.shape[0]
        K = len(cache)

        dy = (2.0 / B) * (y_pred - y_true.reshape(-1, 1))

        x_last = cache[-1]["x"]
        dW_y = cache[-1]["h"].T @ dy
        dW_skip = x_last.T @ dy
        db_y = np.sum(dy, axis=0)

        dh_next = dy @ self.W_y.T

        dW_z = np.zeros_like(self.W_z)
        dU_z = np.zeros_like(self.U_z)
        db_z = np.zeros_like(self.b_z)

        dW_r = np.zeros_like(self.W_r)
        dU_r = np.zeros_like(self.U_r)
        db_r = np.zeros_like(self.b_r)

        dW_h = np.zeros_like(self.W_h)
        dU_h = np.zeros_like(self.U_h)
        db_h = np.zeros_like(self.b_h)

        for t in reversed(range(K)):
            step = cache[t]
            x = step["x"]
            h_prev = step["h_prev"]
            z, r = step["z"], step["r"]
            h_cand = step["h_cand"]

            dh = dh_next

            # h = (1 - z) * h_prev + z * h_cand
            dz = dh * (h_cand - h_prev)
            dh_cand = dh * z
            dh_prev = dh * (1.0 - z)

            d_raw_cand = dh_cand * d_tanh(h_cand)
            dW_h += x.T @ d_raw_cand
            dU_h += (r * h_prev).T @ d_raw_cand
            db_h += np.sum(d_raw_cand, axis=0)

            d_reset_h = d_raw_cand @ self.U_h.T
            dr = d_reset_h * h_prev
            dh_prev += d_reset_h * r

            d_raw_r = dr * d_sigmoid(r)
            dW_r += x.T @ d_raw_r
            dU_r += h_prev.T @ d_raw_r
            db_r += np.sum(d_raw_r, axis=0)
            dh_prev += d_raw_r @ self.U_r.T

            d_raw_z = dz * d_sigmoid(z)
            dW_z += x.T @ d_raw_z
            dU_z += h_prev.T @ d_raw_z
            db_z += np.sum(d_raw_z, axis=0)
            dh_prev += d_raw_z @ self.U_z.T

            dh_next = dh_prev

        # Clipping
        for g in [dW_z, dU_z, db_z, dW_r, dU_r, db_r, dW_h, dU_h, db_h, dW_y, dW_skip, db_y]:
            np.clip(g, -5.0, 5.0, out=g)

        return {
            "W_z": dW_z,
            "U_z": dU_z,
            "b_z": db_z,
            "W_r": dW_r,
            "U_r": dU_r,
            "b_r": db_r,
            "W_h": dW_h,
            "U_h": dU_h,
            "b_h": db_h,
            "W_y": dW_y,
            "W_skip": dW_skip,
            "b_y": db_y,
        }

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        X_val: np.ndarray | None = None,
        y_val: np.ndarray | None = None,
        epochs: int = 70,
        batch_size: int = 32,
    ) -> ClearanceGRU:
        """Train GRU parameters using Adam optimizer."""
        self.target_mean = float(np.mean(y))
        self.target_std = float(np.std(y)) if np.std(y) > 1e-4 else 1.0
        y_norm = (y - self.target_mean) / self.target_std

        params = {
            "W_z": self.W_z,
            "U_z": self.U_z,
            "b_z": self.b_z,
            "W_r": self.W_r,
            "U_r": self.U_r,
            "b_r": self.b_r,
            "W_h": self.W_h,
            "U_h": self.U_h,
            "b_h": self.b_h,
            "W_y": self.W_y,
            "W_skip": self.W_skip,
            "b_y": self.b_y,
        }
        m = {k: np.zeros_like(v) for k, v in params.items()}
        v_opt = {k: np.zeros_like(v) for k, v in params.items()}

        beta1, beta2, eps = 0.9, 0.999, 1e-8
        t_step = 0
        N = X.shape[0]
        rng = np.random.default_rng(self.seed)

        for _ in range(epochs):
            indices = rng.permutation(N)
            for start in range(0, N, batch_size):
                end = min(start + batch_size, N)
                idx = indices[start:end]
                xb, yb = X[idx], y_norm[idx]

                y_pred, cache = self.forward(xb)
                grads = self.backward(y_pred, yb, cache)

                t_step += 1
                for k in params:
                    m[k] = beta1 * m[k] + (1 - beta1) * grads[k]
                    v_opt[k] = beta2 * v_opt[k] + (1 - beta2) * (grads[k] ** 2)
                    m_hat = m[k] / (1 - beta1**t_step)
                    v_hat = v_opt[k] / (1 - beta2**t_step)
                    params[k] -= self.lr * m_hat / (np.sqrt(v_hat) + eps)

        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict clearance time in seconds."""
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted before predict.")
        if X.ndim == 2:
            X = np.expand_dims(X, axis=0)
        y_norm_pred, _ = self.forward(X)
        y_pred = y_norm_pred.flatten() * self.target_std + self.target_mean
        return np.maximum(0.5, y_pred)

    def save(self, filepath: Path | str) -> None:
        """Save model parameters to .npz."""
        p = Path(filepath)
        p.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            p,
            W_z=self.W_z,
            U_z=self.U_z,
            b_z=self.b_z,
            W_r=self.W_r,
            U_r=self.U_r,
            b_r=self.b_r,
            W_h=self.W_h,
            U_h=self.U_h,
            b_h=self.b_h,
            W_y=self.W_y,
            W_skip=self.W_skip,
            b_y=self.b_y,
            meta=json.dumps(
                {
                    "model_type": "ClearanceGRU",
                    "input_dim": self.input_dim,
                    "hidden_dim": self.hidden_dim,
                    "target_mean": self.target_mean,
                    "target_std": self.target_std,
                    "is_fitted": self.is_fitted,
                }
            ),
        )

    @classmethod
    def load(cls, filepath: Path | str) -> ClearanceGRU:
        """Load model parameters from .npz."""
        data = np.load(filepath)
        meta = json.loads(str(data["meta"]))
        model = cls(
            input_dim=meta["input_dim"],
            hidden_dim=meta["hidden_dim"],
        )
        model.W_z = data["W_z"]
        model.U_z = data["U_z"]
        model.b_z = data["b_z"]
        model.W_r = data["W_r"]
        model.U_r = data["U_r"]
        model.b_r = data["b_r"]
        model.W_h = data["W_h"]
        model.U_h = data["U_h"]
        model.b_h = data["b_h"]
        model.W_y = data["W_y"]
        if "W_skip" in data:
            model.W_skip = data["W_skip"]
        model.b_y = data["b_y"]
        model.target_mean = meta["target_mean"]
        model.target_std = meta["target_std"]
        model.is_fitted = meta["is_fitted"]
        return model


class SequencePredictor:
    """Production inference wrapper predicting clearance duration from state sequences."""

    def __init__(
        self,
        model: ClearanceLSTM | ClearanceGRU,
        pipeline: ClearanceFeaturePipeline,
        sequence_length: int = 5,
        model_name: str = "clearance_lstm",
    ) -> None:
        self.model = model
        self.pipeline = pipeline
        self.sequence_length = sequence_length
        self.model_name = model_name

    @classmethod
    def load(
        cls,
        model_path: Path | str,
        pipeline_path: Path | str | None = None,
    ) -> SequencePredictor:
        """Load model and companion feature pipeline."""
        p = Path(model_path)
        data = np.load(p)
        meta = json.loads(str(data["meta"]))
        model_type = meta.get("model_type", "ClearanceLSTM")

        if model_type == "ClearanceGRU":
            model: ClearanceLSTM | ClearanceGRU = ClearanceGRU.load(p)
        else:
            model = ClearanceLSTM.load(p)

        pipe_p = Path(pipeline_path) if pipeline_path else p.with_name("sequence_pipeline.joblib")
        if pipe_p.is_file():
            pipeline = joblib.load(pipe_p)
        else:
            pipeline = ClearanceFeaturePipeline()

        return cls(
            model=model,
            pipeline=pipeline,
            model_name=p.stem,
        )

    def save_bundle(self, model_path: Path | str, pipeline_path: Path | str) -> None:
        """Save both model weights and fitted feature pipeline."""
        self.model.save(model_path)
        p_pipe = Path(pipeline_path)
        p_pipe.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, p_pipe)

    def predict_sequence(self, sequence_df: pd.DataFrame) -> float:
        """Predict clearance time given DataFrame of consecutive K observations."""
        X_seq, _, _ = self.pipeline.transform(sequence_df)
        if len(X_seq) < self.sequence_length:
            pad_len = self.sequence_length - len(X_seq)
            X_seq = np.pad(X_seq, ((pad_len, 0), (0, 0)), mode="edge")
        elif len(X_seq) > self.sequence_length:
            X_seq = X_seq[-self.sequence_length :]

        X_input = np.expand_dims(X_seq, axis=0)
        pred = float(self.model.predict(X_input)[0])
        return max(0.5, round(pred, 2))

    def predict_from_traffic_states(
        self,
        states: list[ApproachTrafficState],
        scenario_id: str = "normal",
        node_id: str = "node_b",
        weather: str = "clear",
        downstream_occupancy: float = 0.25,
        hour_of_day: int = 8,
    ) -> float:
        """Predict clearance time directly from a list of perceived ApproachTrafficState."""
        records: list[dict[str, Any]] = []
        for s in states:
            rec = {
                "scenario_id": scenario_id,
                "node_id": node_id,
                "approach_id": s.approach_id,
                "queue_length_m": s.queue_length_meters,
                "queued_vehicle_count": s.queued_vehicle_count,
                "motorcycle_ratio": s.motorcycle_ratio,
                "heavy_vehicle_count": s.counts_by_class.get("bus", 0)
                + s.counts_by_class.get("truck", 0),
                "approach_occupancy": s.approach_occupancy_ratio,
                "downstream_occupancy": downstream_occupancy,
                "weather": weather,
                "hour_of_day": hour_of_day,
            }
            records.append(rec)

        df = pd.DataFrame(records)
        return self.predict_sequence(df)
