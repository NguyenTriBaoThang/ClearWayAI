#!/usr/bin/env python3
"""
ClearWayAI - Synthetic Traffic Demand Generator for Vietnamese Mixed Traffic
Generates SUMO route files (.rou.xml) modeling:
- 75% Motorcycles with sublane lateral filtering (ADR-0005)
- 15% Passenger Cars
- 5% SUVs
- 3% Transit Buses
- 2% Commercial Delivery Trucks

Supports standard loading scenarios:
- free_flow: Low demand (approx 450 veh/h/lane, free travel)
- normal: Moderate urban flow (approx 850 veh/h/lane)
- peak: Heavy congestion (approx 1400 veh/h/lane, queue formation)
- spillback: Extreme surge (approx 1800 veh/h/lane, inter-junction queue spillback)
"""

import argparse
import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.dom import minidom

SCENARIOS_DIR = Path(__file__).resolve().parent

# Vehicle Type Definitions (SL2015 Sublane Model)
VTYPES = [
    {
        "id": "motorcycle",
        "vClass": "motorcycle",
        "length": "1.90",
        "width": "0.70",
        "height": "1.20",
        "minGap": "0.40",
        "maxSpeed": "13.89",
        "accel": "3.2",
        "decel": "4.5",
        "laneChangeModel": "SL2015",
        "latAlignment": "arbitrary",
        "minGapLat": "0.20",
        "lcPushy": "0.8",
        "lcAssertive": "0.9",
        "lcSublane": "1.0",
        "guiShape": "motorcycle",
        "color": "1.0,0.8,0.0",
    },
    {
        "id": "car",
        "vClass": "passenger",
        "length": "4.60",
        "width": "1.90",
        "height": "1.50",
        "minGap": "1.50",
        "maxSpeed": "16.67",
        "accel": "2.6",
        "decel": "4.5",
        "laneChangeModel": "SL2015",
        "latAlignment": "center",
        "minGapLat": "0.50",
        "lcPushy": "0.2",
        "lcAssertive": "0.4",
        "lcSublane": "0.5",
        "guiShape": "passenger",
        "color": "0.2,0.6,1.0",
    },
    {
        "id": "suv",
        "vClass": "passenger",
        "length": "4.90",
        "width": "2.00",
        "height": "1.70",
        "minGap": "1.60",
        "maxSpeed": "16.67",
        "accel": "2.4",
        "decel": "4.5",
        "laneChangeModel": "SL2015",
        "latAlignment": "center",
        "minGapLat": "0.50",
        "lcPushy": "0.2",
        "lcAssertive": "0.4",
        "lcSublane": "0.5",
        "guiShape": "passenger/wagon",
        "color": "0.3,0.8,0.4",
    },
    {
        "id": "bus",
        "vClass": "bus",
        "length": "11.00",
        "width": "2.50",
        "height": "3.20",
        "minGap": "2.00",
        "maxSpeed": "13.89",
        "accel": "1.8",
        "decel": "3.5",
        "laneChangeModel": "SL2015",
        "latAlignment": "center",
        "minGapLat": "0.60",
        "lcPushy": "0.1",
        "lcAssertive": "0.2",
        "lcSublane": "0.2",
        "guiShape": "bus",
        "color": "0.9,0.3,0.3",
    },
    {
        "id": "truck",
        "vClass": "truck",
        "length": "8.50",
        "width": "2.50",
        "height": "3.00",
        "minGap": "2.50",
        "maxSpeed": "12.50",
        "accel": "1.5",
        "decel": "3.0",
        "laneChangeModel": "SL2015",
        "latAlignment": "center",
        "minGapLat": "0.60",
        "lcPushy": "0.1",
        "lcAssertive": "0.2",
        "lcSublane": "0.2",
        "guiShape": "truck",
        "color": "0.6,0.6,0.6",
    },
]

# Standard Vietnamese Traffic Mix Probabilities
DEFAULT_MIX = {
    "motorcycle": 0.75,
    "car": 0.15,
    "suv": 0.05,
    "bus": 0.03,
    "truck": 0.02,
}

# Route Templates through Corridor
ROUTE_TEMPLATES = {
    # Arterial Through Routes
    "route_eb_through": "edge_west_to_a edge_a_to_b edge_b_to_c edge_c_to_d edge_d_to_east",
    "route_wb_through": "edge_east_to_d edge_d_to_c edge_c_to_b edge_b_to_a edge_a_to_west",
    # Cross Street Through Routes
    "route_sb_a": "edge_na_to_a edge_a_to_sa",
    "route_nb_a": "edge_sa_to_a edge_a_to_na",
    "route_sb_b": "edge_nb_to_b edge_b_to_sb",
    "route_nb_b": "edge_sb_to_b edge_b_to_nb",
    "route_sb_c": "edge_nc_to_c edge_c_to_sc",
    "route_nb_c": "edge_sc_to_c edge_c_to_nc",
    "route_sb_d": "edge_nd_to_d edge_d_to_sd",
    "route_nb_d": "edge_sd_to_d edge_d_to_nd",
    # Arterial Feeder Inflows (Turning into Corridor toward Hospital)
    "route_na_to_eb": "edge_na_to_a edge_a_to_b edge_b_to_c edge_c_to_d edge_d_to_east",
    "route_sa_to_eb": "edge_sa_to_a edge_a_to_b edge_b_to_c edge_c_to_d edge_d_to_east",
    "route_nb_to_eb": "edge_nb_to_b edge_b_to_c edge_c_to_d edge_d_to_east",
    "route_sb_to_eb": "edge_sb_to_b edge_b_to_c edge_c_to_d edge_d_to_east",
    "route_nc_to_eb": "edge_nc_to_c edge_c_to_d edge_d_to_east",
    "route_sc_to_eb": "edge_sc_to_c edge_c_to_d edge_d_to_east",
}

# Scenario Base Flow Rates (veh/hour across all routes)
SCENARIO_CONFIGS = {
    "free_flow": {
        "description": "Low traffic volume, free-flow speeds, zero signal queue spillback",
        "total_hourly_rate": 1800,
        "arterial_eb_weight": 0.35,
        "arterial_wb_weight": 0.30,
        "cross_street_weight": 0.35,
    },
    "normal": {
        "description": "Balanced urban traffic demand, standard signal queues",
        "total_hourly_rate": 3600,
        "arterial_eb_weight": 0.38,
        "arterial_wb_weight": 0.32,
        "cross_street_weight": 0.30,
    },
    "peak": {
        "description": "Peak hour high congestion, dense queues on Oak-5th Avenue",
        "total_hourly_rate": 6200,
        "arterial_eb_weight": 0.42,
        "arterial_wb_weight": 0.33,
        "cross_street_weight": 0.25,
    },
    "spillback": {
        "description": "Extreme traffic surge, queue spillback across nodes B-C-D",
        "total_hourly_rate": 8500,
        "arterial_eb_weight": 0.45,
        "arterial_wb_weight": 0.35,
        "cross_street_weight": 0.20,
    },
}


def sample_vtype(rng: random.Random, mix: dict[str, float]) -> str:
    """Sample a vehicle type based on probability distribution."""
    r = rng.random()
    cumulative = 0.0
    for vtype, prob in mix.items():
        cumulative += prob
        if r <= cumulative:
            return vtype
    return "motorcycle"


def generate_demand(
    scenario: str = "normal",
    duration: float = 300.0,
    seed: int = 42,
    output_path: Path | None = None,
    mix: dict[str, float] | None = None,
) -> Path:
    """
    Generate deterministic SUMO route XML (.rou.xml) for a given scenario.
    """
    if scenario not in SCENARIO_CONFIGS:
        raise ValueError(
            f"Unknown scenario: {scenario}. Choose from {list(SCENARIO_CONFIGS.keys())}"
        )

    config = SCENARIO_CONFIGS[scenario]
    active_mix = mix or DEFAULT_MIX
    rng = random.Random(seed)

    root = ET.Element("routes")

    # 1. Embed Vehicle Types
    for vt in VTYPES:
        ET.SubElement(root, "vType", **vt)

    # 2. Embed Standard Routes
    for rid, edges in ROUTE_TEMPLATES.items():
        ET.SubElement(root, "route", id=rid, edges=edges)

    # 3. Compute Route Flow Weights
    route_weights: dict[str, float] = {}
    eb_weight = config["arterial_eb_weight"]
    wb_weight = config["arterial_wb_weight"]
    cross_weight = config["cross_street_weight"]

    # Through arterial corridor
    route_weights["route_eb_through"] = eb_weight * 0.70
    route_weights["route_wb_through"] = wb_weight * 0.85

    # Cross street routes (divided among 8 cross flows)
    cross_flows = [
        "route_sb_a",
        "route_nb_a",
        "route_sb_b",
        "route_nb_b",
        "route_sb_c",
        "route_nb_c",
        "route_sb_d",
        "route_nb_d",
    ]
    for r in cross_flows:
        route_weights[r] = (cross_weight * 0.60) / len(cross_flows)

    # Turning into EB corridor
    feeder_turns = [
        "route_na_to_eb",
        "route_sa_to_eb",
        "route_nb_to_eb",
        "route_sb_to_eb",
        "route_nc_to_eb",
        "route_sc_to_eb",
    ]
    for r in feeder_turns:
        route_weights[r] = (eb_weight * 0.30 + cross_weight * 0.40) / len(feeder_turns)

    # Normalize weights
    total_w = sum(route_weights.values())
    route_weights = {k: v / total_w for k, v in route_weights.items()}

    # 4. Generate Vehicles across duration using Poisson arrival process
    total_hourly = config["total_hourly_rate"]
    total_rate_per_sec = total_hourly / 3600.0

    vehicles = []
    veh_counter = 0

    for route_id, w in route_weights.items():
        flow_rate_per_sec = total_rate_per_sec * w
        if flow_rate_per_sec <= 0:
            continue

        t = rng.expovariate(flow_rate_per_sec)
        while t < duration:
            vtype = sample_vtype(rng, active_mix)
            depart_speed = "max"
            depart_lane = "best"
            # Motorcycles can start on arbitrary lateral sublanes
            depart_pos_lat = f"{rng.uniform(-1.0, 1.0):.2f}" if vtype == "motorcycle" else "0.0"

            vehicles.append(
                {
                    "id": f"veh_{scenario}_{veh_counter:05d}",
                    "type": vtype,
                    "route": route_id,
                    "depart": f"{t:.2f}",
                    "departSpeed": depart_speed,
                    "departLane": depart_lane,
                    "departPosLat": depart_pos_lat,
                }
            )
            veh_counter += 1
            t += rng.expovariate(flow_rate_per_sec)

    # Sort vehicles chronologically by departure time
    vehicles.sort(key=lambda v: float(v["depart"]))

    # Add vehicles to XML root
    for v in vehicles:
        ET.SubElement(root, "vehicle", **v)

    # Format and save
    if output_path is None:
        output_path = SCENARIOS_DIR / f"corridor_{scenario}.rou.xml"

    rough = ET.tostring(root, "utf-8")
    reparsed = minidom.parseString(rough)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(reparsed.toprettyxml(indent="    "))

    print(
        f"Generated {output_path.name}: {len(vehicles)} vehicles over {duration:.0f}s (Seed: {seed})"
    )
    return output_path


def generate_all_presets(duration: float = 300.0, seed: int = 42) -> list[Path]:
    """Generate all 4 standard scenario route presets."""
    generated = []
    for scn in SCENARIO_CONFIGS:
        out = SCENARIOS_DIR / f"corridor_{scn}.rou.xml"
        path = generate_demand(scenario=scn, duration=duration, seed=seed, output_path=out)
        generated.append(path)
    return generated


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic traffic demand for ClearWayAI corridor."
    )
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIO_CONFIGS.keys()),
        default=None,
        help="Scenario to generate",
    )
    parser.add_argument(
        "--all", action="store_true", help="Generate all 4 standard scenario presets"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=300.0,
        help="Simulation duration in seconds (default: 300s)",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for deterministic generation"
    )
    parser.add_argument("--output", type=str, default=None, help="Output .rou.xml path")
    args = parser.parse_args()

    print("=" * 70)
    print("🚦 ClearWayAI - Synthetic Traffic Demand Generator (Vietnamese Mix)")
    print("=" * 70)

    if args.all or args.scenario is None:
        paths = generate_all_presets(duration=args.duration, seed=args.seed)
        print(f"🎉 Generated {len(paths)} scenario route files successfully!")
    else:
        out = Path(args.output) if args.output else None
        generate_demand(
            scenario=args.scenario, duration=args.duration, seed=args.seed, output_path=out
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
