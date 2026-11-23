"""
ClearWayAI - Automated Test Suite for Task 53: Variable Message Sign (VMS) Advisory System.

Verifies:
1. VMS gantry topology and coordinates spanning the 4 arterial intersections (A–D).
2. VMSManager advisory state evaluation across Nominal, Pre-clearance, Emergency Corridor, and Recovery.
3. Bilingual Vietnamese / English advisory message formatting and safety compliance.
4. FastAPI REST API endpoints (/api/v1/corridor/vms and /api/v1/corridor/vms/{node_id}).
5. 3D Digital Twin VMSOverheadGantryMesh structure, dynamic canvas texture, and CorridorCityEnvironment integration.
6. Operations dashboard VMSAdvisoryCard UI component.
"""

from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.src.main import app
from controller.vms.vms_manager import (
    VMS_GANTRY_TOPOLOGY,
    VMSAdvisoryMode,
    VMSManager,
)

client = TestClient(app)


def test_vms_gantry_topology_and_coordinates():
    """Verify standard placement of 4 overhead gantries ahead of intersections A-D."""
    assert len(VMS_GANTRY_TOPOLOGY) == 4
    for nid in ["node_a", "node_b", "node_c", "node_d"]:
        assert nid in VMS_GANTRY_TOPOLOGY

    gantry_a = VMS_GANTRY_TOPOLOGY["node_a"]
    assert gantry_a["board_id"] == "VMS-A"
    assert gantry_a["gantry_x_m"] == -80.0
    assert gantry_a["target_stopline_x"] == 0.0

    gantry_b = VMS_GANTRY_TOPOLOGY["node_b"]
    assert gantry_b["board_id"] == "VMS-B"
    assert gantry_b["gantry_x_m"] == 170.0
    assert gantry_b["target_stopline_x"] == 250.0

    gantry_c = VMS_GANTRY_TOPOLOGY["node_c"]
    assert gantry_c["board_id"] == "VMS-C"
    assert gantry_c["gantry_x_m"] == 420.0
    assert gantry_c["target_stopline_x"] == 500.0

    gantry_d = VMS_GANTRY_TOPOLOGY["node_d"]
    assert gantry_d["board_id"] == "VMS-D"
    assert gantry_d["gantry_x_m"] == 670.0
    assert gantry_d["target_stopline_x"] == 750.0


def test_vms_manager_nominal_evaluation():
    """Verify all gantries show nominal advisory when no emergency mission is active."""
    mgr = VMSManager()
    corridor_status = mgr.evaluate_corridor(
        ev_active=False,
        ev_x=None,
        sim_time=10.0,
    )
    assert corridor_status.active_emergency is False
    assert corridor_status.corridor_status == "NOMINAL_TRAFFIC"
    assert len(corridor_status.boards) == 4

    for board in corridor_status.boards.values():
        assert board.mode == VMSAdvisoryMode.NOMINAL
        assert board.recommended_speed_kmh == 50
        assert board.flashing_strobe is False
        assert board.chevron_direction == "NONE"
        assert "BÌNH AN" in board.message_line_1_vi
        assert "50 KM/H" in board.message_line_2_en


def test_vms_manager_emergency_corridor_evaluation():
    """Verify spatial progression triggers EMERGENCY_CORRIDOR, PRE_CLEARANCE, and NOMINAL."""
    mgr = VMSManager()
    # Ambulance approaching Node A at x = -100m (Node A stopline x = 0m, dist = 100m)
    corridor_status = mgr.evaluate_corridor(
        ev_active=True,
        ev_x=-100.0,
        ev_speed_mps=18.5,
        ev_id="AMB-339",
        sim_time=20.0,
    )
    assert corridor_status.active_emergency is True
    assert corridor_status.corridor_status == "EMERGENCY_CORRIDOR_ACTIVE"
    assert corridor_status.emergency_vehicle_id == "AMB-339"

    # Node A: dist = 100m <= 180m -> EMERGENCY_CORRIDOR
    board_a = corridor_status.boards["node_a"]
    assert board_a.mode == VMSAdvisoryMode.EMERGENCY_CORRIDOR
    assert board_a.recommended_speed_kmh == 30
    assert board_a.flashing_strobe is True
    assert board_a.chevron_direction == "RIGHT"
    assert "CẤP CỨU" in board_a.message_line_1_vi
    assert "AMB-339" in board_a.message_line_2_en

    # Node B: dist = 250 - (-100) = 350m (180m < dist <= 450m) -> PRE_CLEARANCE
    board_b = corridor_status.boards["node_b"]
    assert board_b.mode == VMSAdvisoryMode.PRE_CLEARANCE
    assert board_b.recommended_speed_kmh == 40
    assert board_b.flashing_strobe is True
    assert "GIẢI TỎA" in board_b.message_line_1_vi

    # Node D: dist = 750 - (-100) = 850m (> 450m) -> NOMINAL
    board_d = corridor_status.boards["node_d"]
    assert board_d.mode == VMSAdvisoryMode.NOMINAL
    assert board_d.recommended_speed_kmh == 50
    assert board_d.flashing_strobe is False


def test_vms_manager_caution_recovery_evaluation():
    """Verify EV clearing an intersection initiates CAUTION_RECOVERY on that gantry."""
    mgr = VMSManager()
    # Ambulance at x = 30m (Node A stopline x = 0m -> dist = -30m)
    board_a = mgr.evaluate_board(
        node_id="node_a",
        ev_active=True,
        ev_x=30.0,
        sim_time=30.0,
    )
    assert board_a.mode == VMSAdvisoryMode.CAUTION_RECOVERY
    assert board_a.recommended_speed_kmh == 40
    assert board_a.flashing_strobe is False
    assert "ĐIỀU TIẾT" in board_a.message_line_1_vi


def test_vms_fastapi_endpoints():
    """Verify GET /api/v1/corridor/vms and /api/v1/corridor/vms/{node_id}."""
    # 1. Full corridor VMS endpoint
    res_corridor = client.get("/api/v1/corridor/vms?sim_time=15.0")
    assert res_corridor.status_code == 200
    data_c = res_corridor.json()
    assert "boards" in data_c
    assert "node_a" in data_c["boards"]
    assert "node_d" in data_c["boards"]
    assert data_c["provenance"] == "CLEARWAY_VMS_ADVISORY"

    # 2. Single board endpoint
    res_node_a = client.get("/api/v1/corridor/vms/node_a?sim_time=15.0")
    assert res_node_a.status_code == 200
    data_a = res_node_a.json()
    assert data_a["board_id"] == "VMS-A"
    assert data_a["node_id"] == "node_a"
    assert data_a["gantry_x_m"] == -80.0

    # 3. Unknown node 404
    res_unknown = client.get("/api/v1/corridor/vms/unknown_node")
    assert res_unknown.status_code == 404


def test_vms_3d_modules_exist_and_structure():
    """Verify TypeScript/React 3D digital twin VMS mesh and operations card exist."""
    repo_root = Path(__file__).resolve().parent.parent
    twin_dir = repo_root / "apps" / "web" / "src" / "features" / "digital-twin"
    ops_dir = repo_root / "apps" / "web" / "src" / "features" / "operations"

    # 1. VMSOverheadGantryMesh.ts
    gantry_file = twin_dir / "VMSOverheadGantryMesh.ts"
    assert gantry_file.is_file()
    with open(gantry_file, encoding="utf-8") as f:
        src = f.read()
    assert "VMSOverheadGantryMesh" in src
    assert "buildGantryStructure" in src
    assert "drawCanvasAdvisory" in src
    assert "updateAdvisory" in src
    assert "dispose" in src

    # 2. CorridorCityEnvironment.ts integration
    env_file = twin_dir / "CorridorCityEnvironment.ts"
    assert env_file.is_file()
    with open(env_file, encoding="utf-8") as f:
        env_src = f.read()
    assert "vmsGantriesGroup" in env_src
    assert "buildVMSGantries" in env_src
    assert "updateVMS" in env_src

    # 3. VMSAdvisoryCard.tsx
    card_file = ops_dir / "VMSAdvisoryCard.tsx"
    assert card_file.is_file()
    with open(card_file, encoding="utf-8") as f:
        card_src = f.read()
    assert "VMSAdvisoryCard" in card_src
    assert "VMS-A" in card_src
    assert "VMS-D" in card_src

