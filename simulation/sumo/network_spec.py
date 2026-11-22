"""
ClearWayAI - SUMO Corridor Network Specification
Defines geometric constants, node positions, edge IDs, traffic light phase mappings,
and detector layouts for the 4-intersection Oak-5th arterial corridor (Nodes A-D).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class NodeDefinition:
    node_id: str
    x: float
    y: float
    node_type: str = "traffic_light"
    description: str = ""


@dataclass(frozen=True)
class EdgeDefinition:
    edge_id: str
    from_node: str
    to_node: str
    num_lanes: int
    speed_mps: float
    width: float = 3.2
    is_arterial: bool = False


# Primary Corridor Intersections (A -> D)
INTERSECTIONS: dict[str, NodeDefinition] = {
    "node_a": NodeDefinition(
        node_id="node_a",
        x=0.0,
        y=0.0,
        node_type="traffic_light",
        description="Intersection A - West Corridor Entry / Feeder Gate",
    ),
    "node_b": NodeDefinition(
        node_id="node_b",
        x=300.0,
        y=0.0,
        node_type="traffic_light",
        description="Intersection B - Mid-West Junction & Transit Crossing",
    ),
    "node_c": NodeDefinition(
        node_id="node_c",
        x=600.0,
        y=0.0,
        node_type="traffic_light",
        description="Intersection C - Oak & 5th Avenue (Digital Twin Primary Anchor)",
    ),
    "node_d": NodeDefinition(
        node_id="node_d",
        x=900.0,
        y=0.0,
        node_type="traffic_light",
        description="Intersection D - East Junction / Metropolitan Hospital Access",
    ),
}

# Boundary Feeder Nodes
FEEDER_NODES: dict[str, NodeDefinition] = {
    "node_west_in": NodeDefinition("node_west_in", -200.0, 0.0, "priority", "West Corridor Inflow"),
    "node_west_out": NodeDefinition(
        "node_west_out", -200.0, 0.0, "priority", "West Corridor Outflow"
    ),
    "node_east_in": NodeDefinition("node_east_in", 1100.0, 0.0, "priority", "East Corridor Inflow"),
    "node_east_out": NodeDefinition(
        "node_east_out", 1100.0, 0.0, "priority", "East Corridor Outflow"
    ),
    # North cross-street boundary nodes
    "node_na_in": NodeDefinition("node_na_in", 0.0, 200.0, "priority", "North Approach A Inflow"),
    "node_nb_in": NodeDefinition("node_nb_in", 300.0, 200.0, "priority", "North Approach B Inflow"),
    "node_nc_in": NodeDefinition("node_nc_in", 600.0, 200.0, "priority", "North Approach C Inflow"),
    "node_nd_in": NodeDefinition("node_nd_in", 900.0, 200.0, "priority", "North Approach D Inflow"),
    # South cross-street boundary nodes
    "node_sa_in": NodeDefinition("node_sa_in", 0.0, -200.0, "priority", "South Approach A Inflow"),
    "node_sb_in": NodeDefinition(
        "node_sb_in", 300.0, -200.0, "priority", "South Approach B Inflow"
    ),
    "node_sc_in": NodeDefinition(
        "node_sc_in", 600.0, -200.0, "priority", "South Approach C Inflow"
    ),
    "node_sd_in": NodeDefinition(
        "node_sd_in", 900.0, -200.0, "priority", "South Approach D Inflow"
    ),
}

# Arterial Corridor Segments (Eastbound / Westbound)
CORRIDOR_EDGES: list[EdgeDefinition] = [
    # Eastbound (West -> East)
    EdgeDefinition(
        "edge_west_to_a", "node_west_in", "node_a", num_lanes=3, speed_mps=16.67, is_arterial=True
    ),
    EdgeDefinition(
        "edge_a_to_b", "node_a", "node_b", num_lanes=3, speed_mps=16.67, is_arterial=True
    ),
    EdgeDefinition(
        "edge_b_to_c", "node_b", "node_c", num_lanes=3, speed_mps=16.67, is_arterial=True
    ),
    EdgeDefinition(
        "edge_c_to_d", "node_c", "node_d", num_lanes=3, speed_mps=16.67, is_arterial=True
    ),
    EdgeDefinition(
        "edge_d_to_east", "node_d", "node_east_out", num_lanes=3, speed_mps=16.67, is_arterial=True
    ),
    # Westbound (East -> West)
    EdgeDefinition(
        "edge_east_to_d", "node_east_in", "node_d", num_lanes=3, speed_mps=16.67, is_arterial=True
    ),
    EdgeDefinition(
        "edge_d_to_c", "node_d", "node_c", num_lanes=3, speed_mps=16.67, is_arterial=True
    ),
    EdgeDefinition(
        "edge_c_to_b", "node_c", "node_b", num_lanes=3, speed_mps=16.67, is_arterial=True
    ),
    EdgeDefinition(
        "edge_b_to_a", "node_b", "node_a", num_lanes=3, speed_mps=16.67, is_arterial=True
    ),
    EdgeDefinition(
        "edge_a_to_west", "node_a", "node_west_out", num_lanes=3, speed_mps=16.67, is_arterial=True
    ),
]

# Physical Dimensions & Timing Constraints
LANE_WIDTH: float = 3.2  # meters
SUBLANE_RESOLUTION: float = 0.64  # meters (allows 5 sublanes per 3.2m lane)
STEP_LENGTH: float = 0.1  # seconds (10 Hz simulation tick)
CORRIDOR_LENGTH_METERS: float = 900.0  # node_a to node_d
TOTAL_NETWORK_LENGTH_METERS: float = 1300.0  # -200m to +1100m

# Standard Signal Timing Parameters
MIN_GREEN_SEC: float = 10.0
MAX_GREEN_SEC: float = 65.0
YELLOW_SEC: float = 4.0
ALL_RED_SEC: float = 2.0
NOMINAL_CYCLE_SEC: float = 72.0
