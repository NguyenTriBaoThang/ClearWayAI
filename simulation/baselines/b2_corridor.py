"""
ClearWayAI - Baseline B2: Corridor Coordination (Static Green-Wave Preemption)
Simulates traditional corridor-wide emergency preemption:
When an emergency vehicle enters the arterial corridor, all signals along the corridor route (A-D)
are simultaneously locked to Arterial Green without dynamic queue clearance or post-clearance recovery.
"""

from typing import Any

from simulation.baselines.base_controller import BaseSignalController


class B2CorridorController(BaseSignalController):
    """
    Baseline B2: Corridor Coordination (Static Arterial Green-Wave).
    Monitors the corridor entry point (West gate, x = -150m):
    - When an emergency vehicle is detected entering the corridor:
      ALL intersections (Nodes A, B, C, D) are locked to Arterial Green (Phase 0).
    - Signals remain locked until the emergency vehicle fully exits Node D (x >= 950m).
    - Drawbacks:
      1. Massive cross-street delay (cross streets locked at Red for the full transit duration).
      2. No dynamic queue drainage: standing queues remain at stoplines, forcing the ambulance to decelerate.
      3. No post-clearance equilibrium recovery: intersections abruptly return to desynchronized fixed cycles.
    """

    CORRIDOR_ENTRY_X = -150.0
    CORRIDOR_EXIT_X = 950.0

    def __init__(
        self,
        intersections: list[str] | None = None,
        cycle_time: float = 72.0,
    ):
        super().__init__(intersections=intersections, cycle_time=cycle_time)
        self.is_corridor_preempted: bool = False
        self.transition_timer: float = 0.0
        self.reset()

    def reset(self) -> None:
        self.metrics.total_steps = 0
        self.metrics.preemption_events = 0
        self.metrics.total_preemption_duration_sec = 0.0
        self.is_corridor_preempted = False
        self.transition_timer = 0.0

    def get_nominal_phase(self, t: float) -> int:
        """Returns standard Webster phase at time t."""
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
        """
        Advances corridor signal controller.
        Locks all 4 intersections to Phase 0 if emergency vehicle is in the corridor.
        """
        self.metrics.total_steps += 1
        nominal_phase = self.get_nominal_phase(sim_time)

        # Locate emergency vehicle
        amb = next(
            (v for v in active_vehicles.values() if v.get("is_emergency")),
            None,
        )

        in_corridor = False
        if amb is not None:
            amb_x = amb.get("x", -999.0)
            if self.CORRIDOR_ENTRY_X <= amb_x <= self.CORRIDOR_EXIT_X:
                in_corridor = True

        if in_corridor:
            if not self.is_corridor_preempted:
                self.is_corridor_preempted = True
                self.metrics.preemption_events += 1
                if nominal_phase in [3, 4, 5]:
                    self.transition_timer = 6.0  # 4s yellow + 2s all-red

            self.metrics.total_preemption_duration_sec += dt

            if self.transition_timer > 0.0:
                self.transition_timer -= dt
                phase = 4 if self.transition_timer > 2.0 else 5
            else:
                phase = 0

            return dict.fromkeys(self.intersections, phase)
        else:
            self.is_corridor_preempted = False
            self.transition_timer = 0.0
            return dict.fromkeys(self.intersections, nominal_phase)
