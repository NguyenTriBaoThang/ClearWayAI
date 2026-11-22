# ClearWayAI UI Visual Acceptance Protocol (`docs/UI_VISUAL_ACCEPTANCE.md`)

This document defines the strict visual acceptance criteria, regional quality gates, and asset checklist required to verify that the implementation faithfully matches [assets/reference/dashboard-target.png](../assets/reference/dashboard-target.png).

---

## 1. Regional Acceptance Quality Gates

### 1.1 Gate 1: TopBar & Global Navigation
- [x] **Suite Title:** Displays "Smart City Operations Suite" with vertical divider.
- [x] **Brand Title:** Displays "ClearWay AI — Traffic Control Digital Twin" with glowing teal activity icon.
- [x] **Safety Gate:** Displays `SIMULATION ONLY` and `DEMO FIXTURE` provenance badge.
- [x] **Clock Separation:** Distinctly separates simulation time (`2025-01-15 14:27:36 (SIM)`) from real host time (`Host UTC`).
- [x] **Status Pill:** Green glowing pill indicating `● LIVE SIM`.
- [x] **Action Icons:** Notification bell with counter badge `4`, Settings gear, and Operator avatar `OP`.

### 1.2 Gate 2: Top-Left Panel (V2X Hardware Status)
- [x] **Network ID:** Displays `RM-INT-0457` in monospace cyan.
- [x] **Node Topology:** 4 horizontal device nodes connected by flow lines:
  - On-Board Units (1,842 Online, 99.2%)
  - RSU (42 Online, 100%)
  - Edge Controller (Online)
  - Signal Controller (Online, 8 Phases)
- [x] **Telemetry Strip:** Shows V2X Status: Active, Latency: 11 ms, Packet Loss: 0.2%.
- [x] **Provenance Honesty:** Clearly marks status as `Simulated` when no physical RSU is connected.

### 1.3 Gate 3: Top-Middle Panel (Phase Split Timing Table)
- [x] **Header:** Oak St. & 5th Ave (INT-0457) split timing.
- [x] **Table Columns:** Approach, Red, Yellow, Green, Cycle, Split.
- [x] **All 4 Approaches Present:**
  - N - Oak St. (NB): Red 67s, Yellow 4s, Green 49s, Cycle 120s, Split 41%
  - S - Oak St. (SB): Red 67s, Yellow 4s, Green 49s, Cycle 120s, Split 41%
  - E - 5th Ave. (EB): Red 49s, Yellow 4s, Green 67s, Cycle 120s, Split 56%
  - W - 5th Ave. (WB): Red 49s, Yellow 4s, Green 67s, Cycle 120s, Split 56%
- [x] **Color Coding:** Red values in `#ef476f`, Yellow values in `#ffd166`, Green values in `#06d6a0`, Splits in `#38bdf8`.

### 1.4 Gate 4: Top-Right Panel (Adaptive Signal & Queue Chart)
- [x] **Cycle & Phase Cards:** Cycle Time (120s), Current Phase (P3 E-W Thru), Next Phase (P4 E-W Left).
- [x] **Queue vs Capacity SVG Chart:**
  - Dual line chart with 0–120s X-axis and 0–120 veh Y-axis.
  - Cyan curve for Queue (veh) and stepped red dashed line for Capacity.
  - Occupancy badge: `76%`.
- [x] **Optimization Metrics:** Phase Optimization (`-19% Delay`), Avg. Queue (`87 m`), Backlog (`45 m`).

### 1.5 Gate 5: Center 3D Digital Twin Viewport
- [x] **True WebGL Canvas:** Implemented via Three.js `WebGLRenderer` and `PerspectiveCamera` with active animation loop.
- [x] **No Fake Images:** Never renders a static background screenshot to fake 3D traffic.
- [x] **Isometric Geometry:** Road intersection with lanes, stoplines, curbs, and crosswalks.
- [x] **Contextual Buildings:** Multi-story perimeter city blocks with architectural facades.
- [x] **Dynamic Route Ribbons:**
  - Standard green vehicular turning ribbons.
  - Conflict turning ribbons in red.
  - Emergency corridor chevron ribbon path in cyan/blue dotted line.
- [x] **Vehicle Callouts:** Speed badges (`57 km/h`, `46 km/h`, `68 km/h`) and vehicle IDs (`602`, `438`, `217`, `356`, `318`, etc.).
- [x] **Emergency Mission Callout:** `Emergency Route Active (AMB-339) | ETA to Hospital: 3.4 min`.
- [x] **Bottom Floating HUD:** `Digital Twin INT-0457 | V2X Status Active | Occupancy 76% | Avg. Speed 52 km/h | Delay -19%`.

### 1.6 Gate 6: Bottom-Left Panel (IoT Sensor Network & Map)
- [x] **5 Sensor Categories:** Cameras (112/112), LiDAR (48/48), Loop (96/96), RSUs (42/42), Controllers (8/8).
- [x] **Data Layer Toggles:** Checkboxes for Traffic Flow, Sensor Coverage, V2X, Incident, Emergency Corridor, Parking.
- [x] **Mini City Map:** Vector topology with corridor line, intersection nodes, Hospital marker `H`, Compass `N`, and metric scale bar.

### 1.7 Gate 7: Bottom-Right Panel (Analytics, Gauge & Alerts)
- [x] **Volume Bars:** Hourly volume for NB (1210), SB (1438), EB (2185), WB (2061).
- [x] **Travel Time Bars:** N→S (2.6m, -18%), S→N (2.8m, -17%), E→W (3.9m, +6%), W→E (3.7m, +4%).
- [x] **Radial Performance Gauge:** Circular progress indicator displaying `82 / 100` with Throughput (+15%), Delay (-19%), Stops (-22%).
- [x] **Anomaly Detection List:** Critical alert for active ambulance route AMB-339, Warnings for 5th Ave EB queue (87m) and Oak St SB speed drop (28 km/h).

---

## 2. 3D Scene Asset Requirement Matrix

| Asset Category | Required Elements | Fidelity Requirement |
| :--- | :--- | :--- |
| **Emergency Vehicles**| $\ge 1$ Ambulance | Red & blue flashing roof strobes, priority route HUD |
| **Motorcycles** | Motorbikes / Scooters | True physical scale (~2.0m length), sublane clustering |
| **Passenger Vehicles** | Sedans, SUVs, Taxis | Variety of colors, proper wheel alignment, stopline compliance |
| **Heavy Vehicles** | Transit Bus, Delivery Truck | Proper scale (~10–12m bus length), turn radius compliance |
| **Road Markings** | Zebra crosswalks, arrows | Anti-aliased geometry/textures, yellow box junctions |
| **Traffic Signals** | 4 multi-aspect signal poles | Emissive lens materials (Red, Yellow, Green) synced to phase |
| **Urban Architecture** | Commercial buildings | Perimeter blocks providing urban street canyon perspective |

---

## 3. Resolution Verification Targets

1. **`1254 × 1254` (Blueprint Target Ratio):**  
   All panels remain in exact proportion to the reference image without clipping or horizontal overflow.
2. **`1440 × 900` (Standard Laptop View):**  
   Responsive 3-tier CSS grid with center 3D viewport height >= 380px.
3. **`1920 × 1080` (Full HD Command Center):**  
   Generous card spacing, high-DPI canvas rendering, 3D viewport height >= 520px.

---

## 4. Verification Sign-Off Table

| Task ID | Reviewer / Role | Date | Verdict | Evidence |
| :---: | :---: | :---: | :---: | :--- |
| **T05** | Senior Full-Stack Engineer | 2026-11-22 | **VERIFIED** | `docs/UI_REFERENCE_SPEC.md`, `docs/UI_VISUAL_ACCEPTANCE.md`, reference image confirmed 1254x1254 |

