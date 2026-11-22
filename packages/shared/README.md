# ClearWayAI Shared Domain Types (`packages/shared`)

Shared TypeScript domain interfaces, enums, and data transfer objects (DTOs) utilized across `apps/web`, `docs-site`, and future client libraries.

---

## 1. Directory Structure

```
packages/shared/
├── src/
│   ├── index.ts            # Entrypoint exporting all types
│   └── types.ts            # Core domain models and provenance types
├── package.json
├── tsconfig.json
└── README.md
```

---

## 2. Exported Core Types

- `SystemStatus`: Operational mode, safety parameters, module status, and timestamp.
- `OperationalMode`: `'SIMULATION' | 'OFFLINE_VIDEO' | 'SHADOW_ADVISORY' | 'AUTHORIZED_PILOT'`.
- `DataProvenance`: `'DEMO_FIXTURE' | 'SUMO_SIMULATED' | 'OFFLINE_VIDEO' | 'SHADOW_ADVISORY' | 'LIVE_CONNECTED'`.
- `VehicleState`: Spatial position, heading, velocity, vehicle class, and priority mission metadata.
- `SignalState`: Approach split timing (Red, Yellow, Green, Cycle, Split) and phase countdowns.
- `HardwareStatus`: RSU, OBU, Edge controller, latency, and packet loss metrics.
- `EmergencyMission`: Ambulance/Firetruck priority route corridor declarations.

---

## 3. Building

```bash
# Build TypeScript declarations (.d.ts) and CommonJS output
pnpm --filter @clearway/shared build
```

