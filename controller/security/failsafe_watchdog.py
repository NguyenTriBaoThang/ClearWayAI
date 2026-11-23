"""
ClearWayAI - Fail-Safe Heartbeat Watchdog & Autonomous Degradation (`controller.security.failsafe_watchdog`).

Implements formal safety Invariant 6 (INV-06):
"If edge controllers lose V2X/RSU communication or backend telemetry heartbeats for more than
T_timeout (500ms), controllers must autonomously degrade to local fixed-time Webster cycle."

Monitors:
1. V2X telemetry channel
2. Edge camera perception pipeline
3. AI clearance inference gateway
4. Corridor coordination orchestrator

Operational States:
- HEALTHY: All heartbeats within 500ms nominal window. Full AI preemption enabled.
- DEGRADED: Telemetry jitter (500ms - 1000ms). Warning raised, new preemption requests held.
- TRIPPED_FAILSAFE: Heartbeat severed (> 1000ms). All active priority preemption overrides
  are aborted, signals fall back autonomously to local Webster cycle timing.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        def __str__(self) -> str:
            return str(self.value)


class WatchdogOperationalState(StrEnum):
    """Operational health state of the signal control system watchdog."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    TRIPPED_FAILSAFE = "TRIPPED_FAILSAFE"


@dataclass
class WatchdogChannelStatus:
    """Real-time monitoring metrics for an individual communication channel."""

    channel_id: str
    last_heartbeat_sec: float
    elapsed_since_heartbeat_sec: float
    is_healthy: bool
    is_timed_out: bool


@dataclass
class WatchdogEvaluationReport:
    """Comprehensive snapshot of system watchdog health."""

    state: WatchdogOperationalState
    is_safe_to_control: bool
    fallback_engaged: bool
    primary_failure_channel: str | None
    channel_statuses: dict[str, WatchdogChannelStatus]
    safe_phase: int
    timestamp_sec: float
    provenance: str = "FAIL_SAFE_WATCHDOG"


class FailSafeWatchdog:
    """
    Autonomous heartbeat watchdog guarding safety boundaries (INV-06).
    Enforces deterministic fallback upon communication disruption.
    """

    DEFAULT_CHANNELS = [
        "v2x_telemetry",
        "camera_perception",
        "ai_inference_gateway",
        "corridor_coordinator",
    ]

    def __init__(
        self,
        channels: list[str] | None = None,
        timeout_sec: float = 0.5,  # 500ms threshold (INV-06)
        trip_threshold_sec: float = 1.0,  # 1.0s hard cutoff
        nominal_cycle_sec: float = 72.0,
    ) -> None:
        self.channels = channels or list(self.DEFAULT_CHANNELS)
        self.timeout_sec = timeout_sec
        self.trip_threshold_sec = trip_threshold_sec
        self.nominal_cycle_sec = nominal_cycle_sec

        self._last_heartbeats: dict[str, float] = {}
        self._current_state = WatchdogOperationalState.HEALTHY
        self._trip_count = 0
        self.reset()

    def reset(self) -> None:
        """Reset watchdog timestamps to initialized state."""
        self._last_heartbeats = dict.fromkeys(self.channels, 0.0)
        self._current_state = WatchdogOperationalState.HEALTHY
        self._trip_count = 0

    def record_heartbeat(self, channel_id: str, sim_time: float) -> None:
        """Record live heartbeat pulse from an operational subsystem channel."""
        self._last_heartbeats[channel_id] = sim_time

    def get_nominal_webster_phase(self, sim_time: float) -> int:
        """Compute standard Webster fixed-time phase for autonomous fallback."""
        t_cycle = sim_time % self.nominal_cycle_sec
        if t_cycle < 35.0:
            return 0  # Arterial Green
        elif t_cycle < 38.0:
            return 1  # Arterial Yellow
        elif t_cycle < 40.0:
            return 2  # All-Red
        elif t_cycle < 65.0:
            return 3  # Cross Green
        elif t_cycle < 68.0:
            return 4  # Cross Yellow
        else:
            return 5  # All-Red

    def evaluate_watchdog(self, sim_time: float) -> WatchdogEvaluationReport:
        """
        Evaluate channel health against timeout thresholds and enforce degradation policy.
        """
        statuses = {}
        max_elapsed = 0.0
        worst_channel: str | None = None

        for ch in self.channels:
            last_hb = self._last_heartbeats.get(ch, 0.0)
            elapsed = max(0.0, sim_time - last_hb)
            is_healthy = elapsed <= self.timeout_sec
            is_timed_out = elapsed > self.trip_threshold_sec

            statuses[ch] = WatchdogChannelStatus(
                channel_id=ch,
                last_heartbeat_sec=last_hb,
                elapsed_since_heartbeat_sec=round(elapsed, 3),
                is_healthy=is_healthy,
                is_timed_out=is_timed_out,
            )

            if elapsed > max_elapsed:
                max_elapsed = elapsed
                worst_channel = ch

        # State Transition Logic
        if max_elapsed <= self.timeout_sec:
            state = WatchdogOperationalState.HEALTHY
            safe_to_control = True
            fallback = False
        elif max_elapsed <= self.trip_threshold_sec:
            state = WatchdogOperationalState.DEGRADED
            safe_to_control = False
            fallback = False
        else:
            state = WatchdogOperationalState.TRIPPED_FAILSAFE
            safe_to_control = False
            fallback = True
            if self._current_state != WatchdogOperationalState.TRIPPED_FAILSAFE:
                self._trip_count += 1

        self._current_state = state
        safe_phase = self.get_nominal_webster_phase(sim_time)

        return WatchdogEvaluationReport(
            state=state,
            is_safe_to_control=safe_to_control,
            fallback_engaged=fallback,
            primary_failure_channel=worst_channel if max_elapsed > self.timeout_sec else None,
            channel_statuses=statuses,
            safe_phase=safe_phase,
            timestamp_sec=sim_time,
        )
