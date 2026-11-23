/**
 * ClearWayAI - SUMO / Real-time Telemetry Trajectory Provider (`SumoTrajectorySource.ts`)
 *
 * Ingests live microscopic simulation snapshots from SUMO / TraCI (via WebSocket or REST),
 * converts spatial coordinates from SUMO network space into Three.js 3D WebGL world space,
 * performs dead reckoning and linear interpolation between simulation ticks,
 * detects STALE frames when WebSocket packet latency exceeds threshold,
 * and maintains vehicle kinematic states and emergency priority along the 1,000m corridor.
 */

import { VehicleClass, DataProvenance } from '@clearway/shared';
import { VehicleSnapshot, VehicleTrajectorySource, VehicleMotionStatus } from './VehicleTrajectorySource';

export interface SumoVehicleTelemetryItem {
  vehicle_id: string;
  vehicle_class?: string;
  speed_kmh: number;
  position_x: number;
  position_y: number;
  position_z?: number;
  heading_deg: number;
  lane_id?: string;
  is_priority_vehicle?: boolean;
  mission_id?: string;
  provenance?: DataProvenance;
}

export interface SumoSignalState {
  intersection_id?: string;
  current_phase?: number;
  traffic_lights?: Record<string, number>;
  preemption_active?: boolean;
}

export interface SumoTelemetrySnapshotInput {
  intersection_id?: string;
  sim_time_sec: number;
  timestamp?: string;
  vehicles?: SumoVehicleTelemetryItem[];
  signals?: SumoSignalState | any;
  traffic_lights?: Record<string, number>;
  active_mission?: any;
  provenance?: DataProvenance;
}

interface BufferedSnapshot {
  simTimeSec: number;
  wallTimeMs: number;
  vehicles: Map<string, VehicleSnapshot>;
}

export class SumoTrajectorySource implements VehicleTrajectorySource {
  public readonly sourceId: DataProvenance = 'SUMO_SIMULATED';

  // Double-buffer for smooth interpolation between consecutive simulation frames
  private buffer: BufferedSnapshot[] = [];
  private currentVehicles: Map<string, VehicleSnapshot> = new Map();
  private lastIngestWallTimeMs: number = 0;
  private readonly STALE_THRESHOLD_MS: number = 2500;

  // Active traffic light phases per node
  public nodePhases: Map<string, number> = new Map([
    ['node_a', 0],
    ['node_b', 0],
    ['node_c', 0],
    ['node_d', 0],
  ]);
  public activeMission: any = null;
  public latestSimTimeSec: number = 0;

  constructor() {
    this.reset();
  }

  /**
   * Reset internal buffers and vehicle maps
   */
  public reset(): void {
    this.buffer = [];
    this.currentVehicles.clear();
    this.lastIngestWallTimeMs = 0;
    this.latestSimTimeSec = 0;
    this.nodePhases.set('node_a', 0);
    this.nodePhases.set('node_b', 0);
    this.nodePhases.set('node_c', 0);
    this.nodePhases.set('node_d', 0);
  }

  /**
   * Ingest a live microscopic simulation telemetry snapshot from SUMO / TraCI
   */
  public ingestTelemetrySnapshot(snapshot: SumoTelemetrySnapshotInput): void {
    const wallNow = typeof performance !== 'undefined' ? performance.now() : Date.now();
    this.lastIngestWallTimeMs = wallNow;
    this.latestSimTimeSec = snapshot.sim_time_sec;

    // Parse and update signal phases if present
    if (snapshot.traffic_lights) {
      for (const [nodeId, phase] of Object.entries(snapshot.traffic_lights)) {
        this.nodePhases.set(nodeId, Number(phase));
      }
    } else if (snapshot.signals && typeof snapshot.signals.current_phase === 'number') {
      const p = Number(snapshot.signals.current_phase);
      this.nodePhases.set('node_a', p);
      this.nodePhases.set('node_b', p);
      this.nodePhases.set('node_c', p);
      this.nodePhases.set('node_d', p);
    }

    if (snapshot.active_mission) {
      this.activeMission = snapshot.active_mission;
    }

    // Convert vehicles array into typed VehicleSnapshot map
    const newVehicles = new Map<string, VehicleSnapshot>();
    const vehList = snapshot.vehicles || [];

    for (const v of vehList) {
      const snap = this.mapSumoVehicleToSnapshot(v, snapshot.sim_time_sec, wallNow);
      newVehicles.set(snap.id, snap);
      this.currentVehicles.set(snap.id, snap);
    }

    // Push into interpolation buffer (keep last 3 frames)
    this.buffer.push({
      simTimeSec: snapshot.sim_time_sec,
      wallTimeMs: wallNow,
      vehicles: newVehicles,
    });

    if (this.buffer.length > 3) {
      this.buffer.shift();
    }
  }

  /**
   * Converts raw SUMO vehicle telemetry into 3D world space VehicleSnapshot
   */
  public mapSumoVehicleToSnapshot(
    v: SumoVehicleTelemetryItem,
    simTimeSec: number,
    wallTimeMs: number
  ): VehicleSnapshot {
    const id = v.vehicle_id;
    const isPriority = Boolean(
      v.is_priority_vehicle ||
      id.includes('AMB') ||
      id.includes('FIRE') ||
      v.vehicle_class === 'emergency_ambulance' ||
      v.vehicle_class === 'emergency_fire'
    );

    // Map vehicle class
    let vehicleClass: VehicleClass = 'passenger_car';
    if (id.includes('AMB') || v.vehicle_class === 'emergency_ambulance') {
      vehicleClass = 'emergency_ambulance';
    } else if (id.includes('FIRE') || v.vehicle_class === 'emergency_fire') {
      vehicleClass = 'emergency_fire';
    } else if (v.vehicle_class === 'motorcycle' || id.startsWith('MOTO')) {
      vehicleClass = 'motorcycle';
    } else if (v.vehicle_class === 'bus' || id.startsWith('BUS')) {
      vehicleClass = 'bus';
    } else if (v.vehicle_class === 'truck' || id.startsWith('TRUCK')) {
      vehicleClass = 'truck';
    } else if (v.vehicle_class === 'suv' || id.startsWith('SUV')) {
      vehicleClass = 'suv';
    }

    // Map SUMO 2D coordinates to Three.js 3D world coordinates:
    // 5th Ave runs East-West along X axis (-150m to 900m)
    // Cross streets run North-South along Z axis
    const x3d = v.position_x;
    const y3d = 0.2; // Elevation above road surface (y=0.01)

    // Center lateral position inside correct lane if position_y is 0
    let z3d = v.position_y;
    if (Math.abs(z3d) < 0.1) {
      if (Math.abs(v.heading_deg - 90) < 30) {
        // Eastbound along 5th Ave: South side lane (z = +1.75m)
        z3d = 1.75;
      } else if (Math.abs(v.heading_deg - 270) < 30) {
        // Westbound along 5th Ave: North side lane (z = -1.75m)
        z3d = -1.75;
      }
    }

    const speedKmh = Math.max(0, v.speed_kmh);
    const speedMs = speedKmh / 3.6;

    // Determine motion status
    let status: VehicleMotionStatus = 'RUNNING';
    if (speedKmh < 1.0) {
      status = 'WAITING_SIGNAL';
    } else if (isPriority) {
      status = 'PRIORITY_CORRIDOR';
    }

    return {
      id,
      vehicle_class: vehicleClass,
      x: x3d,
      y: y3d,
      z: z3d,
      heading: v.heading_deg,
      speed_ms: speedMs,
      speed_kmh: speedKmh,
      current_lane_id: v.lane_id || '5th_ave_corridor',
      route: v.lane_id || 'route_corridor_through',
      is_priority_vehicle: isPriority,
      mission_id: v.mission_id || (isPriority ? 'MISSION-AMB-339' : undefined),
      provenance: v.provenance || this.sourceId,
      timestamp: simTimeSec * 1000,
      status,
      waiting_time_s: speedKmh < 1.0 ? 1.0 : 0.0,
    };
  }

  /**
   * Return vehicle snapshots with smooth interpolation and bounded dead reckoning
   */
  public getSnapshotsAtTime(timeMs: number): VehicleSnapshot[] {
    const wallNow = typeof performance !== 'undefined' ? performance.now() : timeMs;
    const isStale = (wallNow - this.lastIngestWallTimeMs) > this.STALE_THRESHOLD_MS;

    if (this.buffer.length === 0) {
      return Array.from(this.currentVehicles.values());
    }

    // If only one snapshot exists, return its vehicles
    if (this.buffer.length === 1) {
      return Array.from(this.buffer[0].vehicles.values()).map((v) => ({
        ...v,
        status: isStale ? 'STALE' : v.status,
      }));
    }

    // Interpolate between the last two buffered snapshots
    const prev = this.buffer[this.buffer.length - 2];
    const curr = this.buffer[this.buffer.length - 1];
    const dt = Math.max(50, curr.wallTimeMs - prev.wallTimeMs);
    const elapsed = wallNow - curr.wallTimeMs;
    const alpha = Math.min(Math.max(elapsed / dt, 0), 1.5);

    const result: VehicleSnapshot[] = [];

    for (const [id, currVeh] of curr.vehicles.entries()) {
      const prevVeh = prev.vehicles.get(id);

      if (prevVeh && alpha <= 1.0) {
        // Linear spatial interpolation between prev and curr ticks
        const interpX = prevVeh.x + (currVeh.x - prevVeh.x) * alpha;
        const interpZ = prevVeh.z + (currVeh.z - prevVeh.z) * alpha;
        result.push({
          ...currVeh,
          x: interpX,
          z: interpZ,
          status: isStale ? 'STALE' : currVeh.status,
        });
      } else if (alpha > 1.0 && alpha <= 2.0 && !isStale) {
        // Bounded dead-reckoning extrapolation
        const extraSec = (elapsed - dt) / 1000;
        const headingRad = (currVeh.heading * Math.PI) / 180;
        const extraX = currVeh.speed_ms * Math.sin(headingRad) * extraSec;
        const extraZ = -currVeh.speed_ms * Math.cos(headingRad) * extraSec;
        result.push({
          ...currVeh,
          x: currVeh.x + extraX,
          z: currVeh.z + extraZ,
          status: currVeh.status,
        });
      } else {
        result.push({
          ...currVeh,
          status: isStale ? 'STALE' : currVeh.status,
        });
      }
    }

    return result;
  }

  public getVehicleState(vehicleId: string): VehicleSnapshot | null {
    return this.currentVehicles.get(vehicleId) || null;
  }

  public getAllVehicleIds(): string[] {
    return Array.from(this.currentVehicles.keys());
  }

  public getActiveVehicleCount(): number {
    return this.currentVehicles.size;
  }

  public isStreamFresh(): boolean {
    const wallNow = typeof performance !== 'undefined' ? performance.now() : Date.now();
    return this.lastIngestWallTimeMs > 0 && (wallNow - this.lastIngestWallTimeMs) <= this.STALE_THRESHOLD_MS;
  }
}
