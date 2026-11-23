"""
ClearWayAI - Baseline B1: Reactive Local Preemption Controller
Simulates conventional optical / proximity-based emergency vehicle preemption (e.g. 3M Opticom).
Detects emergency vehicles within a 100m localized proximity zone and forces early phase truncation
to Arterial Green without multi-intersection corridor coordination.
"""

from typing import Any

from simulation.baselines.base_controller import BaseSignalController

# Intersection stopline coordinates along the Eastbound corridor (meters)
INTERSECTION_STOPLINES = {
    "node_a": 0.0,
    "node_b": 300.0,
    "node_c": 600.0,
    "node_d": 900.0,
}


class B1ReactiveController(BaseSignalController):
    """
    Baseline B1: Reactive Local Preemption Controller.
    Each intersection independently monitors a 100m upstream proximity zone.
    When an emergency vehicle is detected approaching:
    - If currently Green for Arterial (Phase 0), it extends Green until the vehicle clears.
    - If currently Green for Cross Street (Phase 3), it truncates and transitions through
      Yellow (Phase 4) and All-Red (Phase 5) to Emergency Arterial Green (Phase 0).
    - Releases back to standard fixed-time cycle after vehicle clears intersection stopline.
    """

    PROXIMITY_DETECTION_METERS = 100.0
    CLEARANCE_EXIT_METERS = 15.0

    def __init__(
        self,
        intersections: list[str] | None = None,
        cycle_time: float = 72.0,
        detection_distance: float = 100.0,
    ):
        super().__init__(intersections=intersections, cycle_time=cycle_time)
        self.detection_distance = detection_distance
        self.stoplines = {nid: INTERSECTION_STOPLINES.get(nid, 0.0) for nid in self.intersections}
        self.preempted_nodes: set[str] = set()
        self.transition_timers: dict[str, float] = {}
        self.reset()

    def reset(self) -> None:
        self.metrics.total_steps = 0
        self.metrics.preemption_events = 0
        self.metrics.total_preemption_duration_sec = 0.0
        self.preempted_nodes.clear()
        self.transition_timers.clear()

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
        Calculates signal phase for each intersection, applying local proximity preemption
        if an emergency vehicle is detected within 100m.
        """
        self.metrics.total_steps += 1
        nominal_phase = self.get_nominal_phase(sim_time)
        result_phases = {}

        # Locate emergency vehicle along the corridor
        amb = next(
            (v for v in active_vehicles.values() if v.get("is_emergency")),
            None,
        )

        for nid in self.intersections:
            stopline = self.stoplines[nid]
            is_in_zone = False

            if amb is not None:
                amb_x = amb.get("x", -999.0)
                # Detection zone: stopline - detection_distance <= amb_x <= stopline + exit_meters
                if (
                    (stopline - self.detection_distance)
                    <= amb_x
                    <= (stopline + self.CLEARANCE_EXIT_METERS)
                ):
                    is_in_zone = True

            if is_in_zone:
                if nid not in self.preempted_nodes:
                    self.preempted_nodes.add(nid)
                    self.metrics.preemption_events += 1
                    # Initialize transition timer if we need yellow/all-red clearance
                    if nominal_phase in [3, 4, 5]:
                        self.transition_timers[nid] = 6.0  # 4s yellow + 2s all-red

                self.metrics.total_preemption_duration_sec += dt

                # Handle transition from cross street to arterial green
                if nid in self.transition_timers and self.transition_timers[nid] > 0.0:
                    self.transition_timers[nid] -= dt
                    if self.transition_timers[nid] > 2.0:
                        # Yellow clearance
                        result_phases[nid] = 4
                    else:
                        # All-red clearance
                        result_phases[nid] = 5
                else:
                    # Emergency Arterial Green
                    result_phases[nid] = 0
            else:
                if nid in self.preempted_nodes:
                    self.preempted_nodes.remove(nid)
                    self.transition_timers.pop(nid, None)

                result_phases[nid] = nominal_phase

        return result_phases
