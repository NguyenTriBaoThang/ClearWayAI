# ClearWayAI Backend API (`apps/api`)

FastAPI backend service responsible for serving REST API endpoints, orchestrating TraCI simulation connections, serving AI clearance estimates, and providing high-throughput WebSocket snapshot streams for the 3D Digital Twin and dashboard.

---

## 1. Directory Structure

```
apps/api/
├── src/
│   ├── __init__.py
│   ├── config.py           # Pydantic environment configuration
│   ├── schemas.py          # Pydantic models (Health, SystemStatus, Telemetry)
│   └── main.py             # FastAPI entrypoint, CORS, route handlers
├── tests/
│   ├── __init__.py
│   ├── test_health.py      # Health check endpoint tests
│   └── test_status.py      # System safety mode and provenance tests
├── Dockerfile              # Production Python 3.11 container image
└── README.md
```

---

## 2. Environment Variables

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `API_HOST` | string | `0.0.0.0` | Binding host address |
| `API_PORT` | integer | `8000` | Port for the HTTP & WebSocket server |
| `SAFETY_MODE` | string | `SIMULATION` | Operational mode (`SIMULATION`, `SHADOW_ADVISORY`) |
| `SIMULATION_ONLY` | boolean | `true` | Strict lock preventing public roadside control |
| `DATA_PROVENANCE` | string | `DEMO_FIXTURE`| Provenance tag (`DEMO_FIXTURE`, `SUMO_SIMULATED`) |
| `DEMO_MODE` | boolean | `true` | Toggles fallback demonstration seed data |

---

## 3. Running Locally

```bash
# Start server with live reload on port 8000
python -m uvicorn apps.api.src.main:app --reload --host 0.0.0.0 --port 8000
```

- **Interactive API Docs (Swagger):** `http://localhost:8000/docs`
- **ReDoc Documentation:** `http://localhost:8000/redoc`
- **Health Check:** `http://localhost:8000/health`
- **System Status:** `http://localhost:8000/api/v1/system/status`

---

## 4. Inputs & Outputs

- **Inputs:** Client requests for simulation state, mission activation (`/api/v1/missions`), and WebSocket subscriptions.
- **Outputs:** Strict Pydantic JSON contracts declaring health, safety status, and vehicle/signal snapshot frames.

---

## 5. Automated Tests

```bash
# Run API test suite
pytest apps/api/tests -v
```
