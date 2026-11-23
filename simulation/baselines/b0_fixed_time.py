"""
ClearWayAI - Baseline B0: Fixed-Time Signal Controller
Implements standard Webster pre-timed fixed signal splits without vehicle actuation
or emergency priority preemption.
"""

from typing import Any

from simulation.baselines.base_controller import BaseSignalController


class B0FixedTimeController(BaseSignalController):
    """
    Baseline B0: Fixed-Time Traffic Signal Controller.
    Runs a deterministic 72-second cycle split for all corridor intersections:
    - Phase 0 (0-35s): Arterial EB/WB Green (35s)
    - Phase 1 (35-39s): Arterial EB/WB Yellow (4s)
    - Phase 2 (39-41s): All-Red Clearance (2s)
    - Phase 3 (41-66s): Cross Street NB/SB Green (25s)
    - Phase 4 (66-70s): Cross Street NB/SB Yellow (4s)
    - Phase 5 (70-72s): All-Red Clearance (2s)
    Provides zero preemption for emergency vehicles.
    """

    def __init__(
        self,
        intersections: list[str] | None = None,
        cycle_time: float = 72.0,
    ):
        super().__init__(intersections=intersections, cycle_time=cycle_time)
        self.reset()

    def reset(self) -> None:
        self.metrics.total_steps = 0
        self.metrics.preemption_events = 0
        self.metrics.total_preemption_duration_sec = 0.0

    def get_phase_at_time(self, t: float) -> int:
        """Computes active phase based purely on fixed-time cycle position."""
        cycle_pos = t % self.cycle_time
        if cycle_pos < 35.0:
            return 0
        elif cycle_pos < 39.0:
            return 1
        elif cycle_pos < 41.0:
            return 2
        elif cycle_pos < 66.0:
            return 3
        elif cycle_pos < 70.0:
            return 4
        else:
            return 5

    def step(
        self,
        sim_time: float,
        active_vehicles: dict[str, dict[str, Any]],
        dt: float = 0.1,
    ) -> dict[str, int]:
        """Returns the fixed-time phase for each intersection at sim_time."""
        self.metrics.total_steps += 1
        phase = self.get_phase_at_time(sim_time)
        return dict.fromkeys(self.intersections, phase)
