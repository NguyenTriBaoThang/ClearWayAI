export type OperationalMode =
  | 'SIMULATION'
  | 'OFFLINE_VIDEO'
  | 'SHADOW_ADVISORY'
  | 'AUTHORIZED_PILOT';

export type DataProvenance =
  | 'DEMO_FIXTURE'
  | 'SUMO_SIMULATED'
  | 'OFFLINE_VIDEO'
  | 'SHADOW_ADVISORY'
  | 'LIVE_CONNECTED';

export interface SystemStatus {
  status: 'operational' | 'degraded' | 'offline';
  mode: OperationalMode;
  simulation_only: boolean;
  public_signal_control_permitted: boolean;
  data_provenance: DataProvenance;
  demo_mode_enabled: boolean;
  modules: {
    simulation: string;
    ai_clearance: string;
    traffic_signals: string;
    digital_twin: string;
    v2x_telemetry: string;
    hardware_bridge: string;
  };
  active_scenario: string;
  timestamp: string;
  message: string;
}

export interface HealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy';
  service: string;
  version: string;
  timestamp: string;
  environment: string;
}
