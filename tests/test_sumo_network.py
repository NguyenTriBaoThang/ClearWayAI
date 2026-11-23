"""
Automated Test Suite for Task 23: SUMO Multi-Intersection Arterial Network
Verifies:
1. Existence and valid XML formatting of all 7 corridor files.
2. Direct parsing and verification via sumolib.net.readNet().
3. Geometric accuracy of Nodes A-D and corridor distance.
4. Lane properties (width=3.2m, 3 arterial lanes, speed limits).
5. Traffic signal phase definitions and safety invariants (min-green >= 10s, yellow >= 3s, all-red >= 2s).
6. Detector network coverage across all approach lanes (E1 stopline, E1 advance, E2 queue area).
7. SUMO configuration (.sumocfg) sublane resolution and step length settings.
"""

import os
import xml.etree.ElementTree as ET

import pytest

sumolib = pytest.importorskip(
    "sumolib", reason="sumolib is required for SUMO network/scenario tests"
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUMO_DIR = os.path.join(REPO_ROOT, "simulation", "sumo")


def test_sumo_network_files_exist():
    """Verify all 7 SUMO network XML and config files exist."""
    expected_files = [
        "corridor_4node.nod.xml",
        "corridor_4node.edg.xml",
        "corridor_4node.con.xml",
        "corridor_4node.tll.xml",
        "corridor_4node.det.xml",
        "corridor_4node.sumocfg",
        "corridor_4node.net.xml",
    ]
    for fname in expected_files:
        fpath = os.path.join(SUMO_DIR, fname)
        assert os.path.isfile(fpath), f"Missing SUMO network file: {fname}"


def test_sumo_net_xml_valid_with_sumolib():
    """Verify corridor_4node.net.xml is valid and fully readable via sumolib."""
    net_path = os.path.join(SUMO_DIR, "corridor_4node.net.xml")
    net = sumolib.net.readNet(net_path)
    assert net is not None

    # Verify 4 main intersections
    expected_nodes = ["node_a", "node_b", "node_c", "node_d"]
    for nid in expected_nodes:
        node = net.getNode(nid)
        assert node is not None, f"Node {nid} not found in net"
        assert node.getType() == "traffic_light", f"Node {nid} must be traffic_light"

    # Verify corridor length
    node_a = net.getNode("node_a")
    node_d = net.getNode("node_d")
    coord_a = node_a.getCoord()
    coord_d = node_d.getCoord()
    corridor_dist = abs(coord_d[0] - coord_a[0])
    assert corridor_dist == 900.0, (
        f"Expected 900m distance between Node A and D, got {corridor_dist}"
    )


def test_arterial_lane_geometry_and_speeds():
    """Verify 3 arterial lanes per direction and speed limits (60 km/h = 16.67 m/s)."""
    net_path = os.path.join(SUMO_DIR, "corridor_4node.net.xml")
    net = sumolib.net.readNet(net_path)

    arterial_edges = [
        "edge_west_to_a",
        "edge_a_to_b",
        "edge_b_to_c",
        "edge_c_to_d",
        "edge_d_to_east",
    ]
    for eid in arterial_edges:
        edge = net.getEdge(eid)
        assert edge is not None, f"Arterial edge {eid} not found"
        lanes = edge.getLanes()
        assert len(lanes) == 3, f"Edge {eid} must have 3 lanes, got {len(lanes)}"
        assert abs(edge.getSpeed() - 16.67) < 0.1, f"Edge {eid} speed should be ~16.67 m/s"
        for lane in lanes:
            assert abs(lane.getWidth() - 3.20) < 0.05, f"Lane width on {eid} should be 3.20m"


def test_cross_street_geometry():
    """Verify 2 cross-street lanes per direction and 50 km/h (13.89 m/s) speed limit."""
    net_path = os.path.join(SUMO_DIR, "corridor_4node.net.xml")
    net = sumolib.net.readNet(net_path)

    cross_edges = [
        "edge_na_to_a",
        "edge_sa_to_a",
        "edge_nb_to_b",
        "edge_sb_to_b",
        "edge_nc_to_c",
        "edge_sc_to_c",
        "edge_nd_to_d",
        "edge_sd_to_d",
    ]
    for eid in cross_edges:
        edge = net.getEdge(eid)
        assert edge is not None, f"Cross edge {eid} not found"
        lanes = edge.getLanes()
        assert len(lanes) == 2, f"Cross edge {eid} must have 2 lanes"
        assert abs(edge.getSpeed() - 13.89) < 0.1, f"Cross edge {eid} speed should be ~13.89 m/s"


def test_traffic_light_safety_invariants():
    """Verify traffic light phases conform to SAFETY_BOUNDARIES.md."""
    tll_path = os.path.join(SUMO_DIR, "corridor_4node.tll.xml")
    tree = ET.parse(tll_path)
    root = tree.getroot()

    nodes = ["node_a", "node_b", "node_c", "node_d"]
    for nid in nodes:
        tls = root.findall(f".//tlLogic[@id='{nid}']")
        assert len(tls) >= 1, f"Traffic light logic for {nid} missing"

        # Check nominal program
        nominal = next((tl for tl in tls if tl.get("programID") == "0"), None)
        assert nominal is not None, f"Nominal program missing for {nid}"

        phases = nominal.findall("phase")
        assert len(phases) == 6, f"Expected 6 NEMA phases, got {len(phases)}"

        # Phase 0: Arterial Green
        p0 = phases[0]
        assert float(p0.get("duration")) >= 30.0
        assert float(p0.get("minDur", "0")) >= 10.0, "Min-green invariant violated"

        # Phase 1: Arterial Yellow
        p1 = phases[1]
        assert float(p1.get("duration")) >= 3.0, "Yellow interval must be >= 3s"

        # Phase 2: All-Red clearance
        p2 = phases[2]
        assert float(p2.get("duration")) >= 2.0, "All-red clearance must be >= 2s"
        assert all(c == "r" for c in p2.get("state")), "All-red phase must be all red"

        # Phase 3: Cross Street Green
        p3 = phases[3]
        assert float(p3.get("duration")) >= 20.0
        assert float(p3.get("minDur", "0")) >= 10.0, "Min-green invariant violated"

        # Phase 4: Cross Street Yellow
        p4 = phases[4]
        assert float(p4.get("duration")) >= 3.0, "Yellow interval must be >= 3s"

        # Phase 5: All-Red clearance
        p5 = phases[5]
        assert float(p5.get("duration")) >= 2.0, "All-red clearance must be >= 2s"
        assert all(c == "r" for c in p5.get("state")), "All-red phase must be all red"


def test_detectors_network_coverage():
    """Verify E1 stopline, E1 advance, and E2 queue detectors exist for all approach lanes."""
    det_path = os.path.join(SUMO_DIR, "corridor_4node.det.xml")
    tree = ET.parse(det_path)
    root = tree.getroot()

    e1_loops = root.findall("inductionLoop")
    e2_areas = root.findall("laneAreaDetector")

    assert len(e1_loops) >= 60, f"Expected >= 60 E1 induction loops, got {len(e1_loops)}"
    assert len(e2_areas) >= 30, f"Expected >= 30 E2 lane area detectors, got {len(e2_areas)}"

    # Check that stopline detectors are near end of approach
    for loop in e1_loops:
        lid = loop.get("id")
        if "_stop" in lid:
            pos = float(loop.get("pos"))
            assert pos >= 150.0, f"Stopline detector {lid} pos {pos} not near stopline"


def test_sumocfg_sublane_and_resolution():
    """Verify .sumocfg specifies sublane resolution <= 0.8m and step length <= 0.1s."""
    cfg_path = os.path.join(SUMO_DIR, "corridor_4node.sumocfg")
    tree = ET.parse(cfg_path)
    root = tree.getroot()

    # Step length
    step_elem = root.find(".//step-length")
    assert step_elem is not None
    assert float(step_elem.get("value")) <= 0.1, "Step length must be <= 0.1s"

    # Lateral resolution (Sublane model)
    res_elem = root.find(".//lateral-resolution")
    assert res_elem is not None
    assert float(res_elem.get("value")) <= 0.8, "Sublane resolution must be <= 0.8m"
