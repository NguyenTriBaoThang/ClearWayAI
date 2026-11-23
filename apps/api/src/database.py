"""SQLite / Relational Database Layer for ClearWayAI API (`apps.api.src.database`).

Provides persistence for:
1. Simulation runs & episodes (`simulations`).
2. Priority emergency missions (`missions`).
3. Signal state transitions & safety gateway interventions (`signal_logs`).
4. AI queue clearance predictions & model metadata (`clearance_predictions`).
"""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class SimulationRecord:
    """Database record for a simulation episode."""

    simulation_id: str
    name: str
    scenario_id: str
    status: str
    started_at: str
    stopped_at: str | None = None
    total_steps: int = 0
    emergency_events: int = 0
    metadata_json: str = "{}"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["metadata"] = json.loads(self.metadata_json) if self.metadata_json else {}
        return d


@dataclass
class MissionRecord:
    """Database record for an emergency vehicle priority mission."""

    mission_id: str
    vehicle_id: str
    vehicle_type: str
    status: str
    origin: str
    destination: str
    dispatched_at: str
    arrived_at: str | None = None
    current_position_m: float = -200.0
    current_speed_mps: float = 0.0
    progress_ratio: float = 0.0
    target_speed_mps: float = 18.5
    priority_level: int = 1
    route_nodes_json: str = '["node_a", "node_b", "node_c", "node_d"]'

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["route_nodes"] = json.loads(self.route_nodes_json) if self.route_nodes_json else []
        d["current_speed_kmh"] = round(self.current_speed_mps * 3.6, 1)
        return d


@dataclass
class SignalLogRecord:
    """Database record for a traffic signal phase event or safety intervention."""

    id: int | None
    timestamp: float
    node_id: str
    phase: int
    operational_mode: str
    is_safe: bool
    intervention_reason: str | None
    details_json: str = "{}"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["details"] = json.loads(self.details_json) if self.details_json else {}
        return d


@dataclass
class ClearancePredictionRecord:
    """Database record for an AI clearance inference event."""

    id: int | None
    timestamp: float
    node_id: str
    predicted_clearance_sec: float
    confidence_score: float
    model_name: str
    fallback_used: bool
    fallback_tier: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DatabaseManager:
    """Thread-safe SQLite database manager for ClearWayAI backend."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._lock = threading.Lock()
        if self.db_path != ":memory:":
            p = Path(self.db_path)
            p.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock, self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS simulations (
                    simulation_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    scenario_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    stopped_at TEXT,
                    total_steps INTEGER DEFAULT 0,
                    emergency_events INTEGER DEFAULT 0,
                    metadata_json TEXT DEFAULT '{}'
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS missions (
                    mission_id TEXT PRIMARY KEY,
                    vehicle_id TEXT NOT NULL,
                    vehicle_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    origin TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    dispatched_at TEXT NOT NULL,
                    arrived_at TEXT,
                    current_position_m REAL DEFAULT -200.0,
                    current_speed_mps REAL DEFAULT 0.0,
                    progress_ratio REAL DEFAULT 0.0,
                    target_speed_mps REAL DEFAULT 18.5,
                    priority_level INTEGER DEFAULT 1,
                    route_nodes_json TEXT DEFAULT '["node_a", "node_b", "node_c", "node_d"]'
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signal_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    node_id TEXT NOT NULL,
                    phase INTEGER NOT NULL,
                    operational_mode TEXT NOT NULL,
                    is_safe INTEGER NOT NULL,
                    intervention_reason TEXT,
                    details_json TEXT DEFAULT '{}'
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clearance_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    node_id TEXT NOT NULL,
                    predicted_clearance_sec REAL NOT NULL,
                    confidence_score REAL NOT NULL,
                    model_name TEXT NOT NULL,
                    fallback_used INTEGER NOT NULL,
                    fallback_tier TEXT
                );
            """)
            conn.commit()

    # --- Simulation Operations ---
    def create_simulation(self, record: SimulationRecord) -> SimulationRecord:
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO simulations (simulation_id, name, scenario_id, status, started_at, stopped_at, total_steps, emergency_events, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.simulation_id,
                    record.name,
                    record.scenario_id,
                    record.status,
                    record.started_at,
                    record.stopped_at,
                    record.total_steps,
                    record.emergency_events,
                    record.metadata_json,
                ),
            )
            conn.commit()
        return record

    def get_simulation(self, simulation_id: str) -> SimulationRecord | None:
        with self._lock, self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM simulations WHERE simulation_id = ?",
                (simulation_id,),
            ).fetchone()
            if not row:
                return None
            return SimulationRecord(
                simulation_id=row["simulation_id"],
                name=row["name"],
                scenario_id=row["scenario_id"],
                status=row["status"],
                started_at=row["started_at"],
                stopped_at=row["stopped_at"],
                total_steps=row["total_steps"],
                emergency_events=row["emergency_events"],
                metadata_json=row["metadata_json"],
            )

    def list_simulations(self, limit: int = 50) -> list[SimulationRecord]:
        with self._lock, self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM simulations ORDER BY started_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [
                SimulationRecord(
                    simulation_id=row["simulation_id"],
                    name=row["name"],
                    scenario_id=row["scenario_id"],
                    status=row["status"],
                    started_at=row["started_at"],
                    stopped_at=row["stopped_at"],
                    total_steps=row["total_steps"],
                    emergency_events=row["emergency_events"],
                    metadata_json=row["metadata_json"],
                )
                for row in rows
            ]

    def update_simulation_step(
        self,
        simulation_id: str,
        total_steps: int,
        emergency_events: int | None = None,
    ) -> None:
        with self._lock, self._get_connection() as conn:
            if emergency_events is not None:
                conn.execute(
                    "UPDATE simulations SET total_steps = ?, emergency_events = ? WHERE simulation_id = ?",
                    (total_steps, emergency_events, simulation_id),
                )
            else:
                conn.execute(
                    "UPDATE simulations SET total_steps = ? WHERE simulation_id = ?",
                    (total_steps, simulation_id),
                )
            conn.commit()

    def stop_simulation(self, simulation_id: str, stopped_at: str) -> None:
        with self._lock, self._get_connection() as conn:
            conn.execute(
                "UPDATE simulations SET status = 'STOPPED', stopped_at = ? WHERE simulation_id = ?",
                (stopped_at, simulation_id),
            )
            conn.commit()

    # --- Mission Operations ---
    def save_mission(self, record: MissionRecord) -> MissionRecord:
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO missions (
                    mission_id, vehicle_id, vehicle_type, status, origin, destination,
                    dispatched_at, arrived_at, current_position_m, current_speed_mps,
                    progress_ratio, target_speed_mps, priority_level, route_nodes_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.mission_id,
                    record.vehicle_id,
                    record.vehicle_type,
                    record.status,
                    record.origin,
                    record.destination,
                    record.dispatched_at,
                    record.arrived_at,
                    record.current_position_m,
                    record.current_speed_mps,
                    record.progress_ratio,
                    record.target_speed_mps,
                    record.priority_level,
                    record.route_nodes_json,
                ),
            )
            conn.commit()
        return record

    def get_mission(self, mission_id: str) -> MissionRecord | None:
        with self._lock, self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM missions WHERE mission_id = ?",
                (mission_id,),
            ).fetchone()
            if not row:
                return None
            return MissionRecord(
                mission_id=row["mission_id"],
                vehicle_id=row["vehicle_id"],
                vehicle_type=row["vehicle_type"],
                status=row["status"],
                origin=row["origin"],
                destination=row["destination"],
                dispatched_at=row["dispatched_at"],
                arrived_at=row["arrived_at"],
                current_position_m=row["current_position_m"],
                current_speed_mps=row["current_speed_mps"],
                progress_ratio=row["progress_ratio"],
                target_speed_mps=row["target_speed_mps"],
                priority_level=row["priority_level"],
                route_nodes_json=row["route_nodes_json"],
            )

    def list_missions(self, limit: int = 50) -> list[MissionRecord]:
        with self._lock, self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM missions ORDER BY dispatched_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [
                MissionRecord(
                    mission_id=row["mission_id"],
                    vehicle_id=row["vehicle_id"],
                    vehicle_type=row["vehicle_type"],
                    status=row["status"],
                    origin=row["origin"],
                    destination=row["destination"],
                    dispatched_at=row["dispatched_at"],
                    arrived_at=row["arrived_at"],
                    current_position_m=row["current_position_m"],
                    current_speed_mps=row["current_speed_mps"],
                    progress_ratio=row["progress_ratio"],
                    target_speed_mps=row["target_speed_mps"],
                    priority_level=row["priority_level"],
                    route_nodes_json=row["route_nodes_json"],
                )
                for row in rows
            ]

    # --- Signal & Clearance Logging Operations ---
    def log_signal_event(self, record: SignalLogRecord) -> None:
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO signal_logs (timestamp, node_id, phase, operational_mode, is_safe, intervention_reason, details_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.timestamp,
                    record.node_id,
                    record.phase,
                    record.operational_mode,
                    1 if record.is_safe else 0,
                    record.intervention_reason,
                    record.details_json,
                ),
            )
            conn.commit()

    def log_clearance_prediction(self, record: ClearancePredictionRecord) -> None:
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO clearance_predictions (
                    timestamp, node_id, predicted_clearance_sec, confidence_score, model_name, fallback_used, fallback_tier
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.timestamp,
                    record.node_id,
                    record.predicted_clearance_sec,
                    record.confidence_score,
                    record.model_name,
                    1 if record.fallback_used else 0,
                    record.fallback_tier,
                ),
            )
            conn.commit()


# Default global database instance
db = DatabaseManager()
