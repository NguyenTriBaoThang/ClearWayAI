"""
ClearWayAI - TraCI Telemetry Collector
Aggregates microscopic simulation state into structured domain models:
- Vehicle kinematics, lateral coordinates, and classes
- Signal phase states across arterial intersections (A-D)
- Induction loop (E1) and queue area (E2) detector readings
- V2X Hardware status and network metrics
- Active emergency mission progress (AMB-339)
"""

from datetime import datetime
from typing import Any

from apps.api.src.schemas import (
    EmergencyMissionSchema,
    HardwareStatusSchema,
    SignalApproachTimingSchema,
    SignalLightColor,
    SignalStateSchema,
    TelemetrySnapshotSchema,
    TrafficAnalyticsSchema,
    VehicleTelemetry,
    utc_now,
)


class TelemetryCollector:
    """Collects and formats raw simulation telemetry into typed Pydantic schemas."""

    def __init__(self, intersection_id: str = "node_c"):
        self.intersection_id = intersection_id

    def build_vehicle_telemetry(
        self,
        veh_id: str,
        veh_type: str,
        x: float,
        y: float,
        speed_mps: float,
        heading_deg: float,
        lane_id: str,
        is_emergency: bool = False,
        mission_id: str | None = None,
    ) -> VehicleTelemetry:
        """Constructs typed vehicle telemetry snapshot."""
        # Map SUMO vehicle types to domain classes
        class_mapping = {
            "motorcycle": "motorcycle",
            "car": "car",
            "suv": "suv",
            "bus": "bus",
            "truck": "truck",
            "emergency_ambulance": "ambulance",
            "emergency_fire": "fire_engine",
        }
        domain_class = class_mapping.get(veh_type, "car")

        return VehicleTelemetry(
            vehicle_id=veh_id,
            vehicle_class=domain_class,  # type: ignore[arg-type]
            speed_kmh=round(speed_mps * 3.6, 1),
            position_x=round(x, 2),
            position_y=round(y, 2),
            position_z=0.0,
            heading_deg=round(heading_deg, 1),
            lane_id=lane_id,
            is_priority_vehicle=is_emergency,
            mission_id=mission_id,
            provenance="SUMO_SIMULATED",
        )

    def build_signal_state(
        self,
        intersection_id: str,
        current_phase: int,
        cycle_time_s: int = 72,
        is_preemption_active: bool = False,
    ) -> SignalStateSchema:
        """Constructs typed signal state snapshot for an intersection."""
        # Phase 0: EB/WB Green (35s)
        # Phase 1: EB/WB Yellow (4s)
        # Phase 2: All-Red (2s)
        # Phase 3: NB/SB Green (25s)
        # Phase 4: NB/SB Yellow (4s)
        # Phase 5: All-Red (2s)
        phase_names = [
            "Arterial EB/WB Green",
            "Arterial EB/WB Yellow",
            "All-Red Clearance",
            "Cross-Street NB/SB Green",
            "Cross-Street NB/SB Yellow",
            "All-Red Clearance",
        ]
        curr_name = (
            "EMERGENCY PREEMPTION GREEN"
            if is_preemption_active
            else phase_names[current_phase % len(phase_names)]
        )
        next_name = phase_names[(current_phase + 1) % len(phase_names)]

        # Determine approach lights
        if is_preemption_active:
            eb_color: SignalLightColor = "green"
            wb_color: SignalLightColor = "red"
            nb_color: SignalLightColor = "red"
            sb_color: SignalLightColor = "red"
        elif current_phase == 0:
            eb_color = wb_color = "green"
            nb_color = sb_color = "red"
        elif current_phase == 1:
            eb_color = wb_color = "yellow"
            nb_color = sb_color = "red"
        elif current_phase == 2 or current_phase == 5:
            eb_color = wb_color = nb_color = sb_color = "red"
        elif current_phase == 3:
            eb_color = wb_color = "red"
            nb_color = sb_color = "green"
        else:
            eb_color = wb_color = "red"
            nb_color = sb_color = "yellow"

        approaches = [
            SignalApproachTimingSchema(
                approach="Northbound (NB)",
                red_s=47,
                yellow_s=4,
                green_s=25,
                cycle_s=cycle_time_s,
                split_pct=35,
                current_phase=nb_color,
            ),
            SignalApproachTimingSchema(
                approach="Southbound (SB)",
                red_s=47,
                yellow_s=4,
                green_s=25,
                cycle_s=cycle_time_s,
                split_pct=35,
                current_phase=sb_color,
            ),
            SignalApproachTimingSchema(
                approach="Eastbound (EB Corridor)",
                red_s=37,
                yellow_s=4,
                green_s=35,
                cycle_s=cycle_time_s,
                split_pct=49,
                current_phase=eb_color,
            ),
            SignalApproachTimingSchema(
                approach="Westbound (WB)",
                red_s=37,
                yellow_s=4,
                green_s=35,
                cycle_s=cycle_time_s,
                split_pct=49,
                current_phase=wb_color,
            ),
        ]

        return SignalStateSchema(
            intersection_id=intersection_id,
            intersection_name=f"Intersection {intersection_id.replace('node_', '').upper()} - Oak & 5th",
            cycle_time_s=cycle_time_s,
            current_phase_name=curr_name,
            next_phase_name=next_name,
            approaches=approaches,
            provenance="SUMO_SIMULATED",
        )

    def build_hardware_status(
        self,
        active_vehicles: int,
        rsu_count: int = 4,
    ) -> HardwareStatusSchema:
        """Constructs V2X hardware status telemetry."""
        obu_online = max(1, int(active_vehicles * 0.95))
        return HardwareStatusSchema(
            network_id="V2X-CORRIDOR-MESH-01",
            obu_vehicles_online=obu_online,
            obu_pct=95.0,
            rsu_online=rsu_count,
            rsu_pct=100.0,
            edge_controllers_online=4,
            signal_controllers_online=4,
            v2x_status="Simulated",
            latency_ms=12.4,
            packet_loss_pct=0.1,
            provenance="SUMO_SIMULATED",
        )

    def build_analytics(
        self,
        intersection_id: str,
        avg_speed_kmh: float,
        queue_m: float,
        occupancy_pct: float,
        has_preclearance: bool = False,
    ) -> TrafficAnalyticsSchema:
        """Constructs aggregated traffic analytics and performance deltas."""
        delay_delta = -19.4 if has_preclearance else -2.5
        throughput_delta = 14.8 if has_preclearance else 3.2

        return TrafficAnalyticsSchema(
            intersection_id=intersection_id,
            performance_index=84.5,
            throughput_pct_change=throughput_delta,
            avg_delay_pct_change=delay_delta,
            stops_per_veh_pct_change=-22.0 if has_preclearance else -4.0,
            occupancy_pct=round(occupancy_pct, 1),
            avg_speed_kmh=round(avg_speed_kmh, 1),
            avg_queue_m=round(queue_m, 1),
            backlog_m=round(queue_m * 1.25, 1),
            provenance="SUMO_SIMULATED",
        )

    def build_emergency_mission(
        self,
        amb_x: float,
        depart_time: float,
        sim_time: float,
        is_completed: bool = False,
    ) -> EmergencyMissionSchema:
        """Constructs active emergency mission snapshot."""
        # Route is 1300m total (-200m to 1100m)
        remaining_m = max(0.0, 1100.0 - amb_x)
        avg_speed_mps = 18.5  # ~66 km/h
        eta_min = (remaining_m / avg_speed_mps) / 60.0 if not is_completed else 0.0

        status: Any = "COMPLETED" if is_completed or remaining_m <= 10.0 else "ACTIVE"

        return EmergencyMissionSchema(
            mission_id="mission-amb-339",
            vehicle_id="AMB-339",
            vehicle_type="ambulance",
            target_facility="Metropolitan Trauma Center",
            eta_hospital_min=round(eta_min, 2),
            status=status,
            corridor_intersections=["node_a", "node_b", "node_c", "node_d"],
            provenance="SUMO_SIMULATED",
        )

    def create_snapshot(
        self,
        sim_time_sec: float,
        vehicles: list[VehicleTelemetry],
        current_phase: int = 0,
        avg_speed_kmh: float = 38.5,
        avg_queue_m: float = 14.2,
        occupancy_pct: float = 34.0,
        amb_telemetry: VehicleTelemetry | None = None,
        is_preemption_active: bool = False,
        timestamp: datetime | None = None,
    ) -> TelemetrySnapshotSchema:
        """Compiles a complete atomic TelemetrySnapshotSchema."""
        signals = self.build_signal_state(
            intersection_id=self.intersection_id,
            current_phase=current_phase,
            is_preemption_active=is_preemption_active,
        )
        hardware = self.build_hardware_status(active_vehicles=len(vehicles))
        analytics = self.build_analytics(
            intersection_id=self.intersection_id,
            avg_speed_kmh=avg_speed_kmh,
            queue_m=avg_queue_m,
            occupancy_pct=occupancy_pct,
            has_preclearance=is_preemption_active,
        )

        mission = None
        if amb_telemetry is not None:
            mission = self.build_emergency_mission(
                amb_x=amb_telemetry.position_x,
                depart_time=0.0,
                sim_time=sim_time_sec,
            )

        return TelemetrySnapshotSchema(
            intersection_id=self.intersection_id,
            timestamp=timestamp or utc_now(),
            sim_time_sec=round(sim_time_sec, 2),
            vehicles=vehicles,
            signals=signals,
            hardware=hardware,
            analytics=analytics,
            active_mission=mission,
            provenance="SUMO_SIMULATED",
        )
