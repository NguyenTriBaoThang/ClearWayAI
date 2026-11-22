/**
 * Dashboard & Panel Type Definitions
 */

export interface TelemetrySummary {
  fps: number;
  latencyMs: number;
  wsConnected: boolean;
  safetyInterlockActive: boolean;
  simulationOnly: boolean;
  activeScenario: string;
}

export interface IntersectionInfo {
  id: string;
  name: string;
  status: 'ONLINE' | 'OFFLINE' | 'DEGRADED';
  activePhase: string;
  currentPhaseTimeLeft: number;
  totalCycleTime: number;
}

export interface CameraPreset {
  id: 'isometric' | 'topDown' | 'intersection' | 'chase';
  label: string;
}

export type ViewportMode = 'ORTHOGRAPHIC' | 'PERSPECTIVE';

export interface EmergencyCorridorStatus {
  active: boolean;
  missionId: string;
  vehicleId: string;
  vehicleType: string;
  speedKmh: number;
  etaSec: number;
  clearancePct: number;
  routeLanes: string[];
}
