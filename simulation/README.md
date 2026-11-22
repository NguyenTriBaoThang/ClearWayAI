# ClearWayAI Microscopic Traffic Simulation (`simulation`)

Orchestrates microscopic traffic modeling using **Eclipse SUMO** and the Python **TraCI** interface.

---

## 1. Directory Structure

```
simulation/
├── sumo/                   # Network definitions (.net.xml, .nod.xml, .edg.xml, .con.xml, .tll.xml)
├── scenarios/              # Traffic demand scenarios (Free, Normal, Peak, Spillback)
├── traci/                  # TraCI simulation manager, step controllers, and replay serializers
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

