import { VehicleClass } from '@clearway/shared';
import { VehicleSnapshot, VehicleTrajectorySource, VehicleMotionStatus } from './VehicleTrajectorySource';

interface VehicleRouteDef {
  id: string;
  vehicle_class: VehicleClass;
  is_priority_vehicle: boolean;
  mission_id?: string;
  routeType: 'EB_STRAIGHT' | 'WB_STRAIGHT' | 'NB_STRAIGHT' | 'SB_STRAIGHT' | 'NB_RIGHT' | 'EB_LEFT' | 'STANDBY';
  laneId: string;
  nominalSpeedKmh: number;
  initialOffset: number; // initial distance offset in meters along path
  cycleOffsetSec: number; // phase time offset
}

/**
 * Deterministic vehicle snapshot fixture generator.
 * Produces realistic, repeatable urban traffic patterns for INT-0457
 * with stop line deceleration, signal waiting, green wave acceleration,
 * turning trajectories, and emergency priority corridor clearance.
 */
export class VehicleSnapshotFixture implements VehicleTrajectorySource {
  public readonly sourceId = 'DEMO_FIXTURE' as const;

  private vehicleDefs: VehicleRouteDef[] = [];
  private cachedSnapshots: Map<string, VehicleSnapshot> = new Map();

  constructor() {
    this.initVehicleDefinitions();
  }

  private initVehicleDefinitions(): void {
    // 1. Emergency Ambulance AMB-339 (Eastbound Priority Corridor)
    this.vehicleDefs.push({
      id: 'AMB-339',
      vehicle_class: 'emergency_ambulance',
      is_priority_vehicle: true,
      mission_id: 'MISSION-AMB-339',
      routeType: 'EB_STRAIGHT',
      laneId: '5TH_EB_L1',
      nominalSpeedKmh: 62,
      initialOffset: -38,
      cycleOffsetSec: 0,
    });

    // 2. Emergency Fire Engine FIRE-09 (Standby at South curb)
    this.vehicleDefs.push({
      id: 'FIRE-09',
      vehicle_class: 'emergency_fire',
      is_priority_vehicle: true,
      mission_id: 'STANDBY-FIRE-09',
      routeType: 'STANDBY',
      laneId: '5TH_WB_L2',
      nominalSpeedKmh: 0,
      initialOffset: 0,
      cycleOffsetSec: 0,
    });

    // 3. Urban Transit Buses
    this.vehicleDefs.push(
      {
        id: 'BUS-104',
        vehicle_class: 'bus',
        is_priority_vehicle: false,
        routeType: 'WB_STRAIGHT',
        laneId: '5TH_WB_L1',
        nominalSpeedKmh: 34,
        initialOffset: 36,
        cycleOffsetSec: 3,
      },
      {
        id: 'BUS-202',
        vehicle_class: 'bus',
        is_priority_vehicle: false,
        routeType: 'NB_STRAIGHT',
        laneId: 'OAK_NB_L1',
        nominalSpeedKmh: 30,
        initialOffset: 32,
        cycleOffsetSec: 12,
      }
    );

    // 4. Delivery Cargo Trucks
    this.vehicleDefs.push(
      {
        id: 'TRUCK-55',
        vehicle_class: 'truck',
        is_priority_vehicle: false,
        routeType: 'SB_STRAIGHT',
        laneId: 'OAK_SB_L2',
        nominalSpeedKmh: 28,
        initialOffset: -35,
        cycleOffsetSec: 8,
      },
      {
        id: 'TRUCK-72',
        vehicle_class: 'truck',
        is_priority_vehicle: false,
        routeType: 'EB_STRAIGHT',
        laneId: '5TH_EB_L2',
        nominalSpeedKmh: 32,
        initialOffset: -28,
        cycleOffsetSec: 15,
      }
    );

    // 5. Crossover SUVs (4 vehicles: SUV-01, SUV-02, SUV-03, SUV-04)
    for (let i = 1; i <= 4; i++) {
      const routes: VehicleRouteDef['routeType'][] = ['EB_STRAIGHT', 'WB_STRAIGHT', 'NB_STRAIGHT', 'SB_STRAIGHT'];
      const lanes = ['5TH_EB_L2', '5TH_WB_L2', 'OAK_NB_L2', 'OAK_SB_L2'];
      this.vehicleDefs.push({
        id: `SUV-0${i}`,
        vehicle_class: 'suv',
        is_priority_vehicle: false,
        routeType: routes[(i - 1) % routes.length],
        laneId: lanes[(i - 1) % lanes.length],
        nominalSpeedKmh: 42,
        initialOffset: -20 - i * 6,
        cycleOffsetSec: i * 4,
      });
    }

    // 6. Passenger Sedans (12 vehicles: CAR-01 to CAR-12)
    for (let i = 1; i <= 12; i++) {
      const isEven = i % 2 === 0;
      const routeIdx = i % 4;
      const routes: VehicleRouteDef['routeType'][] = ['EB_STRAIGHT', 'WB_STRAIGHT', 'NB_STRAIGHT', 'SB_STRAIGHT'];
      const lanes = ['5TH_EB_L1', '5TH_WB_L1', 'OAK_NB_L1', 'OAK_SB_L1'];
      const padId = i < 10 ? `0${i}` : `${i}`;
      this.vehicleDefs.push({
        id: `CAR-${padId}`,
        vehicle_class: 'passenger_car',
        is_priority_vehicle: false,
        routeType: i === 5 ? 'NB_RIGHT' : i === 9 ? 'EB_LEFT' : routes[routeIdx],
        laneId: lanes[routeIdx],
        nominalSpeedKmh: isEven ? 45 : 38,
        initialOffset: -16 - (i % 5) * 8,
        cycleOffsetSec: (i * 3.5) % 30,
      });
    }

    // 7. Urban High-Density Motorcycles / Scooters (20 vehicles: MOTO-01 to MOTO-20)
    for (let i = 1; i <= 20; i++) {
      const padId = i < 10 ? `0${i}` : `${i}`;
      const approach = i % 4;
      let route: VehicleRouteDef['routeType'] = 'EB_STRAIGHT';
      let lane = '5TH_EB_L1';

      if (approach === 0) {
        route = 'EB_STRAIGHT';
        lane = i % 2 === 0 ? '5TH_EB_L1' : '5TH_EB_L2';
      } else if (approach === 1) {
        route = 'WB_STRAIGHT';
        lane = i % 2 === 0 ? '5TH_WB_L1' : '5TH_WB_L2';
      } else if (approach === 2) {
        route = 'NB_STRAIGHT';
        lane = i % 2 === 0 ? 'OAK_NB_L1' : 'OAK_NB_L2';
      } else {
        route = 'SB_STRAIGHT';
        lane = i % 2 === 0 ? 'OAK_SB_L1' : 'OAK_SB_L2';
      }

      this.vehicleDefs.push({
        id: `MOTO-${padId}`,
        vehicle_class: 'motorcycle',
        is_priority_vehicle: false,
        routeType: route,
        laneId: lane,
        nominalSpeedKmh: 30 + (i % 4) * 3,
        initialOffset: -12 - (i % 6) * 3.5, // Denser queueing near stop lines
        cycleOffsetSec: (i * 2.2) % 30,
      });
    }
  }

  /**
   * Deterministic signal state query for INT-0457:
   * Cycle: 60s
   * 0s - 25s: East-West Green, North-South Red
   * 25s - 28s: East-West Yellow, North-South Red
   * 28s - 30s: All-Red Clearance
   * 30s - 55s: North-South Green, East-West Red
   * 55s - 58s: North-South Yellow, East-West Red
   * 58s - 60s: All-Red Clearance
   */
  public getSignalPhase(timeMs: number): {
    ewPhase: 'GREEN' | 'YELLOW' | 'RED';
    nsPhase: 'GREEN' | 'YELLOW' | 'RED';
    cycleSec: number;
  } {
    const cycleSec = (timeMs / 1000) % 60;
    if (cycleSec < 25) {
      return { ewPhase: 'GREEN', nsPhase: 'RED', cycleSec };
    } else if (cycleSec < 28) {
      return { ewPhase: 'YELLOW', nsPhase: 'RED', cycleSec };
    } else if (cycleSec < 30) {
      return { ewPhase: 'RED', nsPhase: 'RED', cycleSec };
    } else if (cycleSec < 55) {
      return { ewPhase: 'RED', nsPhase: 'GREEN', cycleSec };
    } else if (cycleSec < 58) {
      return { ewPhase: 'RED', nsPhase: 'YELLOW', cycleSec };
    } else {
      return { ewPhase: 'RED', nsPhase: 'RED', cycleSec };
    }
  }

  /**
   * Compute deterministic state for all vehicles at a specific timestamp.
   */
  public getSnapshotsAtTime(timeMs: number): VehicleSnapshot[] {
    const { ewPhase, nsPhase } = this.getSignalPhase(timeMs);
    const snapshots: VehicleSnapshot[] = [];

    const corridorLength = 76; // from -38m to +38m

    for (const def of this.vehicleDefs) {
      // 1. Standby vehicles (e.g. FIRE-09)
      if (def.routeType === 'STANDBY') {
        const snap: VehicleSnapshot = {
          id: def.id,
          vehicle_class: def.vehicle_class,
          x: -32,
          y: 0,
          z: -5.25,
          heading: 90,
          speed_ms: 0,
          speed_kmh: 0,
          current_lane_id: def.laneId,
          route: 'STANDBY',
          is_priority_vehicle: true,
          mission_id: def.mission_id,
          provenance: this.sourceId,
          timestamp: timeMs,
          status: 'RUNNING',
          waiting_time_s: 0,
        };
        this.cachedSnapshots.set(def.id, snap);
        snapshots.push(snap);
        continue;
      }

      // 2. Emergency Priority Ambulance AMB-339
      if (def.is_priority_vehicle && def.id === 'AMB-339') {
        const speedMs = def.nominalSpeedKmh / 3.6; // ~17.2 m/s
        const totalTravelTimeSec = corridorLength / speedMs;
        const progressSec = ((timeMs / 1000) + def.cycleOffsetSec) % (totalTravelTimeSec + 2);
        const posX = Math.min(-38 + progressSec * speedMs, 38);
        const isRunning = posX < 37.5;

        const snap: VehicleSnapshot = {
          id: def.id,
          vehicle_class: def.vehicle_class,
          x: posX,
          y: 0,
          z: 1.75, // Centered on 5TH_EB_L1
          heading: 90, // Facing East (+X)
          speed_ms: isRunning ? speedMs : 0,
          speed_kmh: isRunning ? def.nominalSpeedKmh : 0,
          current_lane_id: def.laneId,
          route: 'PRIORITY_CORRIDOR_EB',
          is_priority_vehicle: true,
          mission_id: def.mission_id,
          provenance: this.sourceId,
          timestamp: timeMs,
          status: isRunning ? 'PRIORITY_CORRIDOR' : 'ARRIVED',
          waiting_time_s: 0,
        };
        this.cachedSnapshots.set(def.id, snap);
        snapshots.push(snap);
        continue;
      }

      // 3. Regular traffic streams with signal compliance
      const isEW = def.routeType === 'EB_STRAIGHT' || def.routeType === 'WB_STRAIGHT' || def.routeType === 'EB_LEFT';
      const approachPhase = isEW ? ewPhase : nsPhase;
      const nominalSpeedMs = def.nominalSpeedKmh / 3.6;

      // Base offset and cyclic progression
      const tSec = (timeMs / 1000) + def.cycleOffsetSec;
      const cyclePeriod = 40; // 40s travel/cycle per vehicle
      const rawDistance = (tSec % cyclePeriod) * nominalSpeedMs + def.initialOffset;

      // Distance modulo corridor bounds
      let dist = ((rawDistance + 40) % 80) - 40; // -40m to +40m
      let actualSpeedMs = nominalSpeedMs;
      let status: VehicleMotionStatus = 'RUNNING';
      let waitingTime = 0;

      // Stop line check: approach stop line is at distance -14m before intersection center
      const isApproachingStop = dist >= -16 && dist <= -13;
      if (approachPhase === 'RED' && isApproachingStop) {
        // Halt at stop line
        dist = -14.2;
        actualSpeedMs = 0;
        status = 'WAITING_SIGNAL';
        waitingTime = 12.5;
      } else if (approachPhase === 'YELLOW' && dist < -15 && dist > -18) {
        // Decelerate for yellow
        dist = -15;
        actualSpeedMs = nominalSpeedMs * 0.4;
        status = 'WAITING_SIGNAL';
      }

      // Compute 3D coordinates based on route
      let x = 0;
      let z = 0;
      let heading = 0;

      switch (def.routeType) {
        case 'EB_STRAIGHT': {
          x = dist;
          z = def.laneId.endsWith('L1') ? 1.75 : 5.25;
          heading = 90;
          break;
        }
        case 'WB_STRAIGHT': {
          x = -dist;
          z = def.laneId.endsWith('L1') ? -1.75 : -5.25;
          heading = 270;
          break;
        }
        case 'NB_STRAIGHT': {
          x = def.laneId.endsWith('L1') ? -1.75 : -5.25;
          z = -dist;
          heading = 0; // Moving towards -Z (North)
          break;
        }
        case 'SB_STRAIGHT': {
          x = def.laneId.endsWith('L1') ? 1.75 : 5.25;
          z = dist;
          heading = 180; // Moving towards +Z (South)
          break;
        }
        case 'NB_RIGHT': {
          // Northbound turning right to Eastbound: from x=-5.25, z>0 to x>0, z=5.25
          if (dist < -14) {
            x = -5.25;
            z = -dist;
            heading = 0;
          } else if (dist <= 0) {
            // Arc turning
            const alpha = (dist + 14) / 14; // 0 to 1
            const angle = alpha * (Math.PI / 2);
            x = -5.25 + 10.5 * (1 - Math.cos(angle));
            z = 14 - 8.75 * Math.sin(angle);
            heading = 90 * alpha;
          } else {
            x = dist;
            z = 5.25;
            heading = 90;
          }
          break;
        }
        case 'EB_LEFT': {
          // Eastbound turning left to Northbound
          if (dist < -10) {
            x = dist;
            z = 1.75;
            heading = 90;
          } else if (dist <= 5) {
            const alpha = (dist + 10) / 15;
            x = -10 + 8.25 * Math.sin(alpha * (Math.PI / 2));
            z = 1.75 - 3.5 * alpha;
            heading = 90 - 90 * alpha;
          } else {
            x = -1.75;
            z = -(dist - 5);
            heading = 0;
          }
          break;
        }
      }

      const snap: VehicleSnapshot = {
        id: def.id,
        vehicle_class: def.vehicle_class,
        x,
        y: 0,
        z,
        heading,
        speed_ms: actualSpeedMs,
        speed_kmh: Math.round(actualSpeedMs * 3.6 * 10) / 10,
        current_lane_id: def.laneId,
        route: def.routeType,
        is_priority_vehicle: def.is_priority_vehicle,
        provenance: this.sourceId,
        timestamp: timeMs,
        status,
        waiting_time_s: waitingTime,
      };

      this.cachedSnapshots.set(def.id, snap);
      snapshots.push(snap);
    }

    return snapshots;
  }

  public getVehicleState(vehicleId: string): VehicleSnapshot | null {
    return this.cachedSnapshots.get(vehicleId) || null;
  }

  public getAllVehicleIds(): string[] {
    return this.vehicleDefs.map((v) => v.id);
  }

  public reset(): void {
    this.cachedSnapshots.clear();
  }
}
