<div align="center">
  <img src="../assets/branding/clearway-banner.jpg" alt="ClearWay AI UI Specification Banner" width="100%" style="border-radius: 8px; max-width: 950px; margin-bottom: 16px; box-shadow: 0 8px 32px rgba(0,0,0,0.4);" />
</div>

# ClearWayAI UI Reference Specification (`docs/UI_REFERENCE_SPEC.md`)

> **Source Document:** Derived from direct pixel, layout, and color analysis of [assets/reference/dashboard-target.png](../assets/reference/dashboard-target.png) (1254×1254 px, 3.8 MB).  
> **Mandatory Rule:** The reference image serves as the design and layout goal. It is **NOT** a background texture or screenshot overlay. The center viewport must remain a live, interactive WebGL Three.js canvas.

---

## 1. High-Level Blueprint Overview

The interface represents the **ClearWay AI Smart City Operations Suite — Traffic Control Digital Twin** monitoring intersection **Oak St. & 5th Ave (INT-0457)**.

```
+-----------------------------------------------------------------------------------------------+
| TOPBAR: Suite Title | ClearWay AI Brand | Safety Gate: SIMULATION | Clock (SIM vs UTC) | Icons|
+-----------------------------------------------------------------------------------------------+
| S | [ TOP-LEFT (1.2fr) ]          | [ TOP-MIDDLE (1.0fr) ]        | [ TOP-RIGHT (1.3fr) ]     |
| I | V2I/V2X Hardware Status       | Oak St & 5th Ave Phase Table  | Adaptive Signal Dashboard |
| D | OBU, RSU, Edge, Latency       | Approach, Red, Ylw, Grn, Split| Queue vs Capacity Chart   |
| E +-------------------------------------------------------------------------------------------+
| B |                                                                                           |
| A |                                 CENTER VIEWPORT (~55-60%)                                 |
| R |                               Three.js WebGL 3D Digital Twin                              |
|   |                  Isometric 3D Intersection, Vehicles, Signal Poles,                       |
|   |                     Dynamic Chevron Arrows & Emergency Corridor                           |
|   |                                                                                           |
|   | [Floating HUD: Digital Twin INT-0457 | V2X Active | Occ 76% | Avg Speed 52km/h | -19% ]   |
|   +-------------------------------------------------------------------------------------------+
|   | [ BOTTOM-LEFT (1.2fr) ]                               | [ BOTTOM-RIGHT (1.3fr) ]          |
|   | IoT Sensor Network & City Map Overview                | Traffic & Operations Analytics    |
|   | Sensor device counts, layer toggles, mini vector map  | Hourly volume bars, travel times, |
|   | with hospital marker & scale bar                      | radial gauge (82/100), alerts     |
+---+-------------------------------------------------------------------------------------------+
```

---

## 📸 Implemented Runtime Interface (Giao diện Thực tế Đã Hiện thực)

Dưới đây là 4 khung nhìn chính của hệ thống đã được triển khai hoàn chỉnh theo chuẩn kiến trúc:

<table align="center" width="100%">
<tr>
<td align="center" width="50%">
  <a href="../assets/screenshots/welcome-portal.jpg">
    <img src="../assets/screenshots/welcome-portal.jpg" width="100%" style="border-radius: 6px; border: 1px solid #1e293b;" alt="ClearWay AI Welcome Portal & Module Hub"/>
  </a>
  <br/><b>1. Welcome Portal & Operations Hub</b>
  <br/><i>Lobby điều hướng trung tâm với 3 phân hệ chính: Operations Dashboard, 3D Digital Twin View và SUMO Microscopic Simulation.</i>
</td>
<td align="center" width="50%">
  <a href="../assets/screenshots/operations-dashboard.jpg">
    <img src="../assets/screenshots/operations-dashboard.jpg" width="100%" style="border-radius: 6px; border: 1px solid #1e293b;" alt="Integrated Real-Time Operations Dashboard"/>
  </a>
  <br/><b>2. Real-Time Operations Dashboard</b>
  <br/><i>Bảng điều hành tác chiến tích hợp: V2X telemetry, pha đèn nút giao INT-0457, biểu đồ thích ứng RL/Heuristic và khung nhìn 3D Digital Twin trung tâm.</i>
</td>
</tr>
<tr>
<td align="center" width="50%">
  <a href="../assets/screenshots/digital-twin-3d.jpg">
    <img src="../assets/screenshots/digital-twin-3d.jpg" width="100%" style="border-radius: 6px; border: 1px solid #1e293b;" alt="Full-Screen 3D WebGL Digital Twin Viewport"/>
  </a>
  <br/><b>3. Full-Screen 3D WebGL Digital Twin</b>
  <br/><i>Khung nhìn bản sao kỹ thuật số 3D toàn màn hình kiểm tra chi tiết giao lộ và hành lang 1.000m (Nodes A–D) với góc xoay tự do và Chase Camera bám theo xe cấp cứu.</i>
</td>
<td align="center" width="50%">
  <a href="../assets/screenshots/analytics-iot-map.jpg">
    <img src="../assets/screenshots/analytics-iot-map.jpg" width="100%" style="border-radius: 6px; border: 1px solid #1e293b;" alt="IoT Sensor Network & Operations Analytics"/>
  </a>
  <br/><b>4. IoT Sensor Network & GIS Operations Analytics</b>
  <br/><i>Mạng lưới 306 cảm biến IoT/RSU, bản đồ hành lang cấp cứu GIS thời gian thực, biểu đồ lưu lượng phương tiện và bảng nhật ký bất thường sự cố.</i>
</td>
</tr>
</table>

---

## 2. Color System & Design Tokens

### 2.1 Backgrounds & Surfaces

| Token Name | Hex Code | RGB | Purpose |
| :--- | :--- | :--- | :--- |
| `--bg-main` | `#070D1E` | `rgb(7, 13, 30)` | Global viewport background |
| `--bg-shell` | `#0B152D` | `rgb(11, 21, 45)` | Sidebar, sub-containers, tooltips |
| `--bg-card` | `#0D1B38` | `rgb(13, 27, 56)` | Panel card body background |
| `--bg-card-header`| `#122347` | `rgb(18, 35, 71)` | Panel card header bar |
| `--bg-card-sub` | `#0A1128` | `rgb(10, 17, 40)` | Nested chart boxes, table rows |

### 2.2 Borders & Dividers

| Token Name | Hex Code | RGB | Purpose |
| :--- | :--- | :--- | :--- |
| `--border-card` | `#1B2F5B` | `rgb(27, 47, 91)` | Primary panel boundary (1px solid) |
| `--border-subtle` | `#162547` | `rgb(22, 37, 71)` | Inner grid lines, table cell dividers |
| `--border-accent` | `#00E5FF` | `rgb(0, 229, 255)` | Active selection highlight |

### 2.3 Semantic Status & Telemetry Accents

| Token Name | Hex Code | Semantic Role | Reference Usage in Image |
| :--- | :--- | :--- | :--- |
| `--accent-cyan` | `#00E5FF` | V2X Telemetry, Primary Flow | OBU lines, queue curves, active route |
| `--accent-teal` | `#00F5D4` | Brand Accent, Positive | Header brand icon, RSU icons |
| `--accent-green` | `#06D6A0` | Online, Green Phase, Benefit | 100% online, green light, -19% delay |
| `--accent-yellow` | `#FFD166` | Amber Phase, Warning | Signal yellow (4s), rising queue alert |
| `--accent-red` | `#EF476F` | Red Phase, Critical, Conflict | Signal red (67s/49s), emergency alert |
| `--accent-blue` | `#38BDF8` | Corridor Ribbon, Hospital H | Ambulance chevron path, hospital icon |

### 2.4 Typography Colors

| Token Name | Hex Code | Purpose |
| :--- | :--- | :--- |
| `--text-primary` | `#F8FAFC` | Main headings, primary values |
| `--text-secondary`| `#CBD5E1` | Secondary labels, table text |
| `--text-muted` | `#94A3B8` | Column headers, units (veh/h, km/h, m) |
| `--text-dim` | `#64748B` | Footnotes, inactive indicators |

---

## 3. Typography Guidelines

- **Primary Font Family:** `Inter`, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif.
- **Monospace Metric Font:** `JetBrains Mono`, "SF Mono", Consolas, monospace.
- **Font Scale:**
  - App Header Brand: `15px` / `700` weight
  - Panel Headers: `13px` / `600` weight (letter-spacing: `0.02em`)
  - Big KPI Values: `20px–24px` / `800` weight (monospace)
  - Table Cell Text: `11px–12px` / `500` (labels), `700` (durations)
  - Micro Callouts: `9px–10px` / `600` weight

---

## 4. Detailed Panel Specifications

### 4.1 TopBar (Height: 48px)
- **Left:** "Smart City Operations Suite" divider "ClearWay AI — Traffic Control Digital Twin".
- **Center:** Safety Gate badge: `● SIMULATION ONLY` | `DEMO FIXTURE`.
- **Right:**
  - Live mode pill: `● LIVE SIM` (Green glow).
  - Dual Timestamps: Simulation Time (`2025-01-15 14:27:36 (SIM)`) and Host Clock (`Host UTC: HH:MM:SS`).
  - Notification bell with unread badge count `4`.
  - Settings icon and operator profile avatar `OP`.

### 4.2 Top-Left: V2I/V2X Communication & Hardware Status (1.2fr)
- **Network ID:** `RM-INT-0457`.
- **4 Connected Nodes:**
  1. *On-Board Units (Vehicles):* 1,842 Online (99.2%).
  2. *RSU (Roadside Unit):* 42 Online (100%).
  3. *Edge Controller (Intersection):* Online (Primary).
  4. *Signal Controller (8 Phases):* Online (V2I C-V2X / DSRC).
- **Status Footer:** V2X Status: Active, Latency: 11 ms, Packet Loss: 0.2%.

### 4.3 Top-Middle: Oak St. & 5th Ave Approach Split Timing (1.0fr)
- **Intersection ID:** `INT-0457`.
- **Timing Table:**
  | Approach | Red | Yellow | Green | Cycle | Split |
  | :--- | :---: | :---: | :---: | :---: | :---: |
  | N - Oak St. (NB) | 67s | 4s | 49s | 120s | 41% |
  | S - Oak St. (SB) | 67s | 4s | 49s | 120s | 41% |
  | E - 5th Ave. (EB) | 49s | 4s | 67s | 120s | 56% |
  | W - 5th Ave. (WB) | 49s | 4s | 67s | 120s | 56% |

### 4.4 Top-Right: Adaptive Traffic Signal Control Dashboard (1.3fr)
- **Cycle Time:** `120s`.
- **Current Phase:** `P3 (E-W Thru)`.
- **Next Phase:** `P4 (E-W Left)`.
- **Queue vs Capacity Chart:**
  - X-Axis: 0 to 120s (ticks: 30, 60, 90, 120s).
  - Y-Axis: Queue (veh) 0 to 120 (ticks: 40, 80, 120).
  - Cyan curve: Queue (veh).
  - Red dashed stepped line: Capacity.
  - Occupancy badge: `76%`.
- **Phase Optimization KPI:** `↓ -19% Delay (vs. fixed-time)`.
- **Congestion Metrics:** `Avg. Queue: 87 m`, `Backlog: 45 m`.

### 4.5 Center: 3D WebGL Digital Twin Viewport (~55-60% height)
- **Scene Objects:**
  - 4-way signalized intersection with dedicated left/right turn lanes, crosswalk zebra stripes, lane division lines, stoplines.
  - Contextual multi-story urban buildings with glass facade textures and street-level storefronts.
  - Sidewalks, street lamps, traffic light poles with emissive lens materials.
  - Vehicles: >= 1 ambulance with animated emergency strobes, passenger sedans, SUVs, buses, and Vietnamese motorcycles.
  - Dynamic route overlays: Curved green ribbons for standard flow, red curves for conflict movements, blue dotted chevron path for emergency corridor.
  - Vehicle speed callout badges: `57 km/h`, `46 km/h`, `68 km/h`.
  - Emergency Mission floating callout: `Emergency Route Active (AMB-339) | ETA to Hospital: 3.4 min`.
  - Floating bottom telemetry pill: `Digital Twin INT-0457 | V2X Status Active | Occupancy 76% | Avg. Speed 52 km/h | Delay -19%`.

### 4.6 Bottom-Left: IoT Sensor Network & City Map Overview (1.2fr)
- **Sensor Inventory:**
  - Traffic Cameras: `112 / 112 Online` (Red camera icon)
  - LiDAR Sensors: `48 / 48 Online` (Cyan radar icon)
  - Loop Detectors: `96 / 96 Online` (Blue disc icon)
  - RSUs (V2I): `42 / 42 Online` (Yellow radio tower icon)
  - Signal Controllers: `8 / 8 Online` (Green CPU icon)
- **Data Layers (City) Checkboxes:**
  - [x] Traffic Flow
  - [x] Sensor Coverage
  - [x] V2X Network
  - [x] Incident / Event
  - [x] Emergency Corridor
  - [ ] Parking Occupancy
- **Mini Vector City Map:**
  - Arterial street grid with highlighted corridor route (cyan dotted line).
  - Intersection sensor node markers.
  - Hospital marker `H` (blue box).
  - Compass Rose `N` and metric scale bar (`0 250 500 1,000 m`).

### 4.7 Bottom-Right: Traffic & Operations Analytics (1.3fr)
- **Real-time Traffic Volume (veh/h):**
  - NB: 1,210 veh/h
  - SB: 1,438 veh/h
  - EB: 2,185 veh/h
  - WB: 2,061 veh/h
- **Average Travel Time (intersection zone):**
  - N → S: `2.6 min (-18%)`
  - S → N: `2.8 min (-17%)`
  - E → W: `3.9 min (+6%)`
  - W → E: `3.7 min (+4%)`
- **Intersection Performance Index:**
  - Circular radial gauge: `82 / 100` (+7 pts vs last hour).
  - Throughput: `+15%`.
  - Avg. Delay: `-19%`.
  - Stops / Veh: `-22%`.
- **Anomaly Detection & Alerts:**
  - `Critical:` Emergency vehicle route active (AMB-339) — priority control in progress.
  - `Warning:` Rising queue on 5th Ave. (EB) (87 m, +34% in 5 min).
  - `Warning:` Abnormal speed drop on Oak St. (SB) (avg 28 km/h, -46%).

---

## 5. Responsive Breakpoint Matrix

| Breakpoint | Dimensions | Layout Behavior |
| :--- | :--- | :--- |
| **Reference (1:1)** | `1254 × 1254` | Exact square proportions matching user blueprint image. |
| **Standard Laptop** | `1440 × 900` | Full 3-tier view, padding: 8px, 3D viewport height ~380px. |
| **Full HD Desktop** | `1920 × 1080` | Spacious 3-tier view, padding: 12px, 3D viewport height ~520px. |
| **Small Display** | `1280 × 800` | Compact metrics, internal scroll on tables if needed. |

