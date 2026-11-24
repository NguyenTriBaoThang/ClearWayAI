"""Test suite verifying Docker configurations, production deployment readiness,
final release report dossier, release notes, and packaging manifest for v0.1.0-mvp (Task 58).
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_docker_compose_configurations():
    """Verify both development and production docker-compose YAML files are well-formed."""
    dev_compose_path = REPO_ROOT / "docker-compose.yml"
    prod_compose_path = REPO_ROOT / "docker-compose.prod.yml"

    assert dev_compose_path.exists(), "Missing docker-compose.yml"
    assert prod_compose_path.exists(), "Missing docker-compose.prod.yml"

    with open(dev_compose_path, encoding="utf-8") as f:
        dev_data = yaml.safe_load(f)

    with open(prod_compose_path, encoding="utf-8") as f:
        prod_data = yaml.safe_load(f)

    # Core services check
    for service_name in ["api", "web"]:
        assert service_name in dev_data["services"], (
            f"Service {service_name} missing from dev compose"
        )
        assert service_name in prod_data["services"], (
            f"Service {service_name} missing from prod compose"
        )

    # Production compose should define healthchecks, resource limits, and network
    api_prod = prod_data["services"]["api"]
    assert "healthcheck" in api_prod
    assert "deploy" in api_prod and "resources" in api_prod["deploy"]
    assert "networks" in prod_data and "clearway-net" in prod_data["networks"]


def test_dockerfiles_and_nginx_config():
    """Verify Dockerfiles and Nginx web server configuration."""
    api_dockerfile = REPO_ROOT / "apps" / "api" / "Dockerfile"
    web_dockerfile = REPO_ROOT / "apps" / "web" / "Dockerfile"
    nginx_conf = REPO_ROOT / "apps" / "web" / "nginx.conf"

    assert api_dockerfile.exists(), "Missing apps/api/Dockerfile"
    assert web_dockerfile.exists(), "Missing apps/web/Dockerfile"
    assert nginx_conf.exists(), "Missing apps/web/nginx.conf"

    api_content = api_dockerfile.read_text(encoding="utf-8")
    assert "COPY apps/api" in api_content
    assert "COPY controller" in api_content
    assert "COPY ai" in api_content
    assert "COPY simulation" in api_content

    web_content = web_dockerfile.read_text(encoding="utf-8")
    assert "FROM node" in web_content
    assert "FROM nginx" in web_content

    nginx_content = nginx_conf.read_text(encoding="utf-8")
    assert "listen 3000;" in nginx_content
    assert "try_files $uri $uri/ /index.html;" in nginx_content
    assert "gzip on;" in nginx_content


def test_final_release_report_completeness():
    """Verify that docs/FINAL_RELEASE_REPORT.md exists and covers all required sections."""
    report_path = REPO_ROOT / "docs" / "FINAL_RELEASE_REPORT.md"
    assert report_path.exists(), "Missing docs/FINAL_RELEASE_REPORT.md"

    content = report_path.read_text(encoding="utf-8")
    lines = content.strip().splitlines()
    assert len(lines) >= 150, f"Report is too brief: {len(lines)} lines"

    # Check key sections
    assert "Executive Summary" in content
    assert "Kiến trúc Hệ thống" in content or "Architecture" in content
    assert "JIT Pre-Clearance" in content or "Pre-clearance" in content
    assert "Sublane Model" in content
    assert "Signal Safety Gateway" in content
    assert "Kết quả Thực nghiệm Khoa học" in content or "Benchmarks" in content
    assert "B0" in content and "B1" in content and "B2" in content
    assert "Nghị định 13/2023/ND-CP" in content
    assert "docker-compose" in content
    assert "PITCH_DECK.md" in content and "DEFENSE_QA.md" in content


def test_release_notes_integrity():
    """Verify that RELEASE_NOTES_v0.1.0-mvp.md exists and contains accurate release metadata."""
    notes_path = REPO_ROOT / "RELEASE_NOTES_v0.1.0-mvp.md"
    assert notes_path.exists(), "Missing RELEASE_NOTES_v0.1.0-mvp.md"

    content = notes_path.read_text(encoding="utf-8")
    assert "v0.1.0-mvp" in content
    assert "Subsystem Breakdown" in content
    assert "Scientific Benchmark Summary" in content
    assert "Quickstart & Production Deployment" in content
    assert "-42.6%" in content


def test_packaging_script_and_manifest_generation():
    """Execute packaging script and verify output release_manifest.json."""
    from scripts.package_release import (
        CORE_DELIVERABLES,
        generate_release_manifest,
        verify_deliverables,
    )

    manifest_entries = verify_deliverables()
    assert len(manifest_entries) == len(CORE_DELIVERABLES)
    assert len(manifest_entries) >= 20

    test_manifest_path = REPO_ROOT / "release_manifest.json"
    manifest_data = generate_release_manifest(manifest_entries, test_manifest_path)

    assert manifest_data["release_version"] == "v0.1.0-mvp"
    assert manifest_data["verified_tasks"] in ["58/60", "60/60"]
    assert manifest_data["completion_ratio"] >= 0.96
    assert len(manifest_data["files"]) == len(CORE_DELIVERABLES)

    for _rel_path, meta in manifest_data["files"].items():
        assert meta["size_bytes"] > 0
        assert len(meta["sha256"]) == 64  # valid SHA-256 hex string
