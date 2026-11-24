"""Proximal Policy Optimization (PPO) Actor-Critic Agent for Corridor Signal Coordination (Task 59).

Implements vectorized Actor-Critic neural networks, Generalized Advantage Estimation (GAE),
and clipped surrogate objective optimization in pure NumPy for high-performance,
zero-external-dependency execution.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np


def softmax(x: np.ndarray) -> np.ndarray:
    """Numerically stable softmax along last axis."""
    e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return e_x / np.sum(e_x, axis=-1, keepdims=True)


@dataclass
class PPOConfig:
    """Hyperparameters for PPO Actor-Critic optimization."""

    obs_dim: int = 25
    action_dim: int = 4
    hidden_dim: int = 64
    sub_hidden_dim: int = 32
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_epsilon: float = 0.20
    learning_rate: float = 3e-4
    value_coef: float = 0.5
    entropy_coef: float = 0.01
    epochs_per_update: int = 4
    batch_size: int = 32


class AdamOptimizer:
    """Vectorized Adam optimizer for dictionary of NumPy parameter arrays."""

    def __init__(
        self,
        params: dict[str, np.ndarray],
        lr: float = 3e-4,
        beta1: float = 0.9,
        beta2: float = 0.999,
        eps: float = 1e-8,
    ):
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.m: dict[str, np.ndarray] = {k: np.zeros_like(v) for k, v in params.items()}
        self.v: dict[str, np.ndarray] = {k: np.zeros_like(v) for k, v in params.items()}
        self.t = 0

    def step(self, params: dict[str, np.ndarray], grads: dict[str, np.ndarray]) -> None:
        """Apply gradient update with bias-corrected first and second moments."""
        self.t += 1
        lr_t = self.lr * (np.sqrt(1.0 - self.beta2**self.t) / (1.0 - self.beta1**self.t))

        for k in params:
            if k not in grads:
                continue
            g = np.clip(grads[k], -5.0, 5.0)  # Gradient clipping
            self.m[k] = self.beta1 * self.m[k] + (1.0 - self.beta1) * g
            self.v[k] = self.beta2 * self.v[k] + (1.0 - self.beta2) * (g * g)
            params[k] -= lr_t * self.m[k] / (np.sqrt(self.v[k]) + self.eps)


class ActorCriticPolicy:
    """Two-head Actor-Critic neural network for discrete action space."""

    def __init__(self, config: PPOConfig, seed: int | None = None):
        self.config = config
        self._rng = np.random.default_rng(seed)

        obs_d = config.obs_dim
        h_d = config.hidden_dim
        sub_h = config.sub_hidden_dim
        act_d = config.action_dim

        # Xavier / He weight initialization
        scale_a1 = np.sqrt(2.0 / (obs_d + h_d))
        scale_a2 = np.sqrt(2.0 / (h_d + sub_h))
        scale_a3 = np.sqrt(2.0 / (sub_h + act_d))

        self.params: dict[str, np.ndarray] = {
            # Actor network
            "w_a1": self._rng.normal(0, scale_a1, (obs_d, h_d)).astype(np.float32),
            "b_a1": np.zeros(h_d, dtype=np.float32),
            "w_a2": self._rng.normal(0, scale_a2, (h_d, sub_h)).astype(np.float32),
            "b_a2": np.zeros(sub_h, dtype=np.float32),
            "w_a3": self._rng.normal(0, scale_a3, (sub_h, act_d)).astype(np.float32) * 0.1,
            "b_a3": np.zeros(act_d, dtype=np.float32),
            # Critic network
            "w_c1": self._rng.normal(0, scale_a1, (obs_d, h_d)).astype(np.float32),
            "b_c1": np.zeros(h_d, dtype=np.float32),
            "w_c2": self._rng.normal(0, scale_a2, (h_d, sub_h)).astype(np.float32),
            "b_c2": np.zeros(sub_h, dtype=np.float32),
            "w_c3": self._rng.normal(0, scale_a2, (sub_h, 1)).astype(np.float32) * 0.1,
            "b_c3": np.zeros(1, dtype=np.float32),
        }

    def forward_actor(self, obs: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compute action logits and probabilities. Returns (probs, h1, h2)."""
        h1 = np.tanh(obs @ self.params["w_a1"] + self.params["b_a1"])
        h2 = np.tanh(h1 @ self.params["w_a2"] + self.params["b_a2"])
        logits = h2 @ self.params["w_a3"] + self.params["b_a3"]
        probs = softmax(logits)
        return probs, h1, h2

    def forward_critic(self, obs: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Compute state value V(s). Returns (value, h1, h2)."""
        h1 = np.tanh(obs @ self.params["w_c1"] + self.params["b_c1"])
        h2 = np.tanh(h1 @ self.params["w_c2"] + self.params["b_c2"])
        val = (h2 @ self.params["w_c3"] + self.params["b_c3"]).squeeze(-1)
        return val, h1, h2

    def select_action(
        self, obs: np.ndarray, deterministic: bool = False
    ) -> tuple[int, float, float]:
        """Sample action given observation. Returns (action, log_prob, value)."""
        probs, _, _ = self.forward_actor(obs)
        value, _, _ = self.forward_critic(obs)

        if deterministic:
            action = int(np.argmax(probs))
        else:
            action = int(self._rng.choice(self.config.action_dim, p=probs))

        prob_a = max(1e-8, float(probs[action]))
        log_prob = float(np.log(prob_a))
        return action, log_prob, float(value)

    def evaluate_batch(
        self, obs_b: np.ndarray, act_b: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Evaluate action log probabilities, state values, and entropy on a batch."""
        probs, _, _ = self.forward_actor(obs_b)
        vals, _, _ = self.forward_critic(obs_b)

        # Batch indexing for action probabilities
        batch_size = obs_b.shape[0]
        act_probs = probs[np.arange(batch_size), act_b]
        log_probs = np.log(np.maximum(1e-8, act_probs))

        # Entropy: -sum(p * log(p))
        entropy = -np.sum(probs * np.log(np.maximum(1e-8, probs)), axis=-1)

        return log_probs, vals, entropy


class PPOAgent:
    """Proximal Policy Optimization (PPO) Agent for Multi-Intersection Coordination."""

    def __init__(self, config: PPOConfig | None = None, seed: int | None = None):
        self.config = config or PPOConfig()
        self.policy = ActorCriticPolicy(self.config, seed=seed)
        self.optimizer = AdamOptimizer(self.policy.params, lr=self.config.learning_rate)

        # Rollout storage buffers
        self.reset_buffer()

    def reset_buffer(self) -> None:
        """Clear the rollout buffer."""
        self.states: list[np.ndarray] = []
        self.actions: list[int] = []
        self.rewards: list[float] = []
        self.values: list[float] = []
        self.log_probs: list[float] = []
        self.dones: list[bool] = []

    def store_transition(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        value: float,
        log_prob: float,
        done: bool,
    ) -> None:
        """Store a single experience transition."""
        self.states.append(state.copy())
        self.actions.append(action)
        self.rewards.append(reward)
        self.values.append(value)
        self.log_probs.append(log_prob)
        self.dones.append(done)

    def compute_gae(self, last_val: float) -> tuple[np.ndarray, np.ndarray]:
        """Compute Generalized Advantage Estimation (GAE) and target returns."""
        num_steps = len(self.rewards)
        advantages = np.zeros(num_steps, dtype=np.float32)
        last_gae = 0.0

        for t in reversed(range(num_steps)):
            next_non_terminal = 1.0 - float(self.dones[t])
            next_value = last_val if t == num_steps - 1 else self.values[t + 1]
            delta = (
                self.rewards[t]
                + self.config.gamma * next_value * next_non_terminal
                - self.values[t]
            )
            advantages[t] = last_gae = (
                delta + self.config.gamma * self.config.gae_lambda * next_non_terminal * last_gae
            )

        returns = advantages + np.array(self.values, dtype=np.float32)
        return advantages, returns

    def update(self, last_val: float) -> dict[str, float]:
        """Perform PPO update over stored rollouts."""
        if len(self.states) == 0:
            return {}

        advantages, returns = self.compute_gae(last_val)

        # Normalize advantages
        adv_std = np.std(advantages)
        adv_mean = np.mean(advantages)
        norm_advantages = (advantages - adv_mean) / (adv_std + 1e-8)

        obs_arr = np.array(self.states, dtype=np.float32)
        act_arr = np.array(self.actions, dtype=np.int32)
        old_log_probs = np.array(self.log_probs, dtype=np.float32)

        total_loss_accum = 0.0
        policy_loss_accum = 0.0
        value_loss_accum = 0.0
        entropy_accum = 0.0

        num_samples = len(self.states)
        indices = np.arange(num_samples)

        for _ in range(self.config.epochs_per_update):
            np.random.shuffle(indices)
            for start_idx in range(0, num_samples, self.config.batch_size):
                end_idx = min(start_idx + self.config.batch_size, num_samples)
                batch_idx = indices[start_idx:end_idx]

                b_obs = obs_arr[batch_idx]
                b_act = act_arr[batch_idx]
                b_old_lp = old_log_probs[batch_idx]
                b_adv = norm_advantages[batch_idx]
                b_ret = returns[batch_idx]

                # Evaluate forward pass on batch
                probs, h1_a, h2_a = self.policy.forward_actor(b_obs)
                vals, h1_c, h2_c = self.policy.forward_critic(b_obs)

                b_sz = b_obs.shape[0]
                act_probs = probs[np.arange(b_sz), b_act]
                new_lp = np.log(np.maximum(1e-8, act_probs))

                # Importance ratio
                ratios = np.exp(new_lp - b_old_lp)

                # Clipped surrogate objective
                surr1 = ratios * b_adv
                surr2 = (
                    np.clip(ratios, 1.0 - self.config.clip_epsilon, 1.0 + self.config.clip_epsilon)
                    * b_adv
                )
                policy_loss = -np.mean(np.minimum(surr1, surr2))

                # Value function MSE loss
                val_diff = vals - b_ret
                value_loss = 0.5 * np.mean(val_diff**2)

                # Entropy bonus
                entropy = -np.mean(np.sum(probs * np.log(np.maximum(1e-8, probs)), axis=-1))

                total_loss = (
                    policy_loss
                    + self.config.value_coef * value_loss
                    - self.config.entropy_coef * entropy
                )

                # Compute Gradients analytically for backpropagation
                grads: dict[str, np.ndarray] = {}

                # 1. Critic Gradients
                # dL/dV = (V - R) / b_sz * value_coef
                dV = (val_diff / b_sz) * self.config.value_coef
                grads["w_c3"] = h2_c.T @ dV[:, None]
                grads["b_c3"] = np.sum(dV, axis=0, keepdims=True)

                dh2_c = (dV[:, None] @ self.policy.params["w_c3"].T) * (1.0 - h2_c**2)
                grads["w_c2"] = h1_c.T @ dh2_c
                grads["b_c2"] = np.sum(dh2_c, axis=0)

                dh1_c = (dh2_c @ self.policy.params["w_c2"].T) * (1.0 - h1_c**2)
                grads["w_c1"] = b_obs.T @ dh1_c
                grads["b_c1"] = np.sum(dh1_c, axis=0)

                # 2. Actor Gradients
                # surrogate gradient dL/d(logits)
                # When surr1 < surr2 (or not clipped), d(surr)/d(new_lp) = ratios * b_adv
                active_mask = (surr1 <= surr2) | (np.abs(ratios - 1.0) < self.config.clip_epsilon)
                d_lp = np.where(active_mask, -ratios * b_adv / b_sz, 0.0)

                # Softmax derivative: d(lp_a)/d(logits) = 1(k=a) - probs[k]
                d_logits = -probs * d_lp[:, None]
                d_logits[np.arange(b_sz), b_act] += (1.0 - probs[np.arange(b_sz), b_act]) * d_lp

                # Entropy gradient: d(H)/d(logits) = -probs * (log(probs) + H)
                H_k = np.sum(probs * np.log(np.maximum(1e-8, probs)), axis=-1, keepdims=True)
                d_entropy = probs * (np.log(np.maximum(1e-8, probs)) - H_k)
                d_logits -= self.config.entropy_coef * (d_entropy / b_sz)

                grads["w_a3"] = h2_a.T @ d_logits
                grads["b_a3"] = np.sum(d_logits, axis=0)

                dh2_a = (d_logits @ self.policy.params["w_a3"].T) * (1.0 - h2_a**2)
                grads["w_a2"] = h1_a.T @ dh2_a
                grads["b_a2"] = np.sum(dh2_a, axis=0)

                dh1_a = (dh2_a @ self.policy.params["w_a2"].T) * (1.0 - h1_a**2)
                grads["w_a1"] = b_obs.T @ dh1_a
                grads["b_a1"] = np.sum(dh1_a, axis=0)

                # Apply optimizer step
                self.optimizer.step(self.policy.params, grads)

                total_loss_accum += float(total_loss)
                policy_loss_accum += float(policy_loss)
                value_loss_accum += float(value_loss)
                entropy_accum += float(entropy)

        self.reset_buffer()

        num_updates = self.config.epochs_per_update * max(
            1, (num_samples // self.config.batch_size)
        )
        return {
            "total_loss": total_loss_accum / num_updates,
            "policy_loss": policy_loss_accum / num_updates,
            "value_loss": value_loss_accum / num_updates,
            "entropy": entropy_accum / num_updates,
        }

    def save_checkpoint(self, path: Path) -> None:
        """Save policy weights and configuration to JSON/npz manifest."""
        path.parent.mkdir(parents=True, exist_ok=True)
        serializable_params = {k: v.tolist() for k, v in self.policy.params.items()}
        data = {
            "config": asdict(self.config),
            "params": serializable_params,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def load_checkpoint(self, path: Path) -> None:
        """Load policy weights and configuration from JSON manifest."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for k, v in data["params"].items():
            if k in self.policy.params:
                self.policy.params[k] = np.array(v, dtype=np.float32)
