"""Verification test suite for Task 21: System Requirements Specification, ADRs, and Schemas."""

import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS_DIR = os.path.join(REPO_ROOT, "docs")
ADR_DIR = os.path.join(DOCS_DIR, "adr")
SCHEMAS_DIR = os.path.join(REPO_ROOT, "packages", "shared", "schemas")
API_SRC = os.path.join(REPO_ROOT, "apps", "api", "src")

# Add API_SRC to path for schema imports
if API_SRC not in sys.path:
    sys.path.insert(0, API_SRC)

from schemas import (
    EmergencyMissionSchema,
    HardwareStatusSchema,
    SignalStateSchema,
    SystemStatusResponse,
    TrafficAnalyticsSchema,
)


def test_srs_document_exists_and_complete():
    """Verify SRS.md exists, defines FR-01 through FR-10, NFRs, and 4 operational modes."""
    srs_path = os.path.join(DOCS_DIR, "SRS.md")
    assert os.path.exists(srs_path), f"File {srs_path} must exist!"

    with open(srs_path, encoding="utf-8") as f:
        content = f.read()

    # Functional Requirements
    assert "FR-01" in content
    assert "FR-02" in content
    assert "FR-03" in content
    assert "FR-04" in content
    assert "FR-05" in content
    assert "FR-06" in content
    assert "FR-07" in content
    assert "FR-08" in content
    assert "FR-09" in content
    assert "FR-10" in content

    # Non-Functional Requirements
    assert "NFR-01" in content
    assert "NFR-02" in content
    assert "NFR-03" in content
    assert "NFR-04" in content
    assert "NFR-05" in content

    # 4 Operational Modes
    assert "SIMULATION" in content
    assert "OFFLINE_VIDEO" in content
    assert "SHADOW_ADVISORY" in content
    assert "AUTHORIZED_PILOT" in content


def test_safety_boundaries_document_and_invariants():
    """Verify SAFETY_BOUNDARIES.md defines invariants INV-01 to INV-06 and MMU interlock."""
    safety_path = os.path.join(DOCS_DIR, "SAFETY_BOUNDARIES.md")
    assert os.path.exists(safety_path), f"File {safety_path} must exist!"

    with open(safety_path, encoding="utf-8") as f:
        content = f.read()

    # Invariants
    assert "INV-01" in content  # Mutual exclusion
    assert "INV-02" in content  # Min green >= 10s
    assert "INV-03" in content  # Max green <= 75s
    assert "INV-04" in content  # Yellow >= 3s
    assert "INV-05" in content  # All-red >= 2s
    assert "INV-06" in content  # Comms timeout 500ms
    assert "public_signal_control" in content or "public_signal_control_permitted" in content


def test_adr_records_exist_and_indexed():
    """Verify ADR directory contains README and all 6 architectural decision records."""
    assert os.path.exists(ADR_DIR)
    expected_adrs = [
        "README.md",
        "0001-monorepo-structure.md",
        "0002-data-provenance-and-simulation-mode.md",
        "0003-digital-twin-threejs-webgl.md",
        "0004-independent-safety-interlock.md",
        "0005-mixed-motorcycle-sublane-model.md",
        "0006-moving-horizon-emergency-preclearance.md",
    ]

    for adr in expected_adrs:
        fp = os.path.join(ADR_DIR, adr)
        assert os.path.exists(fp), f"ADR file {adr} must exist in {ADR_DIR}!"
        with open(fp, encoding="utf-8") as f:
            text = f.read()
            assert "Context" in text or "Title" in text
            assert "Decision" in text or "Status" in text


def test_pydantic_schemas_validation():
    """Verify that backend Pydantic models instantiate and validate domain data."""
    # 1. SystemStatus
    sys_status = SystemStatusResponse()
    assert sys_status.status == "operational"
    assert sys_status.simulation_only is True
    assert sys_status.public_signal_control_permitted is False
    assert sys_status.data_provenance == "DEMO_FIXTURE"

    # 2. HardwareStatus
    hw = HardwareStatusSchema(
        network_id="RM-INT-0457",
        obu_vehicles_online=1842,
        obu_pct=99.2,
        rsu_online=42,
        rsu_pct=100.0,
        edge_controllers_online=2,
        signal_controllers_online=4,
        v2x_status="Active",
        latency_ms=11.2,
        packet_loss_pct=0.2,
        provenance="DEMO_FIXTURE",
    )
    assert hw.obu_vehicles_online == 1842
    assert hw.latency_ms == 11.2

    # 3. SignalState
    sig = SignalStateSchema(
        intersection_id="INT-0457",
        intersection_name="Oak St & 5th Ave",
        cycle_time_s=120,
        current_phase_name="P3_EW_THRU",
        next_phase_name="P4_EW_LEFT",
        approaches=[
            {
                "approach": "E - 5th Ave. (EB)",
                "red_s": 49,
                "yellow_s": 4,
                "green_s": 67,
                "cycle_s": 120,
                "split_pct": 56,
                "current_phase": "green",
            }
        ],
        provenance="DEMO_FIXTURE",
    )
    assert sig.cycle_time_s == 120
    assert sig.approaches[0].current_phase == "green"

    # 4. EmergencyMission
    mission = EmergencyMissionSchema(
        mission_id="EM-2026-088",
        vehicle_id="AMB-339",
        vehicle_type="ambulance",
        target_facility="Metropolitan General Hospital",
        eta_hospital_min=0.7,
        status="ACTIVE",
        corridor_intersections=["INT-0455", "INT-0456", "INT-0457", "INT-0458"],
        provenance="DEMO_FIXTURE",
    )
    assert mission.vehicle_id == "AMB-339"

    # 5. TrafficAnalytics
    analytics = TrafficAnalyticsSchema(
        intersection_id="INT-0457",
        performance_index=82.0,
        throughput_pct_change=15.0,
        avg_delay_pct_change=-19.0,
        stops_per_veh_pct_change=-22.0,
        occupancy_pct=76.0,
        avg_speed_kmh=34.6,
        avg_queue_m=87.0,
        backlog_m=45.0,
        provenance="DEMO_FIXTURE",
    )
    assert analytics.performance_index == 82.0
    assert analytics.avg_delay_pct_change == -19.0


def test_json_schemas_exist_and_valid():
    """Verify that JSON schema export files exist, are valid JSON, and have expected schemas."""
    expected_schemas = [
        "SystemStatus.json",
        "TelemetrySnapshot.json",
        "HardwareStatus.json",
        "SignalState.json",
        "EmergencyMission.json",
        "TrafficAnalytics.json",
        "VehicleTelemetry.json",
    ]

    for sf in expected_schemas:
        fp = os.path.join(SCHEMAS_DIR, sf)
        assert os.path.exists(fp), f"JSON Schema file {sf} must exist in {SCHEMAS_DIR}!"
        with open(fp, encoding="utf-8") as f:
            data = json.load(f)
            assert "title" in data
            assert "type" in data or "properties" in data

