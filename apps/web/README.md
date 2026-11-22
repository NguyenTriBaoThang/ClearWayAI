# ClearWayAI Web Application (`apps/web`)

Modern React + Vite + TypeScript web application serving as the primary Traffic Operations Center and 3D Digital Twin command viewport.

---

## 1. Directory Structure

```
apps/web/
├── public/                 # Static public assets
├── src/
│   ├── components/         # Reusable UI primitives (StatusBadge, NotImplemented)
│   ├── features/
│   │   ├── digital-twin/   # Three.js WebGL canvas (DigitalTwinCanvas)
│   │   └── operations/     # Blueprint cards (V2X, PhaseTiming, AdaptiveSignal, IoT, Analytics)
│   ├── layout/             # Shell, TopBar (clocks, modes), Sidebar navigation
│   ├── pages/              # Route pages (Home, Dashboard, DigitalTwin, Simulation, Experiments, Settings)
│   ├── services/           # Typed API client connecting to FastAPI backend
│   ├── types/              # Frontend TypeScript interfaces
│   ├── App.tsx             # React Router routing
│   ├── index.css           # Operations Center dark theme styling
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
- **No Fake Overlays:** Strictly does not use static screenshots or stock images as pseudo-3D scene representations.
- **Unimplemented Routes:** Routes without connected backend modules display a clear `STATUS: NOT_IMPLEMENTED` card indicating the scheduled roadmap task.

