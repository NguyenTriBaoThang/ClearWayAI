# ClearWayAI Microscopic Traffic Simulation (`simulation`)

Orchestrates microscopic traffic modeling using **Eclipse SUMO** and the Python **TraCI** interface.

---

## 1. Directory Structure

```
simulation/
├── sumo/                   # Network definitions (.net.xml, .nod.xml, .edg.xml, .con.xml, .tll.xml)
├── scenarios/              # Traffic demand scenarios (Free, Normal, Peak, Spillback)
├── traci/                  # TraCI simulation manager, step controllers, and replay serializers
├── baselines/              # Standardized baseline signal controllers (B0, B1, B2, B3) (Task 44)
├── experiments/            # Scientific benchmark evaluator & demo scenario runner (Tasks 45, 55)
└── README.md
```

---

## 2. Microscopic Traffic Modeling Features

- **Synthetic Arterial Corridor:** 4 sequential intersections (Nodes A–D) connecting feeder routes to a central medical center approach.
- **Motorcycle Sublane Model:** Realistic lateral clearance and filtering between queuing vehicles (`latAlignment="arbitrary"`).
- **Blue-Light Vehicle Dynamics:** Emergency ambulances with custom right-of-way yielding logic.
- **Deterministic Replay:** Each scenario is locked by seed, allowing identical replication of baseline (Fixed-Time) and ClearWay AI experimental runs.

---

## 3. Running Simulations

```bash
# Run simulation step via CLI (requires SUMO installed)
python -m simulation.traci.manager --scenario peak --seed 42
```

---

## 4. Standardized Baselines (`simulation/baselines`)

Provides standardized signal controllers for fair, reproducible scientific benchmarking:
- **B0: Fixed-Time Webster (`b0_fixed_time.py`):** Fixed 72s cycle, zero priority preemption. Negative control.
- **B1: Reactive Local (`b1_reactive.py`):** Traditional localized optical preemption triggered 100m upstream of stopline.
- **B2: Static Corridor Lockout (`b2_corridor.py`):** Static green-wave locking all arterial phases simultaneously upon EV corridor entry.
- **B3: ClearWay AI (`b3_clearway.py`):** Moving-horizon predictive pre-clearance with JIT shockwave evacuation.

---

## 5. Scientific Benchmark Evaluator (`simulation/experiments`)

Managed via `simulation/experiments/scientific_evaluator.py`:
- Automates multi-seed, multi-scenario Monte Carlo runs comparing B0, B1, B2, and ClearWay AI.
- Evaluates 6 core metrics:
  1. Emergency Vehicle Corridor Travel Time ($s$)
  2. Number of Complete Emergency Vehicle Stops ($stops$)
  3. Average Emergency Vehicle Travel Speed ($km/h$)
  4. Average Cross-Street Private Vehicle Delay ($s$)
  5. Cross-Street Maximum Queue Spillback ($m$)
  6. Signal Safety Invariants (INV-01 to INV-06) Compliance Rate ($pct$)
- Emits publication-grade JSON reports and tabular summaries.

```bash
# Execute scientific benchmark evaluation across all 4 controllers
python simulation/experiments/scientific_evaluator.py --scenario peak --seeds 42,43,44
```

---

## 6. Live Demo Scenario Orchestrator (`demo_scenario_runner.py`)

Managed via `simulation/experiments/demo_scenario_runner.py`:
- Orchestrates multi-act demonstration runs (`docs/DEMO_SCENARIOS.md`):
  - **Act 1:** Congested Arterial Baseline ($t = 0\text{--}30\text{s}$)
  - **Act 2:** Emergency Vehicle Dispatch & Predictive JIT Clearing ($t = 30\text{--}80\text{s}$)
  - **Act 3:** Post-Clearance Smooth Recovery & Civil De-escalation ($t = 80\text{--}120\text{s}$)
- Ingests real-time VMS advisory states, MMU safety gating, and ESP32 telemetry, saving a timeline JSON replay (`demo_timeline.json`).

```bash
# Execute automated demo run
python simulation/experiments/demo_scenario_runner.py --output demo_timeline.json
```

