import { HealthCheck, SystemStatus } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function fetchHealth(): Promise<HealthCheck> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) throw new Error(`Health check failed with status: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('API /health unavailable, using offline fallback schema:', err);
    return {
      status: 'degraded',
      service: 'clearway-api (offline)',
      version: '0.1.0',
      timestamp: new Date().toISOString(),
      environment: 'disconnected',
    };
  }
}

export async function fetchSystemStatus(): Promise<SystemStatus> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/system/status`);
    if (!res.ok) throw new Error(`Status check failed with status: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('API /api/v1/system/status unavailable, using fallback schema:', err);
    return {
      status: 'degraded',
      mode: 'SIMULATION',
      simulation_only: true,
      public_signal_control_permitted: false,
      data_provenance: 'DEMO_FIXTURE',
      demo_mode_enabled: true,
      modules: {
        simulation: 'PLANNED',
        ai_clearance: 'PLANNED',
        traffic_signals: 'PLANNED',
        digital_twin: 'PLANNED',
        v2x_telemetry: 'UNAVAILABLE',
        hardware_bridge: 'PLANNED',
      },
      active_scenario: 'demo-oak-5th-intersection',
      timestamp: new Date().toISOString(),
      message: 'Operating in local client fallback mode. Backend currently unreachable.',
    };
  }
}
