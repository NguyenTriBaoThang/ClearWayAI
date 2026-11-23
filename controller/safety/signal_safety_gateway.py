"""ClearWayAI Independent Signal Safety Gateway (`controller.safety`).

Emulates a hardware Malfunction Management Unit (MMU) / Conflict Monitor Unit (CMU)
providing an independent, deterministic zero-trust safety boundary between
optimization algorithms (pre-clearance, coordinator, recovery, RL) and traffic signals.

Enforces formal safety invariants:
1. INV-01: Conflict-Free Vehicular Mutual Exclusion (Green-Green and Green-Yellow exclusion).
2. INV-02: Minimum Green Interval Enforcement ($T_{\\text{min\\_green}} \\ge 10.0\\text{s}$).
3. INV-03: Maximum Green Interval Enforcement ($T_{\\text{max\\_green}} \\le 75.0\\text{s}$).
4. INV-04: Minimum Yellow Change Interval ($T_{\\text{yellow}} \\ge 3.0\\text{s}$, derived from ITE kinematic equation).
5. INV-05: Minimum All-Red Clearance Interval ($T_{\\text{all\\_red}} \\ge 2.0\\text{s}$).
6. INV-06: Communication Loss & Heartbeat Watchdog Timeout ($T_{\\text{timeout}} \\le 2.0\\text{s}$).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class SignalColor(StrEnum):
    """Signal lens display colors."""

    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"


class GatewayTripReason(StrEnum):
    """Formal classification of intercepted safety invariant violations."""

    NONE = "NONE"
    CONFLICT_GREEN_GREEN = "CONFLICT_GREEN_GREEN"
    MIN_GREEN_VIOLATION = "MIN_GREEN_VIOLATION"
    MAX_GREEN_EXCEEDED = "MAX_GREEN_EXCEEDED"
    YELLOW_TRUNCATION_VIOLATION = "YELLOW_TRUNCATION_VIOLATION"
    ALL_RED_SKIPPED_VIOLATION = "ALL_RED_SKIPPED_VIOLATION"
    HEARTBEAT_TIMEOUT = "HEARTBEAT_TIMEOUT"
    INVALID_PHASE_INDEX = "INVALID_PHASE_INDEX"


class GatewayOperationalMode(StrEnum):
    """Operational mode of the Signal Safety Gateway."""

    NORMAL_PASSTHROUGH = "NORMAL_PASSTHROUGH"
    CLAMPED_SAFE = "CLAMPED_SAFE"
    FAILSAFE_ALL_RED = "FAILSAFE_ALL_RED"
    FALLBACK_WEBSTER = "FALLBACK_WEBSTER"


@dataclass
class SafetyGatewayConfig:
    """Safety thresholds adhering to ITE standards and CW-SAFE-001 specification."""

    min_green_sec: float = 10.0
    max_green_sec: float = 75.0
    min_yellow_sec: float = 3.0
    min_all_red_sec: float = 2.0
    heartbeat_timeout_sec: float = 2.0
    nominal_cycle_sec: float = 72.0

    # NEMA 6-Phase Standard Mapping
    arterial_phase_green: int = 0
    arterial_phase_yellow: int = 1
    arterial_phase_all_red: int = 2
    cross_phase_green: int = 3
    cross_phase_yellow: int = 4
    cross_phase_all_red: int = 5

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SafetyInterventionRecord:
    """Audit log entry capturing an intercepted unsafe signal command."""

    timestamp_sec: float
    node_id: str
    proposed_phase: int
    sanitized_phase: int
    trip_reason: GatewayTripReason
    operational_mode: GatewayOperationalMode
    description: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["trip_reason"] = str(self.trip_reason)
        d["operational_mode"] = str(self.operational_mode)
        return d


@dataclass
class SafetyGatewayReport:
    """Safety assessment report for an individual intersection node."""

    node_id: str
    operational_mode: GatewayOperationalMode
    sanitized_phase: int
    phase_elapsed_sec: float
    current_approach_colors: dict[str, SignalColor]
    is_safe: bool
    intervention: SafetyInterventionRecord | None
    last_heartbeat_timestamp: float
    total_interventions_count: int
    provenance: str = "INDEPENDENT_SIGNAL_SAFETY_GATEWAY"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["operational_mode"] = str(self.operational_mode)
        d["current_approach_colors"] = {k: str(v) for k, v in self.current_approach_colors.items()}
        d["intervention"] = self.intervention.to_dict() if self.intervention else None
        return d


@dataclass
class CorridorSafetyAudit:
    """Consolidated safety audit across all corridor intersections."""

    all_nodes_safe: bool
    reports_by_node: dict[str, SafetyGatewayReport]
    sanitized_phases: dict[str, int]
    total_interventions_corridor: int
    timestamp_sec: float
    provenance: str = "INDEPENDENT_SIGNAL_SAFETY_GATEWAY"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["reports_by_node"] = {k: v.to_dict() for k, v in self.reports_by_node.items()}
        return d


# NEMA 6-Phase Approach Color Manifest
PHASE_APPROACH_COLORS: dict[int, dict[str, SignalColor]] = {
    0: {
        "eb": SignalColor.GREEN,
        "wb": SignalColor.GREEN,
        "nb": SignalColor.RED,
        "sb": SignalColor.RED,
    },
    1: {
        "eb": SignalColor.YELLOW,
        "wb": SignalColor.YELLOW,
        "nb": SignalColor.RED,
        "sb": SignalColor.RED,
    },
    2: {
        "eb": SignalColor.RED,
        "wb": SignalColor.RED,
        "nb": SignalColor.RED,
        "sb": SignalColor.RED,
    },
    3: {
        "eb": SignalColor.RED,
        "wb": SignalColor.RED,
        "nb": SignalColor.GREEN,
        "sb": SignalColor.GREEN,
    },
    4: {
        "eb": SignalColor.RED,
        "wb": SignalColor.RED,
        "nb": SignalColor.YELLOW,
        "sb": SignalColor.YELLOW,
    },
    5: {
        "eb": SignalColor.RED,
        "wb": SignalColor.RED,
        "nb": SignalColor.RED,
        "sb": SignalColor.RED,
    },
}


class SignalSafetyGateway:
    """Zero-trust Malfunction Management Unit intercepting and verifying all signal plans."""

    def __init__(
        self,
        config: SafetyGatewayConfig | None = None,
        node_ids: list[str] | None = None,
    ) -> None:
        self.config = config or SafetyGatewayConfig()
        self.node_ids = node_ids or ["node_a", "node_b", "node_c", "node_d"]

        # Hardware-emulated internal registers
        self._current_phases: dict[str, int] = dict.fromkeys(self.node_ids, self.config.arterial_phase_green)
        self._phase_start_times: dict[str, float] = dict.fromkeys(self.node_ids, 0.0)
        self._last_heartbeats: dict[str, float] = dict.fromkeys(self.node_ids, 0.0)
        self._operational_modes: dict[str, GatewayOperationalMode] = dict.fromkeys(self.node_ids, GatewayOperationalMode.NORMAL_PASSTHROUGH)
        self._interventions: list[SafetyInterventionRecord] = []
        self._interventions_count: dict[str, int] = dict.fromkeys(self.node_ids, 0)

    def reset(self) -> None:
        """Reset internal hardware registers to initial baseline."""
        for nid in self.node_ids:
            self._current_phases[nid] = self.config.arterial_phase_green
            self._phase_start_times[nid] = 0.0
            self._last_heartbeats[nid] = 0.0
            self._operational_modes[nid] = GatewayOperationalMode.NORMAL_PASSTHROUGH
            self._interventions_count[nid] = 0
        self._interventions.clear()

    @staticmethod
    def get_approach_colors(phase: int) -> dict[str, SignalColor]:
        """Return vehicular approach colors for a specific NEMA phase index."""
        return PHASE_APPROACH_COLORS.get(
            phase,
            {
                "eb": SignalColor.RED,
                "wb": SignalColor.RED,
                "nb": SignalColor.RED,
                "sb": SignalColor.RED,
            },
        )

    @staticmethod
    def check_conflict_free(colors: dict[str, SignalColor]) -> bool:
        """Verify vehicular mutual exclusion (INV-01): Green/Yellow EW must not co-exist with Green/Yellow NS."""
        ew_active = colors.get("eb") in (SignalColor.GREEN, SignalColor.YELLOW) or colors.get(
            "wb"
        ) in (SignalColor.GREEN, SignalColor.YELLOW)
        ns_active = colors.get("nb") in (SignalColor.GREEN, SignalColor.YELLOW) or colors.get(
            "sb"
        ) in (SignalColor.GREEN, SignalColor.YELLOW)
        return not (ew_active and ns_active)

    def get_nominal_phase(self, sim_time: float) -> int:
        """Standard Webster cycle phase timing for fail-safe fallback."""
        cfg = self.config
        t_cycle = sim_time % cfg.nominal_cycle_sec
        if t_cycle < 35.0:
            return cfg.arterial_phase_green
        elif t_cycle < 38.0:
            return cfg.arterial_phase_yellow
        elif t_cycle < 40.0:
            return cfg.arterial_phase_all_red
        elif t_cycle < 65.0:
            return cfg.cross_phase_green
        elif t_cycle < 68.0:
            return cfg.cross_phase_yellow
        else:
            return cfg.cross_phase_all_red

    def verify_and_sanitize_command(
        self,
        node_id: str,
        proposed_phase: int,
        sim_time: float,
        heartbeat: bool = True,
    ) -> SafetyGatewayReport:
        """Inspect proposed phase command against all formal safety invariants and clamp if unsafe."""
        cfg = self.config

        # Register node if not seen before
        if node_id not in self._current_phases:
            self._current_phases[node_id] = cfg.arterial_phase_green
            self._phase_start_times[node_id] = sim_time
            self._last_heartbeats[node_id] = sim_time
            self._operational_modes[node_id] = GatewayOperationalMode.NORMAL_PASSTHROUGH
            self._interventions_count[node_id] = 0

        # Update heartbeat
        if heartbeat:
            self._last_heartbeats[node_id] = sim_time

        last_hb = self._last_heartbeats[node_id]
        current_phase = self._current_phases[node_id]
        phase_start = self._phase_start_times[node_id]
        phase_elapsed = max(0.0, sim_time - phase_start)

        intervention: SafetyInterventionRecord | None = None
        sanitized_phase = proposed_phase
        mode = GatewayOperationalMode.NORMAL_PASSTHROUGH

        # Invariant 6 (INV-06): Heartbeat Watchdog Check
        if (sim_time - last_hb) > cfg.heartbeat_timeout_sec:
            mode = GatewayOperationalMode.FALLBACK_WEBSTER
            sanitized_phase = self.get_nominal_phase(sim_time)
            intervention = SafetyInterventionRecord(
                timestamp_sec=sim_time,
                node_id=node_id,
                proposed_phase=proposed_phase,
                sanitized_phase=sanitized_phase,
                trip_reason=GatewayTripReason.HEARTBEAT_TIMEOUT,
                operational_mode=mode,
                description=f"Heartbeat timeout ({(sim_time - last_hb):.2f}s > {cfg.heartbeat_timeout_sec}s). Reverting to autonomous Webster fallback.",
            )
            self._record_intervention(intervention)
            self._current_phases[node_id] = sanitized_phase
            return self._build_report(node_id, mode, sanitized_phase, phase_elapsed, intervention)

        # Invariant check: Valid Phase Index [0, 5]
        if proposed_phase not in range(0, 6):
            mode = GatewayOperationalMode.FAILSAFE_ALL_RED
            sanitized_phase = cfg.arterial_phase_all_red
            intervention = SafetyInterventionRecord(
                timestamp_sec=sim_time,
                node_id=node_id,
                proposed_phase=proposed_phase,
                sanitized_phase=sanitized_phase,
                trip_reason=GatewayTripReason.INVALID_PHASE_INDEX,
                operational_mode=mode,
                description=f"Proposed phase {proposed_phase} is invalid. Dropping to Fail-Safe All-Red.",
            )
            self._record_intervention(intervention)
            self._current_phases[node_id] = sanitized_phase
            self._phase_start_times[node_id] = sim_time
            return self._build_report(node_id, mode, sanitized_phase, 0.0, intervention)

        # Check Mutual Exclusion (INV-01) on proposed phase
        proposed_colors = self.get_approach_colors(proposed_phase)
        if not self.check_conflict_free(proposed_colors):
            mode = GatewayOperationalMode.FAILSAFE_ALL_RED
            sanitized_phase = cfg.arterial_phase_all_red
            intervention = SafetyInterventionRecord(
                timestamp_sec=sim_time,
                node_id=node_id,
                proposed_phase=proposed_phase,
                sanitized_phase=sanitized_phase,
                trip_reason=GatewayTripReason.CONFLICT_GREEN_GREEN,
                operational_mode=mode,
                description=f"Proposed phase {proposed_phase} creates green-green conflict. Dropping to Fail-Safe All-Red.",
            )
            self._record_intervention(intervention)
            self._current_phases[node_id] = sanitized_phase
            self._phase_start_times[node_id] = sim_time
            return self._build_report(node_id, mode, sanitized_phase, 0.0, intervention)

        # Transition Invariants
        if proposed_phase == current_phase:
            # Holding current phase: Check Maximum Green (INV-03)
            if current_phase in (
                cfg.arterial_phase_green,
                cfg.cross_phase_green,
            ) and phase_elapsed >= (cfg.max_green_sec - 1e-4):
                # Max green exceeded: force transition to Yellow
                forced_yellow = (
                    cfg.arterial_phase_yellow
                    if current_phase == cfg.arterial_phase_green
                    else cfg.cross_phase_yellow
                )
                mode = GatewayOperationalMode.CLAMPED_SAFE
                sanitized_phase = forced_yellow
                intervention = SafetyInterventionRecord(
                    timestamp_sec=sim_time,
                    node_id=node_id,
                    proposed_phase=proposed_phase,
                    sanitized_phase=sanitized_phase,
                    trip_reason=GatewayTripReason.MAX_GREEN_EXCEEDED,
                    operational_mode=mode,
                    description=f"Maximum green interval ({cfg.max_green_sec}s) exceeded. Forcing transition to Yellow.",
                )
                self._record_intervention(intervention)
                self._current_phases[node_id] = sanitized_phase
                self._phase_start_times[node_id] = sim_time
                return self._build_report(node_id, mode, sanitized_phase, 0.0, intervention)
            else:
                # Normal holding
                mode = GatewayOperationalMode.NORMAL_PASSTHROUGH
                sanitized_phase = current_phase
                return self._build_report(node_id, mode, sanitized_phase, phase_elapsed, None)

        # Proposed phase is DIFFERENT from current phase: Validate transition sequence
        # Case 1: Currently Green (Phase 0 or Phase 3)
        if current_phase in (cfg.arterial_phase_green, cfg.cross_phase_green):
            # Check Invariant 2 (INV-02): Minimum Green Enforcement
            if phase_elapsed < (cfg.min_green_sec - 1e-4):
                mode = GatewayOperationalMode.CLAMPED_SAFE
                sanitized_phase = current_phase
                intervention = SafetyInterventionRecord(
                    timestamp_sec=sim_time,
                    node_id=node_id,
                    proposed_phase=proposed_phase,
                    sanitized_phase=sanitized_phase,
                    trip_reason=GatewayTripReason.MIN_GREEN_VIOLATION,
                    operational_mode=mode,
                    description=f"Minimum green ({cfg.min_green_sec}s) not reached (elapsed: {phase_elapsed:.1f}s). Clamping to Green.",
                )
                self._record_intervention(intervention)
                return self._build_report(
                    node_id, mode, sanitized_phase, phase_elapsed, intervention
                )

            # Check Invariant 4 (INV-04): Mandatory Yellow (cannot skip directly to Red or opposing Green)
            required_yellow = (
                cfg.arterial_phase_yellow
                if current_phase == cfg.arterial_phase_green
                else cfg.cross_phase_yellow
            )
            if proposed_phase != required_yellow:
                # Attempted to skip yellow!
                mode = GatewayOperationalMode.CLAMPED_SAFE
                sanitized_phase = required_yellow
                intervention = SafetyInterventionRecord(
                    timestamp_sec=sim_time,
                    node_id=node_id,
                    proposed_phase=proposed_phase,
                    sanitized_phase=sanitized_phase,
                    trip_reason=GatewayTripReason.YELLOW_TRUNCATION_VIOLATION,
                    operational_mode=mode,
                    description=f"Attempted to skip mandatory yellow change. Clamping to Yellow ({required_yellow}).",
                )
                self._record_intervention(intervention)
                self._current_phases[node_id] = sanitized_phase
                self._phase_start_times[node_id] = sim_time
                return self._build_report(node_id, mode, sanitized_phase, 0.0, intervention)

            # Valid transition to Yellow
            self._current_phases[node_id] = proposed_phase
            self._phase_start_times[node_id] = sim_time
            return self._build_report(
                node_id, GatewayOperationalMode.NORMAL_PASSTHROUGH, proposed_phase, 0.0, None
            )

        # Case 2: Currently Yellow (Phase 1 or Phase 4)
        if current_phase in (cfg.arterial_phase_yellow, cfg.cross_phase_yellow):
            # Check Invariant 4 (INV-04): Yellow Duration cannot be truncated
            if phase_elapsed < (cfg.min_yellow_sec - 1e-4):
                mode = GatewayOperationalMode.CLAMPED_SAFE
                sanitized_phase = current_phase
                intervention = SafetyInterventionRecord(
                    timestamp_sec=sim_time,
                    node_id=node_id,
                    proposed_phase=proposed_phase,
                    sanitized_phase=sanitized_phase,
                    trip_reason=GatewayTripReason.YELLOW_TRUNCATION_VIOLATION,
                    operational_mode=mode,
                    description=f"Yellow duration ({cfg.min_yellow_sec}s) not completed (elapsed: {phase_elapsed:.1f}s). Clamping Yellow.",
                )
                self._record_intervention(intervention)
                return self._build_report(
                    node_id, mode, sanitized_phase, phase_elapsed, intervention
                )

            # Check Invariant 5 (INV-05): Mandatory All-Red Clearance (cannot skip directly to opposing Green)
            required_all_red = (
                cfg.arterial_phase_all_red
                if current_phase == cfg.arterial_phase_yellow
                else cfg.cross_phase_all_red
            )
            if proposed_phase != required_all_red:
                mode = GatewayOperationalMode.CLAMPED_SAFE
                sanitized_phase = required_all_red
                intervention = SafetyInterventionRecord(
                    timestamp_sec=sim_time,
                    node_id=node_id,
                    proposed_phase=proposed_phase,
                    sanitized_phase=sanitized_phase,
                    trip_reason=GatewayTripReason.ALL_RED_SKIPPED_VIOLATION,
                    operational_mode=mode,
                    description=f"Attempted to skip mandatory all-red clearance. Clamping to All-Red ({required_all_red}).",
                )
                self._record_intervention(intervention)
                self._current_phases[node_id] = sanitized_phase
                self._phase_start_times[node_id] = sim_time
                return self._build_report(node_id, mode, sanitized_phase, 0.0, intervention)

            # Valid transition to All-Red
            self._current_phases[node_id] = proposed_phase
            self._phase_start_times[node_id] = sim_time
            return self._build_report(
                node_id, GatewayOperationalMode.NORMAL_PASSTHROUGH, proposed_phase, 0.0, None
            )

        # Case 3: Currently All-Red (Phase 2 or Phase 5)
        if current_phase in (cfg.arterial_phase_all_red, cfg.cross_phase_all_red):
            # Check Invariant 5 (INV-05): All-Red Duration cannot be truncated
            if phase_elapsed < (cfg.min_all_red_sec - 1e-4):
                mode = GatewayOperationalMode.CLAMPED_SAFE
                sanitized_phase = current_phase
                intervention = SafetyInterventionRecord(
                    timestamp_sec=sim_time,
                    node_id=node_id,
                    proposed_phase=proposed_phase,
                    sanitized_phase=sanitized_phase,
                    trip_reason=GatewayTripReason.ALL_RED_SKIPPED_VIOLATION,
                    operational_mode=mode,
                    description=f"All-red clearance ({cfg.min_all_red_sec}s) not completed (elapsed: {phase_elapsed:.1f}s). Clamping All-Red.",
                )
                self._record_intervention(intervention)
                return self._build_report(
                    node_id, mode, sanitized_phase, phase_elapsed, intervention
                )

            # All-Red has elapsed: transition to opposing Green is permitted
            self._current_phases[node_id] = proposed_phase
            self._phase_start_times[node_id] = sim_time
            return self._build_report(
                node_id, GatewayOperationalMode.NORMAL_PASSTHROUGH, proposed_phase, 0.0, None
            )

        # Fallback passthrough
        self._current_phases[node_id] = proposed_phase
        self._phase_start_times[node_id] = sim_time
        return self._build_report(
            node_id, GatewayOperationalMode.NORMAL_PASSTHROUGH, proposed_phase, 0.0, None
        )

    def audit_corridor_phases(
        self,
        proposed_phases: dict[str, int],
        sim_time: float,
        heartbeat: bool = True,
    ) -> CorridorSafetyAudit:
        """Audit and sanitize phase commands across all corridor intersections simultaneously."""
        reports: dict[str, SafetyGatewayReport] = {}
        sanitized_phases: dict[str, int] = {}
        all_safe = True
        total_interventions = 0

        for nid in self.node_ids:
            prop = proposed_phases.get(nid, self._current_phases.get(nid, 0))
            rep = self.verify_and_sanitize_command(
                node_id=nid,
                proposed_phase=prop,
                sim_time=sim_time,
                heartbeat=heartbeat,
            )
            reports[nid] = rep
            sanitized_phases[nid] = rep.sanitized_phase
            if not rep.is_safe:
                all_safe = False
            if rep.intervention is not None:
                total_interventions += 1

        return CorridorSafetyAudit(
            all_nodes_safe=all_safe,
            reports_by_node=reports,
            sanitized_phases=sanitized_phases,
            total_interventions_corridor=total_interventions,
            timestamp_sec=sim_time,
        )

    def _record_intervention(self, intervention: SafetyInterventionRecord) -> None:
        self._interventions.append(intervention)
        self._interventions_count[intervention.node_id] = (
            self._interventions_count.get(intervention.node_id, 0) + 1
        )

    def _build_report(
        self,
        node_id: str,
        mode: GatewayOperationalMode,
        phase: int,
        phase_elapsed: float,
        intervention: SafetyInterventionRecord | None,
    ) -> SafetyGatewayReport:
        is_safe = mode in (
            GatewayOperationalMode.NORMAL_PASSTHROUGH,
            GatewayOperationalMode.CLAMPED_SAFE,
        )
        return SafetyGatewayReport(
            node_id=node_id,
            operational_mode=mode,
            sanitized_phase=phase,
            phase_elapsed_sec=round(phase_elapsed, 2),
            current_approach_colors=self.get_approach_colors(phase),
            is_safe=is_safe,
            intervention=intervention,
            last_heartbeat_timestamp=self._last_heartbeats.get(node_id, 0.0),
            total_interventions_count=self._interventions_count.get(node_id, 0),
        )
