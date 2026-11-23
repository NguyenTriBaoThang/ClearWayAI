"""
ClearWayAI - Telemetry Replay Controller
Provides frame-accurate, variable-speed playback of recorded simulation sessions.
Allows seek, pause, play, step forward/backward, and continuous time synchronization.
"""

from pathlib import Path

from apps.api.src.schemas import TelemetrySnapshotSchema
from simulation.traci.snapshot_exporter import SnapshotExporter


class ReplayController:
    """Controls playback of recorded simulation snapshot logs."""

    def __init__(self, log_path: Path | str | None = None):
        self.snapshots: list[TelemetrySnapshotSchema] = []
        self.current_index: int = 0
        self.current_time: float = 0.0
        self.is_playing: bool = False
        self.playback_speed: float = 1.0  # 1.0x, 2.0x, 4.0x

        if log_path is not None:
            self.load_log(log_path)

    def load_log(self, file_path: Path | str) -> int:
        """Loads a recorded JSONL simulation log."""
        self.snapshots = SnapshotExporter.load_jsonl(file_path)
        self.current_index = 0
        self.current_time = self.snapshots[0].sim_time_sec if self.snapshots else 0.0
        self.is_playing = False
        return len(self.snapshots)

    def load_snapshots(self, snapshots: list[TelemetrySnapshotSchema]) -> int:
        """Directly loads a memory buffer of snapshots."""
        self.snapshots = snapshots
        self.current_index = 0
        self.current_time = self.snapshots[0].sim_time_sec if self.snapshots else 0.0
        self.is_playing = False
        return len(self.snapshots)

    def play(self) -> None:
        """Starts replay playback."""
        self.is_playing = True

    def pause(self) -> None:
        """Pauses replay playback."""
        self.is_playing = False

    def toggle(self) -> bool:
        """Toggles between play and pause."""
        self.is_playing = not self.is_playing
        return self.is_playing

    def set_speed(self, speed_multiplier: float) -> None:
        """Sets playback speed multiplier (e.g. 0.5x, 1.0x, 2.0x, 4.0x)."""
        if speed_multiplier > 0.0:
            self.playback_speed = speed_multiplier

    def seek(self, target_time_sec: float) -> TelemetrySnapshotSchema | None:
        """Seeks to the snapshot closest to target_time_sec."""
        if not self.snapshots:
            return None

        # Binary search or scan for closest snapshot
        closest_idx = 0
        min_diff = float("inf")
        for i, s in enumerate(self.snapshots):
            diff = abs(s.sim_time_sec - target_time_sec)
            if diff < min_diff:
                min_diff = diff
                closest_idx = i

        self.current_index = closest_idx
        self.current_time = self.snapshots[closest_idx].sim_time_sec
        return self.snapshots[closest_idx]

    def step(self, dt: float = 0.1) -> TelemetrySnapshotSchema | None:
        """
        Advances replay by dt * playback_speed and returns current snapshot.
        If at end, stops playback.
        """
        if not self.snapshots:
            return None

        if self.is_playing:
            self.current_time += dt * self.playback_speed

            # Advance index to match current_time
            while (
                self.current_index < len(self.snapshots) - 1
                and self.snapshots[self.current_index + 1].sim_time_sec <= self.current_time
            ):
                self.current_index += 1

            if self.current_index >= len(self.snapshots) - 1:
                self.is_playing = False

        return self.snapshots[self.current_index]

    def step_forward(self) -> TelemetrySnapshotSchema | None:
        """Steps forward by one discrete snapshot frame."""
        if not self.snapshots:
            return None
        if self.current_index < len(self.snapshots) - 1:
            self.current_index += 1
            self.current_time = self.snapshots[self.current_index].sim_time_sec
        return self.snapshots[self.current_index]

    def step_backward(self) -> TelemetrySnapshotSchema | None:
        """Steps backward by one discrete snapshot frame."""
        if not self.snapshots:
            return None
        if self.current_index > 0:
            self.current_index -= 1
            self.current_time = self.snapshots[self.current_index].sim_time_sec
        return self.snapshots[self.current_index]

    def get_current_snapshot(self) -> TelemetrySnapshotSchema | None:
        """Returns the current snapshot."""
        if not self.snapshots:
            return None
        return self.snapshots[self.current_index]

    def get_total_duration(self) -> float:
        """Returns total duration of recorded session in seconds."""
        if len(self.snapshots) < 2:
            return 0.0
        return self.snapshots[-1].sim_time_sec - self.snapshots[0].sim_time_sec

    def get_progress_pct(self) -> float:
        """Returns playback progress percentage (0.0 to 100.0)."""
        duration = self.get_total_duration()
        if duration <= 0.0:
            return 100.0 if self.snapshots else 0.0
        start = self.snapshots[0].sim_time_sec
        return min(100.0, max(0.0, ((self.current_time - start) / duration) * 100.0))
