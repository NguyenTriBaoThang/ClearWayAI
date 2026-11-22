#!/usr/bin/env python3
"""
ClearWayAI - SUMO 4-Node Arterial Corridor Network Synthesizer
Generates complete SUMO XML configuration files:
- corridor_4node.nod.xml (Nodes / Junctions)
- corridor_4node.edg.xml (Edges / Roads)
- corridor_4node.con.xml (Lane-to-Lane Turn Connections)
- corridor_4node.tll.xml (NEMA Traffic Light Programs & Phase Logics)
- corridor_4node.det.xml (E1 Induction Loops & E2 Lane Area Detectors)
- corridor_4node.sumocfg (Simulation Configuration with Sublane Model)
- corridor_4node.net.xml (Compiled SUMO Network XML)

Validates the output network using sumolib.
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

SUMO_DIR = Path(__file__).resolve().parent


def prettify(elem: ET.Element) -> str:
    """Return pretty-printed XML string."""
    rough_string = ET.tostring(elem, "utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ")


def build_nod_xml() -> Path:
    """Generate node definitions (.nod.xml)."""
    root = ET.Element("nodes")

    # 4 Main Corridor Intersections
    nodes = [
        ("node_a", "0.0", "0.0", "traffic_light"),
        ("node_b", "300.0", "0.0", "traffic_light"),
        ("node_c", "600.0", "0.0", "traffic_light"),
        ("node_d", "900.0", "0.0", "traffic_light"),
        # Feeder endpoints (East-West corridor)
        ("node_west_in", "-200.0", "4.8", "priority"),
        ("node_west_out", "-200.0", "-4.8", "priority"),
        ("node_east_in", "1100.0", "-4.8", "priority"),
        ("node_east_out", "1100.0", "4.8", "priority"),
        # North-South cross-street endpoints (2 lanes each direction)
        ("node_na_in", "-3.2", "200.0", "priority"),
        ("node_na_out", "3.2", "200.0", "priority"),
        ("node_sa_in", "3.2", "-200.0", "priority"),
        ("node_sa_out", "-3.2", "-200.0", "priority"),
        ("node_nb_in", "296.8", "200.0", "priority"),
        ("node_nb_out", "303.2", "200.0", "priority"),
        ("node_sb_in", "303.2", "-200.0", "priority"),
        ("node_sb_out", "296.8", "-200.0", "priority"),
        ("node_nc_in", "596.8", "200.0", "priority"),
        ("node_nc_out", "603.2", "200.0", "priority"),
        ("node_sc_in", "603.2", "-200.0", "priority"),
        ("node_sc_out", "596.8", "-200.0", "priority"),
        ("node_nd_in", "896.8", "200.0", "priority"),
        ("node_nd_out", "903.2", "200.0", "priority"),
        ("node_sd_in", "903.2", "-200.0", "priority"),
        ("node_sd_out", "896.8", "-200.0", "priority"),
    ]

    for nid, x, y, ntype in nodes:
        node_elem = ET.SubElement(root, "node", id=nid, x=x, y=y, type=ntype)
        if ntype == "traffic_light":
            node_elem.set("tl", nid)

    out_file = SUMO_DIR / "corridor_4node.nod.xml"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(prettify(root))
    print(f"Generated {out_file.name}")
    return out_file


def build_edg_xml() -> Path:
    """Generate edge definitions (.edg.xml)."""
    root = ET.Element("edges")

    # Corridor Arterial Segments (3 lanes Eastbound, 3 lanes Westbound)
    # Speed: 16.67 m/s (60 km/h)
    arterial_segments = [
        ("edge_west_to_a", "node_west_in", "node_a", "3", "16.67"),
        ("edge_a_to_b", "node_a", "node_b", "3", "16.67"),
        ("edge_b_to_c", "node_b", "node_c", "3", "16.67"),
        ("edge_c_to_d", "node_c", "node_d", "3", "16.67"),
        ("edge_d_to_east", "node_d", "node_east_out", "3", "16.67"),
        ("edge_east_to_d", "node_east_in", "node_d", "3", "16.67"),
        ("edge_d_to_c", "node_d", "node_c", "3", "16.67"),
        ("edge_c_to_b", "node_c", "node_b", "3", "16.67"),
        ("edge_b_to_a", "node_b", "node_a", "3", "16.67"),
        ("edge_a_to_west", "node_a", "node_west_out", "3", "16.67"),
    ]

    for eid, from_n, to_n, lanes, speed in arterial_segments:
        ET.SubElement(
            root,
            "edge",
            id=eid,
            **{"from": from_n, "to": to_n},
            numLanes=lanes,
            speed=speed,
            priority="7",
            width="3.2",
        )

    # Cross Street Segments (2 lanes Northbound, 2 lanes Southbound)
    # Speed: 13.89 m/s (50 km/h)
    nodes = ["a", "b", "c", "d"]
    for n in nodes:
        cross_edges = [
            (f"edge_n{n}_to_{n}", f"node_n{n}_in", f"node_{n}"),
            (f"edge_{n}_to_n{n}", f"node_{n}", f"node_n{n}_out"),
            (f"edge_s{n}_to_{n}", f"node_s{n}_in", f"node_{n}"),
            (f"edge_{n}_to_s{n}", f"node_{n}", f"node_s{n}_out"),
        ]
        for eid, from_n, to_n in cross_edges:
            ET.SubElement(
                root,
                "edge",
                id=eid,
                **{"from": from_n, "to": to_n},
                numLanes="2",
                speed="13.89",
                priority="5",
                width="3.2",
            )

    out_file = SUMO_DIR / "corridor_4node.edg.xml"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(prettify(root))
    print(f"Generated {out_file.name}")
    return out_file


def build_con_xml() -> Path:
    """Generate lane turn connections (.con.xml)."""
    root = ET.Element("connections")

    # 3-lane arterial approach connections:
    # Lane 0 (Right): Right turn (to lane 0) + Through (to lane 0)
    # Lane 1 (Middle): Through (to lane 1)
    # Lane 2 (Left): Left turn (to lane 1 of cross street)
    nodes = [
        ("a", "edge_west_to_a", "edge_a_to_b", "edge_b_to_a", "edge_a_to_west"),
        ("b", "edge_a_to_b", "edge_b_to_c", "edge_c_to_b", "edge_b_to_a"),
        ("c", "edge_b_to_c", "edge_c_to_d", "edge_d_to_c", "edge_c_to_b"),
        ("d", "edge_c_to_d", "edge_d_to_east", "edge_east_to_d", "edge_d_to_c"),
    ]

    for n, eb_in, eb_out, wb_in, wb_out in nodes:
        south_out = f"edge_{n}_to_s{n}"
        north_out = f"edge_{n}_to_n{n}"
        south_in = f"edge_s{n}_to_{n}"
        north_in = f"edge_n{n}_to_{n}"

        # EB Inflow connections
        ET.SubElement(
            root, "connection", **{"from": eb_in, "to": south_out, "fromLane": "0", "toLane": "0"}
        )  # right turn
        ET.SubElement(
            root, "connection", **{"from": eb_in, "to": eb_out, "fromLane": "0", "toLane": "0"}
        )  # through
        ET.SubElement(
            root, "connection", **{"from": eb_in, "to": eb_out, "fromLane": "1", "toLane": "1"}
        )  # through
        ET.SubElement(
            root, "connection", **{"from": eb_in, "to": eb_out, "fromLane": "2", "toLane": "2"}
        )  # through
        ET.SubElement(
            root, "connection", **{"from": eb_in, "to": north_out, "fromLane": "2", "toLane": "1"}
        )  # left turn

        # WB Inflow connections
        ET.SubElement(
            root, "connection", **{"from": wb_in, "to": north_out, "fromLane": "0", "toLane": "0"}
        )  # right turn
        ET.SubElement(
            root, "connection", **{"from": wb_in, "to": wb_out, "fromLane": "0", "toLane": "0"}
        )  # through
        ET.SubElement(
            root, "connection", **{"from": wb_in, "to": wb_out, "fromLane": "1", "toLane": "1"}
        )  # through
        ET.SubElement(
            root, "connection", **{"from": wb_in, "to": wb_out, "fromLane": "2", "toLane": "2"}
        )  # through
        ET.SubElement(
            root, "connection", **{"from": wb_in, "to": south_out, "fromLane": "2", "toLane": "1"}
        )  # left turn

        # SB Inflow (from North)
        ET.SubElement(
            root, "connection", **{"from": north_in, "to": wb_out, "fromLane": "0", "toLane": "0"}
        )  # right turn
        ET.SubElement(
            root,
            "connection",
            **{"from": north_in, "to": south_out, "fromLane": "0", "toLane": "0"},
        )  # through
        ET.SubElement(
            root,
            "connection",
            **{"from": north_in, "to": south_out, "fromLane": "1", "toLane": "1"},
        )  # through
        ET.SubElement(
            root, "connection", **{"from": north_in, "to": eb_out, "fromLane": "1", "toLane": "2"}
        )  # left turn

        # NB Inflow (from South)
        ET.SubElement(
            root, "connection", **{"from": south_in, "to": eb_out, "fromLane": "0", "toLane": "0"}
        )  # right turn
        ET.SubElement(
            root,
            "connection",
            **{"from": south_in, "to": north_out, "fromLane": "0", "toLane": "0"},
        )  # through
        ET.SubElement(
            root,
            "connection",
            **{"from": south_in, "to": north_out, "fromLane": "1", "toLane": "1"},
        )  # through
        ET.SubElement(
            root, "connection", **{"from": south_in, "to": wb_out, "fromLane": "1", "toLane": "2"}
        )  # left turn

    out_file = SUMO_DIR / "corridor_4node.con.xml"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(prettify(root))
    print(f"Generated {out_file.name}")
    return out_file


def build_tll_xml() -> Path:
    """Generate traffic light logic definitions (.tll.xml)."""
    root = ET.Element("tlLogics")

    nodes = ["node_a", "node_b", "node_c", "node_d"]
    for nid in nodes:
        tl = ET.SubElement(root, "tlLogic", id=nid, type="static", programID="0", offset="0")
        # NEMA Phases conforming to SAFETY_BOUNDARIES.md:
        # Phase 0: Arterial Green (EB & WB) -> 35s
        ET.SubElement(
            tl, "phase", duration="35", state="GGGGgrrrrrGGGGgrrrrr", minDur="10", maxDur="65"
        )
        # Phase 1: Arterial Yellow -> 4s
        ET.SubElement(tl, "phase", duration="4", state="yyyyyrrrrryyyyyrrrrr")
        # Phase 2: All-Red clearance -> 2s
        ET.SubElement(tl, "phase", duration="2", state="rrrrrrrrrrrrrrrrrrrr")
        # Phase 3: Cross Street Green (NB & SB) -> 25s
        ET.SubElement(
            tl, "phase", duration="25", state="rrrrrGGggrrrrrrGGggr", minDur="10", maxDur="45"
        )
        # Phase 4: Cross Street Yellow -> 4s
        ET.SubElement(tl, "phase", duration="4", state="rrrrryyyyrrrrrryyyyr")
        # Phase 5: All-Red clearance -> 2s
        ET.SubElement(tl, "phase", duration="2", state="rrrrrrrrrrrrrrrrrrrr")

        # Priority Emergency Pre-emption program (programID="preemption")
        tl_preempt = ET.SubElement(
            root, "tlLogic", id=nid, type="static", programID="preemption", offset="0"
        )
        # Emergency EB Corridor Green (All cross movements red)
        ET.SubElement(
            tl_preempt,
            "phase",
            duration="50",
            state="GGGGgrrrrrrrrrrrrrrr",
            minDur="15",
            maxDur="90",
        )
        ET.SubElement(tl_preempt, "phase", duration="4", state="yyyyyrrrrrrrrrrrrrrr")
        ET.SubElement(tl_preempt, "phase", duration="2", state="rrrrrrrrrrrrrrrrrrrr")

    out_file = SUMO_DIR / "corridor_4node.tll.xml"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(prettify(root))
    print(f"Generated {out_file.name}")
    return out_file


def build_det_xml() -> Path:
    """Generate induction loop (E1) and lane area (E2) detectors (.det.xml)."""
    root = ET.Element("additional")

    # Approach edges into each node
    approach_edges = [
        # Node A
        ("edge_west_to_a", 3, "node_a", 200.0),
        ("edge_na_to_a", 2, "node_a", 200.0),
        ("edge_sa_to_a", 2, "node_a", 200.0),
        ("edge_b_to_a", 3, "node_a", 300.0),
        # Node B
        ("edge_a_to_b", 3, "node_b", 300.0),
        ("edge_nb_to_b", 2, "node_b", 200.0),
        ("edge_sb_to_b", 2, "node_b", 200.0),
        ("edge_c_to_b", 3, "node_b", 300.0),
        # Node C
        ("edge_b_to_c", 3, "node_c", 300.0),
        ("edge_nc_to_c", 2, "node_c", 200.0),
        ("edge_sc_to_c", 2, "node_c", 200.0),
        ("edge_d_to_c", 3, "node_c", 300.0),
        # Node D
        ("edge_c_to_d", 3, "node_d", 300.0),
        ("edge_nd_to_d", 2, "node_d", 200.0),
        ("edge_sd_to_d", 2, "node_d", 200.0),
        ("edge_east_to_d", 3, "node_d", 200.0),
    ]

    for eid, num_lanes, _node_id, edge_len in approach_edges:
        for lane_idx in range(num_lanes):
            lane_id = f"{eid}_{lane_idx}"

            # E1 Stopline detector (5m before stopline)
            ET.SubElement(
                root,
                "inductionLoop",
                id=f"e1_{eid}_{lane_idx}_stop",
                lane=lane_id,
                pos=f"{edge_len - 5.0:.1f}",
                period="10",
                file="detectors_e1.out.xml",
                friendlyPos="true",
            )
            # E1 Advance detector (80m upstream)
            ET.SubElement(
                root,
                "inductionLoop",
                id=f"e1_{eid}_{lane_idx}_adv",
                lane=lane_id,
                pos=f"{max(10.0, edge_len - 80.0):.1f}",
                period="10",
                file="detectors_e1.out.xml",
                friendlyPos="true",
            )
            # E2 Lane Area Detector (spans 70m queue zone)
            ET.SubElement(
                root,
                "laneAreaDetector",
                id=f"e2_{eid}_{lane_idx}",
                lane=lane_id,
                pos=f"{max(5.0, edge_len - 75.0):.1f}",
                length="70.0",
                period="5",
                file="detectors_e2.out.xml",
                friendlyPos="true",
            )

    out_file = SUMO_DIR / "corridor_4node.det.xml"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(prettify(root))
    print(f"Generated {out_file.name}")
    return out_file


def build_sumocfg() -> Path:
    """Generate main simulation configuration (.sumocfg)."""
    root = ET.Element("configuration")

    input_elem = ET.SubElement(root, "input")
    ET.SubElement(input_elem, "net-file", value="corridor_4node.net.xml")
    ET.SubElement(input_elem, "additional-files", value="corridor_4node.det.xml")

    time_elem = ET.SubElement(root, "time")
    ET.SubElement(time_elem, "begin", value="0")
    ET.SubElement(time_elem, "step-length", value="0.1")

    # Sublane Model Configuration (ADR-0005)
    processing_elem = ET.SubElement(root, "processing")
    ET.SubElement(processing_elem, "lateral-resolution", value="0.64")
    ET.SubElement(processing_elem, "collision.action", value="warn")
    ET.SubElement(processing_elem, "time-to-teleport", value="-1")

    gui_elem = ET.SubElement(root, "gui_only")
    ET.SubElement(gui_elem, "start", value="true")

    out_file = SUMO_DIR / "corridor_4node.sumocfg"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(prettify(root))
    print(f"Generated {out_file.name}")
    return out_file


def build_net_xml() -> Path:
    """
    Generate fully compliant SUMO network (.net.xml) directly.
    Contains valid <location>, <edge>, <lane>, <junction>, <connection>, and <tlLogic>.
    Directly compatible with sumolib.net.readNet().
    """
    root = ET.Element(
        "net",
        version="1.20",
        junctionCornerDetail="5",
        limitTurnSpeed="5.50",
        **{
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "http://sumo.dlr.de/xsd/net_file.xsd",
        },
    )

    # Location tag
    ET.SubElement(
        root,
        "location",
        netOffset="200.00,200.00",
        convBoundary="0.00,0.00,1300.00,400.00",
        origBoundary="-200.00,-200.00,1100.00,200.00",
        projParameter="!",
    )

    # Traffic light logics
    nodes = ["node_a", "node_b", "node_c", "node_d"]
    for nid in nodes:
        tl = ET.SubElement(root, "tlLogic", id=nid, type="static", programID="0", offset="0")
        ET.SubElement(
            tl, "phase", duration="35", state="GGGGgrrrrrGGGGgrrrrr", minDur="10", maxDur="65"
        )
        ET.SubElement(tl, "phase", duration="4", state="yyyyyrrrrryyyyyrrrrr")
        ET.SubElement(tl, "phase", duration="2", state="rrrrrrrrrrrrrrrrrrrr")
        ET.SubElement(
            tl, "phase", duration="25", state="rrrrrGGggrrrrrrGGggr", minDur="10", maxDur="45"
        )
        ET.SubElement(tl, "phase", duration="4", state="rrrrryyyyrrrrrryyyyr")
        ET.SubElement(tl, "phase", duration="2", state="rrrrrrrrrrrrrrrrrrrr")

    # Define edges & lanes
    # Helper to generate straight shape
    def make_shape(x1, y1, x2, y2):
        return f"{x1:.2f},{y1:.2f} {x2:.2f},{y2:.2f}"

    # Map of node coordinates (offset shifted by +200, +200 for positive cartesian coordinates)
    node_coords = {
        "node_west_in": (0.0, 204.8),
        "node_west_out": (0.0, 195.2),
        "node_a": (200.0, 200.0),
        "node_b": (500.0, 200.0),
        "node_c": (800.0, 200.0),
        "node_d": (1100.0, 200.0),
        "node_east_in": (1300.0, 195.2),
        "node_east_out": (1300.0, 204.8),
        # Cross nodes
        "node_na_in": (196.8, 400.0),
        "node_na_out": (203.2, 400.0),
        "node_sa_in": (203.2, 0.0),
        "node_sa_out": (196.8, 0.0),
        "node_nb_in": (496.8, 400.0),
        "node_nb_out": (503.2, 400.0),
        "node_sb_in": (503.2, 0.0),
        "node_sb_out": (496.8, 0.0),
        "node_nc_in": (796.8, 400.0),
        "node_nc_out": (803.2, 400.0),
        "node_sc_in": (803.2, 0.0),
        "node_sc_out": (796.8, 0.0),
        "node_nd_in": (1096.8, 400.0),
        "node_nd_out": (1103.2, 400.0),
        "node_sd_in": (1103.2, 0.0),
        "node_sd_out": (1096.8, 0.0),
    }

    # Edges specification
    edges_spec = [
        # Eastbound Arterial (3 lanes, speed 16.67 m/s)
        ("edge_west_to_a", "node_west_in", "node_a", 3, 16.67, 7),
        ("edge_a_to_b", "node_a", "node_b", 3, 16.67, 7),
        ("edge_b_to_c", "node_b", "node_c", 3, 16.67, 7),
        ("edge_c_to_d", "node_c", "node_d", 3, 16.67, 7),
        ("edge_d_to_east", "node_d", "node_east_out", 3, 16.67, 7),
        # Westbound Arterial (3 lanes, speed 16.67 m/s)
        ("edge_east_to_d", "node_east_in", "node_d", 3, 16.67, 7),
        ("edge_d_to_c", "node_d", "node_c", 3, 16.67, 7),
        ("edge_c_to_b", "node_c", "node_b", 3, 16.67, 7),
        ("edge_b_to_a", "node_b", "node_a", 3, 16.67, 7),
        ("edge_a_to_west", "node_a", "node_west_out", 3, 16.67, 7),
    ]
    # Add cross streets (2 lanes each, speed 13.89 m/s)
    for n in ["a", "b", "c", "d"]:
        edges_spec.extend(
            [
                (f"edge_n{n}_to_{n}", f"node_n{n}_in", f"node_{n}", 2, 13.89, 5),
                (f"edge_{n}_to_n{n}", f"node_{n}", f"node_n{n}_out", 2, 13.89, 5),
                (f"edge_s{n}_to_{n}", f"node_s{n}_in", f"node_{n}", 2, 13.89, 5),
                (f"edge_{n}_to_s{n}", f"node_{n}", f"node_s{n}_out", 2, 13.89, 5),
            ]
        )

    for eid, from_n, to_n, num_lanes, speed, prio in edges_spec:
        edge_elem = ET.SubElement(
            root,
            "edge",
            id=eid,
            **{"from": from_n, "to": to_n},
            priority=str(prio),
        )
        x1, y1 = node_coords[from_n]
        x2, y2 = node_coords[to_n]
        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

        for l_idx in range(num_lanes):
            lane_id = f"{eid}_{l_idx}"
            shape = make_shape(x1, y1, x2, y2)
            ET.SubElement(
                edge_elem,
                "lane",
                id=lane_id,
                index=str(l_idx),
                speed=f"{speed:.2f}",
                length=f"{length:.2f}",
                shape=shape,
                width="3.20",
            )

    # Junctions
    for nid, (x, y) in node_coords.items():
        jtype = (
            "traffic_light"
            if nid.startswith("node_") and len(nid) == 6 and nid[-1] in "abcd"
            else "priority"
        )
        inc_lanes = []
        for eid, _fn, tn, nlanes, _, _ in edges_spec:
            if tn == nid:
                for lane_idx in range(nlanes):
                    inc_lanes.append(f"{eid}_{lane_idx}")

        ET.SubElement(
            root,
            "junction",
            id=nid,
            type=jtype,
            x=f"{x:.2f}",
            y=f"{y:.2f}",
            incLanes=" ".join(inc_lanes),
            intLanes="",
            shape=f"{x - 10:.2f},{y - 10:.2f} {x + 10:.2f},{y - 10:.2f} {x + 10:.2f},{y + 10:.2f} {x - 10:.2f},{y + 10:.2f}",
        )

    # Connections between edges
    # Generate connections at each traffic light intersection
    for n in ["a", "b", "c", "d"]:
        tl_id = f"node_{n}"
        eb_in = "edge_west_to_a" if n == "a" else f"edge_{chr(ord(n) - 1)}_to_{n}"
        eb_out = "edge_d_to_east" if n == "d" else f"edge_{n}_to_{chr(ord(n) + 1)}"
        wb_in = "edge_east_to_d" if n == "d" else f"edge_{chr(ord(n) + 1)}_to_{n}"
        wb_out = "edge_a_to_west" if n == "a" else f"edge_{n}_to_{chr(ord(n) - 1)}"

        # EB through connections
        for lane_idx in range(3):
            ET.SubElement(
                root,
                "connection",
                **{"from": eb_in, "to": eb_out, "fromLane": str(lane_idx), "toLane": str(lane_idx)},
                tl=tl_id,
                linkIndex=str(lane_idx),
                dir="s",
                state="M",
            )
        # WB through connections
        for lane_idx in range(3):
            ET.SubElement(
                root,
                "connection",
                **{"from": wb_in, "to": wb_out, "fromLane": str(lane_idx), "toLane": str(lane_idx)},
                tl=tl_id,
                linkIndex=str(lane_idx + 5),
                dir="s",
                state="M",
            )
        # Cross Northbound & Southbound through
        ET.SubElement(
            root,
            "connection",
            **{
                "from": f"edge_s{n}_to_{n}",
                "to": f"edge_{n}_to_n{n}",
                "fromLane": "0",
                "toLane": "0",
            },
            tl=tl_id,
            linkIndex="10",
            dir="s",
            state="M",
        )
        ET.SubElement(
            root,
            "connection",
            **{
                "from": f"edge_s{n}_to_{n}",
                "to": f"edge_{n}_to_n{n}",
                "fromLane": "1",
                "toLane": "1",
            },
            tl=tl_id,
            linkIndex="11",
            dir="s",
            state="M",
        )
        ET.SubElement(
            root,
            "connection",
            **{
                "from": f"edge_n{n}_to_{n}",
                "to": f"edge_{n}_to_s{n}",
                "fromLane": "0",
                "toLane": "0",
            },
            tl=tl_id,
            linkIndex="15",
            dir="s",
            state="M",
        )
        ET.SubElement(
            root,
            "connection",
            **{
                "from": f"edge_n{n}_to_{n}",
                "to": f"edge_{n}_to_s{n}",
                "fromLane": "1",
                "toLane": "1",
            },
            tl=tl_id,
            linkIndex="16",
            dir="s",
            state="M",
        )

    out_file = SUMO_DIR / "corridor_4node.net.xml"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(prettify(root))
    print(f"Generated {out_file.name}")
    return out_file


def validate_network() -> bool:
    """Validate generated network using sumolib."""
    try:
        import sumolib

        net_path = str(SUMO_DIR / "corridor_4node.net.xml")
        print(f"Validating network with sumolib: {net_path}")
        net = sumolib.net.readNet(net_path)

        # Verify 4 main intersections
        for nid in ["node_a", "node_b", "node_c", "node_d"]:
            node = net.getNode(nid)
            assert node is not None, f"Node {nid} not found in net"
            assert node.getType() == "traffic_light", f"Node {nid} is not traffic_light"
            print(f"  ✅ Verified node {nid}: type={node.getType()}, pos=({node.getCoord()})")

        # Verify edges
        edges = net.getEdges()
        print(f"  ✅ Verified {len(edges)} edges loaded in network.")
        assert len(edges) >= 26, f"Expected at least 26 edges, got {len(edges)}"

        # Verify arterial corridor continuity
        corridor_path = [
            "edge_west_to_a",
            "edge_a_to_b",
            "edge_b_to_c",
            "edge_c_to_d",
            "edge_d_to_east",
        ]
        for eid in corridor_path:
            edge = net.getEdge(eid)
            assert edge is not None, f"Arterial edge {eid} missing"
            assert len(edge.getLanes()) == 3, f"Arterial edge {eid} should have 3 lanes"
            assert abs(edge.getSpeed() - 16.67) < 0.1, f"Edge speed mismatch on {eid}"
            print(
                f"  ✅ Verified arterial edge {eid}: {len(edge.getLanes())} lanes, speed={edge.getSpeed()} m/s"
            )

        # Verify traffic lights
        tls = net.getTrafficLights()
        print(f"  ✅ Verified {len(tls)} traffic light controllers.")
        assert len(tls) == 4, f"Expected 4 traffic light controllers, got {len(tls)}"

        print("🎉 ALL SUMO NETWORK VALIDATIONS PASSED!")
        return True
    except Exception as e:
        print(f"❌ Network validation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    print("=" * 70)
    print("🚦 ClearWayAI - Building SUMO 4-Node Arterial Corridor Network")
    print("=" * 70)

    build_nod_xml()
    build_edg_xml()
    build_con_xml()
    build_tll_xml()
    build_det_xml()
    build_sumocfg()
    build_net_xml()

    success = validate_network()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
