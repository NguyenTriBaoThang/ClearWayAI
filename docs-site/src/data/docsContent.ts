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
> ClearWayAI operates strictly in isolated microscopic simulation (SUMO) and shadow advisory modes. Under no circumstances does this software interface with or actuate live public roadside traffic signals without certified hardware-in-the-loop validation and agency pilot authorization.

### Core Architecture Pillars

1. **True WebGL 3D Digital Twin:** High-performance isometric Three.js viewport rendering vehicles, lanes, signal poles, and emergency corridors in real-time.
2. **Deterministic SUMO / TraCI Simulation:** Synchronous vehicle movements, mixed traffic (motorcycles, buses, cars), and blue-light emergency vehicle dynamics.
3. **AI Clearance-Time Estimation:** Tabular (XGBoost) and temporal (LSTM) machine learning models predicting the exact duration required to clear queues ahead of arriving ambulances.
4. **Safety-First Corridor Controller:** Independent Signal Safety Gateway enforcing green-conflict matrices, minimum green intervals, and mandatory yellow/all-red transitions.
5. **Operational Dashboard:** Responsive control center providing V2X telemetry, phase timing breakdowns, queue capacity charts, and IoT sensor network visibility.
    `,
  },
  {
    id: 'problem-novelty',
    title: 'Problem & Novelty',
    category: '1. Getting Started',
    status: 'PLANNED',
    tasks: ['T21', 'T38', 'T39'],
    summary: 'Analysis of conventional preemption limitations versus ClearWayAI predictive multi-intersection coordination.',
    content: `
# Problem Statement & Novelty

### The Urban Emergency Transit Bottleneck

Traditional emergency vehicle preemption systems (such as optical or acoustic emitters) suffer from three fatal flaws:
- **Reactive Local Preemption:** Green lights are triggered only when the emergency vehicle is 50–100m away, when cross-street queues are already heavily stopped.
- **Upstream Spillback & Gridlock:** Clearing one intersection blindly often dumps traffic directly into an already clogged downstream junction.
- **Severe Normal Traffic Starvation:** Prolonged green phases for priority vehicles disrupt network cycle coordination, causing cascading delays lasting 20–45 minutes.

### The ClearWayAI Novelty: Predictive Moving-Horizon Pre-clearance

Instead of reacting when the ambulance is at the intersection stopline, ClearWayAI computes:

$$\\Delta t_{\\text{trigger}} = \\text{ETA}_{\\text{EV}} - \\hat{T}_{\\text{clear}} - T_{\\text{transition}} - T_{\\text{buffer}}$$

Where:
- $\\text{ETA}_{\\text{EV}}$: Predicted arrival time based on microscopic telemetry.
- $\\hat{T}_{\\text{clear}}$: AI-predicted time needed to disperse the existing vehicle queue in the corridor lane.
- $T_{\\text{transition}}$: Mandatory yellow, all-red, and minimum pedestrian clearance intervals.
- $T_{\\text{buffer}}$: Safety margin calibrated against model uncertainty.

By initiating pre-clearance precisely when needed—neither too early nor too late—the corridor opens just as the emergency vehicle arrives, and normal recovery cycles resume immediately afterwards.
    `,
  },
  {
    id: 'architecture',
    title: 'System Architecture',
    category: '1. Getting Started',
    status: 'VERIFIED',
    tasks: ['T01', 'T21', 'T42'],
    summary: 'High-level architecture, subsystem boundaries, and data flow pipelines.',
    content: `
# System Architecture

ClearWayAI is structured as a modular monorepo cleanly separating physical models, simulation engines, AI inference, and presentation layers.

\`\`\`mermaid
flowchart TD
    subgraph Data & Perception
        CAM[Traffic Cameras / Video] --> YoloTrack[YOLO Detection + ByteTrack]
        YoloTrack --> TrafficState[Traffic State Estimator]
        SUMO_SIM[SUMO Microscopic Simulation] --> TraCI[TraCI Telemetry Adapter]
    end

    subgraph Intelligence & Planning
        TrafficState & TraCI --> ML_Reg[Clearance Predictor: XGBoost / LSTM]
        MissionMgr[Emergency Mission Manager] --> ETAService[Multi-Node ETA Service]
        ML_Reg & ETAService --> CorridorScheduler[Moving-Horizon Corridor Controller]
    end

    subgraph Safety & Execution
        CorridorScheduler --> SafetyGate[Signal Safety Gateway]
        SafetyGate -->|Approved Phase Plans| SUMO_Act[SUMO Actuation Engine]
        SafetyGate -->|Optional| HardwareModel[ESP32 Physical LED Model]
    end

    subgraph Digital Twin & UI
        TraCI & SafetyGate --> WS_Bus[FastAPI WebSocket Event Bus]
        WS_Bus --> WebGL3D[Three.js 3D Digital Twin]
        WS_Bus --> Dashboard[Operations Dashboard UI]
    end
\`\`\`

### Key Architectural Tenets
- **Single Source of Truth:** SUMO/TraCI (or recorded replay) serves as the primary clock and physical state authority.
- **Fail-Safe Gateways:** AI models output *recommendations*; only the deterministic Safety Gateway can command signal phase switches.
- **Real-Time WebGL Streaming:** WebSocket frames serialize vehicle transforms ($x, y, heading, speed$) directly to Three.js InstancedMesh buffers.
    `,
  },

  // --- 2. System & Safety ---
  {
    id: 'system-modules',
    title: 'System Modules Breakdown',
    category: '2. System & Safety',
    status: 'VERIFIED',
    tasks: ['T01', 'T21'],
    summary: 'Detailed responsibility matrix for all monorepo directories and packages.',
    content: `
# System Modules Breakdown

The ClearWayAI repository contains the following core packages:

| Directory | Language / Framework | Primary Responsibility |
| :--- | :--- | :--- |
| \`apps/api\` | Python / FastAPI | REST endpoints, WebSocket event bus, telemetry proxy. |
| \`apps/web\` | React / Vite / Three.js | Operator dashboard, 3D Digital Twin, analytics panels. |
| \`docs-site\` | React / Vite / TypeScript | Comprehensive developer and research documentation. |
| \`packages/shared\` | TypeScript | Shared domain schemas, enums, and data contracts. |
| \`ai/detection\` | Python / YOLO11 | Vehicle detection tuned for Vietnamese mixed traffic. |
| \`ai/tracking\` | Python / ByteTrack | Multi-object tracking and trajectory extraction. |
| \`ai/clearance\` | Python / XGBoost / PyTorch | Tabular and LSTM clearance time predictors. |
| \`controller\` | Python | Moving-horizon corridor scheduler and Signal Safety Gateway. |
| \`simulation/sumo\` | XML / SUMO | Road networks, lane graphs, and intersection topologies. |
| \`simulation/traci\` | Python / TraCI | Step controllers, snapshot serializes, and seed replays. |
| \`hardware\` | C++ / Arduino / ESP32 | Microcontroller firmware for physical miniature LED signals. |
| \`data\` | Parquet / JSON | Seed fixtures, annotations, and training manifests. |
    `,
  },
  {
    id: 'controller-safety',
    title: 'Controller & Safety Gateway',
    category: '2. System & Safety',
    status: 'PLANNED',
    tasks: ['T38', 'T39', 'T40', 'T41'],
    summary: 'The deterministic Signal Safety Gateway, conflict matrices, and state machine transitions.',
    content: `
# Controller & Safety Gateway

> [!IMPORTANT]
> The Safety Gateway operates as a mathematically verified deterministic filter. Machine learning models never directly set signal phases.

### Safety Invariants Enforced by the Gateway

1. **Conflict Matrix Verification:** Under no circumstances may opposing or conflicting movements show Green simultaneously.
2. **Minimum Green Enforcement:** An active green phase must persist for at least $T_{\\text{min\\_green}}$ (typically 10–15s) to prevent driver confusion and rear-end collisions.
3. **Mandatory Yellow & All-Red:** Transitioning from Green to Red requires a mandatory Yellow interval (3–4s) followed by an All-Red interval (2s).
4. **Pedestrian Clearance Protection:** Walk signals transition to flashing don't-walk and solid don't-walk before vehicular movements begin.
5. **Watchdog Heartbeat:** If the upstream AI controller fails to provide a valid heartbeat within 2.0 seconds, the junction reverts to its safe pre-programmed fixed-time schedule.

### Corridor State Machine

\`\`\`mermaid
stateDiagram-v2
    [*] --> STANDBY: Normal Traffic Cycle
    STANDBY --> PREPARE: Mission Authenticated & ETA < T_horizon
    PREPARE --> PRE_CLEAR: t >= t_trigger (Queue clearing initiated)
    PRE_CLEAR --> PASS: Corridor open & EV entering junction
    PASS --> RECOVER: EV confirmed downstream
    RECOVER --> STANDBY: Normal green distribution restored
    PRE_CLEAR --> FALLBACK: Watchdog timeout or Safety Violation
    FALLBACK --> STANDBY: Manual reset or timer expiry
\`\`\`
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

### Default Configuration
In \`.env\`, the following variables are locked:
\`\`\`bash
SAFETY_MODE=SIMULATION
SIMULATION_ONLY=true
PUBLIC_SIGNAL_CONTROL_PERMITTED=false
\`\`\`
Any attempt by a network request or script to invoke actuator endpoints without proper cryptographic tokens in non-simulation mode triggers an immediate HTTP 403 Forbidden and security audit log.
    `,
  },

  // --- 3. Simulation & Digital Twin ---
  {
    id: 'sumo-traci',
    title: 'SUMO & TraCI Microscopic Simulation',
    category: '3. Simulation & Digital Twin',
    status: 'PLANNED',
    tasks: ['T23', 'T24', 'T25', 'T26'],
    summary: 'Synthetic intersection corridor, mixed motorcycle traffic, and TraCI stepping.',
    content: `
# SUMO & TraCI Simulation

Microscopic simulation in ClearWayAI is powered by **Eclipse SUMO (Simulation of Urban MObility)** communicating via the Python TraCI API.

### Synthetic Network Corridor (Oak St. & 5th Ave)
The baseline corridor consists of 4 sequential signalized intersections:
- **Node A:** Ingress feeder junction
- **Node B:** Primary showcase intersection (Oak St. & 5th Ave — INT-0457)
- **Node C:** Intermediate arterial junction
- **Node D:** Hospital egress approach

### Vietnamese Mixed Traffic Modeling
Unlike standard Western simulations, Vietnamese urban corridors exhibit high motorcycle ratios (60%–80%). We configure SUMO's sublane model:
- \`sublane=true\` with \`latAlignment="arbitrary"\`
- Vehicle types: \`motorcycle\`, \`passenger_car\`, \`suv\`, \`bus\`, \`emergency_ambulance\`
- Lateral clearance: 0.3m for motorcycles, enabling realistic filtering between queuing cars.
    `,
  },
  {
    id: '3d-digital-twin',
    title: '3D Digital Twin & WebGL Engine',
    category: '3. Simulation & Digital Twin',
    status: 'IN_PROGRESS',
    tasks: ['T01', 'T07', 'T08', 'T09', 'T10', 'T46'],
    summary: 'Real-time Three.js WebGL canvas rendering, isometric camera, and vehicle instancing.',
    content: `
# 3D Digital Twin & WebGL Engine

The digital twin viewport is built using **Three.js** and WebGL. It provides a real-time, interactive representation of the urban intersection.

### Rendering Architecture
- **Isometric Perspective Camera:** Positioned at $(40, 45, 40)$ looking at $(0, 0, 0)$, providing the isometric view seen in the design blueprint.
- **InstancedMesh Vehicle Rendering:** Normal vehicles (motorcycles, sedans, SUVs) are rendered using Three.js \`InstancedMesh\`, allowing hundreds of vehicles to animate at 60 FPS with minimal draw calls.
- **Dedicated Emergency Mesh:** The ambulance mesh is rendered as an independent entity with animated light strobes and interactive HUD callouts.
- **Real Three.js Canvas:** The application strictly initializes a true WebGL canvas; static screenshots or fake video overlays are prohibited.
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

The reference image provided by the user is stored at:  
\`assets/reference/dashboard-target.png\` (1254×1254 px, 3.8 MB).

> [!NOTE]
> **DESIGN REFERENCE NOTICE:**  
> The reference image represents the design and layout goal. It is **not** a screenshot of a running application. Our engineering implementation builds this layout using React components and a live Three.js 3D viewport.

### Blueprint Layout Breakdown

1. **Top Bar:** System branding ("ClearWay AI — Traffic Control Digital Twin"), simulation time indicator, live status pill, alerts count, and operator profile.
2. **Top-Left Panel:** V2I/V2V Communication & Hardware Status (OBU count, RSU status, Edge controller, Latency, Packet loss).
3. **Top-Middle Panel:** Oak St. & 5th Ave (INT-0457) signal timing table (Approach, Red, Yellow, Green, Cycle, Split).
4. **Top-Right Panel:** Adaptive Traffic Signal Control Dashboard (Cycle time, Current/Next phase, Queue vs Capacity chart, Delay reduction KPI).
5. **Center Viewport (~60% screen):** 3D WebGL isometric intersection showing road geometry, zebra crossings, moving traffic, and active emergency corridor chevron arrows.
6. **Bottom-Left Panel:** IoT Sensor Network inventory & mini vector city map with layer toggles.
7. **Bottom-Right Panel:** Traffic & Operations Analytics (Hourly volume bars, travel time bars, performance radial gauge, anomaly alerts).
    `,
  },
  {
    id: 'ui-screenshot-fidelity',
    title: 'UI Screenshot Fidelity & Pixel Checklist',
    category: '3. Simulation & Digital Twin',
    status: 'PLANNED',
    tasks: ['T05', 'T20'],
    summary: 'Pixel-level acceptance criteria across standard resolutions (1920x1080, 1440x900, 1254x1254).',
    content: `
# UI Screenshot Fidelity & Pixel Checklist

To ensure fidelity without sacrificing usability, ClearWayAI defines responsive visual gates:

### Resolution Checkpoints
- **1254×1254:** Exact aspect ratio of user reference image.
- **1440×900:** Standard developer and laptop workstation breakpoint.
- **1920×1080:** Full HD operations command room display.

### Visual Quality Checklist
- [ ] Color Palette: Deep Navy background (\`#070d1e\`), Panel card headers (\`#122347\`), Cyan accents (\`#00e5ff\`), Signal Green (\`#06d6a0\`), Yellow (\`#ffd166\`), Red (\`#ef476f\`).
- [ ] Typography: Monospace font (\`JetBrains Mono\`) for all metrics, timers, and junction IDs; Clean sans-serif (\`Inter\`) for prose.
- [ ] Borders & Glows: Subtle 1px borders (\`#1b2f5b\`) with soft glassmorphism shadows.
- [ ] 3D Alignment: Center WebGL canvas aligns flush with surrounding panels without layout shift.
    `,
  },
  {
    id: 'coordinate-mapping',
    title: 'Coordinate & Scene Mapping',
    category: '3. Simulation & Digital Twin',
    status: 'PLANNED',
    tasks: ['T08', 'T23', 'T46', 'T47'],
    summary: 'Mathematical transformation between SUMO simulation coordinates and WebGL 3D space.',
    content: `
# Coordinate & Scene Mapping

To achieve perfect synchronization between SUMO and the Three.js viewport, coordinates undergo a standardized transformation:

### Coordinate Systems
- **SUMO World Coordinates:** 2D Cartesian plane $(X_{\\text{sumo}}, Y_{\\text{sumo}})$ in meters, where $(0,0)$ is network bottom-left and heading $\\theta_{\\text{sumo}}$ is $0^\\circ$ North (clockwise).
- **Three.js World Coordinates:** 3D right-handed system $(X_{\\text{three}}, Y_{\\text{three}}, Z_{\\text{three}})$, where $Y$ is vertical elevation and heading $\\theta_{\\text{three}}$ is counter-clockwise radians.

### Transformation Equations

$$X_{\\text{three}} = X_{\\text{sumo}} - X_{\\text{origin}}$$

$$Y_{\\text{three}} = Z_{\\text{elevation}}$$

$$Z_{\\text{three}} = -(Y_{\\text{sumo}} - Y_{\\text{origin}})$$

$$\\theta_{\\text{three}} = -\\text{radians}(\\theta_{\\text{sumo}}) + \\frac{\\pi}{2}$$
    `,
  },
  {
    id: 'simulation-comparison',
    title: 'Simulation Comparison Engine',
    category: '3. Simulation & Digital Twin',
    status: 'PLANNED',
    tasks: ['T27', 'T48', 'T51'],
    summary: 'Synchronized dual-run methodology: Fixed-time baseline vs ClearWay AI under identical seeds.',
    content: `
# Simulation Comparison Engine

To scientifically validate that ClearWayAI improves clearance times without creating secondary gridlock, the platform includes a **Synchronized Dual-Run Engine**:

- **Identical Traffic Seeds:** Both the baseline run and the ClearWayAI run receive the exact same vehicle generation seed, vehicle mix, and arrival distributions.
- **Side-by-Side 3D Playback:** The operator can toggle between or view simultaneous split-view 3D renderings of:
  1. **Fixed-Time Baseline (B0):** Ambulance queues behind stopped cars; no pre-clearance.
  2. **ClearWay AI (B3):** Corridor queue is systematically flushed before ambulance arrival.
- **Real-Time Differential Metrics:** Delta calculations on travel time, average vehicle delay, and corridor backlog.
    `,
  },

  // --- 4. AI & Computer Vision ---
  {
    id: 'datasets',
    title: 'Traffic Datasets & Privacy Governance',
    category: '4. AI & Computer Vision',
    status: 'PLANNED',
    tasks: ['T28', 'T29'],
    summary: 'Data collection protocols, annotation standards, and strict privacy scrub pipelines.',
    content: `
# Traffic Datasets & Privacy Governance

All computer vision models in ClearWayAI are trained under strict data governance protocols documented in \`DATA_GOVERNANCE.md\`.

### Data Scrubbing & Privacy Guarantees
- Automated Gaussian blurring applied to all human faces and vehicle license plates.
- No personal identifiable information (PII) is stored in dataset manifests.
- Scene-based splits (Train/Val/Test divided by intersection location and recording day) strictly prevent data leakage across adjacent video frames.
    `,
  },
  {
    id: 'ai-models',
    title: 'AI Vision & Tracking Models',
    category: '4. AI & Computer Vision',
    status: 'PLANNED',
    tasks: ['T30', 'T31', 'T32'],
    summary: 'YOLO11 fine-tuning for mixed traffic, ByteTrack trajectory extraction, and camera calibration.',
    content: `
# AI Vision & Tracking Models

### Vehicle Detection (YOLO11)
Fine-tuned on urban intersection video clips with heavy motorcycle presence:
- Classes: \`motorcycle\`, \`passenger_car\`, \`bus\`, \`truck\`, \`ambulance\`
- Metric Targets: mAP@50 > 0.85, mAP@50:95 > 0.60
- Export formats: PyTorch (\`best.pt\`) and ONNX runtime (\`best.onnx\`)

### Multi-Object Tracking (ByteTrack)
- Maintains persistent vehicle trajectories across heavy occlusion.
- Extracts velocity vectors, stationary stopped duration, and queue front positions.
    `,
  },
  {
    id: 'clearance-prediction',
    title: 'Clearance Time Prediction',
    category: '4. AI & Computer Vision',
    status: 'PLANNED',
    tasks: ['T33', 'T34', 'T35', 'T36'],
    summary: 'Mathematical formulation of clearance time, XGBoost baseline, and LSTM sequence models.',
    content: `
# Clearance Time Prediction

### Clearance Time Definition
Clearance Time ($T_{\\text{clear}}$) is defined as the elapsed time from initiating a green clearing phase until the target emergency corridor segment has sufficient clearance width (>= 3.5m) for the ambulance to proceed without decelerating below target speed.

### Model Comparison
- **Tabular Baseline (XGBoost):** Evaluates snapshot queue length, motorcycle ratio, entry volume, and approach occupancy.
- **Temporal Sequence Model (LSTM / GRU):** Evaluates a sliding temporal window of 20 seconds (20 ticks $\\times$ features) capturing shockwave propagation and vehicle dispersion rates.
    `,
  },
  {
    id: 'sensor-telemetry-provenance',
    title: 'Sensor Telemetry & Data Provenance',
    category: '4. AI & Computer Vision',
    status: 'VERIFIED',
    tasks: ['T01', 'T14', 'T17', 'T28'],
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
  | 'LIVE_CONNECTED';  // Physical verified pilot hardware
\`\`\`

Any card displaying metrics when the simulator or hardware is offline explicitly displays the \`DEMO_FIXTURE\` status badge.
    `,
  },

  // --- 5. Backend & Operations ---
  {
    id: 'api-websocket',
    title: 'API & WebSocket Streaming',
    category: '5. Backend & Operations',
    status: 'VERIFIED',
    tasks: ['T01', 'T42', 'T43'],
    summary: 'FastAPI REST schemas, OpenAPI documentation, and real-time WebSocket state distribution.',
    content: `
# API & WebSocket Streaming

The backend runs on **FastAPI** providing high-throughput asynchronous request handling and WebSocket streaming.

### Core REST Endpoints
- \`GET /health\`: Service readiness and version check.
- \`GET /api/v1/system/status\`: Operational safety mode, active scenario, and module lifecycle status.
- \`GET /api/v1/missions\`: Active and scheduled emergency missions.
- \`POST /api/v1/simulation/step\`: Advance simulation tick (in simulation mode).

### WebSocket Event Stream (\`/ws/simulations/{run_id}\`)
Streams continuous binary or JSON telemetry snapshots at 10 Hz:
\`\`\`json
{
  "seq": 1420,
  "sim_time": 142.0,
  "vehicles": [
    { "id": "veh_42", "class": "motorcycle", "x": 12.4, "y": -4.2, "speed": 45.2, "lane": "oak_sb_1" }
  ],
  "signals": { "INT-0457": { "current_phase": "P3", "seconds_remaining": 14 } },
  "corridor": { "status": "PRE_CLEAR", "target_intersection": "INT-0457", "eta": 28.4 }
}
\`\`\`
    `,
  },
  {
    id: 'dashboard',
    title: 'Operator Dashboard UI',
    category: '5. Backend & Operations',
    status: 'VERIFIED',
    tasks: ['T01', 'T06', 'T44'],
    summary: 'Control room layout, KPI tiles, responsive grid, and operational controls.',
    content: `
# Operator Dashboard UI

The Operations Dashboard in \`apps/web\` acts as the command center for traffic operators and researchers.

### Navigation Routes
- \`/dashboard\`: Main multi-panel operations console.
- \`/digital-twin\`: Dedicated full-screen 3D scene explorer.
- \`/simulation\`: SUMO step controls and scenario selector.
- \`/experiments\`: Multi-seed evaluation and baseline comparison charts.
- \`/settings\`: Safety limits and watchdog configuration.
    `,
  },

  // --- 6. Evaluation & Verification ---
  {
    id: 'evaluation',
    title: 'Evaluation Methodology & Ablation',
    category: '6. Evaluation & Verification',
    status: 'PLANNED',
    tasks: ['T27', 'T51'],
    summary: 'Scientific testing protocols, metrics (travel time, queue backlog), and ablation runs.',
    content: `
# Evaluation Methodology & Ablation

To prove system efficacy scientifically, ClearWayAI benchmark experiments evaluate four algorithms on identical scenarios across $\\ge 10$ random seeds:

1. **B0 (Fixed-Time):** Standard Webster fixed-cycle timing.
2. **B1 (Reactive Blue-Light):** Local sensor green trigger when ambulance is at $50\\text{m}$.
3. **B2 (Distance/ETA Corridor):** Rule-based corridor based purely on speed and distance.
4. **B3 (ClearWay AI):** Predictive pre-clearance with AI clearance time estimation and coordinated downstream recovery.

### Evaluation Metrics
- **EV Travel Time (seconds):** Primary reduction target.
- **EV Stop Count:** Target is zero stops on corridor routes.
- **Network Secondary Delay (veh-sec):** Ensuring non-priority directions are not unduly penalized.
- **Corridor Recovery Time (seconds):** Time to restore normal Webster cycle after vehicle transit.
    `,
  },
  {
    id: 'deployment',
    title: 'Deployment & Containerization',
    category: '6. Evaluation & Verification',
    status: 'VERIFIED',
    tasks: ['T01', 'T58'],
    summary: 'Docker Compose orchestration, environment setups, and GitHub Pages hosting.',
    content: `
# Deployment & Containerization

### Docker Compose Quickstart
\`\`\`bash
# Build and run API and Web services
docker-compose up -d

# Verify container health
docker-compose ps
\`\`\`

### GitHub Pages Deployment
The documentation portal is automatically built and deployed via GitHub Actions to GitHub Pages at:  
\`https://nguyentribaothang.github.io/ClearWayAI/\`
    `,
  },
  {
    id: 'testing',
    title: 'Testing & Verification Gates',
    category: '6. Evaluation & Verification',
    status: 'VERIFIED',
    tasks: ['T01', 'T22', 'T50'],
    summary: 'Unit testing with pytest, frontend type checking, contract verification, and E2E gates.',
    content: `
# Testing & Verification Gates

ClearWayAI enforces strict verification gates across all tasks:

- **Python Tests:** \`python -m pytest\` runs unit tests on schemas, health endpoints, and safety gateway rules.
- **TypeScript Strictness:** Strict type checking (\`tsc\`) on shared packages and web frontends.
- **Docker Compose Config:** Verification of container definitions with \`docker-compose config\`.
- **Visual Fidelity Assertions:** Automated checks confirming reference asset presence and resolution.
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

ClearWayAI's complete implementation roadmap spans 60 granular tasks organized into 10 developmental phases:

- **Phase A (Tasks 01–04, 21–22):** Monorepo, GitHub Governance, Documentation, Safety Specifications.
- **Phase B (Tasks 05–20):** UI Blueprint Locking, Three.js 3D Viewport, Vehicle Assets, Panel Components.
- **Phase C (Tasks 23–27):** SUMO Microscopic Network, Mixed Demand, Emergency Vehicle Modeling, Baselines B0–B2.
- **Phase D (Tasks 28–32):** Video Collection, Annotation Guides, YOLO11 Fine-Tuning, ByteTrack, Traffic State Engine.
- **Phase E (Tasks 33–36):** Clearance Time Dataset Generation, XGBoost & LSTM Models, Model Registry & Fallbacks.
- **Phase F (Tasks 37–41):** Emergency Mission Simulator, Multi-Node Pre-clearance Scheduler, Signal Safety Gateway.
- **Phase G (Tasks 42–45):** FastAPI Backend, WebSocket Event Bus, Operations Dashboard, 2D Corridor Timeline.
- **Phase H (Tasks 46–48):** Multi-Intersection 3D WebGL World, SUMO-to-3D Sync, Split-View Comparison Engine.
- **Phase I (Tasks 49–52):** Explainable Telemetry Logs, End-to-End Testing, Scientific Ablation, Threat Modeling.
- **Phase J (Tasks 53–60):** Physical ESP32 LED Model, Video Demo Pitch, Docs Release, Reinforcement Learning (PPO).
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
**No.** ClearWayAI is locked to \`SIMULATION_ONLY=true\`. It operates in simulation and advisory shadow mode. No live signal control commands are dispatched.

### Q2: How does ClearWayAI handle heavy motorcycle traffic?
SUMO is configured with the sublane model (\`sublane=true\`), allowing realistic lateral filtering. YOLO models are fine-tuned specifically on high-density motorcycle traffic datasets.

### Q3: What happens if an AI model outputs an invalid or unsafe clearance time?
All AI recommendations pass through the **Signal Safety Gateway**. If values are out-of-distribution (OOD) or corrupt, the system falls back to conservative rule-based buffers.

### Q4: Why use Three.js rather than pre-rendered video?
An interactive Three.js 3D viewport allows operators to pan, zoom, inspect individual vehicle states, inspect camera views, and verify lane clearance in real time.
    `,
  },
  {
    id: 'changelog',
    title: 'Changelog & Version History',
    category: '7. Roadmap & Reference',
    status: 'VERIFIED',
    tasks: ['T01', 'T02', 'T03'],
    summary: 'Release history and completed milestones.',
    content: `
# Changelog & Version History

All notable changes to the ClearWayAI codebase are documented here in accordance with [Keep a Changelog](https://keepachangelog.com/).

### [v0.1.0-alpha] — 2026-11-22
#### Added
- **Task 01:** Monorepo scaffold (\`apps/api\`, \`apps/web\`, \`docs-site\`, \`packages/shared\`), FastAPI health/status endpoints, Three.js Digital Twin canvas, Docker Compose configuration.
- **Task 02:** GitHub governance infrastructure: Issue & PR templates, \`CONTRIBUTING.md\`, \`SECURITY.md\`, \`CODEOWNERS\`, \`.gitattributes\` (Git LFS), \`docs/TASK_BOARD.md\`.
- **Task 03:** Technical Documentation website with 24 comprehensive chapters, dark/light mode, real-time search, Mermaid diagrams, code copy, and GitHub Actions Pages workflow.
    `,
  },
];

