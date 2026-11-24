# ClearWayAI Automation & Developer Scripts (`scripts`)

> **Monorepo Quality Gates, Link Verification, Visual Fidelity Audit, and Bootstrap Scripts**

[![Scripts: Python 3](https://img.shields.io/badge/Scripts-Python%203%20%7C%20PowerShell%20%7C%20Bash-blue.svg)](check_all.py)
[![Gates: 5 Passed](https://img.shields.io/badge/Quality%20Gates-5%2F5-brightgreen.svg)](check_all.py)

---

## 1. Directory Structure

```
scripts/
├── check_all.py                     # Primary Monorepo 5-Gate Quality Checker (Task 52)
├── verify_markdown_links.py         # Zero-broken internal relative link validator (Task 57)
├── package_release.py               # Release packaging & SHA-256 manifest generator (Task 58)
├── audit_visual_fidelity_and_fps.py # Visual fidelity, WebGL canvas, and 60 FPS auditor (Task 51)
├── prepare_demo.py                  # Preloader for verified scenarios and demonstration fixtures
├── bootstrap.ps1                    # Windows PowerShell automated setup and dependency installer
├── bootstrap.sh                     # Linux/macOS Bash automated setup and dependency installer
└── README.md
```

---

## 2. Utility Scripts Documentation

### 2.1 Monorepo Quality Checker (`check_all.py`)
Executes all 5 verification gates in sequence to guarantee zero regression before pushing to git:
1. `ruff check .` (Python code style & linting)
2. `pytest` (Complete unit, integration, and safety test suites)
3. `pnpm --filter @clearway/shared build` (Shared TypeScript packages)
4. `pnpm --filter clearway-web build` (Operations Center frontend bundle)
5. `pnpm --filter clearway-docs-site build` (Documentation site bundle)

```bash
python scripts/check_all.py
```

---

### 2.2 Markdown Link Validator (`verify_markdown_links.py`)
Scans all 55+ repository markdown files, extracts internal relative markdown links (`[text](...)`), resolves them against the filesystem, and flags any broken references.

```bash
python scripts/verify_markdown_links.py
```

---

### 2.3 Release Packaging & Integrity Manifest (`package_release.py`)
Validates that all core deliverables and documentation artifacts exist, calculates their SHA-256 cryptographic hashes, and generates `release_manifest.json` for formal release distribution and competition submissions.

```bash
python scripts/package_release.py
python scripts/package_release.py --create-archive
```

---

### 2.4 Visual Fidelity & FPS Auditor (`audit_visual_fidelity_and_fps.py`)
Audits the Three.js 3D Digital Twin and web operations dashboard for:
- Genuine WebGL canvas initialization (rejects static image placeholders).
- 60 FPS frame render budget validation ($\le 16.6\text{ ms}$ render time).
- Cyber Grid dark-mode color palette adherence (Navy `#0a1128`, Cyan `#00f2fe`, Amber `#f59e0b`, Crimson `#ef4444`).
- Instanced mesh rendering and overhead VMS gantry geometry.

```bash
python scripts/audit_visual_fidelity_and_fps.py
```

---

### 2.4 Scenario & Demo Preloader (`prepare_demo.py`)
Copies pre-verified scenario network files, demand configurations, and seed fixtures (`DEMO_FIXTURE`) into their target runtime locations:

```bash
python scripts/prepare_demo.py
```

---

### 2.5 Cross-Platform Environment Bootstrap (`bootstrap.ps1` / `bootstrap.sh`)
Verifies prerequisites (Python 3.10+, Node.js 18+, pnpm), creates virtual environments, installs dependencies, copies `.env.example` $\to$ `.env`, and runs initial smoke tests.

```powershell
# Windows PowerShell
.\scripts\bootstrap.ps1
```

```bash
# Linux / macOS
chmod +x ./scripts/bootstrap.sh
./scripts/bootstrap.sh
```
