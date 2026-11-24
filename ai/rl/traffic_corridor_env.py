"""Gymnasium-Compatible Multi-Intersection Corridor Reinforcement Learning Environment (Task 59).

Models the 1,300m arterial corridor (Nodes A–D) connecting feeder traffic to the
Metropolitan Hospital trauma center under high-density Vietnamese mixed traffic.
Integrates the deterministic SignalSafetyGateway (INV-01 to INV-06) as an active
safety shield intercepting and clamping all RL policy proposals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from controller.safety.signal_safety_gateway import (
    SafetyGatewayConfig,
    SignalSafetyGateway,
)


class DiscreteSpace:
    """Lightweight standalone discrete action space conforming to Gym interface."""

    def __init__(self, n: int, seed: int | None = None):
        self.n = n
        self._rng = np.random.default_rng(seed)

    def sample(self) -> int:
        return int(self._rng.integers(0, self.n))

    def contains(self, x: Any) -> bool:
        return isinstance(x, (int, np.integer)) and 0 <= x < self.n


class BoxSpace:
    """Lightweight standalone continuous observation box space conforming to Gym interface."""

    def __init__(self, low: float, high: float, shape: tuple[int, ...], seed: int | None = None):
        self.low = np.full(shape, low, dtype=np.float32)
        self.high = np.full(shape, high, dtype=np.float32)
        self.shape = shape
        self._rng = np.random.default_rng(seed)

    def sample(self) -> np.ndarray:
        return self._rng.uniform(self.low, self.high).astype(np.float32)

    def contains(self, x: np.ndarray) -> bool:
        return (
            isinstance(x, np.ndarray)
            and x.shape == self.shape
            and np.all(x >= self.low)
            and np.all(x <= self.high)
        )


@dataclass
class IntersectionState:
    """Internal state for a single intersection in the corridor."""

    node_id: str
    stopline_x: float
    current_phase: int  # 0: Arterial Green, 1: Arterial Yellow, 2: Arterial Red, 3: Cross Green, 4: Cross Yellow, 5: Cross Red
    phase_elapsed_sec: float
    arterial_queue_m: float
    cross_queue_m: float
    inflow_rate_veh_min: float


class MultiIntersectionCorridorEnv:
    """Multi-Intersection Arterial Corridor Environment for Reinforcement Learning.

    Conforms to Gymnasium API:
      - reset(seed=None) -> (obs, info)
      - step(action) -> (obs, reward, terminated, truncated, info)
    """

    OBS_DIM: int = 25
    NUM_ACTIONS: int = 4

    ACTION_MAINTAIN: int = 0
    ACTION_TRIGGER_PRECLEARANCE: int = 1
    ACTION_CASCADE_GREEN_WAVE: int = 2
    ACTION_COMPENSATE_RECOVERY: int = 3

    def __init__(
        self,
        dt_macro: float = 1.0,
        max_episode_sec: float = 120.0,
        ev_departure_time: float = 10.0,
        seed: int | None = None,
    ):
        self.dt_macro = dt_macro
        self.max_episode_sec = max_episode_sec
        self.ev_departure_time = ev_departure_time
        self.sim_time: float = 0.0

        self.action_space = DiscreteSpace(self.NUM_ACTIONS, seed=seed)
        self.observation_space = BoxSpace(low=-1.0, high=1.0, shape=(self.OBS_DIM,), seed=seed)

        self._rng = np.random.default_rng(seed)
        self.node_positions = [0.0, 300.0, 600.0, 900.0]  # Nodes A, B, C, D
        self.node_names = ["node_a", "node_b", "node_c", "node_d"]
        self.hospital_x = 1100.0

        # Safety gateway configuration
        self.gateway_config = SafetyGatewayConfig()
        self.gateway = SignalSafetyGateway(config=self.gateway_config, node_ids=self.node_names)

        # Intersections container
        self.intersections: list[IntersectionState] = []

        # Emergency vehicle dynamics
        self.ev_active: bool = False
        self.ev_x: float = -150.0  # Starts upstream of Node A
        self.ev_speed: float = 0.0  # m/s
        self.ev_max_speed: float = 18.5  # ~66.6 km/h priority cruise speed
        self.ev_accel: float = 3.5  # m/s^2
        self.ev_stopped_counter: int = 0
        self.ev_arrival_time: float | None = None

        # Tracking metrics
        self.total_civilian_delay: float = 0.0
        self.safety_shield_interventions: int = 0
        self.phase_switches_count: int = 0

        self.reset(seed=seed)

    def reset(self, seed: int | None = None) -> tuple[np.ndarray, dict[str, Any]]:
        """Reset the environment to initial conditions."""
        if seed is not None:
            self._rng = np.random.default_rng(seed)

        self.sim_time = 0.0
        self.ev_active = False
        self.ev_x = -150.0
        self.ev_speed = 0.0
        self.ev_stopped_counter = 0
        self.ev_arrival_time = None
        self.total_civilian_delay = 0.0
        self.safety_shield_interventions = 0
        self.phase_switches_count = 0

        # Initialize 4 intersections
        self.gateway.reset()
        self.intersections = []
        for i, (name, x_pos) in enumerate(zip(self.node_names, self.node_positions, strict=False)):
            initial_phase = 0 if i % 2 == 0 else 3  # Staggered initial cycles
            self.gateway._current_phases[name] = initial_phase
            self.gateway._phase_start_times[name] = 0.0

            self.intersections.append(
                IntersectionState(
                    node_id=name,
                    stopline_x=x_pos,
                    current_phase=initial_phase,
                    phase_elapsed_sec=0.0,
                    arterial_queue_m=float(self._rng.uniform(15.0, 45.0)),
                    cross_queue_m=float(self._rng.uniform(10.0, 35.0)),
                    inflow_rate_veh_min=float(self._rng.uniform(10.0, 25.0)),
                )
            )

        obs = self._get_observation()
        info = self._get_info()
        return obs, info

    def step(self, action: int) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        """Advance the environment by dt_macro seconds given an RL policy action."""
        # 1. Update EV dispatch status
        if not self.ev_active and self.sim_time >= self.ev_departure_time:
            self.ev_active = True
            self.ev_speed = 5.0

        # 2. Translate RL Macro-Action into Signal Phase Proposals
        shield_penalty = 0.0
        proposals = self._translate_action_to_proposals(action)

        # 3. Pass proposals through the SignalSafetyGateway (Safety Shielding)
        for i, node in enumerate(self.intersections):
            desired_phase = proposals[i]
            report = self.gateway.verify_and_sanitize_command(
                node_id=node.node_id,
                proposed_phase=desired_phase,
                sim_time=self.sim_time,
            )

            if report.intervention is not None:
                self.safety_shield_interventions += 1
                shield_penalty -= 5.0  # Penalize policy for proposing unsafe transitions

            actual_phase = report.sanitized_phase
            if actual_phase != node.current_phase:
                self.phase_switches_count += 1
                node.current_phase = actual_phase
                node.phase_elapsed_sec = 0.0
            else:
                node.phase_elapsed_sec += self.dt_macro

        # 4. Step Traffic Queues & Flow Dynamics
        for node in self.intersections:
            # Arrival flows
            node.arterial_queue_m += (node.inflow_rate_veh_min / 60.0) * 4.5 * self.dt_macro
            node.cross_queue_m += (node.inflow_rate_veh_min * 0.75 / 60.0) * 4.5 * self.dt_macro

            # Discharge on green phases (Phase 0: Arterial Green, Phase 3: Cross Green)
            discharge_rate_mps = 3.5  # meters of queue cleared per second
            if node.current_phase == 0:
                node.arterial_queue_m = max(
                    0.0, node.arterial_queue_m - discharge_rate_mps * self.dt_macro
                )
            elif node.current_phase == 3:
                node.cross_queue_m = max(
                    0.0, node.cross_queue_m - discharge_rate_mps * self.dt_macro
                )

            # Cap queues to storage length
            node.arterial_queue_m = min(150.0, node.arterial_queue_m)
            node.cross_queue_m = min(100.0, node.cross_queue_m)
            self.total_civilian_delay += (
                (node.arterial_queue_m + node.cross_queue_m) * 0.05 * self.dt_macro
            )

        # 5. Step Emergency Vehicle Kinematics
        ev_progress_m = 0.0
        if self.ev_active and self.ev_arrival_time is None:
            # Find next upcoming intersection
            next_node = None
            for node in self.intersections:
                if self.ev_x < node.stopline_x:
                    next_node = node
                    break

            # Check if EV is obstructed by red light or arterial queue
            is_blocked = False
            if next_node is not None:
                dist_to_stopline = next_node.stopline_x - self.ev_x
                if dist_to_stopline <= 60.0 and (
                    next_node.current_phase != 0 or next_node.arterial_queue_m > 15.0
                ):
                    is_blocked = True

            if is_blocked:
                # Decelerate to stop
                self.ev_speed = max(0.0, self.ev_speed - 4.5 * self.dt_macro)
                if self.ev_speed < 0.5:
                    self.ev_stopped_counter += 1
            else:
                # Accelerate towards max priority speed
                self.ev_speed = min(
                    self.ev_max_speed, self.ev_speed + self.ev_accel * self.dt_macro
                )

            ev_step_dist = self.ev_speed * self.dt_macro
            self.ev_x += ev_step_dist
            ev_progress_m = ev_step_dist

            # Check hospital arrival
            if self.ev_x >= self.hospital_x:
                self.ev_arrival_time = self.sim_time

        # 6. Advance Simulation Clock
        self.sim_time += self.dt_macro

        # 7. Evaluate Reward Function
        reward = self._calculate_reward(ev_progress_m, shield_penalty)

        # 8. Check Termination & Truncation
        terminated = bool(self.ev_arrival_time is not None)
        truncated = bool(self.sim_time >= self.max_episode_sec)

        obs = self._get_observation()
        info = self._get_info()

        return obs, reward, terminated, truncated, info

    def _translate_action_to_proposals(self, action: int) -> list[int]:
        """Convert a discrete macro-action into target phase proposals for Nodes A–D."""
        proposals = [node.current_phase for node in self.intersections]

        # Target node where EV is approaching
        target_idx = 0
        for i, node in enumerate(self.intersections):
            if self.ev_x < node.stopline_x + 15.0:
                target_idx = i
                break

        if action == self.ACTION_MAINTAIN:
            # Let nominal cycle advance
            for i, node in enumerate(self.intersections):
                if node.phase_elapsed_sec >= 35.0:
                    proposals[i] = (node.current_phase + 1) % 6
                else:
                    proposals[i] = node.current_phase

        elif action == self.ACTION_TRIGGER_PRECLEARANCE:
            # Request Arterial Green (Phase 0) on the target intersection
            proposals[target_idx] = 0

        elif action == self.ACTION_CASCADE_GREEN_WAVE:
            # Request Arterial Green (Phase 0) on target and downstream nodes
            for i in range(target_idx, len(self.intersections)):
                proposals[i] = 0

        elif action == self.ACTION_COMPENSATE_RECOVERY:
            # Request Cross-Street Green (Phase 3) on nodes behind the EV
            for i in range(0, target_idx):
                proposals[i] = 3

        return proposals

    def _calculate_reward(self, ev_progress_m: float, shield_penalty: float) -> float:
        """Multi-objective reward combining EV velocity, civilian queue penalties, and safety."""
        reward = 0.0

        # 1. EV Progress reward
        if self.ev_active and self.ev_arrival_time is None:
            reward += (self.ev_speed / self.ev_max_speed) * 4.0
            if self.ev_speed < 1.0:
                reward -= 3.0  # Heavy penalty for stopped emergency vehicle

        # 2. Terminal arrival bonus
        if (
            self.ev_arrival_time is not None
            and (self.sim_time - self.ev_arrival_time) <= self.dt_macro
        ):
            # Arrived this step
            time_penalty = (self.ev_arrival_time - self.ev_departure_time) * 0.5
            reward += max(20.0, 100.0 - time_penalty)

        # 3. Civilian queue delay penalties
        total_cross_queue = sum(node.cross_queue_m for node in self.intersections)
        reward -= total_cross_queue * 0.01

        # 4. Chattering penalty
        reward -= 0.1

        # 5. Safety shield violation penalty
        reward += shield_penalty

        return float(reward)

    def _get_observation(self) -> np.ndarray:
        """Construct the 25-dimensional normalized continuous observation vector."""
        obs = np.zeros(self.OBS_DIM, dtype=np.float32)
        idx = 0

        # 4 Nodes x 5 features = 20 features
        for node in self.intersections:
            obs[idx] = np.clip(node.arterial_queue_m / 150.0, 0.0, 1.0)
            obs[idx + 1] = np.clip(node.cross_queue_m / 100.0, 0.0, 1.0)
            obs[idx + 2] = float(node.current_phase) / 5.0
            obs[idx + 3] = np.clip(node.phase_elapsed_sec / 75.0, 0.0, 1.0)
            obs[idx + 4] = np.clip(node.inflow_rate_veh_min / 30.0, 0.0, 1.0)
            idx += 5

        # 5 Emergency Vehicle features
        obs[idx] = 1.0 if self.ev_active else 0.0
        obs[idx + 1] = np.clip((self.ev_x + 150.0) / (self.hospital_x + 150.0), 0.0, 1.0)
        obs[idx + 2] = np.clip(self.ev_speed / self.ev_max_speed, 0.0, 1.0)

        # Distance to next node
        next_dist = 400.0
        target_idx = 3
        for i, node in enumerate(self.intersections):
            if self.ev_x < node.stopline_x:
                next_dist = node.stopline_x - self.ev_x
                target_idx = i
                break
        obs[idx + 3] = np.clip(next_dist / 400.0, 0.0, 1.0)
        obs[idx + 4] = float(target_idx) / 3.0

        return obs

    def _get_info(self) -> dict[str, Any]:
        """Construct informational telemetry dictionary."""
        ev_transit_time = (
            (self.ev_arrival_time - self.ev_departure_time)
            if self.ev_arrival_time is not None
            else (self.sim_time - self.ev_departure_time)
        )
        return {
            "sim_time": self.sim_time,
            "ev_active": self.ev_active,
            "ev_x": self.ev_x,
            "ev_speed_kmh": self.ev_speed * 3.6,
            "ev_stopped_ticks": self.ev_stopped_counter,
            "ev_transit_time_sec": max(0.0, ev_transit_time),
            "safety_shield_interventions": self.safety_shield_interventions,
            "total_civilian_delay": self.total_civilian_delay,
            "phase_switches_count": self.phase_switches_count,
        }
