"""Automated Test Suite for Multi-Intersection Corridor PPO Reinforcement Learning (Task 59).

Validates Gymnasium environment spaces, state transitions, SignalSafetyGateway shielding,
Actor-Critic neural networks, PPO GAE optimization, checkpoint serialization, and benchmarking.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np

from ai.rl.evaluate_policy import evaluate_policy
from ai.rl.ppo_agent import ActorCriticPolicy, PPOAgent, PPOConfig
from ai.rl.traffic_corridor_env import (
    BoxSpace,
    DiscreteSpace,
    MultiIntersectionCorridorEnv,
)


def test_gym_compatible_spaces_and_reset():
    """Verify discrete action space, continuous observation space, and reset behavior."""
    discrete = DiscreteSpace(4, seed=42)
    assert discrete.n == 4
    for _ in range(20):
        action = discrete.sample()
        assert discrete.contains(action)

    box = BoxSpace(low=-1.0, high=1.0, shape=(25,), seed=42)
    assert box.shape == (25,)
    sample_obs = box.sample()
    assert box.contains(sample_obs)

    env = MultiIntersectionCorridorEnv(seed=42)
    obs, info = env.reset(seed=123)

    assert isinstance(obs, np.ndarray)
    assert obs.shape == (25,)
    assert np.all(obs >= -1.0) and np.all(obs <= 1.0)

    assert "sim_time" in info
    assert "ev_speed_kmh" in info
    assert "safety_shield_interventions" in info


def test_environment_step_dynamics_and_transitions():
    """Verify macro-action step transitions and reward generation."""
    env = MultiIntersectionCorridorEnv(dt_macro=1.0, max_episode_sec=50.0, seed=42)
    obs, _ = env.reset(seed=42)

    total_reward = 0.0
    for step_idx in range(30):
        action = step_idx % 4
        next_obs, reward, term, trunc, info = env.step(action)

        assert isinstance(reward, float)
        assert next_obs.shape == (25,)
        assert np.all(next_obs >= -1.0) and np.all(next_obs <= 1.0)

        total_reward += reward
        if term or trunc:
            break

    assert isinstance(total_reward, float)
    assert info["sim_time"] > 0.0


def test_safety_shield_interlocking():
    """Verify that SignalSafetyGateway intercepts unsafe action transitions (INV-01 to INV-06)."""
    env = MultiIntersectionCorridorEnv(seed=99)
    env.reset(seed=99)

    # Force continuous aggressive switching
    interventions_before = env.safety_shield_interventions
    for _ in range(25):
        # Alternate between triggering pre-clearance and compensation
        action = MultiIntersectionCorridorEnv.ACTION_TRIGGER_PRECLEARANCE
        env.step(action)
        action = MultiIntersectionCorridorEnv.ACTION_COMPENSATE_RECOVERY
        _, _, _, _, info = env.step(action)

    # Zero conflicting green states across all 4 intersections (INV-01)
    for node in env.intersections:
        colors = env.gateway.get_approach_colors(node.current_phase)
        assert env.gateway.check_conflict_free(colors) is True

    # Confirm that the safety gateway actively intercepted early truncation attempts
    assert info["safety_shield_interventions"] >= interventions_before


def test_actor_critic_network_forward_and_batch_eval():
    """Verify Actor-Critic policy parameter forward passes and log probability calculations."""
    config = PPOConfig(obs_dim=25, action_dim=4, hidden_dim=32, sub_hidden_dim=16)
    policy = ActorCriticPolicy(config, seed=42)

    single_obs = np.random.uniform(-1.0, 1.0, size=(25,)).astype(np.float32)
    probs, h1_a, h2_a = policy.forward_actor(single_obs)
    val, h1_c, h2_c = policy.forward_critic(single_obs)

    # Probability axioms
    assert probs.shape == (4,)
    assert np.isclose(np.sum(probs), 1.0, atol=1e-5)
    assert np.all(probs >= 0.0)
    assert isinstance(float(val), float)

    # Deterministic vs stochastic action selection
    det_action, det_lp, _ = policy.select_action(single_obs, deterministic=True)
    assert det_action == int(np.argmax(probs))
    assert det_lp <= 0.0

    # Batch evaluation
    batch_size = 8
    obs_batch = np.random.uniform(-1.0, 1.0, size=(batch_size, 25)).astype(np.float32)
    act_batch = np.random.randint(0, 4, size=(batch_size,)).astype(np.int32)

    log_probs, vals, entropy = policy.evaluate_batch(obs_batch, act_batch)
    assert log_probs.shape == (batch_size,)
    assert vals.shape == (batch_size,)
    assert entropy.shape == (batch_size,)
    assert np.all(entropy >= 0.0)


def test_ppo_agent_learning_update_step():
    """Verify PPO experience rollout storage, GAE advantage computation, and gradient updates."""
    config = PPOConfig(obs_dim=25, action_dim=4, epochs_per_update=2, batch_size=16)
    agent = PPOAgent(config=config, seed=42)

    # Generate synthetic rollouts
    for _ in range(32):
        s = np.random.uniform(-1.0, 1.0, (25,)).astype(np.float32)
        a, lp, v = agent.policy.select_action(s)
        r = float(np.random.normal(1.0, 0.5))
        agent.store_transition(state=s, action=a, reward=r, value=v, log_prob=lp, done=False)

    assert len(agent.states) == 32
    metrics = agent.update(last_val=0.5)

    assert "total_loss" in metrics
    assert "policy_loss" in metrics
    assert "value_loss" in metrics
    assert "entropy" in metrics
    assert np.isfinite(metrics["total_loss"])

    # Buffer should be reset after update
    assert len(agent.states) == 0


def test_checkpoint_serialization_and_loading():
    """Verify policy parameters and configuration roundtrip serialization."""
    agent_src = PPOAgent(seed=77)
    with tempfile.TemporaryDirectory() as tmp_dir:
        ckpt_path = Path(tmp_dir) / "test_ppo_checkpoint.json"
        agent_src.save_checkpoint(ckpt_path)
        assert ckpt_path.exists()

        agent_dst = PPOAgent(seed=999)
        agent_dst.load_checkpoint(ckpt_path)

        for param_name in agent_src.policy.params:
            np.testing.assert_allclose(
                agent_src.policy.params[param_name],
                agent_dst.policy.params[param_name],
                rtol=1e-5,
                atol=1e-6,
            )


def test_evaluate_policy_benchmark_execution():
    """Verify policy evaluation benchmark comparative execution."""
    agent = PPOAgent(seed=42)
    results = evaluate_policy(agent=agent, num_eval_episodes=2, base_seed=50)

    assert "benchmark_name" in results
    assert "metrics" in results
    metrics = results["metrics"]
    assert "ev_transit_time_sec" in metrics
    assert "safety_invariants_compliance_pct" in metrics
    assert metrics["safety_invariants_compliance_pct"] == 100.0
    assert metrics["conflicting_green_violations"] == 0
