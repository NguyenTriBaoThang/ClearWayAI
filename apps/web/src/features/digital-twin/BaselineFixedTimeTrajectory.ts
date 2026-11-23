/**
 * ClearWayAI - Baseline B0 Fixed-Time Trajectory Source (`BaselineFixedTimeTrajectory.ts`)
 *
 * Models traffic along the 1,000m corridor under traditional rigid Fixed-Time signal control:
 * - Webster cycle (72s rigid phase splits with zero emergency preemption).
 * - Priority vehicle (AMB-339) experiences red-light stopping and queue spillback delays.
 * - Incurs 2 full stops at Node A and Node C stoplines.
 * - Resulting travel time: ~108s (average speed ~28 km/h).
 */

import { VehicleClass, DataProvenance } from '@clearway/shared';
import { VehicleSnapshot, VehicleTrajectorySource, VehicleMotionStatus } from './VehicleTrajectorySource';

export class BaselineFixedTimeTrajectory implements VehicleTrajectorySource {
  public readonly sourceId: DataProvenance = 'DEMO_FIXTURE';

  private cachedVehicles: Map<string, VehicleSnapshot> = new Map();

  constructor() {
    this.reset();
  }

  public reset(): void {
    this.cachedVehicles.clear();
  }

  /**
   * Computes vehicle states at simulation time (timeMs) under Baseline B0 fixed-time control
   */
  public getSnapshotsAtTime(timeMs: number): VehicleSnapshot[] {
    const t = Math.max(0, (timeMs / 1000) % 115); // Loop 115s simulation episode
    const snapshots: VehicleSnapshot[] = [];

    // --- 1. Emergency Ambulance AMB-339 (Baseline B0 with Red-Light Delays) ---
    let ambX = -150.0;
    let ambSpeedKmh = 50.0;
    let ambStatus: VehicleMotionStatus = 'RUNNING';
    let ambWaiting = 0;

    if (t < 10.0) {
      // Approach Node A: -150m to -12m (Speed 50 km/h = 13.8 m/s)
      ambX = -150.0 + t * 13.8;
      ambSpeedKmh = 50.0;
      ambStatus = 'RUNNING';
    } else if (t < 24.0) {
      // STOP 1 at Node A stopline (x = -12m): Red signal hold (14s delay)
      ambX = -12.0;
      ambSpeedKmh = 0.0;
      ambStatus = 'WAITING_SIGNAL';
      ambWaiting = t - 10.0;
    } else if (t < 44.0) {
      // Node A green: accelerates from -12m to Node B (x = 238m)
      const dt = t - 24.0;
      ambX = -12.0 + dt * 12.5; // ~45 km/h
      ambSpeedKmh = 45.0;
      ambStatus = 'RUNNING';
    } else if (t < 50.0) {
      // Passes Node B on green: x = 238m to 320m
      const dt = t - 44.0;
      ambX = 238.0 + dt * 13.6;
      ambSpeedKmh = 49.0;
      ambStatus = 'RUNNING';
    } else if (t < 64.0) {
      // Approaches Node C stopline (x = 488m)
      const dt = t - 50.0;
      ambX = 320.0 + dt * 12.0;
      ambSpeedKmh = 43.0;
      ambStatus = 'RUNNING';
    } else if (t < 78.0) {
      // STOP 2 at Node C stopline (x = 488m): Red signal & queue backlog (14s delay)
      ambX = 488.0;
      ambSpeedKmh = 0.0;
      ambStatus = 'WAITING_SIGNAL';
      ambWaiting = t - 64.0;
    } else if (t < 98.0) {
      // Node C green: accelerates from 488m to Node D (x = 738m)
      const dt = t - 78.0;
      ambX = 488.0 + dt * 12.5;
      ambSpeedKmh = 45.0;
      ambStatus = 'RUNNING';
    } else if (t < 108.0) {
      // Approaches and arrives at Trauma Center (x = 850m)
      const dt = t - 98.0;
      ambX = Math.min(850.0, 738.0 + dt * 11.2);
      ambSpeedKmh = ambX >= 850.0 ? 0.0 : 40.0;
      ambStatus = ambX >= 850.0 ? 'ARRIVED' : 'RUNNING';
    } else {
      // Arrived at Hospital
      ambX = 850.0;
      ambSpeedKmh = 0.0;
      ambStatus = 'ARRIVED';
    }

    const ambSnap: VehicleSnapshot = {
      id: 'AMB-339',
      vehicle_class: 'emergency_ambulance',
      x: ambX,
      y: 0.2,
      z: 1.75, // Eastbound lane
      heading: 90.0,
      speed_ms: ambSpeedKmh / 3.6,
      speed_kmh: ambSpeedKmh,
      current_lane_id: '5th_eb_lane1',
      route: 'route_eb_through',
      is_priority_vehicle: true,
      mission_id: 'MISSION-AMB-339',
      provenance: 'DEMO_FIXTURE',
      timestamp: timeMs,
      status: ambStatus,
      waiting_time_s: ambWaiting,
    };
    snapshots.push(ambSnap);
    this.cachedVehicles.set(ambSnap.id, ambSnap);

    // --- 2. Surrounding Mixed Traffic (Cars, Buses, Trucks, Motorcycles) ---
    // Background vehicles queuing or cruising along 5th Ave and cross streets
    const bgVehicles = [
      { id: 'CAR-01', cls: 'passenger_car' as VehicleClass, x: -60.0 + ((t * 8) % 400), z: 1.75, h: 90.0, spd: 32.0 },
      { id: 'MOTO-12', cls: 'motorcycle' as VehicleClass, x: -30.0 + ((t * 11) % 450), z: 3.2, h: 90.0, spd: 40.0 },
      { id: 'BUS-104', cls: 'bus' as VehicleClass, x: 600.0 - ((t * 7) % 600), z: -1.75, h: 270.0, spd: 26.0 },
      { id: 'TRUCK-44', cls: 'truck' as VehicleClass, x: 800.0 - ((t * 6) % 650), z: -5.25, h: 270.0, spd: 22.0 },
      { id: 'SUV-08', cls: 'suv' as VehicleClass, x: 250.0, z: -150.0 + ((t * 7) % 300), h: 180.0, spd: 28.0 },
      { id: 'MOTO-55', cls: 'motorcycle' as VehicleClass, x: 500.0, z: 120.0 - ((t * 9) % 250), h: 0.0, spd: 34.0 },
    ];

    for (const bg of bgVehicles) {
      const snap: VehicleSnapshot = {
        id: bg.id,
        vehicle_class: bg.cls,
        x: bg.x,
        y: 0.2,
        z: bg.z,
        heading: bg.h,
        speed_ms: bg.spd / 3.6,
        speed_kmh: bg.spd,
        current_lane_id: 'corridor_mixed_lane',
        route: 'route_corridor_mixed',
        is_priority_vehicle: false,
        provenance: 'DEMO_FIXTURE',
        timestamp: timeMs,
        status: 'RUNNING',
        waiting_time_s: 0,
      };
      snapshots.push(snap);
      this.cachedVehicles.set(bg.id, snap);
    }

    return snapshots;
  }

  public getVehicleState(vehicleId: string): VehicleSnapshot | null {
    return this.cachedVehicles.get(vehicleId) || null;
  }

  public getAllVehicleIds(): string[] {
    return Array.from(this.cachedVehicles.keys());
  }

  /**
   * Return rigid 72s Webster signal phase for intersection at time t (sec)
   */
  public getSignalPhaseAtTime(timeSec: number): number {
    const cycle = timeSec % 72.0;
    if (cycle < 35.0) return 0; // EW Green
    if (cycle < 39.0) return 1; // EW Yellow
    if (cycle < 41.0) return 2; // All-Red
    if (cycle < 66.0) return 3; // NS Green
    if (cycle < 70.0) return 4; // NS Yellow
    return 5; // All-Red
  }
}

