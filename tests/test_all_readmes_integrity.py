"""Test suite verifying the existence, content structure, and internal link integrity
across all 19 project-owned README files in the ClearWayAI monorepo (Task 57).
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

PROJECT_OWNED_READMES = [
    "README.md",
    "ai/README.md",
    "apps/api/README.md",
    "apps/web/README.md",
    "controller/README.md",
    "data/README.md",
    "docs/adr/README.md",
    "docs-site/README.md",
    "hardware/README.md",
    "models/README.md",
    "notebooks/README.md",
    "packages/shared/README.md",
    "scripts/README.md",
    "simulation/README.md",
    "simulation/baselines/README.md",
    "simulation/scenarios/README.md",
    "simulation/sumo/README.md",
    "simulation/traci/README.md",
    "tests/README.md",
]


def test_all_19_readmes_exist():
    """Assert all 19 expected project-owned README.md files exist and are non-empty."""
    assert len(PROJECT_OWNED_READMES) == 19
    for rel_path in PROJECT_OWNED_READMES:
        full_path = REPO_ROOT / rel_path
        assert full_path.exists(), f"Missing README file: {rel_path}"
        assert full_path.is_file(), f"Path is not a regular file: {rel_path}"
        assert full_path.stat().st_size > 50, f"README is unexpectedly short/empty: {rel_path}"


def test_root_readme_content_integrity():
    """Verify that root README.md contains badges, architecture, tech stack, and benchmarks."""
    readme_path = REPO_ROOT / "README.md"
    content = readme_path.read_text(encoding="utf-8")

    # Title & Branding
    assert "ClearWay AI" in content or "ClearWayAI" in content
    assert "3D Digital Twin" in content

    # Status Badge
    assert "Verified" in content

    # Architecture Mermaid
    assert "```mermaid" in content
    assert "flowchart TD" in content

    # Key Subsystems
    assert "Signal Safety Gateway" in content
    assert "VMS" in content or "Variable Message Signs" in content
    assert "ESP32" in content

    # Scientific Benchmarks
    assert "B0" in content and "B1" in content and "B2" in content
    assert "INV-01" in content


def test_module_readmes_content_integrity():
    """Verify key module READMEs contain proper titles, architectural context, and keywords."""
    # 1. Hardware README
    hw_readme = (REPO_ROOT / "hardware" / "README.md").read_text(encoding="utf-8")
    assert "ESP32" in hw_readme
    assert "74HC595" in hw_readme
    assert "clearway_esp32_firmware.ino" in hw_readme
    assert "INV-01" in hw_readme and "INV-06" in hw_readme

    # 2. Apps API README
    api_readme = (REPO_ROOT / "apps" / "api" / "README.md").read_text(encoding="utf-8")
    assert "/api/v1/hardware" in api_readme
    assert "/api/v1/corridor/vms" in api_readme
    assert "hardware.py" in api_readme

    # 3. Apps Web README
    web_readme = (REPO_ROOT / "apps" / "web" / "README.md").read_text(encoding="utf-8")
    assert "Three.js" in web_readme
    assert "VMS" in web_readme or "VMSOverheadGantryMesh" in web_readme
    assert "DecisionAuditDrawer" in web_readme

    # 4. Controller README
    ctrl_readme = (REPO_ROOT / "controller" / "README.md").read_text(encoding="utf-8")
    assert "vms_manager" in ctrl_readme
    assert "esp32_bridge" in ctrl_readme
    assert "INV-01" in ctrl_readme and "INV-06" in ctrl_readme

    # 5. Simulation README
    sim_readme = (REPO_ROOT / "simulation" / "README.md").read_text(encoding="utf-8")
    assert "baselines" in sim_readme
    assert "scientific_evaluator" in sim_readme
    assert "demo_scenario_runner" in sim_readme

    # 6. Tests README
    test_readme = (REPO_ROOT / "tests" / "README.md").read_text(encoding="utf-8")
    assert "pytest" in test_readme
    assert "check_all.py" in test_readme
    assert "INV-01" in test_readme

    # 7. Scripts README
    scripts_readme = (REPO_ROOT / "scripts" / "README.md").read_text(encoding="utf-8")
    assert "check_all.py" in scripts_readme
    assert "verify_markdown_links.py" in scripts_readme


def test_markdown_relative_links_integrity():
    """Verify that verify_markdown_links.py succeeds with zero broken relative links."""
    from scripts.verify_markdown_links import check_markdown_links

    assert check_markdown_links() is True

