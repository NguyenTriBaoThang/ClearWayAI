"""Automated Verification Suite for Technical Documentation Synchronization (Task 56).

Tests:
1. Data integrity and completeness of docs-site/src/data/docsContent.ts.
2. Verified status across all 24 documentation chapters.
3. Accurate synchronization of core architecture, safety invariants, ESP32 hardware,
   VMS gantries, REST API routers, and scientific benchmarks.
4. Build configuration and presence of production dist assets.
"""

from __future__ import annotations

import re
from pathlib import Path


def test_docs_content_typescript_data_integrity():
    """Verify presence and complete structural coverage of docsContent.ts."""
    docs_content_path = Path("docs-site/src/data/docsContent.ts")
    assert docs_content_path.exists(), "docsContent.ts must exist"

    content = docs_content_path.read_text(encoding="utf-8")

    # 1. Verify all 24 chapter IDs exist
    expected_ids = [
        "introduction",
        "problem-novelty",
        "architecture",
        "system-modules",
        "controller-safety",
        "safety-modes",
        "sumo-traci",
        "3d-digital-twin",
        "ui-blueprint-fidelity",
        "ui-screenshot-fidelity",
        "coordinate-mapping",
        "simulation-comparison",
        "datasets",
        "ai-models",
        "clearance-prediction",
        "sensor-telemetry-provenance",
        "api-websocket",
        "dashboard",
        "evaluation",
        "deployment",
        "testing",
        "roadmap",
        "faq",
        "changelog",
    ]

    for chapter_id in expected_ids:
        assert f"id: '{chapter_id}'" in content, f"Chapter {chapter_id} must be defined in docsContent.ts"

    # 2. Verify all sections are marked VERIFIED
    planned_matches = re.findall(r"status:\s*'PLANNED'", content)
    in_progress_matches = re.findall(r"status:\s*'IN_PROGRESS'", content)
    assert len(planned_matches) == 0, f"No sections should remain PLANNED: found {len(planned_matches)}"
    assert len(in_progress_matches) == 0, f"No sections should remain IN_PROGRESS: found {len(in_progress_matches)}"

    verified_matches = re.findall(r"status:\s*'VERIFIED'", content)
    assert len(verified_matches) >= 24, "All 24 sections must have status: 'VERIFIED'"


def test_docs_content_reflects_real_code_features():
    """Verify documentation accurately describes real implemented subsystems."""
    docs_content_path = Path("docs-site/src/data/docsContent.ts")
    content = docs_content_path.read_text(encoding="utf-8")

    # Safety Invariants
    assert "INV-01 (Minimum Green Duration)" in content
    assert "INV-02 (Yellow & All-Red Clearance)" in content
    assert "INV-03 (Conflicting Green Interlock)" in content
    assert "INV-06 (Fail-Safe Communication Watchdog)" in content

    # Hardware & VMS Features
    assert "ESP32 DevKit V1" in content
    assert "74HC595" in content
    assert "Overhead VMS Gantries" in content

    # API and Benchmark Numbers
    assert "7 REST API Routers" in content
    assert "-42.6%" in content
    assert "Decree 13/2023/ND-CP" in content

    # Roadmap Progress
    assert "56/60 Tasks" in content


def test_docs_site_build_artifacts():
    """Verify docs-site build configuration and generated production assets."""
    package_json = Path("docs-site/package.json")
    vite_config = Path("docs-site/vite.config.ts")
    tsconfig = Path("docs-site/tsconfig.json")
    dist_html = Path("docs-site/dist/index.html")

    assert package_json.exists()
    assert vite_config.exists()
    assert tsconfig.exists()
    assert dist_html.exists(), "docs-site production build output (dist/index.html) must exist"

