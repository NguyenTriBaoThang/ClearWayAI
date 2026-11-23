/**
 * ClearWayAI API Contract Types for Operations Dashboard Integration
 */

export interface SimulationItem {
  simulation_id: string;
  name: string;
  scenario_id: string;
  status: string;
  started_at: string;
  stopped_at?: string | null;
  total_steps: number;
  emergency_events: number;
  metadata?: Record<string, unknown>;
}

export interface SimulationStepResult {
  simulation_id: string;
  sim_time_sec: number;
  total_steps: number;
  active_vehicles_count: number;
  traffic_lights: Record<string, number>;
  emergency_vehicle_active: boolean;
  status: string;
}

export interface MissionItem {
  mission_id: string;
  vehicle_id: string;
  vehicle_type: string;
  status: string;
  origin: string;
  destination: string;
  dispatched_at: string;
  arrived_at?: string | null;
  current_position_m: number;
  current_speed_kmh: number;
  progress_ratio: number;
  is_active: boolean;
  route_nodes: string[];
}

export interface NodeETAResult {
  node_id: string;
  stopline_x_m: number;
  distance_to_stopline_m: number;
  eta_seconds: number;
  has_passed: boolean;
  confidence_score: number;
}

export interface MultiNodeETAReport {
  mission_id: string;
  vehicle_id: string;
  current_position_m: number;
  current_speed_kmh: number;
  etas_by_node: Record<string, NodeETAResult>;
  hospital_eta_sec: number;
  calculation_timestamp: number;
  provenance: string;
}

export interface ClearancePredictionResult {
  node_id: string;
  predicted_clearance_sec: number;
  confidence_score: number;
  model_name: string;
  model_type: string;
  fallback_used: boolean;
  fallback_tier?: string | null;
  latency_ms: number;
  provenance: string;
}

export interface CorridorPlanResult {
  mission_id?: string | null;
  vehicle_id?: string | null;
  corridor_status: string;
  current_position_m: number;
  current_speed_kmh: number;
  active_horizon_nodes: string[];
  cleared_nodes: string[];
  commanded_phases: Record<string, number>;
  coordination_offsets_sec: Record<string, number>;
  spillback_alerts: string[];
  total_active_holds: number;
  timestamp_sec: number;
  provenance: string;
}

export interface PreclearanceDecisionResult {
  node_id: string;
  state: string;
  should_actuate: boolean;
  commanded_phase: number;
  delta_trigger_sec: number;
  ev_eta_sec: number;
  predicted_clearance_sec: number;
  reason: string;
}

export interface RecoveryStatusResult {
  node_id: string;
  state: string;
  initial_green_debt_sec: number;
  remaining_green_debt_sec: number;
  current_recovery_cycle: number;
  bonus_green_allocated_sec: number;
  commanded_phase: number;
  is_recovered: boolean;
  reason: string;
}

export interface SafetyAuditResult {
  all_nodes_safe: boolean;
  sanitized_phases: Record<string, number>;
  total_interventions_corridor: number;
  timestamp_sec: number;
  provenance: string;
}

export interface ReplayStatusResult {
  simulation_id: string;
  is_playing: boolean;
  playback_speed: number;
  current_time_sec: number;
  current_index: number;
  total_snapshots: number;
}

export interface SnapshotSummary {
  id?: number | null;
  simulation_id: string;
  sim_time_sec: number;
  timestamp: string;
  active_vehicles_count: number;
  current_phase: number;
  emergency_active: boolean;
}

export interface SnapshotListResult {
  simulation_id: string;
  total_count: number;
  returned_count: number;
  snapshots: SnapshotSummary[];
}

export type ConnectionStatus = 'CONNECTED' | 'CONNECTING' | 'DISCONNECTED' | 'SIMULATED';

export interface WSEventMessage {
  event: string;
  simulation_id?: string;
  timestamp: number;
  data?: Record<string, unknown>;
}

