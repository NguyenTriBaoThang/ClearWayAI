#!/usr/bin/env python3
"""
ClearWayAI - Emergency Mission Injector & Dispatch Service
Injects high-priority emergency vehicles (e.g. AMB-339) into SUMO traffic scenarios.
Configures:
- Vehicle ID (e.g. 'AMB-339')
- Vehicle Type ('emergency_ambulance', 'emergency_fire')
- Corridor route from Western gate to Metropolitan Hospital (Node A -> B -> C -> D)
- Accurate departure time, aggressive sublane speedFactor, and blue-light yielding parameters.
"""

import argparse
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from xml.dom import minidom

SCENARIOS_DIR = Path(__file__).resolve().parent
SUMO_DIR = SCENARIOS_DIR.parent / "sumo"

EMERGENCY_AMBULANCE_VTYPE = {
    "id": "emergency_ambulance",
    "vClass": "emergency",
    "length": "6.50",
    "width": "2.20",
    "height": "2.80",
    "minGap": "1.00",
    "maxSpeed": "22.22",
    "speedFactor": "1.30",
    "accel": "3.5",
    "decel": "5.0",
    "emergencyDecel": "9.0",
    "sigma": "0.1",
    "tau": "0.6",
    "laneChangeModel": "SL2015",
    "latAlignment": "arbitrary",
    "minGapLat": "0.25",
    "lcPushy": "1.0",
    "lcAssertive": "1.0",
    "lcSublane": "1.0",
    "lcStrategic": "2.0",
    "lcCooperative": "0.0",
    "jmDriveAfterYellowTime": "3.0",
    "jmDriveAfterRedTime": "1.5",
    "guiShape": "emergency",
    "color": "1.0,0.2,0.2",
}

EMERGENCY_FIRE_VTYPE = {
    "id": "emergency_fire",
    "vClass": "emergency",
    "length": "9.00",
    "width": "2.50",
    "height": "3.20",
    "minGap": "1.50",
    "maxSpeed": "19.44",
    "speedFactor": "1.20",
    "accel": "2.5",
    "decel": "4.5",
    "emergencyDecel": "8.0",
    "sigma": "0.1",
    "tau": "0.7",
    "laneChangeModel": "SL2015",
    "latAlignment": "center",
    "minGapLat": "0.40",
    "lcPushy": "0.9",
    "lcAssertive": "0.9",
    "lcSublane": "0.8",
    "lcStrategic": "2.0",
    "lcCooperative": "0.0",
    "jmDriveAfterYellowTime": "3.0",
    "jmDriveAfterRedTime": "1.0",
    "guiShape": "firebrigade",
    "color": "0.9,0.1,0.1",
}


@dataclass
class EmergencyMission:
    mission_id: str = "mission-amb-339"
    vehicle_id: str = "AMB-339"
    vtype: str = "emergency_ambulance"
    depart_time: float = 60.0
    route_id: str = "route_eb_through"
    target_hospital: str = "Metropolitan Trauma Center"
    route_nodes: list[str] = field(default_factory=lambda: ["node_a", "node_b", "node_c", "node_d"])
    corridor_edges: str = "edge_west_to_a edge_a_to_b edge_b_to_c edge_c_to_d edge_d_to_east"


def inject_emergency_vehicle(
    base_rou_path: Path,
    output_rou_path: Path,
    mission: EmergencyMission | None = None,
) -> Path:
    """
    Injects an emergency mission vehicle into an existing SUMO route file.
    Ensures vType definitions are present and maintains chronological departure order.
    """
    if mission is None:
        mission = EmergencyMission()

    tree = ET.parse(base_rou_path)
    root = tree.getroot()

    # 1. Ensure Emergency vType is present in the XML
    existing_vtypes = {vt.get("id") for vt in root.findall("vType")}
    if mission.vtype not in existing_vtypes:
        vtype_data = (
            EMERGENCY_AMBULANCE_VTYPE
            if mission.vtype == "emergency_ambulance"
            else EMERGENCY_FIRE_VTYPE
        )
        # Insert vType after existing vTypes
        first_route_idx = 0
        for i, elem in enumerate(root):
            if elem.tag == "route":
                first_route_idx = i
                break
        root.insert(first_route_idx, ET.Element("vType", **vtype_data))

    # 2. Ensure Route is defined
    existing_routes = {r.get("id"): r for r in root.findall("route")}
    if mission.route_id not in existing_routes:
        first_veh_idx = 0
        for i, elem in enumerate(root):
            if elem.tag == "vehicle":
                first_veh_idx = i
                break
        root.insert(
            first_veh_idx, ET.Element("route", id=mission.route_id, edges=mission.corridor_edges)
        )

    # 3. Create the Emergency Vehicle Element
    ev_elem = ET.Element(
        "vehicle",
        id=mission.vehicle_id,
        type=mission.vtype,
        route=mission.route_id,
        depart=f"{mission.depart_time:.2f}",
        departSpeed="max",
        departLane="best",
        departPosLat="0.0",
        color="1.0,0.2,0.2",
    )

    # 4. Insert vehicle in chronological departure order
    vehicles = root.findall("vehicle")
    inserted = False
    for v in vehicles:
        dep = float(v.get("depart", "0.0"))
        if dep >= mission.depart_time:
            # Find index in root children
            root_idx = list(root).index(v)
            root.insert(root_idx, ev_elem)
            inserted = True
            break

    if not inserted:
        root.append(ev_elem)

    # 5. Pretty-print and save
    rough = ET.tostring(root, "utf-8")
    reparsed = minidom.parseString(rough)
    with open(output_rou_path, "w", encoding="utf-8") as f:
        f.write(reparsed.toprettyxml(indent="    "))

    print(
        f"✅ Injected {mission.vehicle_id} ({mission.vtype}) at t={mission.depart_time:.1f}s into {output_rou_path.name}"
    )
    return output_rou_path


def generate_emergency_presets():
    """Generates emergency scenario route presets for normal, peak, and spillback."""
    presets = [
        ("normal", 45.0),
        ("peak", 60.0),
        ("spillback", 75.0),
    ]
    generated = []
    for scn, dep in presets:
        base_rou = SCENARIOS_DIR / f"corridor_{scn}.rou.xml"
        out_rou = SCENARIOS_DIR / f"corridor_{scn}_emergency.rou.xml"
        out_cfg = SCENARIOS_DIR / f"corridor_{scn}_emergency.sumocfg"

        mission = EmergencyMission(depart_time=dep)
        inject_emergency_vehicle(base_rou, out_rou, mission)

        # Generate corresponding .sumocfg
        root_cfg = ET.Element("configuration")
        input_elem = ET.SubElement(root_cfg, "input")
        ET.SubElement(input_elem, "net-file", value="../sumo/corridor_4node.net.xml")
        ET.SubElement(input_elem, "route-files", value=f"corridor_{scn}_emergency.rou.xml")
        ET.SubElement(input_elem, "additional-files", value="../sumo/corridor_4node.det.xml")

        time_elem = ET.SubElement(root_cfg, "time")
        ET.SubElement(time_elem, "begin", value="0")
        ET.SubElement(time_elem, "end", value="300")
        ET.SubElement(time_elem, "step-length", value="0.1")

        proc_elem = ET.SubElement(root_cfg, "processing")
        ET.SubElement(proc_elem, "lateral-resolution", value="0.64")
        ET.SubElement(proc_elem, "collision.action", value="warn")
        ET.SubElement(proc_elem, "time-to-teleport", value="-1")

        gui_elem = ET.SubElement(root_cfg, "gui_only")
        ET.SubElement(gui_elem, "start", value="true")

        rough_cfg = ET.tostring(root_cfg, "utf-8")
        with open(out_cfg, "w", encoding="utf-8") as f:
            f.write(minidom.parseString(rough_cfg).toprettyxml(indent="    "))

        generated.append((out_rou, out_cfg))
    return generated


def main():
    parser = argparse.ArgumentParser(
        description="Inject emergency mission vehicle into SUMO scenario."
    )
    parser.add_argument(
        "--scenario", choices=["free_flow", "normal", "peak", "spillback"], default="peak"
    )
    parser.add_argument(
        "--depart", type=float, default=60.0, help="Ambulance departure time in seconds"
    )
    parser.add_argument(
        "--all", action="store_true", help="Generate all standard emergency scenario presets"
    )
    args = parser.parse_args()

    print("=" * 70)
    print("🚑 ClearWayAI - Emergency Mission Dispatch & Vehicle Injection")
    print("=" * 70)

    if args.all:
        presets = generate_emergency_presets()
        print(f"🎉 Generated {len(presets)} emergency scenario configurations successfully!")
    else:
        base = SCENARIOS_DIR / f"corridor_{args.scenario}.rou.xml"
        out = SCENARIOS_DIR / f"corridor_{args.scenario}_emergency.rou.xml"
        mission = EmergencyMission(depart_time=args.depart)
        inject_emergency_vehicle(base, out, mission)

    return 0


if __name__ == "__main__":
    sys.exit(main())
