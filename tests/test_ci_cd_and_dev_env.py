"""
Test Suite for Task 22: CI/CD, Linting, Testing, and Development Environment Setup
Verifies:
1. GitHub Actions CI/CD workflows (.github/workflows/ci.yml, nightly-benchmark.yml)
2. Pre-commit hooks configuration (.pre-commit-config.yaml)
3. Pyproject tool configurations (Ruff, Mypy, Pytest)
4. Environment variable templates (.env.example in root, apps/api, apps/web)
5. Developer scripts and documentation (scripts/dev_setup.py, scripts/check_all.py, Makefile)
6. Ruff linting execution compliance
"""

import os
import subprocess
import sys

import yaml

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_github_ci_workflow():
    """Verify primary CI workflow exists, is valid YAML, and contains all required jobs."""
    ci_path = os.path.join(REPO_ROOT, ".github", "workflows", "ci.yml")
    assert os.path.isfile(ci_path), f"ci.yml not found at {ci_path}"

    with open(ci_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "name" in data
    triggers = data.get("on") or data.get(True)
    assert triggers is not None
    assert "push" in triggers
    assert "pull_request" in triggers
    assert "workflow_dispatch" in triggers

    jobs = data.get("jobs", {})
    required_jobs = [
        "backend-lint",
        "backend-typecheck",
        "backend-test",
        "frontend-check",
        "safety-invariants-gate",
        "security-audit",
    ]
    for job in required_jobs:
        assert job in jobs, f"Required CI job '{job}' is missing from ci.yml"

    # Verify python matrix test
    test_job = jobs["backend-test"]
    matrix = test_job.get("strategy", {}).get("matrix", {})
    python_versions = matrix.get("python-version", [])
    assert "3.10" in python_versions or "3.11" in python_versions


def test_github_nightly_benchmark_workflow():
    """Verify nightly benchmark workflow exists with valid cron and dispatch triggers."""
    bm_path = os.path.join(REPO_ROOT, ".github", "workflows", "nightly-benchmark.yml")
    assert os.path.isfile(bm_path), f"nightly-benchmark.yml not found at {bm_path}"

    with open(bm_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    triggers = data.get("on") or data.get(True)
    assert triggers is not None
    assert "schedule" in triggers
    assert "workflow_dispatch" in triggers
    assert "jobs" in data
    assert "benchmark" in data["jobs"]


def test_pre_commit_configuration():
    """Verify .pre-commit-config.yaml contains required hygiene and lint hooks."""
    config_path = os.path.join(REPO_ROOT, ".pre-commit-config.yaml")
    assert os.path.isfile(config_path), ".pre-commit-config.yaml not found"

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert "repos" in data
    repo_urls = [r.get("repo", "") for r in data["repos"]]
    assert any("pre-commit-hooks" in url for url in repo_urls)
    assert any("ruff-pre-commit" in url for url in repo_urls)

    hook_ids = []
    for r in data["repos"]:
        for h in r.get("hooks", []):
            hook_ids.append(h.get("id"))

    assert "trailing-whitespace" in hook_ids
    assert "end-of-file-fixer" in hook_ids
    assert "check-yaml" in hook_ids
    assert "check-json" in hook_ids
    assert "detect-private-key" in hook_ids


def test_pyproject_toml_configuration():
    """Verify pyproject.toml contains ruff, mypy, and pytest configuration blocks."""
    pyproject_path = os.path.join(REPO_ROOT, "pyproject.toml")
    assert os.path.isfile(pyproject_path)

    with open(pyproject_path, encoding="utf-8") as f:
        content = f.read()

    assert "[tool.ruff]" in content
    assert "[tool.ruff.lint]" in content
    assert "[tool.mypy]" in content
    assert "[tool.pytest.ini_options]" in content
    assert "line-length" in content
    assert "testpaths" in content


def test_environment_variable_templates():
    """Verify .env.example files exist across root, api, and web with safety defaults."""
    root_env = os.path.join(REPO_ROOT, ".env.example")
    api_env = os.path.join(REPO_ROOT, "apps", "api", ".env.example")
    web_env = os.path.join(REPO_ROOT, "apps", "web", ".env.example")

    assert os.path.isfile(root_env), "Root .env.example missing"
    assert os.path.isfile(api_env), "apps/api/.env.example missing"
    assert os.path.isfile(web_env), "apps/web/.env.example missing"

    with open(root_env, encoding="utf-8") as f:
        root_content = f.read()
    assert "SAFETY_MODE=SIMULATION" in root_content
    assert "SIMULATION_ONLY=true" in root_content

    with open(api_env, encoding="utf-8") as f:
        api_content = f.read()
    assert "SAFETY_MODE=SIMULATION" in api_content
    assert "API_PORT=8000" in api_content

    with open(web_env, encoding="utf-8") as f:
        web_content = f.read()
    assert "VITE_API_BASE_URL" in web_content


def test_developer_tooling_and_scripts():
    """Verify dev_setup.py, check_all.py, verify_markdown_links.py and Makefile exist."""
    assert os.path.isfile(os.path.join(REPO_ROOT, "scripts", "dev_setup.py"))
    assert os.path.isfile(os.path.join(REPO_ROOT, "scripts", "check_all.py"))
    assert os.path.isfile(os.path.join(REPO_ROOT, "scripts", "verify_markdown_links.py"))
    assert os.path.isfile(os.path.join(REPO_ROOT, "Makefile"))
    assert os.path.isfile(os.path.join(REPO_ROOT, "docs", "DEVELOPMENT_ENVIRONMENT.md"))


def test_ruff_linter_zero_errors():
    """Run ruff linter and verify 0 errors across the codebase."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "."],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Ruff reported errors:\n{result.stdout}\n{result.stderr}"
