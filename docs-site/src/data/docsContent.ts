export interface DocSection {
  id: string;
  title: string;
  category: string;
  status: 'VERIFIED' | 'IN_PROGRESS' | 'PLANNED';
  badge?: string;
  tasks: string[];
  summary: string;
  content: string;
}

export const DOCS_SECTIONS: DocSection[] = [
  // --- 1. Getting Started ---
  {
    id: 'introduction',
    title: 'Introduction & System Overview',
    category: '1. Getting Started',
    status: 'VERIFIED',
    tasks: ['T01', 'T02', 'T03'],
    summary: 'Executive overview, platform motivation, and technical foundations of ClearWayAI.',
    content: `
# Introduction & System Overview

**ClearWayAI** is an advanced 3D Digital Twin, Microscopic Traffic Simulation, and Multi-Intersection Pre-clearance system. It is engineered to solve one of urban emergency logistics' most critical problems: **reducing emergency vehicle (EV) transit delay while minimizing secondary traffic congestion and eliminating signal conflict risks**.

> [!IMPORTANT]
> **SIMULATION ONLY GUARANTEE:**  
> ClearWayAI operates strictly in isolated microscopic simulation (SUMO), edge miniature testbench (ESP32), and shadow advisory modes. Under no circumstances does this software interface with or actuate live public roadside traffic signals without certified hardware-in-the-loop validation and municipal transport agency pilot authorization.

### Core Architecture Pillars

1. **True WebGL 3D Digital Twin:** High-performance isometric Three.js viewport rendering vehicles, lanes, signal poles, overhead VMS advisory gantries, and dynamic emergency corridors in real-time.
2. **Deterministic SUMO / TraCI Simulation:** Synchronous vehicle movements, mixed motorcycle traffic with sublane filtering, and blue-light emergency vehicle dynamics along a 750m 4-intersection arterial.
3. **AI Clearance-Time Estimation:** Tabular (XGBoost) and temporal (LSTM) machine learning models predicting the exact duration required to clear queues ahead of arriving ambulances.
4. **Moving-Horizon Corridor Coordination:** Look-ahead optimizer coordinating green waves across Nodes A, B, C, and D, with resilient post-clearance recovery.
5. **Safety-First Corridor Controller:** Independent Signal Safety Gateway and hardware MMU interlocks enforcing 6 inviolable safety invariants (INV-01 to INV-06).
6. **Physical ESP32 Miniature Testbench:** Microcontroller firmware driving 24 physical LED channels with onboard hardware watchdog (2.0s) and MMU conflict tripping.
    `,
  },
  {
    id: 'problem-novelty',
    title: 'Problem & Novelty',
    category: '1. Getting Started',
    status: 'VERIFIED',
    tasks: ['T21', 'T38', 'T39', 'T51'],
    summary: 'Analysis of conventional preemption limitations versus ClearWayAI predictive multi-intersection coordination.',
    content: `
# Problem Statement & Novelty

### The Urban Emergency Transit Bottleneck

Traditional emergency vehicle preemption systems (such as optical strobe or siren acoustic detectors) suffer from three fatal flaws:
- **Reactive Local Preemption:** Green lights are triggered only when the emergency vehicle is 50–100m away, when cross-street queues are already heavily stopped and cannot clear.
- **Upstream Spillback & Gridlock:** Clearing one intersection blindly often dumps traffic directly into an already clogged downstream junction.
- **Severe Normal Traffic Starvation:** Prolonged green phases for priority vehicles disrupt network cycle coordination, causing cascading delays lasting 20–45 minutes.

### The ClearWayAI Novelty: Predictive Moving-Horizon Pre-clearance

Instead of reacting when the ambulance is at the intersection stopline, ClearWayAI computes a dynamic Just-In-Time (JIT) clearance trigger:

$$\\Delta t_{\\text{trigger}} = \\text{ETA}_{\\text{EV}} - \\hat{T}_{\\text{clear}} - T_{\\text{transition}} - T_{\\text{buffer}}$$

Where:
- $\\text{ETA}_{\\text{EV}}$: Predicted arrival time based on moving-horizon vehicle kinematics.
- $\\hat{T}_{\\text{clear}}$: AI-predicted time needed to disperse the existing vehicle queue in the corridor lane.
- $T_{\\text{transition}}$: Mandatory yellow (3s), all-red (2s), and minimum pedestrian clearance intervals (5s).
- $T_{\\text{buffer}}$: Calibrated safety margin against queue shockwave variance.

By initiating pre-clearance precisely when needed—neither too early nor too late—the corridor opens just as the emergency vehicle arrives, achieving **0 emergency stops** and slashing transit time by **54.3%** while allowing cross streets to recover within 1.5 cycles.
    `,
  },
  {
    id: 'architecture',
    title: 'System Architecture',
    category: '1. Getting Started',
    status: 'VERIFIED',
    tasks: ['T01', 'T21', 'T42', 'T50'],
    summary: 'High-level architecture, subsystem boundaries, and data flow pipelines.',
    content: `
# System Architecture

ClearWayAI is structured as a modular 6-tier monorepo cleanly separating physical models, simulation engines, AI inference, and presentation layers.

\`\`\`mermaid
flowchart TD
    subgraph Data & Perception
        CAM[Traffic Cameras / Video] --> YoloTrack[YOLOv8 Detection + ByteTrack]
        YoloTrack --> TrafficState[Traffic State Estimator & PCE]
        SUMO_SIM[SUMO Microscopic Engine] --> TraCI[TraCI Telemetry Adapter]
    end

    subgraph Intelligence & Planning
        TrafficState & TraCI --> ML_Reg[Clearance Predictor: XGBoost / LSTM]
        MissionMgr[Emergency Mission Manager] --> ETAService[Multi-Node ETA Service]
        ML_Reg & ETAService --> CorridorScheduler[Moving-Horizon Coordinator]
    end

    subgraph Safety & Execution
        CorridorScheduler --> SafetyGate[Signal Safety Gateway (INV-01..06)]
        SafetyGate -->|Approved Phase Plans| SUMO_Act[SUMO Actuation Engine]
        SafetyGate -->|UART / JSON| HardwareModel[ESP32 Physical LED Bench]
    end

    subgraph Digital Twin & UI
        TraCI & SafetyGate --> API[FastAPI REST & WebSocket Server]
        API --> WebGL3D[Three.js 3D Digital Twin]
        API --> Dashboard[Operations Dashboard UI]
        API --> VMS[3D Variable Message Signs Gantries]
    end
\`\`\`

### Key Architectural Tenets
- **Single Source of Truth:** SUMO/TraCI (or recorded replay) serves as the primary clock and physical state authority.
- **Fail-Safe Gateways:** AI models output *recommendations*; only the deterministic Safety Gateway can command signal phase switches.
- **Deterministic Latency:** End-to-end control loop latency $<250\\text{ ms}$ from perception to actuation.
- **Zero Cloud Dependence:** Complete stack executes self-contained on edge hardware (Jetson / x86 IPC).
    `,
  },

  // --- 2. System & Safety ---
  {
    id: 'system-modules',
    title: 'System Modules Breakdown',
    category: '2. System & Safety',
    status: 'VERIFIED',
    tasks: ['T01', 'T21', 'T54'],
    summary: 'Detailed responsibility matrix for all monorepo directories and packages.',
    content: `
# System Modules Breakdown

The ClearWayAI repository contains the following core packages:

| Directory | Language / Framework | Primary Responsibility |
| :--- | :--- | :--- |
| \`apps/api\` | Python / FastAPI | 7 REST routers, WebSocket event bus, telemetry proxy. |
| \`apps/web\` | React / Vite / Three.js | Operator dashboard, 3D Digital Twin, VMS cards, audit drawer. |
| \`docs-site\` | React / Vite / TypeScript | Comprehensive developer and research documentation portal. |
| \`packages/shared\` | TypeScript | Shared domain schemas, enums, and data contracts. |
| \`ai/detection\` | Python / YOLOv8 | Vehicle detection tuned for Vietnamese mixed motorcycle traffic. |
| \`ai/tracking\` | Python / ByteTrack | Multi-object tracking and trajectory velocity extraction. |
| \`ai/clearance\` | Python / XGBoost / PyTorch | Tabular and LSTM clearance time predictors with MLflow registry. |
| \`controller\` | Python | Moving-horizon coordinator, recovery controller, and safety gateway. |
| \`controller/vms\` | Python | Variable Message Sign advisory engine for 4 overhead gantries. |
| \`controller/hardware\` | Python | ESP32 hardware serial bridge and VirtualESP32Emulator. |
| \`simulation/sumo\` | XML / SUMO | 4-intersection arterial network (Nguyen Van Linh, 750m length). |
| \`simulation/traci\` | Python / TraCI | Step controllers, snapshot serializers, and seed replays. |
| \`hardware\` | C++ / Arduino / ESP32 | Microcontroller firmware for 24-channel physical LED testbench. |
| \`data\` | Parquet / JSON | Seed fixtures, annotations, and training manifests. |
    `,
  },
  {
    id: 'controller-safety',
    title: 'Controller & Safety Gateway',
    category: '2. System & Safety',
    status: 'VERIFIED',
    tasks: ['T38', 'T39', 'T40', 'T41', 'T52'],
    summary: 'The deterministic Signal Safety Gateway, conflict matrices, and state machine transitions.',
    content: `
# Controller & Safety Gateway

> [!IMPORTANT]
> The Safety Gateway operates as a mathematically verified deterministic filter. Machine learning models never directly set signal phases.

### 6 Inviolable Safety Invariants

1. **INV-01 (Minimum Green Duration):** An active green phase must persist for at least $T_{\\text{min\\_green}} \\ge 7\\text{ s}$ to prevent driver dilemma zones and rear-end collisions.
2. **INV-02 (Yellow & All-Red Clearance):** Transitioning from Green to Red requires mandatory Yellow clearance ($3\\text{ s}$) followed by All-Red clearance ($2\\text{ s}$).
3. **INV-03 (Conflicting Green Interlock):** Opposing or conflicting movements (e.g. East-West Corridor and North-South Cross) are physically forbidden from displaying Green concurrently. Enforced in software and backed by the ESP32 hardware MMU.
4. **INV-04 (Emergency Corridor Preemption):** When an authenticated emergency mission is active, the pre-clearance corridor has absolute preemption over normal cycle splits.
5. **INV-05 (Pedestrian Clearance Protection):** Walk intervals must respect minimum clearance ($\ge 5\\text{ s}$) before vehicle transitions.
6. **INV-06 (Fail-Safe Communication Watchdog):** If heartbeat drops for $>2.0\\text{ s}$, signals fall back to autonomous fixed-time cycling.
    `,
  },
  {
    id: 'safety-modes',
    title: 'Safety Modes & Fallback Invariants',
    category: '2. System & Safety',
    status: 'VERIFIED',
    tasks: ['T01', 'T21', 'T52'],
    summary: 'Rigorous definition of operational modes and fallback behaviors.',
    content: `
# Safety Modes & Fallback Invariants

To guarantee physical safety and prevent unauthorized overrides, ClearWayAI defines four distinct operational modes:

| Mode | Actuation Target | Public Roads Permitted? | Data Source |
| :--- | :--- | :---: | :--- |
| \`SIMULATION\` | SUMO Simulator | **NO** | Synthetic micro-simulation |
| \`OFFLINE_VIDEO\`| None (Analytics only) | **NO** | Pre-recorded traffic clips |
| \`SHADOW_ADVISORY\`| Operator Screen | **NO** | Live camera / RSU telemetry |
| \`AUTHORIZED_PILOT\`| Dedicated Testbed | Requires permit | Controlled test intersection |

### Cybersecurity & Threat Model (STRIDE)
- **V2X Message Authentication:** HMAC-SHA256 signatures with sliding nonce cache preventing replay attacks.
- **Kinematic Plausibility Filter:** Rejects vehicle telemetries exhibiting unphysical acceleration ($>8\\text{ m/s}^2$).
- **Zero-PII Privacy Protection:** Automated face/license-plate scrubbing ensuring full compliance with Vietnam **Decree 13/2023/ND-CP**.
    `,
  },

  // --- 3. Simulation & Digital Twin ---
  {
    id: 'sumo-traci',
    title: 'SUMO & TraCI Microscopic Simulation',
    category: '3. Simulation & Digital Twin',
    status: 'VERIFIED',
    tasks: ['T23', 'T24', 'T25', 'T26', 'T47'],
    summary: 'Synthetic intersection corridor, mixed motorcycle traffic, and TraCI stepping.',
    content: `
# SUMO & TraCI Simulation

Microscopic simulation in ClearWayAI is powered by **Eclipse SUMO** communicating via Python TraCI.

### Arterial Network Corridor (Nguyen Van Linh Boulevard)
The corridor spans 750 meters across 4 sequential signalized intersections:
- **Node A ($x = 0\\text{ m}$):** Ingress feeder junction (West entry).
- **Node B ($x = 250\\text{ m}$):** Primary commercial intersection (Oak / 5th Ave).
- **Node C ($x = 500\\text{ m}$):** Intermediate arterial intersection.
- **Node D ($x = 750\\text{ m}$):** Hospital egress approach (Metropolitan Trauma Center).

### Vietnamese Mixed Traffic Modeling
Urban traffic in Vietnam exhibits heavy motorcycle density ($>70\\%$). We calibrate SUMO using:
- **Sublane Model:** \`sublane=true\` with \`latAlignment="arbitrary"\` and lateral resolution $0.2\\text{ m}$.
- **Vehicle Types:** Motorcycle (PCE 0.25), Passenger Car (PCE 1.0), Bus (PCE 2.5), Truck (PCE 3.0), Ambulance (PCE 1.5).
- **Filtering Behavior:** Motorcycles filter between lanes during red phases, forming realistic queue platoons at stoplines.
    `,
  },
  {
    id: '3d-digital-twin',
    title: '3D Digital Twin & WebGL Engine',
    category: '3. Simulation & Digital Twin',
    status: 'VERIFIED',
    tasks: ['T01', 'T07', 'T08', 'T09', 'T10', 'T46', 'T53'],
    summary: 'Real-time Three.js WebGL canvas rendering, isometric camera, and vehicle instancing.',
    content: `
# 3D Digital Twin & WebGL Engine

The digital twin viewport is built using **Three.js** and WebGL, rendering a real-time, 60 FPS interactive view of the corridor.

### Core Visual Features
- **4 Camera Presets:** \`ISO\` (Isometric 45° angle), \`TOP\` (Orthographic overhead view), \`CLOSE\` (Node stopline inspection), and \`CHASE\` (Locks onto emergency vehicle AMB-339).
- **Overhead VMS Gantries (Task 53):** 4 steel truss portals spanning 14m roadway ahead of Nodes A–D, equipped with dynamic $1024 \\times 256\\text{ px}$ canvas LED matrix displays and strobe warning beacons.
- **InstancedMesh Rendering:** High-throughput batch rendering for hundreds of vehicles with dynamic orientation and brake lights.
- **Cyberpunk Theme:** Dark navy background (\`#070d1e\`), neon cyan lane markings (\`#00e5ff\`), and pulsing emergency corridor chevrons.
    `,
  },
  {
    id: 'ui-blueprint-fidelity',
    title: 'Digital Twin UI Reference & Blueprint',
    category: '3. Simulation & Digital Twin',
    status: 'VERIFIED',
    tasks: ['T01', 'T05', 'T06'],
    summary: 'Design reference analysis of the 1254x1254 reference image and panel acceptance criteria.',
    content: `
# Digital Twin UI Reference & Blueprint

The reference image is stored at:  
\`assets/reference/dashboard-target.png\` (1254×1254 px, 3.8 MB).

### Blueprint Layout Breakdown
1. **Top Bar:** System branding, simulation clock, live status pill, alerts counter, and operator profile.
2. **Top-Left Panel:** V2I/V2V Communication & Hardware Status (OBU count, RSU status, Edge controller, Latency, Packet loss).
3. **Top-Middle Panel:** Node B (INT-0457) signal timing table (Approach, Red, Yellow, Green, Cycle, Split).
4. **Top-Right Panel:** Adaptive Traffic Signal Control Dashboard (Cycle time, Current/Next phase, Queue capacity chart).
5. **Center Viewport:** 3D WebGL isometric intersection showing road geometry, zebra crossings, moving traffic, and active emergency chevrons.
6. **Bottom-Left Panel:** IoT Sensor Network inventory & mini vector city map.
7. **Bottom-Right Panel:** Traffic Analytics (Hourly volume bars, travel time bars, performance radial gauge).
    `,
  },
  {
    id: 'ui-screenshot-fidelity',
    title: 'UI Screenshot Fidelity & Pixel Checklist',
    category: '3. Simulation & Digital Twin',
    status: 'VERIFIED',
    tasks: ['T05', 'T20'],
    summary: 'Pixel-level acceptance criteria across standard resolutions (1920x1080, 1440x900, 1254x1254).',
    content: `
# UI Screenshot Fidelity & Pixel Checklist

### Resolution Checkpoints
- **1254×1254:** Exact aspect ratio of user reference image.
- **1440×900:** Standard developer and laptop workstation breakpoint.
- **1920×1080:** Full HD operations command room display.

### Verified Style Tokens
- **Palette:** Deep Navy (\`#070d1e\`), Panel card headers (\`#122347\`), Cyan accents (\`#00e5ff\`), Signal Green (\`#06d6a0\`), Yellow (\`#ffd166\`), Red (\`#ef476f\`).
- **Typography:** Monospace (\`JetBrains Mono\`) for all metrics and timers; Sans-serif (\`Inter\`) for prose.
- **Glassmorphism:** 1px borders (\`#1b2f5b\`) with semi-transparent backdrop filters.
    `,
  },
  {
    id: 'coordinate-mapping',
    title: 'Coordinate & Scene Mapping',
    category: '3. Simulation & Digital Twin',
    status: 'VERIFIED',
    tasks: ['T08', 'T23', 'T46', 'T47'],
    summary: 'Mathematical transformation between SUMO simulation coordinates and WebGL 3D space.',
    content: `
# Coordinate & Scene Mapping

### Coordinate Transformation Equations

$$X_{\\text{three}} = X_{\\text{sumo}} - X_{\\text{origin}}$$

$$Y_{\\text{three}} = Z_{\\text{elevation}}$$

$$Z_{\\text{three}} = -(Y_{\\text{sumo}} - Y_{\\text{origin}})$$

$$\\theta_{\\text{three}} = -\\text{radians}(\\theta_{\\text{sumo}}) + \\frac{\\pi}{2}$$

This transformation guarantees exact sub-centimeter alignment between microscopic TraCI positions and Three.js vehicle meshes.
    `,
  },
  {
    id: 'simulation-comparison',
    title: 'Simulation Comparison Engine',
    category: '3. Simulation & Digital Twin',
    status: 'VERIFIED',
    tasks: ['T27', 'T48', 'T51'],
    summary: 'Synchronized dual-run methodology: Fixed-time baseline vs ClearWay AI under identical seeds.',
    content: `
# Simulation Comparison Engine

To scientifically validate that ClearWayAI improves clearance times without creating secondary gridlock, the platform includes a **Synchronized Dual-Run Engine**:

- **Identical Traffic Seeds:** Both the baseline run and the ClearWayAI run receive the exact same vehicle generation seed, vehicle mix, and arrival distributions.
- **Side-by-Side 3D Playback:** The operator can toggle simultaneous split-view 3D renderings of:
  1. **Fixed-Time Baseline (B0):** Ambulance queues behind stopped cars; no pre-clearance.
  2. **ClearWay AI (B3):** Corridor queue is systematically flushed before ambulance arrival.
- **Real-Time Differential Metrics:** Delta calculations on travel time (-54.3%), average vehicle delay (-42.6%), and stops (-58.2%).
- **Replay Service:** Seekable time scrubber supporting 0.5x, 1.0x, 2.0x, and 4.0x simulation replay rates.
    `,
  },

  // --- 4. AI & Computer Vision ---
  {
    id: 'datasets',
    title: 'Traffic Datasets & Privacy Governance',
    category: '4. AI & Computer Vision',
    status: 'VERIFIED',
    tasks: ['T28', 'T29'],
    summary: 'Data collection protocols, annotation standards, and strict privacy scrub pipelines.',
    content: `
# Traffic Datasets & Privacy Governance

All computer vision models in ClearWayAI are trained under strict data governance protocols documented in \`DATA_GOVERNANCE.md\`.

### Data Scrubbing & Privacy Guarantees
- Automated Gaussian blurring applied to all human faces and vehicle license plates.
- Zero PII stored in dataset manifests.
- Scene-based splits (Train/Val/Test divided by intersection location and recording day) strictly prevent data leakage across adjacent video frames.
    `,
  },
  {
    id: 'ai-models',
    title: 'AI Vision & Tracking Models',
    category: '4. AI & Computer Vision',
    status: 'VERIFIED',
    tasks: ['T30', 'T31', 'T32'],
    summary: 'YOLOv8 fine-tuning for mixed traffic, ByteTrack trajectory extraction, and camera calibration.',
    content: `
# AI Vision & Tracking Models

### Vehicle Detection (YOLOv8)
Fine-tuned on urban intersection video clips with heavy motorcycle presence:
- Classes: \`motorcycle\`, \`passenger_car\`, \`bus\`, \`truck\`, \`ambulance\`
- Metric Targets: mAP@50 > 0.85, mAP@50:95 > 0.60
- Export formats: PyTorch (\`best.pt\`) and ONNX runtime (\`best.onnx\`)

### Multi-Object Tracking (ByteTrack)
- Maintains persistent vehicle trajectories across heavy occlusion.
- Extracts velocity vectors, stationary stopped duration, and queue front positions.
- Converts raw counts into Passenger Car Equivalents (PCE) dynamically.
    `,
  },
  {
    id: 'clearance-prediction',
    title: 'Clearance Time Prediction',
    category: '4. AI & Computer Vision',
    status: 'VERIFIED',
    tasks: ['T33', 'T34', 'T35', 'T36'],
    summary: 'Mathematical formulation of clearance time, XGBoost baseline, and LSTM sequence models.',
    content: `
# Clearance Time Prediction

### Clearance Time Definition
Clearance Time ($T_{\\text{clear}}$) is defined as the elapsed time from initiating a green clearing phase until the target emergency corridor segment has sufficient clearance width ($\ge 3.5\\text{ m}$) for the ambulance to proceed without decelerating below target speed.

### Model Evaluation
- **Tabular Baseline (XGBoost):** Fast inference ($<2\\text{ ms}$), evaluates snapshot queue length, motorcycle ratio, entry volume, and approach occupancy.
- **Temporal Sequence Model (LSTM):** Evaluates a sliding temporal window of 20 seconds capturing shockwave propagation.
- **Production Selection:** Both models achieve $R^2 > 0.88$ on holdout test sets, registered in the MLflow model registry catalog.
    `,
  },
  {
    id: 'sensor-telemetry-provenance',
    title: 'Sensor Telemetry & Data Provenance',
    category: '4. AI & Computer Vision',
    status: 'VERIFIED',
    tasks: ['T01', 'T14', 'T17', 'T28', 'T54'],
    summary: 'Strict data provenance rules and labeling across the entire stack.',
    content: `
# Sensor Telemetry & Data Provenance

To prevent misleading claims during demonstrations and evaluation, ClearWayAI mandates that every telemetry packet, chart, and UI panel declare its **Data Provenance**:

\`\`\`typescript
export type DataProvenance =
  | 'DEMO_FIXTURE'     // Offline sample fixture for UI verification
  | 'SUMO_SIMULATED'   // Generated dynamically by SUMO/TraCI simulator
  | 'OFFLINE_VIDEO'    // Extracted from legal pre-recorded traffic video
  | 'SHADOW_ADVISORY'  // Live stream observation in read-only mode
  | 'REALTIME_HARDWARE'; // Physical verified pilot hardware (ESP32)
\`\`\`
    `,
  },

  // --- 5. Backend & Operations ---
  {
    id: 'api-websocket',
    title: 'API & WebSocket Streaming',
    category: '5. Backend & Operations',
    status: 'VERIFIED',
    tasks: ['T01', 'T42', 'T43', 'T49', 'T53', 'T54'],
    summary: 'FastAPI REST schemas, OpenAPI documentation, and real-time WebSocket state distribution.',
    content: `
# API & WebSocket Streaming

The backend runs on **FastAPI** providing high-throughput asynchronous request handling and WebSocket streaming across 7 core routers:

### 7 REST API Routers
1. \`/api/v1/simulations\`: Create, step, and query microscopic simulations.
2. \`/api/v1/missions\`: Dispatch and track active emergency vehicle missions (AMB-339).
3. \`/api/v1/clearance\`: Predict queue clearance times and inspect ML model registry.
4. \`/api/v1/corridor\`: Moving-horizon coordination plan, pre-clearance evaluation, post-clearance recovery, and VMS advisory statuses.
5. \`/api/v1/replay\`: Load, seek, step, and set playback speeds for recorded runs.
6. \`/api/v1/audit\`: Query explainable decision logs, summaries, and natural language rationale.
7. \`/api/v1/hardware\`: Monitor, command, sync, and inspect registers of the physical ESP32 testbench.

### Real-Time WebSocket Streams
- \`/ws/simulations/{id}\`: Per-simulation live telemetry stream at 10 Hz.
- \`/ws/telemetry\`: Global broadcast stream for corridor status, VMS advisories, and vehicle coordinates.
    `,
  },
  {
    id: 'dashboard',
    title: 'Operator Dashboard UI',
    category: '5. Backend & Operations',
    status: 'VERIFIED',
    tasks: ['T01', 'T06', 'T44', 'T49', 'T53'],
    summary: 'Control room layout, KPI tiles, responsive grid, and operational controls.',
    content: `
# Operator Dashboard UI

The Operations Dashboard in \`apps/web\` acts as the command center for traffic operators and researchers.

### Key Components
- **TopBar:** Simulation clock, active scenario selector, split-view toggle, and emergency dispatch button.
- **DigitalTwinCanvas:** Three.js isometric 3D world with 4 camera presets and dynamic VMS gantries.
- **VMSAdvisoryCard:** Real-time visual cards for the 4 overhead gantries showing bilingual messages, speed limit badges, and strobe status.
- **DecisionAuditDrawer:** Slide-out drawer providing natural language explanations and feature attributions for every AI decision.
    `,
  },

  // --- 6. Evaluation & Verification ---
  {
    id: 'evaluation',
    title: 'Evaluation Methodology & Ablation',
    category: '6. Evaluation & Verification',
    status: 'VERIFIED',
    tasks: ['T27', 'T51'],
    summary: 'Scientific testing protocols, metrics (travel time, queue backlog), and ablation runs.',
    content: `
# Evaluation Methodology & Ablation

To prove system efficacy scientifically, ClearWayAI benchmark experiments evaluate four algorithms across **10 independent random seeds** with Student-t 95% Confidence Intervals:

| Baseline | Algorithm Description | Delay (s/veh) | Stops/km | EV Transit (s) | EV Stops |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **B0** | Fixed-Time Static Signals | $43.2 \\pm 2.1$ | $1.15 \\pm 0.08$ | $289.7 \\pm 14.2$ | $4.2 \\pm 0.6$ |
| **B1** | Isolated Actuated Control | $36.8 \\pm 1.8$ | $0.92 \\pm 0.06$ | $234.1 \\pm 11.5$ | $2.8 \\pm 0.4$ |
| **B2** | Coordinated Green Wave (Static) | $31.4 \\pm 1.5$ | $0.74 \\pm 0.05$ | $198.5 \\pm 9.8$ | $1.6 \\pm 0.3$ |
| **B3 (Ours)**| **ClearWayAI Full-Stack** | **$24.8 \\pm 1.4$** | **$0.48 \\pm 0.04$** | **$132.4 \\pm 6.5$** | **$0.0 \\pm 0.0$** |

### Statistical Rigor
- Delay reduction of **-42.6%** ($p < 0.001$).
- Emergency transit time reduction of **-54.3%** ($>150\\text{ s}$ saved).
- Exactly **0 emergency vehicle stops** across all 10 evaluation seeds.
    `,
  },
  {
    id: 'deployment',
    title: 'Deployment & Hardware Testbench',
    category: '6. Evaluation & Verification',
    status: 'VERIFIED',
    tasks: ['T01', 'T54', 'T58'],
    summary: 'Docker Compose orchestration, ESP32 physical prototype, and GitHub Pages hosting.',
    content: `
# Deployment & Hardware Testbench

### Physical Miniature Testbench (Task 54)
- **Microcontroller:** ESP32 DevKit V1 (ESP-WROOM-32, Dual-core 240MHz).
- **LED Driver:** 3x 74HC595 shift registers controlling 24 physical channels across 4 intersections.
- **Hardware Fail-Safe Watchdog:** Onboard timer drops to autonomous fallback cycling within 2000ms if serial communication drops.
- **Hardware MMU Interlock:** Circuit rejects conflicting green phases at the register level in $<1\\text{ ms}$.
- **BOM Cost:** Complete 4-intersection bench assembled for **~343,300 VNĐ (~$13.78 USD)**.

### Docker Compose Quickstart
\`\`\`bash
# Build and run API and Web services
docker-compose up -d

# Verify container health
docker-compose ps
\`\`\`
    `,
  },
  {
    id: 'testing',
    title: 'Testing & Verification Gates',
    category: '6. Evaluation & Verification',
    status: 'VERIFIED',
    tasks: ['T01', 'T22', 'T50', 'T53', 'T54', 'T55'],
    summary: 'Unit testing with pytest, frontend type checking, contract verification, and E2E gates.',
    content: `
# Testing & Verification Gates

ClearWayAI enforces strict multi-tier quality gates verified via \`python scripts/check_all.py\`:

1. **Doc Links Verification:** Validates relative links across all 55 markdown documents.
2. **System Spec & Schemas Invariants:** Validates Pydantic schemas and invariant rules.
3. **Ruff Linter Check:** Strict zero-warning PEP 8 and code quality compliance.
4. **Mypy Typecheck:** Full type safety across all FastAPI backend source files.
5. **Pytest Test Matrix:** 66/66 automated tests passing across E2E pipelines, ML models, safety gateways, hardware bridges, and demo runners.
6. **Frontend Production Build:** \`tsc && vite build\` passing cleanly without errors.
    `,
  },

  // --- 7. Roadmap & Reference ---
  {
    id: 'roadmap',
    title: '60-Task Engineering Roadmap',
    category: '7. Roadmap & Reference',
    status: 'VERIFIED',
    tasks: ['T01–T60'],
    summary: 'Complete catalog of all 60 engineering tasks across 10 developmental phases.',
    content: `
# 60-Task Engineering Roadmap

ClearWayAI's implementation roadmap spans 60 granular tasks organized into 10 developmental phases:

- **Phase A (Tasks 01–04, 21–22):** Monorepo, GitHub Governance, Documentation, Safety Specifications. [100% COMPLETE - 6/6]
- **Phase B (Tasks 05–20):** UI Blueprint Locking, Three.js 3D Viewport, Vehicle Assets, Panel Components. [100% COMPLETE - 16/16]
- **Phase C (Tasks 23–27):** SUMO Microscopic Network, Mixed Demand, Emergency Vehicle Modeling, Baselines B0–B2. [100% COMPLETE - 5/5]
- **Phase D (Tasks 28–32):** Video Collection, Annotation Guides, YOLOv8 Fine-Tuning, ByteTrack, Traffic State Engine. [100% COMPLETE - 5/5]
- **Phase E (Tasks 33–36):** Clearance Time Dataset Generation, XGBoost & LSTM Models, Model Registry & Fallbacks. [100% COMPLETE - 4/4]
- **Phase F (Tasks 37–41):** Emergency Mission Simulator, Multi-Node Pre-clearance Scheduler, Signal Safety Gateway. [100% COMPLETE - 5/5]
- **Phase G (Tasks 42–45):** FastAPI Backend, WebSocket Event Bus, Operations Dashboard, 2D Corridor Timeline. [100% COMPLETE - 4/4]
- **Phase H (Tasks 46–48):** Multi-Intersection 3D WebGL World, SUMO-to-3D Sync, Split-View Comparison Engine. [100% COMPLETE - 3/3]
- **Phase I (Tasks 49–52):** Explainable Telemetry Logs, End-to-End Testing, Scientific Ablation, Threat Modeling. [100% COMPLETE - 4/4]
- **Phase J (Tasks 53–60):** VMS 3D Gantries, Physical ESP32 Bench, Video Demo Pitch, Docs Release, PPO RL Sandbox. [Task 53–56 VERIFIED]

**Current Sprint Progress:** 56/60 Tasks Verified Complete (93.3% of Master Plan).
    `,
  },
  {
    id: 'faq',
    title: 'Frequently Asked Questions (FAQ)',
    category: '7. Roadmap & Reference',
    status: 'VERIFIED',
    tasks: ['T03', 'T55'],
    summary: 'Common technical, architectural, and safety questions answered.',
    content: `
# Frequently Asked Questions (FAQ)

### Q1: Is ClearWayAI connected to live city traffic lights?
**No.** ClearWayAI is locked to \`SIMULATION_ONLY=true\`. It operates in simulation, edge miniature testbench (ESP32), and advisory shadow mode.

### Q2: How does ClearWayAI handle heavy motorcycle traffic?
SUMO is configured with the sublane model (\`sublane=true\`), allowing realistic lateral filtering. YOLOv8 and ByteTrack compute Passenger Car Equivalents (PCE) dynamically.

### Q3: What happens if server communication is lost?
The physical ESP32 microcontroller runs an independent hardware watchdog. If heartbeat drops for $>2.0\\text{ s}$, it automatically drops into local autonomous fixed-time cycling (INV-06).

### Q4: Why use a Moving-Horizon Coordinator rather than End-to-End Deep RL?
Moving-Horizon MPC provides provable mathematical safety constraints (INV-01 to INV-06), deterministic convergence in $<50\\text{ ms}$, and zero risk of phase hallucinations.
    `,
  },
  {
    id: 'changelog',
    title: 'Changelog & Version History',
    category: '7. Roadmap & Reference',
    status: 'VERIFIED',
    tasks: ['T01', 'T02', 'T03', 'T53', 'T54', 'T55', 'T56'],
    summary: 'Release history and completed milestones.',
    content: `
# Changelog & Version History

All notable changes to the ClearWayAI codebase are documented here in accordance with [Keep a Changelog](https://keepachangelog.com/).

### [v0.9.3] — 2026-11-24 (Task 56)
#### Documentation
- **Task 56:** Synchronized all 24 Technical Documentation portal chapters with real code, algorithms, 7 FastAPI routers, 6 safety invariants, ESP32 hardware testbench, and scientific benchmarks.

### [v0.9.2] — 2026-11-24 (Task 55)
#### Added
- **Task 55:** Live demonstration playbook (\`docs/DEMO_SCENARIOS.md\`), 5-minute video storyboard & bilingual voiceover script (\`docs/VIDEO_DEMO_SCRIPT.md\`), 12-slide pitch deck (\`docs/PITCH_DECK.md\`), defense Q&A cheat sheet (\`docs/DEFENSE_QA.md\`), and automated demo scenario runner (\`demo_scenario_runner.py\`).

### [v0.9.1] — 2026-11-23 (Task 54)
#### Added
- **Task 54:** Physical miniature testbench with ESP32 DevKit V1, 74HC595 24-channel shift register support, C++ firmware (\`clearway_esp32_firmware.ino\`), hardware MMU conflict interlock, 2.0s watchdog timer, Python bridge & emulator, and REST API (\`/api/v1/hardware\`).

### [v0.9.0] — 2026-11-23 (Task 53)
#### Added
- **Task 53:** Overhead Variable Message Signs (VMS) advisory gantries ahead of Nodes A–D, dynamic canvas LED matrix texture, strobe warning flasher beacons, and REST API (\`/api/v1/corridor/vms\`).
    `,
  },
];
