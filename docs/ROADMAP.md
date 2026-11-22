# ClearWayAI 60-Task Master Roadmap

A complete breakdown of the 60 engineering tasks from monorepo foundation to full physical prototype and competition package.

---

## 1. Phase Breakdown

- **Phase A — Foundation & Governance (Tasks 01–04, 21–22)**
  - T01: Monorepo scaffold & baseline API/Web [VERIFIED]
  - T02: Professional GitHub repository structure [VERIFIED]
  - T03: Technical documentation portal on GitHub Pages [VERIFIED]
  - T04: Comprehensive multi-tier README system [VERIFIED]
  - T21: System specifications (SRS), ADRs, and safety invariants
  - T22: Automated CI/CD, linting, and development environment

- **Phase B — 3D Digital Twin & Blueprint UI (Tasks 05–20)**
  - T05: UI Blueprint & acceptance pixels locking
  - T06: Dashboard layout components (TopBar, Sidebar, Panel frames)
  - T07: Three.js / R3F Canvas isometric camera & orbit controls
  - T08: Roadway intersection 3D modeling (lanes, crosswalks, stoplines)
  - T09: City contextual 3D blocks and urban props
  - T10: Vietnamese vehicle 3D assets & emergency ambulance
  - T11: Lane graph vehicle movement & persistent ID motion interpolation
  - T12: 3D signal poles, pedestrian walk states, and phase transitions
  - T13: Dynamic corridor ribbons, flow arrows, and 3D HUD badges
  - T14: V2I/V2X Communication & Hardware Status card
  - T15: Approach split timing table (Red/Yellow/Green/Cycle/Split)
  - T16: Adaptive signal control & queue-vs-capacity chart
  - T17: IoT sensor list & interactive mini vector city map
  - T18: Traffic analytics, radial performance gauge, and anomaly alerts
  - T19: Operational controls (Start, Pause, Step, Scenario, Mission Drawer)
  - T20: Visual fidelity gate & FPS performance audit

- **Phase C — SUMO Microscopic Simulation (Tasks 23–27)**
  - T23: SUMO synthetic network (Nodes A–D, 1–3 km corridor)
  - T24: Mixed motorcycle traffic demand generator & sublane modeling
  - T25: Emergency vehicle modeling & bluelight yielding logic
  - T26: Python TraCI adapter with deterministic stepping & replay
  - T27: Implementation of 3 baseline controllers (B0 Fixed, B1 Reactive, B2 Corridor)

- **Phase D — Computer Vision & Data Governance (Tasks 28–32)**
  - T28: Traffic video collection & privacy data governance
  - T29: Annotation guidelines & scene-based leakage prevention splits
  - T30: YOLO11 fine-tuning for dense motorcycle traffic
  - T31: ByteTrack trajectory extraction and speed estimation
  - T32: Camera homography calibration & traffic state engine

- **Phase E — Clearance Time AI Models (Tasks 33–36)**
  - T33: Empirical clearance time label generation from physical events
  - T34: Tabular clearance prediction baseline (XGBoost / Random Forest)
  - T35: Temporal sequence clearance prediction (PyTorch LSTM/GRU)
  - T36: Model registry, winner selection, and out-of-distribution fallbacks

- **Phase F — Safety Controller & Coordination (Tasks 37–41)**
  - T37: Emergency mission simulation & multi-intersection ETA estimation
  - T38: Pre-clearance trigger algorithm with safety buffers
  - T39: Moving-horizon multi-intersection corridor coordinator
  - T40: Post-transit queue-aware recovery controller
  - T41: Independent Signal Safety Gateway & conflict checker

- **Phase G — Backend & Operations Integration (Tasks 42–45)**
  - T42: Full FastAPI backend, database models, and API contracts
  - T43: Real-time WebSocket snapshot stream & JSONL replay
  - T44: Production responsive Operations Dashboard
  - T45: 2D corridor route map and coordination timeline

- **Phase H — 3D World & Dual Comparison (Tasks 46–48)**
  - T46: Multi-intersection 3D WebGL world
  - T47: Real-time SUMO-to-3D synchronization
  - T48: Synchronized side-by-side 3D comparison (Fixed vs ClearWay AI)

- **Phase I — Telemetry, Testing & Scientific Evaluation (Tasks 49–52)**
  - T49: Explainable decision telemetry & audit trails
  - T50: End-to-end integration tests (UI → API → AI → SUMO → 3D)
  - T51: Scientific ablation study across 10 random seeds
  - T52: Security audit, threat modeling, and fail-safe testing

- **Phase J — Physical Prototype, Pitch & Release (Tasks 53–60)**
  - T53: Variable Message Signs (VMS) 3D advisory
  - T54: Physical miniature testbench with ESP32 & LED signals
  - T55: 5-minute video demo script, slide deck, and defense Q&A
  - T56: Technical documentation synchronization with real code
  - T57: Final monorepo documentation audit
  - T58: v0.1.0-mvp release packaging and competition submission dossier
  - T59: Reinforcement Learning (PPO) sandbox exploration (P2 Research)
  - T60: Real-camera shadow mode 3D localization (P2 Research)
