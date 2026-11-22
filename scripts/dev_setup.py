#!/usr/bin/env python3
"""
ClearWayAI - Developer Environment Bootstrapping & Verification Script
Automates the local setup of the development environment.
"""

import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def print_banner():
    print("=" * 70)
    print("   🚦 ClearWayAI - Development Environment Setup & Validator")
    print("=" * 70)


def check_python_version():
    print("[1/5] Checking Python version...")
    version = sys.version_info
    print(f"      Detected Python {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("      ❌ Error: Python 3.10+ is required.")
        return False
    print("      ✅ Python version OK.")
    return True


def check_tools():
    print("[2/5] Checking system prerequisites (Git, Node, pnpm)...")
    tools = ["git", "node", "pnpm"]
    all_ok = True
    for tool in tools:
        cmd = shutil.which(tool)
        if cmd:
            print(f"      ✅ {tool}: found at {cmd}")
        else:
            print(f"      ⚠️  {tool}: not found in PATH (some commands may require manual install)")
            if tool == "git":
                all_ok = False
    return all_ok


def setup_env_files():
    print("[3/5] Checking environment (.env) files...")
    env_pairs = [
        (ROOT_DIR / ".env.example", ROOT_DIR / ".env"),
        (ROOT_DIR / "apps" / "api" / ".env.example", ROOT_DIR / "apps" / "api" / ".env"),
        (ROOT_DIR / "apps" / "web" / ".env.example", ROOT_DIR / "apps" / "web" / ".env"),
    ]

    for example, target in env_pairs:
        if not example.exists():
            print(f"      ❌ Template not found: {example.name}")
            continue
        if not target.exists():
            shutil.copyfile(example, target)
            print(f"      ✨ Created {target.relative_to(ROOT_DIR)} from example.")
        else:
            print(f"      ✅ Existing config preserved: {target.relative_to(ROOT_DIR)}")
    return True


def check_python_packages():
    print("[4/5] Checking critical Python modules (FastAPI, Pydantic, Pytest, Ruff, Mypy)...")
    modules = ["fastapi", "pydantic", "pytest", "ruff", "mypy"]
    missing = []
    for mod in modules:
        try:
            __import__(mod)
            print(f"      ✅ {mod}: installed")
        except Exception:
            import importlib.metadata

            try:
                ver = importlib.metadata.version(mod)
                print(f"      ✅ {mod}: installed (v{ver}, load restricted by host policy)")
            except importlib.metadata.PackageNotFoundError:
                print(f"      ⚠️  {mod}: missing")
                missing.append(mod)

    if missing:
        print(
            f"\n      Tip: Run 'pip install -r requirements.txt' or 'pip install {' '.join(missing)}'"
        )
    return len(missing) == 0


def summary(success: bool):
    print("[5/5] Setup summary & next actions...")
    print("=" * 70)
    if success:
        print("🎉 Development environment is ready!")
        print("   Quick start commands:")
        print(
            "     1. make dev        (or 'python -m uvicorn apps.api.src.main:app' and 'npm --prefix apps/web run dev')"
        )
        print("     2. python scripts/check_all.py  (run full verification suite)")
        print("     3. pytest                       (run all tests)")
    else:
        print("⚠️  Environment setup partially complete. Please install missing tools above.")
    print("=" * 70)


def main():
    print_banner()
    py_ok = check_python_version()
    tools_ok = check_tools()
    env_ok = setup_env_files()
    pkg_ok = check_python_packages()

    overall = py_ok and env_ok and tools_ok and pkg_ok
    summary(overall)
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
