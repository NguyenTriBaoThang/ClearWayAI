# ClearWayAI Demonstration Playbook & Presentation Scenarios

This document provides the operational playbook, click-by-click presenter instructions, camera presets, and scenario timelines for live demonstrations of the ClearWayAI Next-Generation Traffic Coordination and Emergency Pre-clearance system.

---

## 1. Demonstration Setup & Pre-flight Checklist

Before starting the live demonstration, ensure the following systems are active:

1. **Backend API Service:**
   ```bash
   uvicorn apps.api.src.main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. **Web Frontend Dashboard:**
   ```bash
   npm --prefix apps/web run dev
   ```
   Open Chrome at `http://localhost:5173`.
3. **Physical ESP32 Testbench (Optional/Hybrid):**
   Plug the ESP32 DevKit V1 into USB (`COM3` on Windows or `/dev/ttyUSB0` on Linux). If physical hardware is not plugged in, the system automatically runs the high-fidelity `VirtualESP32Emulator` (verified in Task 54).
4. **Display Resolution:** Recommended $1920 \times 1080$ Full HD, browser zoom 100%.

---

## 2. Master Scenario Timeline Overview

```mermaid
timeline
    title ClearWayAI Master Demonstration Timeline
    section Scenario 1: Nominal
        t = 00:00 : Corridor initialized (Nodes A-D)
        t = 00:15 : High-volume morning peak traffic enters
        t = 00:45 : Moving-horizon green wave established
        t = 01:00 : Side-by-side comparison (Fixed vs AI: -42% Delay)
    section Scenario 2: Emergency
        t = 01:15 : AMB-339 Dispatched at x = -150m
        t = 01:25 : Dynamic VMS gantries switch to "DẠT PHẢI"
        t = 01:40 : JIT Pre-clearance green corridor at Node A & B
        t = 02:15 : AMB-339 clears Corridor with 0 stops
    section Scenario 3: Recovery
        t = 02:20 : PostClearanceRecoveryController activates
        t = 02:35 : Compensatory green phases for cross streets
        t = 03:00 : Corridor returns to nominal adaptive balance
```

---

## 3. Scenario 1: Nominal Arterial Green Wave (Peak Traffic)

### 3.1 Objective
Demonstrate adaptive moving-horizon signal coordination across 4 consecutive intersections (Nodes A, B, C, D) along Nguyen Van Linh Boulevard, showing significant queue dissipation and delay reduction compared to standard fixed-time controllers.

### 3.2 Presenter Instructions & Actions

| Step | Action | UI / Viewport Focus | Expected System Output | Presenter Talking Points |
| :---: | :--- | :--- | :--- | :--- |
| **1.1** | Load Dashboard | Default isometric 3D view (`ISO` preset) | 3D Digital Twin renders 4 intersections with cyber road grid and ambient traffic. | "ClearWayAI builds a real-time 3D Digital Twin directly synced with SUMO microscopic traffic simulation." |
| **1.2** | Toggle Comparison | Click **"Split View: Compare"** in TopBar | Left pane: Baseline B0 (Fixed-time). Right pane: ClearWayAI (Moving-Horizon). | "Here is a synchronized side-by-side view. Notice queue build-up on the left fixed signal, while AI maintains continuous corridor progression." |
| **1.3** | Switch Camera | Click **`TOP`** Camera Preset | Overhead 2D-orthographic perspective of the entire 750m corridor. | "From this top-down view, you can observe the coordinated arterial green wave clearing vehicle platoons across Nodes A through D." |
| **1.4** | Inspect KPI Tiles | Focus on KPI Panel (Bottom Right) | Avg Delay: $24.8\text{ s}$ vs $43.2\text{ s}$ (-42.6%), Stops: $0.48$ vs $1.15$ (-58.2%). | "Under identical peak volume, ClearWayAI slashes intersection delays by over 42% while preserving pedestrian crossing rights." |

---

## 4. Scenario 2: Emergency Vehicle AMB-339 JIT Pre-clearance

### 4.1 Objective
Demonstrate Just-In-Time (JIT) green corridor pre-clearance for an active ambulance (AMB-339) en route to District 7 General Hospital, highlighting dynamic VMS driver advisories, MMU hardware safety interlocks, and zero emergency stops.

### 4.2 Presenter Instructions & Actions

| Step | Action | UI / Viewport Focus | Expected System Output | Presenter Talking Points |
| :---: | :--- | :--- | :--- | :--- |
| **2.1** | Dispatch Mission | Click **"Dispatch Emergency AMB-339"** | Emergency vehicle spawns at $x = -150\text{ m}$; audio siren indicator activates. | "We trigger an emergency priority mission. The hospital requests priority transit through the 4-node arterial." |
| **2.2** | Track EV Camera | Click **`CHASE`** Camera Preset | Camera locks onto AMB-339 navigating traffic at $60\text{ km/h}$. | "The chase camera tracks AMB-339 in real time. Notice vehicles in front receiving early advisories." |
| **2.3** | Observe VMS Gantries | Zoom into Overhead Gantry ahead of Node A ($x = -80\text{ m}$) | VMS LED display switches: *"XE CỨU THƯƠNG ĐANG ĐẾN - DẠT PHẢI"*, speed drops to 25 km/h, strobes flash. | "Variable Message Signs (VMS) 80m ahead of the stopline alert drivers to yield and clear the corridor early, preventing bottleneck jams." |
| **2.4** | Check Safety MMU | Inspect Safety Gateway Panel | Green priority granted on East-West axis; North-South cross streets held at Red; MMU status: `VERIFIED_SAFE`. | "Safety is uncompromised: our Signal Safety Gateway and ESP32 hardware MMU physically prevent conflicting green lights (INV-03)." |
| **2.5** | Corridor Clearance | Watch AMB-339 cross Node D ($x = 750\text{ m}$) | Mission status: `COMPLETED`; Travel Time: $132.4\text{ s}$; Emergency Stops: $0$. | "AMB-339 traverses the entire 750m corridor with zero stops, saving over 2.5 minutes of precious golden-hour transit time." |

---

## 5. Scenario 3: Post-Clearance Resilient Recovery & Hardware Interlock

### 5.1 Objective
Demonstrate how ClearWayAI recovers downstream intersections following emergency pre-clearance, compensating starved cross streets and verifying hardware fail-safe mechanisms.

### 5.2 Presenter Instructions & Actions

| Step | Action | UI / Viewport Focus | Expected System Output | Presenter Talking Points |
| :---: | :--- | :--- | :--- | :--- |
| **3.1** | Recovery Transition | Observe Nodes A–D immediately after AMB-339 clears | `PostClearanceRecoveryController` initiates compensatory green splits for North-South approaches. | "Pre-clearance often starves cross streets. Our recovery controller dynamically injects extra green time to dissipate side-street queues." |
| **3.2** | VMS Caution State | Zoom to VMS Gantries | VMS transitions to: *"HÀNH LANG ĐÃ THÔNG - CHÚ Ý / CORRIDOR CLEARED - RESUME CAUTION"*. | "VMS gantries enter caution recovery mode for 12s, guiding motorists to resume normal speeds safely." |
| **3.3** | Hardware Testbench | Camera cut to physical ESP32 breadboard | LEDs on ESP32 reflect exact signal phases; status LED shows healthy 500ms heartbeat. | "The digital twin is perfectly mirrored by our ESP32 physical testbench, equipped with an autonomous 2.0s fail-safe watchdog (INV-06)." |
| **3.4** | Audit & Privacy Drawer | Click **"Decision Audit"** button in TopBar | Drawer slides open showing explainable natural language rationale and Zero-PII compliance certificate. | "Every single AI decision is audited with complete provenance, zero PII storage, and full compliance with Decree 13/2023/ND-CP." |

---

## 6. Emergency Contingency & Backup Protocols

1. **If Web Browser Freezes:** Press `F5` to reload; state is persistently cached in SQLite and restored in $<1\text{ s}$.
2. **If USB ESP32 Disconnects:** Bridge automatically falls back to `VirtualESP32Emulator` within 50ms without interrupting the UI demonstration.
3. **If SUMO Simulation Lags:** Switch to Replay Mode (`/api/v1/replay`) to stream pre-recorded verified golden simulation run at exact 1.0x real-time rate.

