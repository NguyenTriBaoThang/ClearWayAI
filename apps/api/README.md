# ClearWayAI Backend API (`apps/api`)

FastAPI backend service responsible for serving REST API endpoints, managing simulation episodes, orchestrating emergency corridor missions, serving ML queue clearance predictions with multi-tier fail-safe fallbacks, evaluating moving-horizon multi-intersection pre-clearance, and executing MMU safety audits.

---

## 1. Directory Structure

```
apps/api/
├── src/
│   ├── __init__.py
│   ├── config.py           # Pydantic environment configuration
│   ├── database.py         # Thread-safe SQLite persistence layer (simulations, missions, signal logs, clearance, snapshots)
│   ├── schemas.py          # Complete Pydantic schemas adhering to domain contracts
│   ├── websocket.py        # Real-time WebSocket connection manager & pub/sub broadcaster
│   ├── routers/            # Modular REST API endpoints (7 Routers)
│   │   ├── __init__.py
│   │   ├── simulations.py  # Lifecycle (create, list, get, step, stop)
│   │   ├── missions.py     # Priority mission dispatch, telemetry, multi-node ETA
│   │   ├── clearance.py    # AI clearance predictions & Model Registry catalog
│   │   ├── corridor.py     # Moving-horizon coordination, JIT trigger, recovery, VMS & MMU safety audit
│   │   ├── replay.py       # Deterministic telemetry replay, snapshots querying & playback controls
│   │   ├── audit.py        # Explainable AI decision audit trails, feature attributions & summary metrics
│   │   └── hardware.py     # ESP32 miniature physical testbench integration & diagnostics
│   └── main.py             # FastAPI entrypoint, CORS, route handlers, WebSocket mounts
├── tests/
│   ├── __init__.py
│   ├── test_health.py      # Health check endpoint tests
│   ├── test_status.py      # System safety mode and provenance tests
│   ├── test_api_endpoints.py # Comprehensive endpoint lifecycle, validation & 404 tests
│   └── test_websocket_stream.py # WebSocket pub/sub, client commands, DB snapshots & replay tests
├── Dockerfile              # Production Python container image
└── README.md
```

---

## 2. API Contract Endpoints

| Category | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **System** | `GET` | `/health`, `/api/v1/health` | Service health status and readiness |
| **System** | `GET` | `/api/v1/system/status` | Safety boundaries, module status, provenance |
| **Simulations** | `POST` | `/api/v1/simulations` | Create and start new corridor simulation episode |
| **Simulations** | `GET` | `/api/v1/simulations` | List historical and active simulation episodes |
| **Simulations** | `GET` | `/api/v1/simulations/{id}` | Get episode telemetry metrics and step counter |
| **Simulations** | `POST` | `/api/v1/simulations/{id}/step` | Advance episode by `dt` seconds |
| **Simulations** | `POST` | `/api/v1/simulations/{id}/stop` | Terminate and finalize simulation episode |
| **Missions** | `POST` | `/api/v1/missions` | Register and dispatch emergency vehicle priority mission |
| **Missions** | `GET` | `/api/v1/missions` | List all historical and active priority missions |
| **Missions** | `GET` | `/api/v1/missions/{id}` | Get mission spatial progress and status |
| **Missions** | `GET` | `/api/v1/missions/{id}/eta` | Compute multi-node kinematic arrival ETAs (Nodes A–D, Hospital) |
| **Missions** | `POST` | `/api/v1/missions/{id}/telemetry` | Update vehicle coordinates and velocity |
| **Clearance AI** | `POST` | `/api/v1/clearance/predict` | Predict queue shockwave clearance duration via ML champion |
| **Clearance AI** | `GET` | `/api/v1/clearance/registry` | Query Model Registry catalog and fallback hierarchy |
| **Corridor & VMS** | `GET` | `/api/v1/corridor/plan` | Query real-time moving-horizon coordination plan |
| **Corridor & VMS** | `POST` | `/api/v1/corridor/preclearance/evaluate` | Evaluate JIT trigger $\Delta t_{\text{trigger}}$ for intersection |
| **Corridor & VMS** | `POST` | `/api/v1/corridor/recovery/initiate` | Initiate multi-cycle smooth post-clearance recovery |
| **Corridor & VMS** | `GET` | `/api/v1/corridor/safety/audit` | Execute hardware-level MMU zero-trust safety audit |
| **Corridor & VMS** | `GET` | `/api/v1/corridor/vms` | Query active advisory states across 4 VMS gantries (-80m, 170m, 420m, 670m) |
| **Corridor & VMS** | `POST` | `/api/v1/corridor/vms/{gantry_id}/override` | Manually override VMS gantry advisory state & text |
| **Corridor & VMS** | `POST` | `/api/v1/corridor/vms/reset` | Reset all VMS gantries to automated corridor coordination |
| **Physical Hardware** | `GET` | `/api/v1/hardware/status` | Query ESP32 connection state, watchdog age, and 24-channel LED states |
| **Physical Hardware** | `POST` | `/api/v1/hardware/test` | Trigger hardware self-test pattern (`CHASE`, `GREEN_WAVE`, `ALL_RED`) |
| **AI Decision Audit** | `GET` | `/api/v1/audit/decisions` | Stream explainable AI decision audit logs with filters |
| **AI Decision Audit** | `GET` | `/api/v1/audit/decisions/{id}` | Retrieve single decision narrative & feature attributions |
| **AI Decision Audit** | `GET` | `/api/v1/audit/summary` | Corridor-wide decision statistics & safety ratio |
| **AI Decision Audit** | `POST` | `/api/v1/audit/explain` | On-the-fly decision explainability & mathematical proof |
| **Replay & Snapshots** | `POST` | `/api/v1/simulations/{id}/replay/load` | Load simulation snapshots into in-memory ReplayController |
| **Replay & Snapshots** | `POST` | `/api/v1/simulations/{id}/replay/play` | Start continuous replay playback |
| **Replay & Snapshots** | `POST` | `/api/v1/simulations/{id}/replay/pause` | Pause replay playback |
| **Replay & Snapshots** | `POST` | `/api/v1/simulations/{id}/replay/seek` | Seek replay buffer to target timestamp |
| **Replay & Snapshots** | `POST` | `/api/v1/simulations/{id}/replay/speed` | Adjust playback speed multiplier (0.5x, 1.0x, 2.0x, 4.0x) |
| **Replay & Snapshots** | `POST` | `/api/v1/simulations/{id}/replay/step` | Step replay forward by `dt` seconds |
| **Replay & Snapshots** | `GET` | `/api/v1/simulations/{id}/replay/status` | Query playback status, timestamp, and buffer size |
| **Replay & Snapshots** | `GET` | `/api/v1/simulations/{id}/snapshots` | Query historical persisted snapshots with time window filter |
| **WebSocket Stream** | `WS` | `/ws/simulations/{id}` | Real-time bidirectional telemetry & control stream for simulation |
| **WebSocket Stream** | `WS` | `/ws/telemetry` | Global real-time telemetry stream across all active simulations |

---

## 3. Environment Variables

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `API_HOST` | string | `0.0.0.0` | Binding host address |
| `API_PORT` | integer | `8000` | Port for HTTP & WebSocket server |
| `SAFETY_MODE` | string | `SIMULATION` | Operational mode (`SIMULATION`, `SHADOW_ADVISORY`) |
| `SIMULATION_ONLY` | boolean | `true` | Strict lock preventing live roadside hardware control |
| `DATA_PROVENANCE` | string | `DEMO_FIXTURE`| Provenance tag (`DEMO_FIXTURE`, `SUMO_SIMULATED`) |
| `DEMO_MODE` | boolean | `true` | Toggles fallback demonstration seed data |

---

## 4. Running Locally

```bash
# Start server with live reload on port 8000
python -m uvicorn apps.api.src.main:app --reload --host 0.0.0.0 --port 8000
```

- **Interactive API Docs (Swagger):** `http://localhost:8000/docs`
- **ReDoc Documentation:** `http://localhost:8000/redoc`

---

## 5. Automated Tests

```bash
python -m pytest apps/api/tests/ -v
```
