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


@dataclass
class SnapshotRecord:
    """Database record for a serialized telemetry snapshot."""

    id: int | None
    simulation_id: str
    sim_time_sec: float
    timestamp: str
    active_vehicles_count: int
    current_phase: int
    emergency_active: bool
    snapshot_json: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionAuditLogRecord:
    """Database record for an explainable AI signal control decision."""

    decision_id: str
    timestamp: float
    sim_time_sec: float
    node_id: str
    decision_type: str
    commanded_phase: int
    previous_phase: int = 0
    mission_id: str | None = None
    vehicle_id: str | None = None
    ev_eta_sec: float = 0.0
    queue_length_m: float = 0.0
    queued_vehicle_count: int = 0
    predicted_clearance_sec: float = 0.0
    transition_time_sec: float = 0.0
    safety_buffer_sec: float = 2.0
    delta_trigger_sec: float = 0.0
    confidence_score: float = 1.0
    model_name: str = "gradient_boosting_champion"
    explanation_narrative: str = ""
    feature_attributions_json: str = "{}"
    safety_status: str = "SAFE"
    provenance: str = "CLEARWAY_EXPLAINABLE_AUDIT"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["feature_attributions"] = (
            json.loads(self.feature_attributions_json) if self.feature_attributions_json else {}
        )
        return d


class DatabaseManager:
    """Thread-safe SQLite database manager for ClearWayAI backend."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._lock = threading.Lock()
        self._memory_conn: sqlite3.Connection | None = None
        if self.db_path != ":memory:":
            p = Path(self.db_path)
            p.parent.mkdir(parents=True, exist_ok=True)
        else:
            self._memory_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._memory_conn.row_factory = sqlite3.Row
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._memory_conn is not None:
            return self._memory_conn
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

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS simulation_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    simulation_id TEXT NOT NULL,
                    sim_time_sec REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    active_vehicles_count INTEGER DEFAULT 0,
                    current_phase INTEGER DEFAULT 0,
                    emergency_active INTEGER DEFAULT 0,
                    snapshot_json TEXT NOT NULL
                );
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_snapshots_sim_time
                ON simulation_snapshots (simulation_id, sim_time_sec);
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS decision_audit_logs (
                    decision_id TEXT PRIMARY KEY,
                    timestamp REAL NOT NULL,
                    sim_time_sec REAL NOT NULL,
                    node_id TEXT NOT NULL,
                    decision_type TEXT NOT NULL,
                    commanded_phase INTEGER NOT NULL,
                    previous_phase INTEGER DEFAULT 0,
                    mission_id TEXT,
                    vehicle_id TEXT,
                    ev_eta_sec REAL DEFAULT 0.0,
                    queue_length_m REAL DEFAULT 0.0,
                    queued_vehicle_count INTEGER DEFAULT 0,
                    predicted_clearance_sec REAL DEFAULT 0.0,
                    transition_time_sec REAL DEFAULT 0.0,
                    safety_buffer_sec REAL DEFAULT 2.0,
                    delta_trigger_sec REAL DEFAULT 0.0,
                    confidence_score REAL DEFAULT 1.0,
                    model_name TEXT DEFAULT 'gradient_boosting_champion',
                    explanation_narrative TEXT NOT NULL,
                    feature_attributions_json TEXT DEFAULT '{}',
                    safety_status TEXT DEFAULT 'SAFE',
                    provenance TEXT DEFAULT 'CLEARWAY_EXPLAINABLE_AUDIT'
                );
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_audit_node_sim_time
                ON decision_audit_logs (node_id, sim_time_sec);
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

    # --- Snapshot Operations ---
    def save_snapshot(
        self,
        simulation_id: str,
        sim_time_sec: float,
        timestamp: str,
        active_vehicles_count: int,
        current_phase: int,
        emergency_active: bool,
        snapshot_json: str,
    ) -> int:
        with self._lock, self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO simulation_snapshots (
                    simulation_id, sim_time_sec, timestamp, active_vehicles_count,
                    current_phase, emergency_active, snapshot_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    simulation_id,
                    sim_time_sec,
                    timestamp,
                    active_vehicles_count,
                    current_phase,
                    1 if emergency_active else 0,
                    snapshot_json,
                ),
            )
            conn.commit()
            return cursor.lastrowid or 0

    def get_snapshots(
        self,
        simulation_id: str,
        start_time: float | None = None,
        end_time: float | None = None,
        limit: int = 100,
    ) -> list[SnapshotRecord]:
        with self._lock, self._get_connection() as conn:
            query = "SELECT * FROM simulation_snapshots WHERE simulation_id = ?"
            params: list[Any] = [simulation_id]
            if start_time is not None:
                query += " AND sim_time_sec >= ?"
                params.append(start_time)
            if end_time is not None:
                query += " AND sim_time_sec <= ?"
                params.append(end_time)
            query += " ORDER BY sim_time_sec ASC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, tuple(params)).fetchall()
            return [
                SnapshotRecord(
                    id=row["id"],
                    simulation_id=row["simulation_id"],
                    sim_time_sec=row["sim_time_sec"],
                    timestamp=row["timestamp"],
                    active_vehicles_count=row["active_vehicles_count"],
                    current_phase=row["current_phase"],
                    emergency_active=bool(row["emergency_active"]),
                    snapshot_json=row["snapshot_json"],
                )
                for row in rows
            ]

    def count_snapshots(self, simulation_id: str) -> int:
        with self._lock, self._get_connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as count FROM simulation_snapshots WHERE simulation_id = ?",
                (simulation_id,),
            ).fetchone()
            return row["count"] if row else 0

    # --- Explainable Decision Audit Operations ---
    def log_decision_audit(self, record: DecisionAuditLogRecord) -> None:
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO decision_audit_logs (
                    decision_id, timestamp, sim_time_sec, node_id, decision_type, commanded_phase,
                    previous_phase, mission_id, vehicle_id, ev_eta_sec, queue_length_m,
                    queued_vehicle_count, predicted_clearance_sec, transition_time_sec,
                    safety_buffer_sec, delta_trigger_sec, confidence_score, model_name,
                    explanation_narrative, feature_attributions_json, safety_status, provenance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.decision_id,
                    record.timestamp,
                    record.sim_time_sec,
                    record.node_id,
                    record.decision_type,
                    record.commanded_phase,
                    record.previous_phase,
                    record.mission_id,
                    record.vehicle_id,
                    record.ev_eta_sec,
                    record.queue_length_m,
                    record.queued_vehicle_count,
                    record.predicted_clearance_sec,
                    record.transition_time_sec,
                    record.safety_buffer_sec,
                    record.delta_trigger_sec,
                    record.confidence_score,
                    record.model_name,
                    record.explanation_narrative,
                    record.feature_attributions_json,
                    record.safety_status,
                    record.provenance,
                ),
            )
            conn.commit()

    def get_decision_audit(self, decision_id: str) -> DecisionAuditLogRecord | None:
        with self._lock, self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM decision_audit_logs WHERE decision_id = ?",
                (decision_id,),
            ).fetchone()
            if not row:
                return None
            return DecisionAuditLogRecord(
                decision_id=row["decision_id"],
                timestamp=row["timestamp"],
                sim_time_sec=row["sim_time_sec"],
                node_id=row["node_id"],
                decision_type=row["decision_type"],
                commanded_phase=row["commanded_phase"],
                previous_phase=row["previous_phase"],
                mission_id=row["mission_id"],
                vehicle_id=row["vehicle_id"],
                ev_eta_sec=row["ev_eta_sec"],
                queue_length_m=row["queue_length_m"],
                queued_vehicle_count=row["queued_vehicle_count"],
                predicted_clearance_sec=row["predicted_clearance_sec"],
                transition_time_sec=row["transition_time_sec"],
                safety_buffer_sec=row["safety_buffer_sec"],
                delta_trigger_sec=row["delta_trigger_sec"],
                confidence_score=row["confidence_score"],
                model_name=row["model_name"],
                explanation_narrative=row["explanation_narrative"],
                feature_attributions_json=row["feature_attributions_json"],
                safety_status=row["safety_status"],
                provenance=row["provenance"],
            )

    def query_decision_audits(
        self,
        node_id: str | None = None,
        decision_type: str | None = None,
        mission_id: str | None = None,
        limit: int = 50,
    ) -> list[DecisionAuditLogRecord]:
        with self._lock, self._get_connection() as conn:
            query = "SELECT * FROM decision_audit_logs WHERE 1=1"
            params: list[Any] = []
            if node_id and isinstance(node_id, str):
                query += " AND LOWER(node_id) = LOWER(?)"
                params.append(node_id)
            if decision_type and isinstance(decision_type, str):
                query += " AND decision_type = ?"
                params.append(decision_type)
            if mission_id and isinstance(mission_id, str):
                query += " AND mission_id = ?"
                params.append(mission_id)
            query += " ORDER BY sim_time_sec DESC, timestamp DESC LIMIT ?"
            params.append(int(limit) if isinstance(limit, (int, float)) else 50)

            rows = conn.execute(query, tuple(params)).fetchall()
            return [
                DecisionAuditLogRecord(
                    decision_id=row["decision_id"],
                    timestamp=row["timestamp"],
                    sim_time_sec=row["sim_time_sec"],
                    node_id=row["node_id"],
                    decision_type=row["decision_type"],
                    commanded_phase=row["commanded_phase"],
                    previous_phase=row["previous_phase"],
                    mission_id=row["mission_id"],
                    vehicle_id=row["vehicle_id"],
                    ev_eta_sec=row["ev_eta_sec"],
                    queue_length_m=row["queue_length_m"],
                    queued_vehicle_count=row["queued_vehicle_count"],
                    predicted_clearance_sec=row["predicted_clearance_sec"],
                    transition_time_sec=row["transition_time_sec"],
                    safety_buffer_sec=row["safety_buffer_sec"],
                    delta_trigger_sec=row["delta_trigger_sec"],
                    confidence_score=row["confidence_score"],
                    model_name=row["model_name"],
                    explanation_narrative=row["explanation_narrative"],
                    feature_attributions_json=row["feature_attributions_json"],
                    safety_status=row["safety_status"],
                    provenance=row["provenance"],
                )
                for row in rows
            ]

    def get_decision_audit_summary(self) -> dict[str, Any]:
        with self._lock, self._get_connection() as conn:
            row_total = conn.execute("SELECT COUNT(*) as cnt FROM decision_audit_logs").fetchone()
            total = row_total["cnt"] if row_total else 0
            if total == 0:
                return {
                    "total_decisions": 0,
                    "preemption_triggers": 0,
                    "green_holds": 0,
                    "mmu_interventions": 0,
                    "anti_starvation_aborts": 0,
                    "recoveries": 0,
                    "avg_confidence": 1.0,
                    "avg_delta_margin_sec": 0.0,
                    "safe_ratio": 1.0,
                }

            triggers = conn.execute(
                "SELECT COUNT(*) as c FROM decision_audit_logs WHERE decision_type = 'PRE_CLEARANCE_TRIGGER'"
            ).fetchone()["c"]
            holds = conn.execute(
                "SELECT COUNT(*) as c FROM decision_audit_logs WHERE decision_type = 'GREEN_HOLD_EXTENDED'"
            ).fetchone()["c"]
            interventions = conn.execute(
                "SELECT COUNT(*) as c FROM decision_audit_logs WHERE decision_type = 'MMU_SAFETY_OVERRIDE'"
            ).fetchone()["c"]
            aborts = conn.execute(
                "SELECT COUNT(*) as c FROM decision_audit_logs WHERE decision_type = 'ANTI_STARVATION_ABORT'"
            ).fetchone()["c"]
            recoveries = conn.execute(
                "SELECT COUNT(*) as c FROM decision_audit_logs WHERE decision_type = 'RECOVERY_INITIATED'"
            ).fetchone()["c"]
            safe_cnt = conn.execute(
                "SELECT COUNT(*) as c FROM decision_audit_logs WHERE safety_status = 'SAFE'"
            ).fetchone()["c"]
            stats = conn.execute(
                "SELECT AVG(confidence_score) as avg_c, AVG(delta_trigger_sec) as avg_d FROM decision_audit_logs"
            ).fetchone()

            avg_conf = stats["avg_c"] if stats and stats["avg_c"] is not None else 1.0
            avg_delta = stats["avg_d"] if stats and stats["avg_d"] is not None else 0.0

            return {
                "total_decisions": total,
                "preemption_triggers": triggers,
                "green_holds": holds,
                "mmu_interventions": interventions,
                "anti_starvation_aborts": aborts,
                "recoveries": recoveries,
                "avg_confidence": round(avg_conf, 3),
                "avg_delta_margin_sec": round(avg_delta, 2),
                "safe_ratio": round(safe_cnt / total, 3),
            }


# Default global database instance
db = DatabaseManager()
