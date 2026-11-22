"""
Automated Test Suite for Task 25: Emergency Vehicle Simulation & Blue-Light Yielding
Verifies:
1. Emergency vehicle type definitions (AMB-339 ambulance, fire engine) in vtypes.add.xml.
2. SpeedFactor, sublane parameters (SL2015, arbitrary latAlignment), and dimensions.
3. Surrounding vehicle yielding cooperation parameters (lcCooperative=1.0).
4. Emergency mission injection logic (AMB-339 inserted in chronological departure order).
5. Existence and structure of emergency scenario route and config files (.rou.xml, .sumocfg).
6. Topological validity of emergency corridor route against corridor_4node.net.xml.
7. Lateral clearance width (>= 3.0m) and pre-clearance transit time model.
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path

import sumolib

from simulation.scenarios.emergency_behavior import EmergencyCorridorAnalyzer
from simulation.scenarios.emergency_mission import (
    EmergencyMission,
    inject_emergency_vehicle,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENARIOS_DIR = os.path.join(REPO_ROOT, "simulation", "scenarios")
SUMO_DIR = os.path.join(REPO_ROOT, "simulation", "sumo")


def test_emergency_vtypes_attributes():
    """Verify vtypes.add.xml defines emergency vehicles and cooperative yielding."""
    vtypes_path = os.path.join(SUMO_DIR, "vtypes.add.xml")
    assert os.path.isfile(vtypes_path)

    tree = ET.parse(vtypes_path)
    root = tree.getroot()
    vtypes = {vt.get("id"): vt for vt in root.findall("vType")}

    # Check emergency ambulance
    assert "emergency_ambulance" in vtypes
    amb = vtypes["emergency_ambulance"]
    assert amb.get("vClass") == "emergency"
    assert float(amb.get("maxSpeed")) >= 20.0  # >= 72 km/h
    assert float(amb.get("speedFactor", "1.0")) >= 1.25  # aggressive speed override
    assert amb.get("laneChangeModel") == "SL2015"
    assert amb.get("latAlignment") == "arbitrary"
    assert float(amb.get("accel")) >= 3.0

    # Check emergency fire engine
    assert "emergency_fire" in vtypes
    fire = vtypes["emergency_fire"]
    assert fire.get("vClass") == "emergency"
    assert float(fire.get("length")) >= 8.5

    # Check surrounding traffic cooperative yielding
    for vid in ["motorcycle", "car", "suv", "bus", "truck"]:
        vt = vtypes[vid]
        assert vt.get("lcCooperative") == "1.0", (
            f"Vehicle type {vid} should have lcCooperative=1.0 for yielding"
        )


def test_emergency_mission_injector_logic(tmp_path):
    """Verify inject_emergency_vehicle inserts AMB-339 in correct chronological position."""
    base_rou = os.path.join(SCENARIOS_DIR, "corridor_normal.rou.xml")
    out_rou = tmp_path / "test_normal_emergency.rou.xml"

    mission = EmergencyMission(vehicle_id="AMB-339", depart_time=52.5)
    inject_emergency_vehicle(Path(base_rou), out_rou, mission)

    tree = ET.parse(str(out_rou))
    root = tree.getroot()

    # Verify vehicle exists
    amb_veh = next((v for v in root.findall("vehicle") if v.get("id") == "AMB-339"), None)
    assert amb_veh is not None, "AMB-339 was not found in injected route file"
    assert amb_veh.get("type") == "emergency_ambulance"
    assert float(amb_veh.get("depart")) == 52.5

    # Verify chronological departure order
    vehicles = root.findall("vehicle")
    departures = [float(v.get("depart")) for v in vehicles]
    assert departures == sorted(departures), "Departures are not sorted chronologically"


def test_emergency_presets_exist():
    """Verify emergency scenario files exist for normal, peak, and spillback."""
    scenarios = ["normal", "peak", "spillback"]
    for scn in scenarios:
        rou_path = os.path.join(SCENARIOS_DIR, f"corridor_{scn}_emergency.rou.xml")
        cfg_path = os.path.join(SCENARIOS_DIR, f"corridor_{scn}_emergency.sumocfg")

        assert os.path.isfile(rou_path), f"Missing route file: {rou_path}"
        assert os.path.isfile(cfg_path), f"Missing config file: {cfg_path}"

        tree = ET.parse(rou_path)
        amb = next((v for v in tree.getroot().findall("vehicle") if v.get("id") == "AMB-339"), None)
        assert amb is not None, f"AMB-339 missing from {scn} emergency route"


def test_emergency_corridor_route_connectivity():
    """Verify AMB-339 corridor route connects all arterial nodes through to Metropolitan Hospital."""
    net_path = os.path.join(SUMO_DIR, "corridor_4node.net.xml")
    net = sumolib.net.readNet(net_path)
    valid_edge_ids = {e.getID() for e in net.getEdges()}

    rou_path = os.path.join(SCENARIOS_DIR, "corridor_peak_emergency.rou.xml")
    tree = ET.parse(rou_path)
    amb = next(v for v in tree.getroot().findall("vehicle") if v.get("id") == "AMB-339")
    route_id = amb.get("route")

    # Find route definition
    route_elem = next(r for r in tree.getroot().findall("route") if r.get("id") == route_id)
    edges = route_elem.get("edges").split()

    # Route must traverse through West -> A -> B -> C -> D -> East
    assert edges[0] == "edge_west_to_a"
    assert edges[-1] == "edge_d_to_east"
    for eid in edges:
        assert eid in valid_edge_ids, f"Invalid edge {eid} in emergency route"


def test_corridor_clearance_and_yielding_model():
    """Verify lateral clearance width >= 3.0m and pre-clearance transit efficiency."""
    analyzer = EmergencyCorridorAnalyzer(speed_mps=20.0)

    # 1. Test lateral yielding width
    # In sublane model: left car at +1.1m, right car at -1.1m on 3.2m lane
    clearance_width, is_sufficient = analyzer.evaluate_lateral_yielding(
        left_vehicle_lat_pos=1.10,
        right_vehicle_lat_pos=-1.10,
        lane_width=3.20,
    )
    assert clearance_width >= 3.00, f"Available width {clearance_width}m must be >= 3.00m"
    assert is_sufficient is True

    # 2. Test transit time comparison (Pre-Clearance vs Baseline)
    kpis_preclear = analyzer.estimate_transit_time(has_preclearance=True, congestion_level="peak")
    kpis_baseline = analyzer.estimate_transit_time(has_preclearance=False, congestion_level="peak")

    # ClearWay AI pre-clearance has 0 stops and much faster transit time
    assert kpis_preclear.deceleration_events == 0
    assert kpis_baseline.deceleration_events > 0
    assert kpis_preclear.transit_time_sec < kpis_baseline.transit_time_sec * 0.50
    assert kpis_preclear.ambulance_speed_mps > kpis_baseline.ambulance_speed_mps * 2.0
