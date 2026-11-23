# ClearWayAI Web Application (`apps/web`)

Modern React + Vite + TypeScript web application serving as the primary Traffic Operations Center and 3D Digital Twin command viewport.

---

## 1. Directory Structure

```
apps/web/
├── public/                 # Static public assets
├── src/
│   ├── components/         # Reusable UI primitives (PanelFrame, StatusPill, KpiTile, LoadingSkeleton)
│   ├── features/
│   │   ├── corridor/       # 2D Corridor Route Map & Moving-Horizon Coordination Timeline
│   │   ├── dashboard/      # Operations Center real-time context (OperationsContext.tsx)
│   │   ├── digital-twin/   # Three.js WebGL canvas (DigitalTwinCanvas, MultiIntersectionRoadNetwork, CorridorCityEnvironment, MultiSignalController, SceneController)
│   │   └── operations/     # Blueprint cards (V2X, PhaseTiming, AdaptiveSignal, IoT, Analytics, Controls, Drawers)
│   ├── layout/             # Shell, TopBar (clocks, modes, WebSocket status), Sidebar navigation
│   ├── pages/              # Route pages (DashboardPage, DigitalTwinPage, SimulationPage, ExperimentsPage)
│   ├── services/           # Typed API client (api.ts) & WebSocket stream client (websocket.ts)
│   ├── types/              # Frontend TypeScript interfaces (domain, dashboard, api contracts)
│   ├── App.tsx             # React Router routing
│   ├── index.css           # Responsive Cyber Grid dark theme styling (4K to mobile)
│   └── main.tsx            # Application entrypoint
├── Dockerfile              # Multi-stage Nginx container build
├── package.json            # Web dependencies (Three.js, Lucide, React Router)
├── tsconfig.json           # Strict TypeScript configuration
├── vite.config.ts          # Vite bundler configuration
└── README.md
```

---

## 2. Environment Variables

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `VITE_API_BASE_URL` | string | `http://localhost:8000` | Backend API root URL |
| `VITE_WS_BASE_URL` | string | `ws://localhost:8000` | Backend WebSocket stream URL |
| `VITE_DEMO_MODE` | boolean | `true` | Enables offline demonstration fixtures |

---

## 3. Running Locally

```bash
# Start Vite development server (port 3000)
pnpm --filter clearway-web dev

# Build production bundle to dist/
pnpm --filter clearway-web build

# Preview production build locally
pnpm --filter clearway-web preview
```

---

## 4. 3D Digital Twin Guarantees

- **True WebGL Canvas:** Renders a genuine Three.js WebGL canvas with perspective isometric camera, ground grid, directional lighting, and active FPS counter.
- **1,000m Arterial Corridor World:** Full procedural 3D model spanning 5th Avenue across 4 sequential intersections (Node A: Maple St 0m, Node B: Oak St / INT-0457 250m, Node C: Pine St 500m, Node D: Elm St 750m) and the Metropolitan Trauma Center Hospital (850m).
- **Physical Signal Infrastructure:** 16 physical 3D mast signal poles across all 4 intersections with independent phase control and preemption hold.
- **Corridor Camera Presets:** Smooth lerp transitions between full corridor overview (`corridor`), individual intersection close-ups (`nodeA`, `nodeB`, `nodeC`, `nodeD`), trauma center (`hospital`), and vehicle chase (`chase`).
- **No Fake Overlays:** Strictly does not use static screenshots or stock images as pseudo-3D scene representations.
- **Unimplemented Routes:** Routes without connected backend modules display a clear `STATUS: NOT_IMPLEMENTED` card indicating the scheduled roadmap task.

