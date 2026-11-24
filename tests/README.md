# ClearWayAI Automated Testing Suite (`tests`)

> **Comprehensive Multi-Tier Test Suites, Safety Verification Assertions, and Monorepo Quality Gates**

[![Tests: Pytest](https://img.shields.io/badge/Test%20Runner-Pytest-blue.svg)](pyproject.toml)
[![Coverage: 100% Core Invariants](https://img.shields.io/badge/Safety%20Invariants-INV--01..06%20100%25-brightgreen.svg)](../docs/SAFETY_BOUNDARIES.md)
[![Quality Gate: 5/5](https://img.shields.io/badge/Quality%20Gate-5%2F5%20PASS-brightgreen.svg)](../scripts/check_all.py)

---

## 1. Directory Structure & Test Suite Inventory

```
tests/
├── test_api_smoke.py                 # Root API health, route enumeration, and metadata discovery
├── test_system_status.py             # System safety modes, provenance tags, and runtime flags
├── test_simulation_manager.py        # Microscopic simulation lifecycle (start, step, pause, stop)
├── test_telemetry_collector.py       # Spatial coordinate projection, queue metrics, and speed tracking
├── test_synthetic_engine.py          # Zero-dependency synthetic corridor engine and sublane filtering
├── test_replay_controller.py         # Deterministic JSONL frame-accurate replay and playback controls
├── test_yolo_detection.py            # YOLO11 perception inference, bounding boxes, and class confidence
├── test_bytetrack_tracking.py        # Trajectory association, Kalman tracking, and virtual tripwires
├── test_clearance_models.py          # Tabular (XGBoost/GBDT) and sequential (GRU) clearance inference
├── test_model_registry.py            # Model Registry catalog routing and multi-tier fail-safe fallbacks
├── test_multi_node_eta.py            # Kinematic multi-node ETA estimator across corridor Nodes A–D
├── test_preclearance_controller.py   # JIT pre-clearance trigger formulation and state transitions
├── test_moving_horizon_coordination.py# Multi-node moving-horizon green waves and spillback flushing
├── test_recovery_controller.py       # Post-clearance green debt amortization and master resync
├── test_signal_safety_gateway.py     # Deterministic MMU zero-trust interlock (INV-01 to INV-06)
├── test_vms_advisory_system.py       # Variable Message Signs 4-gantry advisory hierarchy (Task 53)
├── test_esp32_physical_testbench.py  # ESP32 C++ firmware framing, 24-ch LEDs, HW MMU & watchdog (Task 54)
├── test_demo_scenario_runner.py      # Automated 3-act demo scenario execution & timeline JSON (Task 55)
├── test_technical_documentation_sync.py # Verification of all 24 chapters in docs-site (Task 56)
├── test_all_readmes_integrity.py     # Verification of all 19 monorepo README files & links (Task 57)
├── test_release_packaging_and_deployment.py # Docker configs, release report, notes & packaging (Task 58)
├── test_ppo_reinforcement_learning.py# Gymnasium corridor env, PPO Actor-Critic & Safety Shield (Task 59)
└── README.md
```

---

## 2. Test Execution Commands

### 2.1 Monorepo Quality Gate (All-in-One Check)
The primary quality assurance entrypoint that validates code style, Python tests, shared type declarations, web bundles, and documentation:
```bash
python scripts/check_all.py
```

### 2.2 Running Python Test Suites
```bash
# Run all unit and integration tests
python -m pytest

# Run with verbose output and test execution timing
python -m pytest -v --durations=10

# Run specific domain test suites
python -m pytest tests/test_signal_safety_gateway.py -v
python -m pytest tests/test_moving_horizon_coordination.py -v
python -m pytest tests/test_vms_advisory_system.py -v
python -m pytest tests/test_esp32_physical_testbench.py -v
python -m pytest tests/test_all_readmes_integrity.py -v
```

### 2.3 Documentation & Relative Link Integrity
```bash
# Verify all internal relative markdown links across 55+ documentation files
python scripts/verify_markdown_links.py
```

---

## 3. Verification Gates & Safety Assertions

All builds and pull requests must satisfy the following zero-compromise criteria:

1. **Gate 1 - Static Analysis & Linting:** `ruff check .` passes with zero linting or formatting errors.
2. **Gate 2 - Python Test Suite:** `pytest` passes with 100% success rate across all unit, integration, and safety tests.
3. **Gate 3 - Shared Package Build:** `pnpm --filter @clearway/shared build` compiles TypeScript declarations without error.
4. **Gate 4 - Frontend Web Application:** `pnpm --filter clearway-web build` compiles the production Vite + Three.js bundle cleanly.
5. **Gate 5 - Documentation Site:** `pnpm --filter clearway-docs-site build` compiles all 24 chapters and static assets to `dist/`.
6. **Safety Invariants Assertions:**
   - **INV-01:** Zero conflicting green/yellow commands across 10,000+ simulation steps.
   - **INV-02:** Minimum green interval ($\ge 10.0\text{s}$) strictly upheld.
   - **INV-03:** Maximum green ceiling ($\le 75.0\text{s}$) strictly enforced.
   - **INV-04:** Yellow change interval ($\ge 3.0\text{s}$) never skipped or truncated.
   - **INV-05:** All-red clearance interval ($\ge 2.0\text{s}$) preserved before conflicting transitions.
   - **INV-06:** Heartbeat watchdog ($2.0\text{s}$) autonomous fallback to fixed-time Webster cycling.
