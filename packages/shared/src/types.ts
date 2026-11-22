/**
 * ClearWayAI Core Shared Domain Types and Enums
 */

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

export type ModuleLifecycleStatus =
  | 'PLANNED'
  | 'IN_PROGRESS'
  | 'IMPLEMENTED'
  | 'VERIFIED';

export type HardwareDeviceStatus = 'UNAVAILABLE' | 'SIMULATED' | 'CONNECTED';

export interface SystemStatus {
  status: 'operational' | 'degraded' | 'offline';
  mode: OperationalMode;
  simulation_only: boolean;
  public_signal_control_permitted: boolean;
  data_provenance: DataProvenance;
  demo_mode_enabled: boolean;
  modules: {
    simulation: ModuleLifecycleStatus;
    ai_clearance: ModuleLifecycleStatus;
    traffic_signals: ModuleLifecycleStatus;
    digital_twin: ModuleLifecycleStatus;
    v2x_telemetry: HardwareDeviceStatus;
    hardware_bridge: ModuleLifecycleStatus;
  };
  active_scenario: string;
  timestamp: string;
  message: string;
}

export type VehicleClass =
  | 'motorcycle'
  | 'passenger_car'
  | 'suv'
  | 'bus'
  | 'truck'
  | 'emergency_ambulance'
  | 'emergency_fire';

export interface VehicleState {
  id: string;
  vehicle_class: VehicleClass;
  x: number;
  y: number;
  z?: number;
  heading: number;
  speed_kmh: number;
  current_lane_id: string;
  is_priority_vehicle: boolean;
  mission_id?: string;
  provenance: DataProvenance;
}

export interface SignalApproachTiming {
  approach: string;
  red_s: number;
  yellow_s: number;
  green_s: number;
  cycle_s: number;
  split_pct: number;
  current_phase: 'red' | 'yellow' | 'green';
}

export interface SignalState {
  intersection_id: string;
  intersection_name: string;
  cycle_time_s: number;
  current_phase_name: string;
  next_phase_name: string;
  approaches: SignalApproachTiming[];
  provenance: DataProvenance;
}

export interface HardwareStatus {
  network_id: string;
  obu_vehicles_online: number;
  obu_pct: number;
  rsu_online: number;
  rsu_pct: number;
  edge_controllers_online: number;
  signal_controllers_online: number;
  v2x_status: 'Active' | 'Degraded' | 'Offline' | 'Simulated';
  latency_ms: number;
  packet_loss_pct: number;
  provenance: DataProvenance;
}

export interface EmergencyMission {
  mission_id: string;
  vehicle_id: string;
  vehicle_type: 'ambulance' | 'firetruck';
  target_facility: string;
  eta_hospital_min: number;
  status: 'ACTIVE' | 'STANDBY' | 'COMPLETED' | 'CANCELLED';
  corridor_intersections: string[];
  provenance: DataProvenance;
}

export interface TrafficAnalytics {
  intersection_id: string;
  performance_index: number;
  throughput_pct_change: number;
  avg_delay_pct_change: number;
  stops_per_veh_pct_change: number;
  occupancy_pct: number;
  avg_speed_kmh: number;
  avg_queue_m: number;
  backlog_m: number;
  provenance: DataProvenance;
}

