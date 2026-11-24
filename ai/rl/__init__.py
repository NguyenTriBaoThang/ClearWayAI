"""ClearWayAI Reinforcement Learning Subsystem (`ai.rl`) (Task 59).

Provides Gymnasium-compatible multi-intersection traffic environments, safety-shielded
policy actuation, and Proximal Policy Optimization (PPO) Actor-Critic agents.
"""

from __future__ import annotations

from ai.rl.evaluate_policy import evaluate_policy
from ai.rl.ppo_agent import ActorCriticPolicy, PPOAgent, PPOConfig
from ai.rl.traffic_corridor_env import (
    BoxSpace,
    DiscreteSpace,
    MultiIntersectionCorridorEnv,
)
from ai.rl.train_ppo import train_ppo

__all__ = [
    "ActorCriticPolicy",
    "BoxSpace",
    "DiscreteSpace",
    "MultiIntersectionCorridorEnv",
    "PPOAgent",
    "PPOConfig",
    "evaluate_policy",
    "train_ppo",
]
