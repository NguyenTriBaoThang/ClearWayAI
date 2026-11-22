# ClearWayAI API Specification & Contracts

Defines REST and WebSocket interface contracts for ClearWayAI services.

---

## 1. REST Endpoints

### 1.1 Service Health
- **Endpoint:** `GET /health` and `GET /api/v1/health`
- **Response `200 OK`:**
  ```json
  {
    "status": "healthy",
    "service": "clearway-api",
    "version": "0.1.0",
    "timestamp": "2026-11-22T15:30:00Z",
    "environment": "development"
  }
  ```

### 1.2 System Status & Safety Boundary
- **Endpoint:** `GET /api/v1/system/status`
- **Response `200 OK`:**
  ```json
  {
    "status": "operational",
    "mode": "SIMULATION",
    "simulation_only": true,
    "public_signal_control_permitted": false,
    "data_provenance": "DEMO_FIXTURE",
    "demo_mode_enabled": true,
    "modules": {
      "simulation": "PLANNED",
      "ai_clearance": "PLANNED",
      "traffic_signals": "PLANNED",
      "digital_twin": "PLANNED",
      "v2x_telemetry": "UNAVAILABLE",
      "hardware_bridge": "PLANNED"
    },
    "active_scenario": "demo-oak-5th-intersection",
    "timestamp": "2026-11-22T15:30:00Z",
    "message": "ClearWayAI System Initialized. All live telemetry and control disabled pending verification."
  }
  ```

---

## 2. Real-time WebSocket Protocol

- **Endpoint:** `WS /ws/simulations/{run_id}`
- **Message Schema:**
  ```json
  {
    "seq": 1042,
    "sim_time": 104.2,
    "run_id": "sim-run-20261122-01",
    "vehicles": [
      {
        "id": "amb_339",
        "vehicle_class": "emergency_ambulance",
        "x": 124.5,
        "y": 0.0,
        "z": -45.2,
        "heading": 1.57,
        "speed_kmh": 68.0,
        "current_lane_id": "5th_ave_eb_1",
        "is_priority_vehicle": true
      }
    ],
    "intersections": {
      "INT-0457": {
        "current_phase": "P3",
        "seconds_remaining": 14.0,
        "active_corridor": true
      }
    }
  }
  ```

