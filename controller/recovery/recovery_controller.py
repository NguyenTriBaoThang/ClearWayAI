"""ClearWayAI Post-Clearance Smooth Recovery State Machine (`controller.recovery`).

Following emergency preemption, cross-street traffic movements accumulate substantial
"Green Debt" (unserved demand resulting from extended red phases).

This module implements the Post-Clearance Smooth Recovery algorithm:
1. Calculates cross-street Green Debt:
   $$G_{\\text{debt}} = \\min\\left(G_{\\text{max}}, T_{\\text{preempt}} \\times \\frac{G_{\\text{cross}}}{C} + \\frac{L_{\\text{queue}}}{v_{\\text{sat}}}\\right)$$
2. Gradual Multi-Cycle Amortization:
   Spreads green debt compensation smoothly across $N_{\\text{cycles}}$ (typically 2-3 cycles)
   to prevent jarring arterial disruption:
   $$\\Delta g_{\\text{bonus}}^{(c)} = \\min\\left(G_{\\text{bonus\\_max}}, \\frac{G_{\\text{debt}}}{N_{\\text{cycles}} - c + 1}\\right)$$
3. Corridor Master Clock Resynchronization:
   Smoothly re-aligns local intersection cycle offsets with corridor master coordination
   clocks (target offset $\\Phi_{\\text{target}}$) to restore optimal progressive green waves.
4. Deterministic State Machine:
   INACTIVE -> HANDOFF -> COMPENSATING -> RESYNCHRONIZING -> EQUILIBRIUM_RESTORED.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class RecoveryState(StrEnum):
    """Operational state of an intersection undergoing post-clearance recovery."""

    INACTIVE = "INACTIVE"
    HANDOFF = "HANDOFF"
    COMPENSATING = "COMPENSATING"
    RESYNCHRONIZING = "RESYNCHRONIZING"
    EQUILIBRIUM_RESTORED = "EQUILIBRIUM_RESTORED"


@dataclass
class RecoveryConfig:
    """Configuration parameters for green debt amortization and clock resynchronization."""

    nominal_cycle_sec: float = 72.0
    nominal_arterial_green_sec: float = 35.0
    nominal_cross_green_sec: float = 25.0
    yellow_duration_sec: float = 3.0
    all_red_duration_sec: float = 2.0
    min_arterial_green_sec: float = 15.0
    min_cross_green_sec: float = 10.0
    max_cross_green_sec: float = 45.0
    max_bonus_per_cycle_sec: float = 12.0
    recovery_cycles_budget: int = 3
    max_recovery_timeout_sec: float = 180.0
    resync_tolerance_sec: float = 1.0
    cycle_stretch_max_ratio: float = 0.15

    # NEMA Standard Phase Mapping
    arterial_phase_green: int = 0
    arterial_phase_yellow: int = 1
    arterial_phase_all_red: int = 2
    cross_phase_green: int = 3
    cross_phase_yellow: int = 4
    cross_phase_all_red: int = 5

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NodeRecoveryStatus:
    """Recovery progress metrics and phase commands for an individual node."""

    node_id: str
    state: RecoveryState
    initial_green_debt_sec: float
    remaining_green_debt_sec: float
    current_recovery_cycle: int
    bonus_green_allocated_sec: float
    offset_error_sec: float
    commanded_phase: int
    phase_remaining_sec: float
    is_recovered: bool
    elapsed_recovery_time_sec: float
    reason: str
    timestamp_sec: float = field(default_factory=time.time)
    provenance: str = "SMOOTH_EQUILIBRIUM_RECOVERY"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["state"] = str(self.state)
        return d


@dataclass
class CorridorRecoveryReport:
    """Consolidated corridor-wide post-clearance recovery report."""

    corridor_recovering_count: int
    all_nodes_equilibrium: bool
    node_reports: dict[str, NodeRecoveryStatus]
    commanded_phases: dict[str, int]
    timestamp_sec: float
    provenance: str = "SMOOTH_EQUILIBRIUM_RECOVERY"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["node_reports"] = {k: v.to_dict() for k, v in self.node_reports.items()}
        return d


class PostClearanceRecoveryController:
    """Manages smooth multi-cycle post-preemption recovery across corridor intersections."""

    DEFAULT_MASTER_OFFSETS: dict[str, float] = {
        "node_a": 0.0,
        "node_b": 16.0,
        "node_c": 32.0,
        "node_d": 48.0,
    }

    def __init__(
        self,
        config: RecoveryConfig | None = None,
        intersections: list[str] | None = None,
        master_cycle_offsets: dict[str, float] | None = None,
    ) -> None:
        self.config = config or RecoveryConfig()
        self.intersections = intersections or ["node_a", "node_b", "node_c", "node_d"]
        self.master_offsets = master_cycle_offsets or dict(self.DEFAULT_MASTER_OFFSETS)

        # Internal tracking per intersection node
        self._node_states: dict[str, RecoveryState] = dict.fromkeys(
            self.intersections, RecoveryState.INACTIVE
        )
        self._initial_debts: dict[str, float] = dict.fromkeys(self.intersections, 0.0)
        self._remaining_debts: dict[str, float] = dict.fromkeys(self.intersections, 0.0)
        self._cycle_counters: dict[str, int] = dict.fromkeys(self.intersections, 0)
        self._recovery_start_times: dict[str, float | None] = dict.fromkeys(self.intersections)
        self._cycle_start_times: dict[str, float] = dict.fromkeys(self.intersections, 0.0)
        self._phase_start_times: dict[str, float] = dict.fromkeys(self.intersections, 0.0)
        self._current_phases: dict[str, int] = dict.fromkeys(
            self.intersections, self.config.arterial_phase_green
        )
        self._current_cycle_splits: dict[str, tuple[float, float]] = dict.fromkeys(
            self.intersections,
            (self.config.nominal_arterial_green_sec, self.config.nominal_cross_green_sec),
        )

    def reset(self) -> None:
        """Reset all internal recovery tracking to inactive initial state."""
        for nid in self.intersections:
            self._node_states[nid] = RecoveryState.INACTIVE
            self._initial_debts[nid] = 0.0
            self._remaining_debts[nid] = 0.0
            self._cycle_counters[nid] = 0
            self._recovery_start_times[nid] = None
            self._cycle_start_times[nid] = 0.0
            self._phase_start_times[nid] = 0.0
            self._current_phases[nid] = self.config.arterial_phase_green
            self._current_cycle_splits[nid] = (
                self.config.nominal_arterial_green_sec,
                self.config.nominal_cross_green_sec,
            )

    def is_recovering(self, node_id: str) -> bool:
        """Check if a specific node is actively undergoing recovery."""
        return self._node_states.get(node_id, RecoveryState.INACTIVE) in (
            RecoveryState.HANDOFF,
            RecoveryState.COMPENSATING,
            RecoveryState.RESYNCHRONIZING,
        )

    def get_nominal_phase(self, sim_time: float, offset_sec: float = 0.0) -> int:
        """Standard Webster cycle phase timing with optional offset for progressive coordination.

        Splits (Cycle = 72s):
        - [0, 35): Phase 0 (Arterial Green, 35s)
        - [35, 39): Phase 1 (Arterial Yellow, 4s -> here 3s yellow + 2s all-red = 35..38, 38..40)
        - [38, 40): Phase 2 (Arterial All-Red, 2s)
        - [40, 65): Phase 3 (Cross Green, 25s)
        - [65, 68): Phase 4 (Cross Yellow, 3s)
        - [68, 72): Phase 5 (Cross All-Red, 4s -> here 2s yellow, 2s all red)
        """
        cfg = self.config
        t_cycle = (sim_time - offset_sec) % cfg.nominal_cycle_sec
        if t_cycle < 0:
            t_cycle += cfg.nominal_cycle_sec

        t_art_yellow = cfg.nominal_arterial_green_sec
        t_art_all_red = t_art_yellow + cfg.yellow_duration_sec
        t_cross_green = t_art_all_red + cfg.all_red_duration_sec
        t_cross_yellow = t_cross_green + cfg.nominal_cross_green_sec
        t_cross_all_red = t_cross_yellow + cfg.yellow_duration_sec

        if t_cycle < t_art_yellow:
            return cfg.arterial_phase_green
        elif t_cycle < t_art_all_red:
            return cfg.arterial_phase_yellow
        elif t_cycle < t_cross_green:
            return cfg.arterial_phase_all_red
        elif t_cycle < t_cross_yellow:
            return cfg.cross_phase_green
        elif t_cycle < t_cross_all_red:
            return cfg.cross_phase_yellow
        else:
            return cfg.cross_phase_all_red

    def compute_offset_error(self, sim_time: float, node_id: str) -> float:
        """Compute phase alignment error between local intersection cycle and corridor master clock."""
        cfg = self.config
        master_offset = self.master_offsets.get(node_id, 0.0)
        expected_pos = (sim_time - master_offset) % cfg.nominal_cycle_sec
        if expected_pos < 0:
            expected_pos += cfg.nominal_cycle_sec

        actual_cycle_start = self._cycle_start_times.get(node_id, 0.0)
        actual_pos = (sim_time - actual_cycle_start) % cfg.nominal_cycle_sec

        error = abs(actual_pos - expected_pos)
        # Circular difference on torus [0, C]
        if error > (cfg.nominal_cycle_sec / 2.0):
            error = cfg.nominal_cycle_sec - error
        return round(error, 2)

    def calculate_green_debt(
        self,
        preemption_duration_sec: float,
        cross_queue_meters: float = 0.0,
    ) -> float:
        """Compute the accumulated green time deficit on the cross-street.

        Combines:
        1. Expected nominal green time lost during preemption hold:
           $$G_{\\text{lost}} = T_{\\text{preempt}} \\times \\frac{G_{\\text{cross}}}{C}$$
        2. Queue discharge clearance demand ($v_{\\text{sat}} \\approx 4.5\\text{ m/s}$):
           $$G_{\\text{queue}} = \\frac{L_{\\text{queue}}}{v_{\\text{sat}}}$$
        """
        cfg = self.config
        nominal_cross_ratio = cfg.nominal_cross_green_sec / cfg.nominal_cycle_sec
        lost_time = preemption_duration_sec * nominal_cross_ratio
        queue_discharge_time = max(0.0, cross_queue_meters / 4.5)

        total_debt = lost_time + queue_discharge_time
        # Bound debt to realistic bounds [0.0s, 36.0s (half cycle)]
        return round(max(0.0, min(36.0, total_debt)), 2)

    def initiate_recovery(
        self,
        node_id: str,
        preemption_duration_sec: float,
        cross_queue_meters: float = 0.0,
        interrupted_nominal_phase: int = 3,
        sim_time: float = 0.0,
    ) -> NodeRecoveryStatus:
        """Trigger handoff from Preclearance CLEARED state to start smooth multi-cycle recovery."""
        cfg = self.config
        debt = self.calculate_green_debt(preemption_duration_sec, cross_queue_meters)

        self._initial_debts[node_id] = debt
        self._remaining_debts[node_id] = debt
        self._cycle_counters[node_id] = 1
        self._recovery_start_times[node_id] = sim_time
        self._cycle_start_times[node_id] = sim_time
        self._phase_start_times[node_id] = sim_time

        # Allocate Cycle 1 split: allocate bonus to cross street, deduct from arterial
        bonus_1 = min(cfg.max_bonus_per_cycle_sec, round(debt / cfg.recovery_cycles_budget, 2))
        arterial_split_1 = max(cfg.min_arterial_green_sec, cfg.nominal_arterial_green_sec - bonus_1)
        cross_split_1 = min(cfg.max_cross_green_sec, cfg.nominal_cross_green_sec + bonus_1)
        self._current_cycle_splits[node_id] = (arterial_split_1, cross_split_1)

        # Transition immediately to Arterial Yellow -> All-Red -> Cross Green (to serve starved cross street first!)
        self._node_states[node_id] = RecoveryState.COMPENSATING
        self._current_phases[node_id] = cfg.arterial_phase_yellow

        offset_err = self.compute_offset_error(sim_time, node_id)
        return NodeRecoveryStatus(
            node_id=node_id,
            state=RecoveryState.COMPENSATING,
            initial_green_debt_sec=debt,
            remaining_green_debt_sec=debt,
            current_recovery_cycle=1,
            bonus_green_allocated_sec=bonus_1,
            offset_error_sec=offset_err,
            commanded_phase=cfg.arterial_phase_yellow,
            phase_remaining_sec=cfg.yellow_duration_sec,
            is_recovered=False,
            elapsed_recovery_time_sec=0.0,
            reason=f"Recovery initiated: Green debt = {debt:.1f}s. Cycle 1 bonus = +{bonus_1:.1f}s to Cross Street.",
            timestamp_sec=sim_time,
        )

    def evaluate_node(
        self,
        node_id: str,
        sim_time: float,
        dt: float = 0.1,
    ) -> NodeRecoveryStatus:
        """Advance recovery timing, adjust splits, and evaluate equilibrium restoration for a node."""
        cfg = self.config
        current_state = self._node_states.get(node_id, RecoveryState.INACTIVE)

        # Case 1: Node is inactive (normal operation or not yet cleared)
        if current_state in (RecoveryState.INACTIVE, RecoveryState.EQUILIBRIUM_RESTORED):
            nominal = self.get_nominal_phase(sim_time, self.master_offsets.get(node_id, 0.0))
            return NodeRecoveryStatus(
                node_id=node_id,
                state=RecoveryState.EQUILIBRIUM_RESTORED,
                initial_green_debt_sec=0.0,
                remaining_green_debt_sec=0.0,
                current_recovery_cycle=self._cycle_counters.get(node_id, 0),
                bonus_green_allocated_sec=0.0,
                offset_error_sec=0.0,
                commanded_phase=nominal,
                phase_remaining_sec=0.0,
                is_recovered=True,
                elapsed_recovery_time_sec=0.0,
                reason="Node operating in nominal equilibrium coordination.",
                timestamp_sec=sim_time,
            )

        start_time = self._recovery_start_times.get(node_id) or sim_time
        elapsed_recovery = sim_time - start_time

        # Watchdog timeout: abort recovery if it exceeds max allowed duration
        if elapsed_recovery >= cfg.max_recovery_timeout_sec:
            self._node_states[node_id] = RecoveryState.EQUILIBRIUM_RESTORED
            nominal = self.get_nominal_phase(sim_time, self.master_offsets.get(node_id, 0.0))
            return NodeRecoveryStatus(
                node_id=node_id,
                state=RecoveryState.EQUILIBRIUM_RESTORED,
                initial_green_debt_sec=self._initial_debts.get(node_id, 0.0),
                remaining_green_debt_sec=0.0,
                current_recovery_cycle=self._cycle_counters.get(node_id, 0),
                bonus_green_allocated_sec=0.0,
                offset_error_sec=0.0,
                commanded_phase=nominal,
                phase_remaining_sec=0.0,
                is_recovered=True,
                elapsed_recovery_time_sec=elapsed_recovery,
                reason=f"Recovery timeout ({cfg.max_recovery_timeout_sec}s reached). Equilibrium forced.",
                timestamp_sec=sim_time,
            )

        # Active recovery cycle timing
        art_green_dur, cross_green_dur = self._current_cycle_splits[node_id]
        active_phase = self._current_phases[node_id]
        phase_start = self._phase_start_times[node_id]
        phase_elapsed = sim_time - phase_start

        current_cycle = self._cycle_counters[node_id]
        rem_debt = self._remaining_debts[node_id]

        # Phase progression logic within compensated cycle:
        # Phase order during recovery:
        # Yellow (Phase 1) -> All-Red (Phase 2) -> Cross Green (Phase 3) -> Cross Yellow (Phase 4)
        # -> Cross All-Red (Phase 5) -> Arterial Green (Phase 0) -> Yellow (Phase 1) ...
        commanded = active_phase
        phase_rem = 0.0

        while True:
            active_phase = self._current_phases[node_id]
            phase_start = self._phase_start_times[node_id]
            phase_elapsed = sim_time - phase_start
            art_green_dur, cross_green_dur = self._current_cycle_splits[node_id]
            current_cycle = self._cycle_counters[node_id]
            rem_debt = self._remaining_debts[node_id]

            if active_phase == cfg.arterial_phase_yellow:
                if phase_elapsed < cfg.yellow_duration_sec:
                    phase_rem = cfg.yellow_duration_sec - phase_elapsed
                    commanded = active_phase
                    break
                self._current_phases[node_id] = cfg.arterial_phase_all_red
                self._phase_start_times[node_id] += cfg.yellow_duration_sec

            elif active_phase == cfg.arterial_phase_all_red:
                if phase_elapsed < cfg.all_red_duration_sec:
                    phase_rem = cfg.all_red_duration_sec - phase_elapsed
                    commanded = active_phase
                    break
                self._current_phases[node_id] = cfg.cross_phase_green
                self._phase_start_times[node_id] += cfg.all_red_duration_sec

            elif active_phase == cfg.cross_phase_green:
                if phase_elapsed < cross_green_dur:
                    phase_rem = cross_green_dur - phase_elapsed
                    commanded = active_phase
                    break
                self._current_phases[node_id] = cfg.cross_phase_yellow
                self._phase_start_times[node_id] += cross_green_dur

            elif active_phase == cfg.cross_phase_yellow:
                if phase_elapsed < cfg.yellow_duration_sec:
                    phase_rem = cfg.yellow_duration_sec - phase_elapsed
                    commanded = active_phase
                    break
                self._current_phases[node_id] = cfg.cross_phase_all_red
                self._phase_start_times[node_id] += cfg.yellow_duration_sec

            elif active_phase == cfg.cross_phase_all_red:
                if phase_elapsed < cfg.all_red_duration_sec:
                    phase_rem = cfg.all_red_duration_sec - phase_elapsed
                    commanded = active_phase
                    break
                self._current_phases[node_id] = cfg.arterial_phase_green
                self._phase_start_times[node_id] += cfg.all_red_duration_sec

            elif active_phase == cfg.arterial_phase_green:
                if phase_elapsed < art_green_dur:
                    phase_rem = art_green_dur - phase_elapsed
                    commanded = active_phase
                    break

                # Full compensated recovery cycle complete!
                allocated_bonus = cross_green_dur - cfg.nominal_cross_green_sec
                new_rem_debt = max(0.0, round(rem_debt - allocated_bonus, 2))
                self._remaining_debts[node_id] = new_rem_debt
                next_cycle = current_cycle + 1
                self._cycle_counters[node_id] = next_cycle

                offset_err = self.compute_offset_error(sim_time, node_id)

                if (new_rem_debt <= 1.0) or (next_cycle > cfg.recovery_cycles_budget):
                    if offset_err <= cfg.resync_tolerance_sec or (
                        next_cycle > cfg.recovery_cycles_budget
                    ):
                        self._node_states[node_id] = RecoveryState.EQUILIBRIUM_RESTORED
                        nominal = self.get_nominal_phase(
                            sim_time, self.master_offsets.get(node_id, 0.0)
                        )
                        return NodeRecoveryStatus(
                            node_id=node_id,
                            state=RecoveryState.EQUILIBRIUM_RESTORED,
                            initial_green_debt_sec=self._initial_debts[node_id],
                            remaining_green_debt_sec=0.0,
                            current_recovery_cycle=current_cycle,
                            bonus_green_allocated_sec=0.0,
                            offset_error_sec=offset_err,
                            commanded_phase=nominal,
                            phase_remaining_sec=0.0,
                            is_recovered=True,
                            elapsed_recovery_time_sec=elapsed_recovery,
                            reason=f"Equilibrium restored after {current_cycle} recovery cycles (offset error {offset_err:.1f}s <= {cfg.resync_tolerance_sec}s).",
                            timestamp_sec=sim_time,
                        )
                    else:
                        self._node_states[node_id] = RecoveryState.RESYNCHRONIZING
                else:
                    self._node_states[node_id] = RecoveryState.COMPENSATING

                # Setup next recovery cycle split
                cycles_left = max(1, cfg.recovery_cycles_budget - next_cycle + 1)
                bonus_next = min(cfg.max_bonus_per_cycle_sec, round(new_rem_debt / cycles_left, 2))
                art_next = max(
                    cfg.min_arterial_green_sec, cfg.nominal_arterial_green_sec - bonus_next
                )
                cross_next = min(cfg.max_cross_green_sec, cfg.nominal_cross_green_sec + bonus_next)
                self._current_cycle_splits[node_id] = (art_next, cross_next)

                # Advance to yellow of next cycle
                self._current_phases[node_id] = cfg.arterial_phase_yellow
                self._phase_start_times[node_id] += art_green_dur
                self._cycle_start_times[node_id] = self._phase_start_times[node_id]

        offset_err = self.compute_offset_error(sim_time, node_id)
        bonus_cur = max(0.0, cross_green_dur - cfg.nominal_cross_green_sec)

        return NodeRecoveryStatus(
            node_id=node_id,
            state=self._node_states[node_id],
            initial_green_debt_sec=self._initial_debts[node_id],
            remaining_green_debt_sec=self._remaining_debts[node_id],
            current_recovery_cycle=current_cycle,
            bonus_green_allocated_sec=bonus_cur,
            offset_error_sec=offset_err,
            commanded_phase=commanded,
            phase_remaining_sec=round(phase_rem, 2),
            is_recovered=False,
            elapsed_recovery_time_sec=round(elapsed_recovery, 2),
            reason=f"Recovery cycle {current_cycle}/{cfg.recovery_cycles_budget} in progress ({self._node_states[node_id]}). Remaining debt: {rem_debt:.1f}s.",
            timestamp_sec=sim_time,
        )

    def evaluate_corridor(
        self,
        sim_time: float,
        dt: float = 0.1,
    ) -> CorridorRecoveryReport:
        """Evaluate post-clearance recovery across all intersections."""
        reports: dict[str, NodeRecoveryStatus] = {}
        commanded: dict[str, int] = {}
        recovering_count = 0
        all_equilibrium = True

        for nid in self.intersections:
            rep = self.evaluate_node(nid, sim_time, dt)
            reports[nid] = rep
            commanded[nid] = rep.commanded_phase
            if not rep.is_recovered:
                recovering_count += 1
                all_equilibrium = False

        return CorridorRecoveryReport(
            corridor_recovering_count=recovering_count,
            all_nodes_equilibrium=all_equilibrium,
            node_reports=reports,
            commanded_phases=commanded,
            timestamp_sec=sim_time,
        )

    def step(self, sim_time: float, dt: float = 0.1) -> dict[str, int]:
        """Simulation step method returning commanded phases for recovering intersections."""
        rep = self.evaluate_corridor(sim_time, dt)
        return rep.commanded_phases
