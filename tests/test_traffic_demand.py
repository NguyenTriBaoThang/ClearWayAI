"""
Automated Test Suite for Task 24: Mixed Traffic Demand Generation & Scenario Loading Profiles
Verifies:
1. Existence and valid XML formatting of vtypes.add.xml and scenario route files (.rou.xml).
2. Vehicle type definitions conform to Vietnamese mix (motorcycle width=0.7m, car=1.9m, bus=2.5m).
3. Sublane model configuration (SL2015, lateral alignment arbitrary for motorcycles).
4. Scenario files exist for all 4 profiles (free_flow, normal, peak, spillback) with matching .sumocfg.
5. Monotonic volume scaling across scenarios (spillback > peak > normal > free_flow).
6. Statistical distribution of generated vehicle classes aligns with Vietnamese mix (70-80% motorcycles).
7. Deterministic reproducibility with random seeds.
8. Route continuity against corridor_4node.net.xml edges.
"""

import os
import xml.etree.ElementTree as ET

import sumolib

from simulation.scenarios.generate_demand import (
    generate_demand,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENARIOS_DIR = os.path.join(REPO_ROOT, "simulation", "scenarios")
SUMO_DIR = os.path.join(REPO_ROOT, "simulation", "sumo")


def test_vtypes_specification():
    """Verify vehicle types file exists and defines Vietnamese mixed traffic attributes."""
    vtypes_path = os.path.join(SUMO_DIR, "vtypes.add.xml")
    assert os.path.isfile(vtypes_path), "vtypes.add.xml missing"

    tree = ET.parse(vtypes_path)
    root = tree.getroot()

    vtypes = {vt.get("id"): vt for vt in root.findall("vType")}
    assert "motorcycle" in vtypes
    assert "car" in vtypes
    assert "suv" in vtypes
    assert "bus" in vtypes
    assert "truck" in vtypes

    # Motorcycle sublane attributes
    moto = vtypes["motorcycle"]
    assert float(moto.get("width")) <= 0.8, "Motorcycle width must be <= 0.8m"
    assert float(moto.get("length")) <= 2.0, "Motorcycle length must be <= 2.0m"
    assert moto.get("laneChangeModel") == "SL2015", "Motorcycle must use SL2015 sublane model"
    assert moto.get("latAlignment") == "arbitrary", (
        "Motorcycle must allow arbitrary lateral alignment"
    )
    assert float(moto.get("minGapLat")) <= 0.25, "Motorcycle lateral gap must be <= 0.25m"

    # Car attributes
    car = vtypes["car"]
    assert float(car.get("width")) >= 1.8
    assert car.get("latAlignment") == "center"

    # Bus attributes
    bus = vtypes["bus"]
    assert float(bus.get("length")) >= 10.0


def test_scenario_files_exist():
    """Verify all 4 scenario route files and .sumocfg configurations exist."""
    scenarios = ["free_flow", "normal", "peak", "spillback"]
    for scn in scenarios:
        rou_path = os.path.join(SCENARIOS_DIR, f"corridor_{scn}.rou.xml")
        cfg_path = os.path.join(SCENARIOS_DIR, f"corridor_{scn}.sumocfg")
        assert os.path.isfile(rou_path), f"Route file missing for {scn}"
        assert os.path.isfile(cfg_path), f"SUMO config file missing for {scn}"

        # Verify .sumocfg XML structure
        tree = ET.parse(cfg_path)
        root = tree.getroot()
        assert root.find(".//net-file").get("value") == "../sumo/corridor_4node.net.xml"
        assert root.find(".//route-files").get("value") == f"corridor_{scn}.rou.xml"
        assert root.find(".//lateral-resolution").get("value") == "0.64"


def test_monotonic_scenario_volumes():
    """Verify vehicle departure volumes scale monotonically: spillback > peak > normal > free_flow."""
    scenarios = ["free_flow", "normal", "peak", "spillback"]
    counts = {}

    for scn in scenarios:
        rou_path = os.path.join(SCENARIOS_DIR, f"corridor_{scn}.rou.xml")
        tree = ET.parse(rou_path)
        vehicles = tree.getroot().findall("vehicle")
        counts[scn] = len(vehicles)

    assert counts["spillback"] > counts["peak"], "spillback volume must exceed peak"
    assert counts["peak"] > counts["normal"], "peak volume must exceed normal"
    assert counts["normal"] > counts["free_flow"], "normal volume must exceed free_flow"


def test_vietnamese_fleet_distribution():
    """Verify generated fleet adheres to Vietnamese traffic mix (70-80% motorcycles)."""
    rou_path = os.path.join(SCENARIOS_DIR, "corridor_peak.rou.xml")
    tree = ET.parse(rou_path)
    vehicles = tree.getroot().findall("vehicle")
    assert len(vehicles) > 100

    type_counts = {}
    for v in vehicles:
        vtype = v.get("type")
        type_counts[vtype] = type_counts.get(vtype, 0) + 1

    total = len(vehicles)
    moto_ratio = type_counts.get("motorcycle", 0) / total
    car_ratio = type_counts.get("car", 0) / total

    # Statistical tolerance around 75% target
    assert 0.68 <= moto_ratio <= 0.82, (
        f"Motorcycle proportion {moto_ratio:.2%} outside expected [68%, 82%]"
    )
    assert 0.10 <= car_ratio <= 0.20, f"Car proportion {car_ratio:.2%} outside expected [10%, 20%]"


def test_deterministic_seed_reproducibility(tmp_path):
    """Verify that generating demand with the same seed produces byte-identical route files."""
    out1 = tmp_path / "test_run1.rou.xml"
    out2 = tmp_path / "test_run2.rou.xml"

    generate_demand(scenario="normal", duration=100.0, seed=999, output_path=out1)
    generate_demand(scenario="normal", duration=100.0, seed=999, output_path=out2)

    with open(out1, encoding="utf-8") as f1, open(out2, encoding="utf-8") as f2:
        assert f1.read() == f2.read(), (
            "Deterministic seed failed to generate identical route outputs"
        )


def test_route_edge_validity():
    """Verify all routes in generated files use valid edges from corridor_4node.net.xml."""
    net_path = os.path.join(SUMO_DIR, "corridor_4node.net.xml")
    net = sumolib.net.readNet(net_path)
    valid_edge_ids = {e.getID() for e in net.getEdges()}

    rou_path = os.path.join(SCENARIOS_DIR, "corridor_peak.rou.xml")
    tree = ET.parse(rou_path)
    routes = tree.getroot().findall("route")
    assert len(routes) > 0

    for r in routes:
        edge_list = r.get("edges").split()
        for edge_id in edge_list:
            assert edge_id in valid_edge_ids, f"Route {r.get('id')} contains invalid edge {edge_id}"
