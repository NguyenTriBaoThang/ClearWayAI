"""
ClearWayAI - Base Traffic Signal Controller
Abstract base class for all baseline and adaptive signal controllers.
Enforces common interfaces, phase mappings, safety constraints, and metric tracking.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ControllerMetrics:
    """Performance metrics tracked by a signal controller."""

    total_steps: int = 0
    preemption_events: int = 0
    total_preemption_duration_sec: float = 0.0
    emergency_stops: int = 0
    emergency_transit_time_sec: float = 0.0
    cross_street_delay_sec: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)


class BaseSignalController(ABC):
    """Abstract base class for intersection and corridor signal controllers."""

    DEFAULT_INTERSECTIONS = ["node_a", "node_b", "node_c", "node_d"]
    CYCLE_TIME = 72.0  # seconds

    def __init__(
        self,
        intersections: list[str] | None = None,
        cycle_time: float = 72.0,
    ):
        self.intersections = intersections or self.DEFAULT_INTERSECTIONS
        self.cycle_time = cycle_time
        self.metrics = ControllerMetrics()

    @abstractmethod
    def step(
        self,
        sim_time: float,
        active_vehicles: dict[str, dict[str, Any]],
        dt: float = 0.1,
    ) -> dict[str, int]:
        """
        Advance the controller by dt seconds.
        Returns a dictionary mapping intersection_id -> current_phase_index (0 to 5).
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset internal controller state for a new simulation run."""
        pass

    def get_approach_colors(self, phase_idx: int) -> dict[str, str]:
        """
        Map a NEMA 6-phase index to standard directional signal colors:
        Phase 0: EB/WB Green, NB/SB Red
        Phase 1: EB/WB Yellow, NB/SB Red
        Phase 2: All-Red
        Phase 3: NB/SB Green, EB/WB Red
        Phase 4: NB/SB Yellow, EB/WB Red
        Phase 5: All-Red
        """
        if phase_idx == 0:
            return {"eb": "green", "wb": "green", "nb": "red", "sb": "red"}
        elif phase_idx == 1:
            return {"eb": "yellow", "wb": "yellow", "nb": "red", "sb": "red"}
        elif phase_idx in (2, 5):
            return {"eb": "red", "wb": "red", "nb": "red", "sb": "red"}
        elif phase_idx == 3:
            return {"eb": "red", "wb": "red", "nb": "green", "sb": "green"}
        elif phase_idx == 4:
            return {"eb": "red", "wb": "red", "nb": "yellow", "sb": "yellow"}
        else:
            return {"eb": "red", "wb": "red", "nb": "red", "sb": "red"}
