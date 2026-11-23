"""
ClearWayAI - Telemetry Snapshot Exporter & Deserializer
Serializes simulation telemetry snapshots into line-delimited JSON (JSONL) files
for deterministic replay, WebSocket streaming, and historical audit analysis.
"""

import json
from pathlib import Path
from typing import Any

from apps.api.src.schemas import TelemetrySnapshotSchema


class SnapshotExporter:
    """Exports and imports simulation snapshots to/from JSONL files."""

    @staticmethod
    def export_jsonl(
        snapshots: list[TelemetrySnapshotSchema],
        output_path: Path | str,
    ) -> Path:
        """Serializes a sequence of TelemetrySnapshotSchema into JSONL."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            for snap in snapshots:
                # Use pydantic model_dump_json for high performance serialization
                line = snap.model_dump_json()
                f.write(line + "\n")

        print(f"✅ Exported {len(snapshots)} snapshots to {path}")
        return path

    @staticmethod
    def load_jsonl(
        file_path: Path | str,
    ) -> list[TelemetrySnapshotSchema]:
        """Loads and parses JSONL file back into TelemetrySnapshotSchema instances."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Snapshot log not found: {path}")

        snapshots = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str:
                    data = json.loads(line_str)
                    snap = TelemetrySnapshotSchema.model_validate(data)
                    snapshots.append(snap)

        return snapshots

    @staticmethod
    def compute_run_summary(
        snapshots: list[TelemetrySnapshotSchema],
    ) -> dict[str, Any]:
        """Computes summary statistics and KPIs across a recorded session."""
        if not snapshots:
            return {
                "total_snapshots": 0,
                "duration_seconds": 0.0,
                "peak_vehicle_count": 0,
                "avg_speed_kmh": 0.0,
                "emergency_mission_detected": False,
            }

        start_time = snapshots[0].sim_time_sec
        end_time = snapshots[-1].sim_time_sec
        duration = end_time - start_time

        veh_counts = [len(s.vehicles) for s in snapshots]
        peak_veh = max(veh_counts) if veh_counts else 0

        speeds = [
            s.analytics.avg_speed_kmh
            for s in snapshots
            if s.analytics is not None and s.analytics.avg_speed_kmh > 0
        ]
        avg_speed = sum(speeds) / len(speeds) if speeds else 0.0

        has_mission = any(s.active_mission is not None for s in snapshots)

        return {
            "total_snapshots": len(snapshots),
            "start_time_sec": start_time,
            "end_time_sec": end_time,
            "duration_seconds": round(duration, 2),
            "peak_vehicle_count": peak_veh,
            "avg_speed_kmh": round(avg_speed, 1),
            "emergency_mission_detected": has_mission,
        }
