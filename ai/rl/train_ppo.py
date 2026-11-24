"""Training Script for Multi-Intersection Corridor PPO Reinforcement Learning (Task 59).

Executes rollouts in MultiIntersectionCorridorEnv, updates Actor-Critic policy
using PPO clipped surrogate objective, and saves policy checkpoints.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np

from ai.rl.ppo_agent import PPOAgent, PPOConfig
from ai.rl.traffic_corridor_env import MultiIntersectionCorridorEnv

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def train_ppo(
    num_episodes: int = 50,
    seed: int = 42,
    checkpoint_path: Path | None = None,
) -> tuple[PPOAgent, dict[str, Any]]:
    """Train PPO agent in the multi-intersection corridor sandbox."""
    np.random.seed(seed)
    config = PPOConfig(learning_rate=3e-4, epochs_per_update=4, batch_size=32)
    agent = PPOAgent(config=config, seed=seed)
    env = MultiIntersectionCorridorEnv(seed=seed)

    history = {
        "episode_rewards": [],
        "transit_times": [],
        "ev_stops": [],
        "shield_interventions": [],
    }

    print(f"🚦 Starting PPO Training for {num_episodes} episodes in Corridor Sandbox...")

    for ep in range(1, num_episodes + 1):
        obs, _info = env.reset(seed=seed + ep)
        ep_reward = 0.0
        done = False

        while not done:
            action, log_prob, val = agent.policy.select_action(obs, deterministic=False)
            next_obs, reward, terminated, truncated, step_info = env.step(action)
            done = terminated or truncated

            agent.store_transition(
                state=obs,
                action=action,
                reward=reward,
                value=val,
                log_prob=log_prob,
                done=done,
            )

            obs = next_obs
            ep_reward += reward

        # Episode completed; compute terminal value for GAE
        _, _, last_val = agent.policy.select_action(obs, deterministic=True)
        train_metrics = agent.update(last_val=last_val)

        history["episode_rewards"].append(ep_reward)
        history["transit_times"].append(step_info["ev_transit_time_sec"])
        history["ev_stops"].append(step_info["ev_stopped_ticks"])
        history["shield_interventions"].append(step_info["safety_shield_interventions"])

        if ep % 10 == 0 or ep == num_episodes:
            avg_rew = np.mean(history["episode_rewards"][-10:])
            avg_time = np.mean(history["transit_times"][-10:])
            print(
                f"  Episode {ep:02d}/{num_episodes:02d} | "
                f"Avg Reward: {avg_rew:6.1f} | "
                f"Avg EV Time: {avg_time:5.1f}s | "
                f"Loss: {train_metrics.get('total_loss', 0.0):.4f}"
            )

    if checkpoint_path is not None:
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        agent.save_checkpoint(checkpoint_path)
        print(f"✅ Saved PPO checkpoint to: {checkpoint_path}")

    return agent, history


def main() -> None:
    parser = argparse.ArgumentParser(description="Train PPO Agent on Corridor Environment.")
    parser.add_argument("--episodes", type=int, default=30, help="Number of training episodes.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=REPO_ROOT / "models" / "rl" / "ppo_corridor_agent.json",
        help="Path to save trained policy checkpoint.",
    )
    args = parser.parse_args()

    train_ppo(num_episodes=args.episodes, seed=args.seed, checkpoint_path=args.checkpoint)


if __name__ == "__main__":
    main()

