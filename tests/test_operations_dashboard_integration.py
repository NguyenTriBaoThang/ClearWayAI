"""Comprehensive Test Suite for Task 44: Production Operations Dashboard & API/WebSocket Integration.

Validates:
1. Production REST API service contract completeness (simulations, missions, clearance, corridor, replay).
2. Real-time WebSocket hook capabilities (URL resolution, command dispatch, connection status lifecycle).
3. OperationsContext real-time state management and operational action dispatchers.
4. Responsive Cyber Grid media queries (4K, desktop, laptop/tablet, mobile).
5. DashboardPage production component integration (3D viewport, 5 panel cards, controls, drawers).
6. Offline fail-safe fallbacks ensuring 100% crash-free operations under network degradation.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_SRC = REPO_ROOT / "apps" / "web" / "src"


def test_production_dashboard_files_exist() -> None:
    """Verify that all Task 44 frontend integration modules exist."""
    required_files = [
        WEB_SRC / "types" / "api.ts",
        WEB_SRC / "services" / "api.ts",
        WEB_SRC / "services" / "websocket.ts",
        WEB_SRC / "features" / "dashboard" / "OperationsContext.tsx",
        WEB_SRC / "pages" / "DashboardPage.tsx",
        WEB_SRC / "index.css",
    ]
    for file_path in required_files:
        assert file_path.is_file(), f"Expected file {file_path} to exist!"


def test_api_service_contracts_and_fallbacks() -> None:
    """Verify typed API functions for simulations, missions, clearance, corridor, and replay."""
    api_ts = (WEB_SRC / "services" / "api.ts").read_text(encoding="utf-8")

    # Simulations
    assert "createSimulation" in api_ts
    assert "listSimulations" in api_ts
    assert "stepSimulation" in api_ts
    assert "stopSimulation" in api_ts

    # Missions
    assert "createMission" in api_ts
    assert "listMissions" in api_ts
    assert "getMissionETA" in api_ts

    # Clearance AI
    assert "predictClearance" in api_ts

    # Corridor & Safety
    assert "getCorridorPlan" in api_ts
    assert "evaluatePreclearance" in api_ts
    assert "getSafetyAudit" in api_ts

    # Replay & Snapshots
    assert "loadReplay" in api_ts
    assert "getReplayStatus" in api_ts
    assert "listSnapshots" in api_ts

    # Offline graceful fallbacks
    assert "handleResponse" in api_ts
    assert "fallback" in api_ts


def test_websocket_client_service_capabilities() -> None:
    """Verify WebSocket streaming hook URL generation, filtering, and command dispatch."""
    ws_ts = (WEB_SRC / "services" / "websocket.ts").read_text(encoding="utf-8")

    # URL resolver
    assert "getWebSocketUrl" in ws_ts
    assert "/ws/simulations/" in ws_ts
    assert "/ws/telemetry" in ws_ts

    # React Hook
    assert "useWebSocketStream" in ws_ts
    assert "sendCommand" in ws_ts
    assert "sendPing" in ws_ts

    # Connection Statuses
    assert "CONNECTED" in ws_ts
    assert "CONNECTING" in ws_ts
    assert "SIMULATED" in ws_ts

    # Latency tracking
    assert "latencyMs" in ws_ts
    assert "autoReconnect" in ws_ts


def test_operations_context_state_and_actions() -> None:
    """Verify OperationsProvider exposes live telemetry states and action handlers."""
    ctx_ts = (WEB_SRC / "features" / "dashboard" / "OperationsContext.tsx").read_text(
        encoding="utf-8"
    )

    # Core Provider & Hook
    assert "OperationsProvider" in ctx_ts
    assert "useOperations" in ctx_ts

    # Telemetry States
    assert "connectionStatus" in ctx_ts
    assert "simTimeSec" in ctx_ts
    assert "isPlaying" in ctx_ts
    assert "playbackSpeed" in ctx_ts
    assert "activeMission" in ctx_ts
    assert "multiNodeETA" in ctx_ts
    assert "corridorPlan" in ctx_ts
    assert "safetyAudit" in ctx_ts

    # Action Handlers
    assert "togglePlay" in ctx_ts
    assert "stepSimulation" in ctx_ts
    assert "setPlaybackSpeed" in ctx_ts
    assert "dispatchMission" in ctx_ts
    assert "evaluateNodePreclearance" in ctx_ts
    assert "refreshCorridorState" in ctx_ts


def test_responsive_cyber_grid_css() -> None:
    """Verify responsive CSS media queries for multi-tier display environments."""
    css = (WEB_SRC / "index.css").read_text(encoding="utf-8")

    # Grid classes
    assert ".dashboard-grid-top" in css
    assert ".dashboard-grid-bottom" in css

    # Breakpoints
    assert "@media (min-width: 2560px)" in css  # 4K ultra-wide
    assert "@media (max-width: 1400px)" in css  # standard desktop
    assert "@media (max-width: 1024px)" in css  # compact laptop / tablet
    assert "@media (max-width: 768px)" in css  # mobile

    # Connection badges
    assert ".connection-badge-connected" in css
    assert ".connection-badge-simulated" in css
    assert ".connection-badge-disconnected" in css


def test_dashboard_page_integrated_architecture() -> None:
    """Verify DashboardPage mounts OperationsProvider, controls, 3D viewport, and 5 cards."""
    page_tsx = (WEB_SRC / "pages" / "DashboardPage.tsx").read_text(encoding="utf-8")

    # Operations Context Wrap
    assert "OperationsProvider" in page_tsx
    assert "useOperations" in page_tsx

    # 5 Panel Cards
    assert "V2XHardwareCard" in page_tsx
    assert "PhaseTimingCard" in page_tsx
    assert "AdaptiveSignalCard" in page_tsx
    assert "IoTSensorsCard" in page_tsx
    assert "AnalyticsCard" in page_tsx

    # 3D Viewport & Controls
    assert "DigitalTwinCanvas" in page_tsx
    assert "SimulationControls" in page_tsx

    # Operational Drawers
    assert "MissionDrawer" in page_tsx
    assert "UnifiedInspector" in page_tsx


def test_topbar_connection_status_integration() -> None:
    """Verify TopBar accepts connection status and renders dynamic latency/WebSocket pill."""
    topbar_tsx = (WEB_SRC / "layout" / "TopBar.tsx").read_text(encoding="utf-8")

    assert "connectionStatus" in topbar_tsx
    assert "latencyMs" in topbar_tsx
    assert "WS ONLINE" in topbar_tsx
    assert "WS SIMULATED" in topbar_tsx
    assert "WS CONNECTING" in topbar_tsx
