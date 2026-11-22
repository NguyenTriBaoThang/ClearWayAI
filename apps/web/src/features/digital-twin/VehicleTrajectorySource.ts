import { VehicleClass, DataProvenance } from '@clearway/shared';

export type VehicleMotionStatus =
  | 'RUNNING'
  | 'WAITING_SIGNAL'
  | 'CLEARING'
  | 'PRIORITY_CORRIDOR'
  | 'STALE'
  | 'ARRIVED';

export interface VehicleSnapshot {
  id: string;
  vehicle_class: VehicleClass;
  x: number;
  y: number;
  z: number;
  heading: number; // Orientation in degrees (0 = North/-Z, 90 = East/+X, 180 = South/+Z, 270 = West/-X)
  speed_ms: number; // Physical velocity in meters/second
  speed_kmh: number; // Velocity in kilometers/hour (strictly speed_ms * 3.6)
  current_lane_id: string;
  route: string;
  is_priority_vehicle: boolean;
  mission_id?: string;
  provenance: DataProvenance;
  timestamp: number; // Milliseconds timestamp of simulation
  status: VehicleMotionStatus;
  waiting_time_s: number;
}

/**
 * Common trajectory provider interface enabling seamless swapping between
 * deterministic fixture playback and live SUMO / TraCI streaming.
 */
export interface VehicleTrajectorySource {
  readonly sourceId: DataProvenance;
  getSnapshotsAtTime(timeMs: number): VehicleSnapshot[];
  getVehicleState(vehicleId: string): VehicleSnapshot | null;
  getAllVehicleIds(): string[];
  reset(): void;
}

