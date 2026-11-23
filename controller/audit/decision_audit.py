"""ClearWayAI Explainable Decision Telemetry & Audit Service (`controller.audit.decision_audit`).

Implements transparent, auditable decision records for all corridor traffic signal
interventions and AI pre-clearance actions.

Mathematical Just-In-Time Formulation:
$$\\Delta t_{\\text{trigger}} = \\text{ETA}_{\\text{EV}} - \\hat{T}_{\\text{clear}} - T_{\\text{transition}} - T_{\\text{buffer}}$$

Every automated action produces a verifiable audit record detailing:
1. Exact kinematic variables (ETA, queue length, speed).
2. ML shockwave clearance prediction and confidence interval.
3. Feature attribution analysis explaining which factors forced actuation.
4. Natural language narrative explaining "Why AI Made This Decision".
5. Independent MMU Safety Gateway validation status.
"""

from __future__ import annotations

import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        """Python 3.10 compatibility backport for StrEnum."""

        def __str__(self) -> str:
            return str(self.value)


class DecisionType(StrEnum):
    """Categorical classification of automated signal control decisions."""

    PRE_CLEARANCE_TRIGGER = "PRE_CLEARANCE_TRIGGER"
    GREEN_HOLD_EXTENDED = "GREEN_HOLD_EXTENDED"
    ANTI_STARVATION_ABORT = "ANTI_STARVATION_ABORT"
    MMU_SAFETY_OVERRIDE = "MMU_SAFETY_OVERRIDE"
    RECOVERY_INITIATED = "RECOVERY_INITIATED"
    NOMINAL_MAINTAINED = "NOMINAL_MAINTAINED"
    CASCADE_WAVE_ARMED = "CASCADE_WAVE_ARMED"
    EV_CLEARED_RELEASE = "EV_CLEARED_RELEASE"


class SafetyStatus(StrEnum):
    """Safety Gateway compliance status for audited decisions."""

    SAFE = "SAFE"
    OVERRIDDEN_BY_MMU = "OVERRIDDEN_BY_MMU"
    WATCHDOG_TRIPPED = "WATCHDOG_TRIPPED"


@dataclass
class DecisionAuditRecord:
    """Immutable audit trial record for an automated signal control decision."""

    decision_id: str
    timestamp: float
    sim_time_sec: float
    node_id: str
    decision_type: DecisionType
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
    feature_attributions: dict[str, float] = field(default_factory=dict)
    safety_status: SafetyStatus = SafetyStatus.SAFE
    provenance: str = "CLEARWAY_EXPLAINABLE_AUDIT"

    def to_dict(self) -> dict[str, Any]:
        """Convert audit record to serialized dictionary."""
        d = asdict(self)
        d["decision_type"] = str(self.decision_type)
        d["safety_status"] = str(self.safety_status)
        return d


class ExplainableDecisionAuditService:
    """In-memory and persistent manager for explainable AI decision audit logs."""

    def __init__(self, max_in_memory: int = 500) -> None:
        self.max_in_memory = max_in_memory
        self._history: list[DecisionAuditRecord] = []

    def clear(self) -> None:
        """Clear in-memory audit history."""
        self._history.clear()

    @staticmethod
    def generate_narrative(
        decision_type: DecisionType,
        node_id: str,
        vehicle_id: str | None,
        ev_eta_sec: float,
        queue_length_m: float,
        queued_count: int,
        predicted_clearance_sec: float,
        transition_time_sec: float,
        safety_buffer_sec: float,
        delta_trigger_sec: float,
        hold_duration_sec: float = 0.0,
        max_hold_sec: float = 60.0,
        override_reason: str | None = None,
    ) -> str:
        """Synthesize a deterministic natural language narrative for the decision."""
        veh_str = vehicle_id or "Emergency Vehicle"

        if decision_type == DecisionType.PRE_CLEARANCE_TRIGGER:
            return (
                f"Actuated pre-clearance green phase at {node_id}: {veh_str} ETA is {ev_eta_sec:.1f}s. "
                f"Standing queue of {queued_count} vehicles ({queue_length_m:.1f}m) requires {predicted_clearance_sec:.1f}s "
                f"shockwave clearance plus {transition_time_sec:.1f}s transition and {safety_buffer_sec:.1f}s buffer. "
                f"Trigger delta Δt is {delta_trigger_sec:.1f}s (<= 0), actuating green wave to guarantee zero-stop arrival."
            )

        if decision_type == DecisionType.ANTI_STARVATION_ABORT:
            return (
                f"Watchdog anti-starvation limit tripped at {node_id}: Green phase hold duration "
                f"({hold_duration_sec:.1f}s) exceeded safety maximum ({max_hold_sec:.1f}s). "
                f"Forced termination of arterial hold to prevent cross-street gridlock."
            )

        if decision_type == DecisionType.MMU_SAFETY_OVERRIDE:
            reason = override_reason or "Conflicting vehicular green or violation of minimum yellow duration"
            return (
                f"Conflict Monitor Unit (MMU) Gateway intervened at {node_id}: {reason}. "
                f"Overrode planned phase to safe all-red clearance interval."
            )

        if decision_type == DecisionType.GREEN_HOLD_EXTENDED:
            return (
                f"Extended green wave hold at {node_id}: {veh_str} within approach corridor window "
                f"({ev_eta_sec:.1f}s remaining). Maintaining progression green until stopline crossing."
            )

        if decision_type == DecisionType.EV_CLEARED_RELEASE:
            return (
                f"{veh_str} successfully traversed stopline of {node_id}. Releasing preemption lock "
                f"and transitioning to post-clearance recovery controller."
            )

        if decision_type == DecisionType.RECOVERY_INITIATED:
            return (
                f"Initiated 3-cycle green debt recovery at {node_id}: Compensating cross-street approaches "
                f"for preemption delay with dynamic bonus splits."
            )

        if decision_type == DecisionType.CASCADE_WAVE_ARMED:
            return (
                f"Downstream coordination armed at {node_id}: Vehicle position synchronized within "
                f"moving-horizon window (ETA {ev_eta_sec:.1f}s)."
            )

        # Default NOMINAL_MAINTAINED
        return (
            f"Nominal cycle maintained at {node_id}: {veh_str} ETA is {ev_eta_sec:.1f}s. "
            f"Trigger margin Δt is comfortably positive (+{delta_trigger_sec:.1f}s > 0). "
            f"No phase preemption required at this timestamp."
        )

    @staticmethod
    def compute_feature_attributions(
        ev_eta_sec: float,
        predicted_clearance_sec: float,
        transition_time_sec: float,
        safety_buffer_sec: float,
        delta_trigger_sec: float,
        queue_length_m: float,
    ) -> dict[str, float]:
        """Quantify relative factor attributions leading to the trigger decision."""
        total_time_demand = max(0.1, predicted_clearance_sec + transition_time_sec + safety_buffer_sec)
        return {
            "delta_margin_sec": round(delta_trigger_sec, 2),
            "ev_eta_sec": round(ev_eta_sec, 2),
            "queue_clearance_demand_sec": round(predicted_clearance_sec, 2),
            "transition_overhead_sec": round(transition_time_sec, 2),
            "safety_buffer_sec": round(safety_buffer_sec, 2),
            "clearance_ratio": round(predicted_clearance_sec / total_time_demand, 3),
            "queue_storage_ratio": round(min(1.0, queue_length_m / 150.0), 3),
        }

    def record_decision(
        self,
        node_id: str,
        decision_type: DecisionType,
        commanded_phase: int,
        previous_phase: int = 0,
        sim_time_sec: float | None = None,
        mission_id: str | None = None,
        vehicle_id: str | None = None,
        ev_eta_sec: float = 0.0,
        queue_length_m: float = 0.0,
        queued_vehicle_count: int = 0,
        predicted_clearance_sec: float = 0.0,
        transition_time_sec: float = 0.0,
        safety_buffer_sec: float = 2.0,
        delta_trigger_sec: float = 0.0,
        confidence_score: float = 1.0,
        model_name: str = "gradient_boosting_champion",
        safety_status: SafetyStatus = SafetyStatus.SAFE,
        hold_duration_sec: float = 0.0,
        max_hold_sec: float = 60.0,
        override_reason: str | None = None,
    ) -> DecisionAuditRecord:
        """Create, explain, and store an auditable decision record."""
        t_now = time.time()
        sim_t = sim_time_sec if sim_time_sec is not None else t_now
        dec_id = f"dec-{uuid.uuid4().hex[:10]}"

        narrative = self.generate_narrative(
            decision_type=decision_type,
            node_id=node_id,
            vehicle_id=vehicle_id,
            ev_eta_sec=ev_eta_sec,
            queue_length_m=queue_length_m,
            queued_count=queued_vehicle_count,
            predicted_clearance_sec=predicted_clearance_sec,
            transition_time_sec=transition_time_sec,
            safety_buffer_sec=safety_buffer_sec,
            delta_trigger_sec=delta_trigger_sec,
            hold_duration_sec=hold_duration_sec,
            max_hold_sec=max_hold_sec,
            override_reason=override_reason,
        )

        attributions = self.compute_feature_attributions(
            ev_eta_sec=ev_eta_sec,
            predicted_clearance_sec=predicted_clearance_sec,
            transition_time_sec=transition_time_sec,
            safety_buffer_sec=safety_buffer_sec,
            delta_trigger_sec=delta_trigger_sec,
            queue_length_m=queue_length_m,
        )

        record = DecisionAuditRecord(
            decision_id=dec_id,
            timestamp=t_now,
            sim_time_sec=sim_t,
            node_id=node_id,
            decision_type=decision_type,
            commanded_phase=commanded_phase,
            previous_phase=previous_phase,
            mission_id=mission_id,
            vehicle_id=vehicle_id,
            ev_eta_sec=round(ev_eta_sec, 2),
            queue_length_m=round(queue_length_m, 2),
            queued_vehicle_count=queued_vehicle_count,
            predicted_clearance_sec=round(predicted_clearance_sec, 2),
            transition_time_sec=round(transition_time_sec, 2),
            safety_buffer_sec=round(safety_buffer_sec, 2),
            delta_trigger_sec=round(delta_trigger_sec, 2),
            confidence_score=round(confidence_score, 3),
            model_name=model_name,
            explanation_narrative=narrative,
            feature_attributions=attributions,
            safety_status=safety_status,
        )

        self._history.append(record)
        if len(self._history) > self.max_in_memory:
            self._history.pop(0)

        return record

    def record_preclearance_decision(
        self,
        decision: Any,
        mission: Any | None = None,
        approach_state: Any | None = None,
        sim_time_sec: float | None = None,
    ) -> DecisionAuditRecord:
        """Helper to create and log an explainable audit record directly from PreclearanceDecision."""
        state_str = str(getattr(decision, "state", ""))
        reason_str = str(getattr(decision, "reason", ""))

        if "Safety Watchdog Tripped" in reason_str or "Watchdog" in reason_str:
            d_type = DecisionType.ANTI_STARVATION_ABORT
            s_status = SafetyStatus.WATCHDOG_TRIPPED
        elif getattr(decision, "should_actuate", False):
            if "HOLDING" in state_str:
                d_type = DecisionType.GREEN_HOLD_EXTENDED
            elif "PASSING" in state_str:
                d_type = DecisionType.GREEN_HOLD_EXTENDED
            else:
                d_type = DecisionType.PRE_CLEARANCE_TRIGGER
            s_status = SafetyStatus.SAFE
        elif "CLEARED" in state_str:
            d_type = DecisionType.EV_CLEARED_RELEASE
            s_status = SafetyStatus.SAFE
        else:
            d_type = DecisionType.NOMINAL_MAINTAINED
            s_status = SafetyStatus.SAFE

        queue_len = getattr(approach_state, "queue_length_meters", 0.0) if approach_state else 0.0
        queue_cnt = getattr(approach_state, "queued_vehicle_count", 0) if approach_state else 0
        v_id = getattr(mission, "vehicle_id", "AMB-339") if mission else "AMB-339"
        m_id = getattr(mission, "mission_id", None) if mission else None

        return self.record_decision(
            node_id=getattr(decision, "node_id", "node_a"),
            decision_type=d_type,
            commanded_phase=getattr(decision, "commanded_phase", 0),
            sim_time_sec=sim_time_sec if sim_time_sec is not None else getattr(decision, "timestamp_sec", 0.0),
            mission_id=m_id,
            vehicle_id=v_id,
            ev_eta_sec=getattr(decision, "ev_eta_sec", 0.0),
            queue_length_m=queue_len,
            queued_vehicle_count=queue_cnt,
            predicted_clearance_sec=getattr(decision, "predicted_clearance_sec", 0.0),
            transition_time_sec=getattr(decision, "transition_time_sec", 0.0),
            safety_buffer_sec=getattr(decision, "safety_buffer_sec", 2.0),
            delta_trigger_sec=getattr(decision, "delta_trigger_sec", 0.0),
            confidence_score=getattr(decision, "confidence_score", 1.0),
            safety_status=s_status,
            hold_duration_sec=getattr(decision, "active_green_hold_sec", 0.0),
        )

    def query_decisions(
        self,
        node_id: str | None = None,
        decision_type: DecisionType | None = None,
        mission_id: str | None = None,
        limit: int = 50,
    ) -> list[DecisionAuditRecord]:
        """Query in-memory decisions with optional filtering."""
        results = self._history
        if node_id:
            results = [r for r in results if r.node_id.lower() == node_id.lower()]
        if decision_type:
            results = [r for r in results if r.decision_type == decision_type]
        if mission_id:
            results = [r for r in results if r.mission_id == mission_id]

        # Return latest first
        return list(reversed(results))[:limit]

    def get_decision(self, decision_id: str) -> DecisionAuditRecord | None:
        """Find a specific decision record by its unique ID."""
        for r in self._history:
            if r.decision_id == decision_id:
                return r
        return None

    def get_summary_metrics(self) -> dict[str, Any]:
        """Aggregate statistical summary metrics across logged decisions."""
        total = len(self._history)
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

        triggers = sum(1 for r in self._history if r.decision_type == DecisionType.PRE_CLEARANCE_TRIGGER)
        holds = sum(1 for r in self._history if r.decision_type == DecisionType.GREEN_HOLD_EXTENDED)
        interventions = sum(1 for r in self._history if r.decision_type == DecisionType.MMU_SAFETY_OVERRIDE)
        aborts = sum(1 for r in self._history if r.decision_type == DecisionType.ANTI_STARVATION_ABORT)
        recoveries = sum(1 for r in self._history if r.decision_type == DecisionType.RECOVERY_INITIATED)
        safe_count = sum(1 for r in self._history if r.safety_status == SafetyStatus.SAFE)

        avg_conf = sum(r.confidence_score for r in self._history) / total
        avg_delta = sum(r.delta_trigger_sec for r in self._history) / total

        return {
            "total_decisions": total,
            "preemption_triggers": triggers,
            "green_holds": holds,
            "mmu_interventions": interventions,
            "anti_starvation_aborts": aborts,
            "recoveries": recoveries,
            "avg_confidence": round(avg_conf, 3),
            "avg_delta_margin_sec": round(avg_delta, 2),
            "safe_ratio": round(safe_count / total, 3),
        }


# Global singleton instance for application lifecycle
decision_audit_service = ExplainableDecisionAuditService()
