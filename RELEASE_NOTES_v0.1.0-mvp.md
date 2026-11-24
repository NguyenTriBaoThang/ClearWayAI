# ClearWayAI Release Notes — v0.1.0-mvp

> **Official Release Notes for ClearWayAI MVP Milestone (`v0.1.0-mvp`)**  
> *Next-Generation 3D Digital Twin, Multi-Intersection Adaptive Signal Coordination & Emergency Corridor Pre-clearance*

- **Release Version:** `v0.1.0-mvp`
- **Release Date:** November 2026
- **Git Branch / Tag:** `main` / `v0.1.0-mvp`
- **Author & Maintainer:** Nguyễn Tri Bão Thắng ([@NguyenTriBaoThang](https://github.com/NguyenTriBaoThang))
- **License:** [MIT License](LICENSE)
- **Monorepo Verification Status:** **58 / 60 Tasks Verified (96.7%)**

---

## 🌟 Highlights & Major Milestones

ClearWayAI `v0.1.0-mvp` represents the complete Minimum Viable Product (MVP) delivery of an intelligent, multi-intersection urban traffic digital twin platform tailored specifically for Vietnamese high-density mixed traffic.

### Key Breakthroughs Delivered in this Release:
1. **Just-In-Time Moving-Horizon Emergency Corridor Pre-Clearance:**
   Replaces legacy static green-wave lockouts with an adaptive moving-horizon pre-clearance window ($750\text{m}$ spatial / $45\text{s}$ temporal lookahead), clearing queues along sequential intersections (Nodes A–D) right as the emergency ambulance approaches.
2. **Microscopic Mixed-Traffic Modeling with Sublane Dynamics:**
   Faithfully reproduces Vietnamese traffic conditions ($70\text{--}85\%$ motorcycles) using SUMO's `SL2015` sublane model ($0.64\text{m}$ resolution) and arbitrary lateral alignment for realistic lane filtering and stopline swarming.
3. **Dual-Engine AI Clearance Time Predictor & Model Registry:**
   Integrates physics-based shockwave evacuation with Gradient Boosting tabular champion ($\text{MAE} = 1.20\text{s}$) and Sequential GRU champion ($\text{MAE} = 4.73\text{s}$, latency $= 0.78\text{ms}$) with dynamic multi-tier fail-safe fallbacks.
4. **Deterministic Signal Safety Gateway (Hardware-Grade MMU Interlock):**
   Strictly enforces 6 fundamental safety invariants (INV-01 to INV-06), preventing conflicting vehicular greens, protecting yellow/all-red change intervals, and falling back autonomously upon communication loss.
5. **Interactive 3D WebGL Digital Twin & Tactical Operations Dashboard:**
   Genuine Three.js WebGL rendering at 60 FPS with isometric perspective, 16 physical signal poles, instanced vehicle traffic, overhead VMS gantries, split-screen dual simulation comparison, and transparent explainable AI decision audit logs.
6. **Physical ESP32 Miniature Breadboard Demonstration Bench:**
   Production C++ Arduino firmware driving 24 discrete signal LEDs via three daisy-chained 74HC595 shift registers with hardware-level bitmask MMU interlock and 2.0s communication watchdog.
7. **Comprehensive Competition & Defense Dossier:**
   Includes the complete Technical Evaluation Report (`docs/FINAL_RELEASE_REPORT.md`), 3-scenario live demo playbook (`docs/DEMO_SCENARIOS.md`), 5-minute video storyboard with bilingual voiceover script (`docs/VIDEO_DEMO_SCRIPT.md`), 12-slide pitch deck (`docs/PITCH_DECK.md`), and defense Q&A cheat sheet (`docs/DEFENSE_QA.md`).

---

## 📦 Subsystem Breakdown

### 1. Web Frontend & 3D Digital Twin (`apps/web`)
- Responsive Cyber Grid dark theme (4K down to mobile).
- Genuine Three.js WebGL Canvas with perspective isometric camera and camera presets (`corridor`, `nodeA`, `nodeB`, `nodeC`, `nodeD`, `hospital`, `chase`).
- 4 Variable Message Signs (VMS) 3D truss gantries with dynamic canvas LED textures.
- Real-time VMS Advisory Card and Explainable AI Decision Audit Drawer.
- Split-View Dual Simulation Comparison (Webster Baseline B0 vs ClearWay AI).

### 2. Backend REST API & WebSocket Bus (`apps/api`)
- 7 Modular FastAPI routers: `simulations`, `missions`, `clearance`, `corridor`, `replay`, `audit`, and `hardware`.
- Real-time WebSocket pub/sub bus (`/ws/simulations/{id}`, `/ws/telemetry`) streaming at 10Hz.
- Thread-safe SQLite persistence layer for episodes, priority missions, and decision audit logs.
- Frame-accurate deterministic telemetry replay controller.

### 3. Coordination & Safety Controller (`controller`)
- Multi-node kinematic ETA calculator with non-linear acceleration curves and weather friction.
- Just-In-Time pre-clearance trigger formulation: $\Delta t_{\text{trigger}} = \text{ETA} - \hat{T}_{\text{clear}} - T_{\text{trans}} - T_{\text{buf}}$.
- Moving-horizon corridor coordinator with cascading green-wave offsets and queue spillback flushing.
- Multi-cycle post-clearance recovery controller amortizing cross-street green debt over 3 cycles.
- Signal Safety Gateway emulating NEMA TS2 MMU (INV-01 through INV-06).
- V2X security gateway with STRIDE threat mitigation, HMAC-SHA256 signatures, and anti-replay windows.

### 4. Microscopic Traffic Simulation (`simulation`)
- 1,300m synthetic arterial corridor comprising 4 sequential intersections (Nodes A–D) and Trauma Center hospital approach.
- Dual-engine architecture: Native Eclipse SUMO TraCI with zero-dependency `SyntheticCorridorEngine` fallback.
- Standardized baseline signal controllers: B0 (Fixed-Time Webster), B1 (Reactive Local Opticom), B2 (Static Green-Wave Lockout), and B3 (ClearWay AI).
- Automated scientific evaluator (`scientific_evaluator.py`) and live demo scenario orchestrator (`demo_scenario_runner.py`).

### 5. Computer Vision & Clearance AI (`ai`)
- Fine-tuned YOLO11s vehicle detector on Vietnamese mixed traffic (88.4% mAP@0.5, $\le 25\text{ms}$ latency).
- ByteTrack trajectory tracker with Kalman motion filtering and virtual tripwires.
- Clearance Model Registry with multi-tier fail-safe hierarchy.
- Planar homography calibration across 4 camera profiles.

### 6. Physical Hardware Testbench (`hardware`)
- C++ Arduino sketch (`hardware/firmware/clearway_esp32_firmware.ino`).
- 24-channel output driving 8 Red, 8 Yellow, and 8 Green LEDs across Nodes A–D.
- Hardware-level MMU conflict interlock and 2.0s communication watchdog.
- Python serial bridge with auto-discovery and in-memory `VirtualESP32Emulator`.

### 7. Documentation & Quality Infrastructure (`docs`, `docs-site`, `scripts`)
- 24-chapter interactive technical documentation website deployed to GitHub Pages.
- Monorepo 5-Gate Quality Checker (`python scripts/check_all.py`).
- Zero-broken-link markdown validator (`python scripts/verify_markdown_links.py`).
- 25+ automated Pytest test suites.

---

## 📊 Scientific Benchmark Summary

Based on 10 independent random seed Monte Carlo runs on the peak congestion scenario (6,200 veh/h, 75% motorcycles):

| Metric | B0 (Webster) | B1 (Opticom) | B2 (Corridor Lockout) | **ClearWay AI** | **Improvement** |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Emergency Travel Time** | $101.4\text{ s}$ | $78.6\text{ s}$ | $64.1\text{ s}$ | **$58.2\text{ s}$** | 🟢 **-42.6% delay** |
| **Emergency Stops** | $2.1\text{ stops}$ | $1.0\text{ stops}$ | $0.2\text{ stops}$ | **$0.0\text{ stops}$** | 🟢 **100% stop elimination** |
| **Emergency Average Speed** | $31.9\text{ km/h}$ | $41.2\text{ km/h}$ | $50.5\text{ km/h}$ | **$55.7\text{ km/h}$** | 🟢 **+74.6% speedup** |
| **Cross-Street Delay** | $24.8\text{ s}$ | $28.3\text{ s}$ | $41.2\text{ s}$ | **$33.2\text{ s}$** | 🟢 **-19.4% delay vs B2** |
| **Cross-Street Max Queue** | $48.5\text{ m}$ | $56.2\text{ m}$ | $89.4\text{ m}$ | **$68.1\text{ m}$** | 🟢 **-23.8% spillback vs B2** |
| **Safety Invariants Rate** | $100\%$ | $100\%$ | $100\%$ | **$100\%$** | 🛡️ **0 MMU violations** |

---

## 🚀 Quickstart & Production Deployment

### Option 1: Docker Compose Production (Recommended)
```bash
# Start all production services in background
docker-compose -f docker-compose.prod.yml up -d

# Verify service health
docker-compose -f docker-compose.prod.yml ps

# Web Dashboard: http://localhost:3000
# API Swagger:   http://localhost:8000/docs
```

### Option 2: Native Monorepo Bootstrap
```bash
# Windows
.\scripts\bootstrap.ps1

# Linux / macOS
chmod +x ./scripts/bootstrap.sh && ./scripts/bootstrap.sh
```

---

## 🔭 Future Horizons (Scheduled Post-MVP Tasks)

- **Task 59:** PPO Reinforcement Learning for Multi-Intersection Adaptive Coordination in Sandboxed Gym Environment.
- **Task 60:** Real Camera Video Feed $\to$ 3D Vehicle Localization & Field Validation.

