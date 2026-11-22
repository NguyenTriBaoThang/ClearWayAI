import * as THREE from 'three';
import { VehicleClass, VehicleState } from '@clearway/shared';
import { VehicleAssetFactory, VehicleMeshBundle } from './VehicleAssetFactory';

export interface ManagedVehicle {
  state: VehicleState;
  bundle: VehicleMeshBundle;
}

/**
 * TrafficVehicleManager orchestrates the 3D fleet across intersection INT-0457:
 * - High-density urban motorcycles/scooters
 * - Passenger sedans, SUVs, transit buses, delivery trucks
 * - Emergency priority ambulance (AMB-339) with active corridor clearance
 * - Emergency rescue fire engine
 * - Real-time vehicle selection raycasting & animated strobe lighting
 */
export class TrafficVehicleManager {
  public group: THREE.Group;
  public factory: VehicleAssetFactory;
  public vehicles: Map<string, ManagedVehicle> = new Map();

  private disposables: { dispose: () => void }[] = [];

  constructor() {
    this.group = new THREE.Group();
    this.group.name = 'TrafficVehicles';
    this.factory = new VehicleAssetFactory();

    this.spawnInitialFleet();
  }

  /**
   * Spawns an initial realistic distribution of vehicles across the 4 approach lanes
   */
  private spawnInitialFleet(): void {
    // 1. Emergency Ambulance AMB-339 (Moving along East-West Priority Corridor)
    this.addVehicle({
      id: 'AMB-339',
      vehicle_class: 'emergency_ambulance',
      x: -18,
      y: 0,
      z: 1.75, // Centered on Eastbound inner lane
      heading: 90, // Facing East (+X)
      speed_kmh: 62,
      current_lane_id: '5TH_EB_L1',
      is_priority_vehicle: true,
      mission_id: 'MISSION-AMB-339',
      provenance: 'DEMO_FIXTURE',
    });

    // 2. City Transit Bus BUS-104 (Westbound Approach)
    this.addVehicle({
      id: 'BUS-104',
      vehicle_class: 'bus',
      x: 28,
      y: 0,
      z: -1.75, // Westbound lane
      heading: 270, // Facing West (-X)
      speed_kmh: 32,
      current_lane_id: '5TH_WB_L1',
      is_priority_vehicle: false,
      provenance: 'DEMO_FIXTURE',
    });

    // 3. Passenger Car CAR-201 (Northbound incoming, queued near stop line)
    this.addVehicle({
      id: 'CAR-201',
      vehicle_class: 'passenger_car',
      x: 1.75,
      y: 0,
      z: -14.5, // Just behind North crosswalk/stop line
      heading: 180, // Facing South (+Z)
      speed_kmh: 0,
      current_lane_id: 'OAK_NB_L1',
      is_priority_vehicle: false,
      provenance: 'DEMO_FIXTURE',
    });

    // 4. Crossover SUV SUV-301 (Northbound lane 2)
    this.addVehicle({
      id: 'SUV-301',
      vehicle_class: 'suv',
      x: 5.25,
      y: 0,
      z: -19.0,
      heading: 180,
      speed_kmh: 0,
      current_lane_id: 'OAK_NB_L2',
      is_priority_vehicle: false,
      provenance: 'DEMO_FIXTURE',
    });

    // 5. Urban Delivery Cargo Truck TRUCK-55 (Southbound incoming)
    this.addVehicle({
      id: 'TRUCK-55',
      vehicle_class: 'truck',
      x: -5.25,
      y: 0,
      z: 22.0,
      heading: 0, // Facing North (-Z)
      speed_kmh: 24,
      current_lane_id: 'OAK_SB_L2',
      is_priority_vehicle: false,
      provenance: 'DEMO_FIXTURE',
    });

    // 6. Passenger Car CAR-202 (Southbound incoming, stopping)
    this.addVehicle({
      id: 'CAR-202',
      vehicle_class: 'passenger_car',
      x: -1.75,
      y: 0,
      z: 15.0,
      heading: 0,
      speed_kmh: 0,
      current_lane_id: 'OAK_SB_L1',
      is_priority_vehicle: false,
      provenance: 'DEMO_FIXTURE',
    });

    // 7. Urban Motorcycle MOTO-01 (High-density Vietnamese scooter waiting in front of cars)
    this.addVehicle({
      id: 'MOTO-01',
      vehicle_class: 'motorcycle',
      x: 2.4,
      y: 0,
      z: -12.5,
      heading: 180,
      speed_kmh: 0,
      current_lane_id: 'OAK_NB_L1',
      is_priority_vehicle: false,
      provenance: 'DEMO_FIXTURE',
    });

    // 8. Urban Motorcycle MOTO-02
    this.addVehicle({
      id: 'MOTO-02',
      vehicle_class: 'motorcycle',
      x: 4.8,
      y: 0,
      z: -12.8,
      heading: 180,
      speed_kmh: 0,
      current_lane_id: 'OAK_NB_L2',
      is_priority_vehicle: false,
      provenance: 'DEMO_FIXTURE',
    });

    // 9. Urban Motorcycle MOTO-03 (Southbound approach)
    this.addVehicle({
      id: 'MOTO-03',
      vehicle_class: 'motorcycle',
      x: -2.4,
      y: 0,
      z: 12.6,
      heading: 0,
      speed_kmh: 0,
      current_lane_id: 'OAK_SB_L1',
      is_priority_vehicle: false,
      provenance: 'DEMO_FIXTURE',
    });

    // 10. Emergency Fire Engine FIRE-09 (Emergency Standby at South curb)
    this.addVehicle({
      id: 'FIRE-09',
      vehicle_class: 'emergency_fire',
      x: -32,
      y: 0,
      z: -5.25,
      heading: 90,
      speed_kmh: 0,
      current_lane_id: '5TH_WB_L2',
      is_priority_vehicle: true,
      provenance: 'DEMO_FIXTURE',
    });
  }

  public addVehicle(state: VehicleState): void {
    let bundle: VehicleMeshBundle;

    switch (state.vehicle_class) {
      case 'motorcycle':
        bundle = this.factory.createMotorcycle(state.id, 0x00e5ff);
        break;
      case 'passenger_car':
        bundle = this.factory.createPassengerCar(state.id, 0x38bdf8);
        break;
      case 'suv':
        bundle = this.factory.createSUV(state.id, 0x06d6a0);
        break;
      case 'bus':
        bundle = this.factory.createBus(state.id, 0x00e5ff);
        break;
      case 'truck':
        bundle = this.factory.createTruck(state.id, 0xffd166);
        break;
      case 'emergency_ambulance':
        bundle = this.factory.createEmergencyAmbulance(state.id);
        break;
      case 'emergency_fire':
        bundle = this.factory.createEmergencyFireEngine(state.id);
        break;
      default:
        bundle = this.factory.createPassengerCar(state.id, 0x94a3b8);
    }

    // Set initial position and heading (heading in degrees: 0 = +Z, 90 = +X, 180 = -Z, 270 = -X)
    bundle.group.position.set(state.x, state.y || 0, state.z || 0);
    bundle.group.rotation.y = (state.heading * Math.PI) / 180;

    // Attach custom user data for raycasting inspection
    bundle.group.userData = {
      vehicleId: state.id,
      vehicleClass: state.vehicle_class,
      speedKmh: state.speed_kmh,
      isPriority: state.is_priority_vehicle,
      missionId: state.mission_id,
    };

    this.group.add(bundle.group);
    this.vehicles.set(state.id, { state, bundle });
  }

  /**
   * Update dynamic vehicle behaviors (emergency lights, corridor motion)
   */
  public update(timeMs: number): void {
    // 1. Update strobe lightbars on all vehicles
    this.vehicles.forEach(({ bundle, state }) => {
      if (bundle.update) {
        bundle.update(timeMs);
      }

      // 2. Animate ambulance AMB-339 traversing along East-West corridor
      if (state.id === 'AMB-339') {
        const progress = ((timeMs * 0.008) % 70) - 35; // from -35m to +35m
        bundle.group.position.x = progress;
        state.x = progress;
      }
    });
  }

  /**
   * Raycast vehicle selection for operator inspector
   */
  public findVehicleByIntersection(intersects: THREE.Intersection[]): VehicleState | null {
    for (const hit of intersects) {
      let obj: THREE.Object3D | null = hit.object;
      while (obj && obj !== this.group) {
        if (obj.userData && obj.userData.vehicleId) {
          const v = this.vehicles.get(obj.userData.vehicleId);
          if (v) return v.state;
        }
        obj = obj.parent;
      }
    }
    return null;
  }

  public setVehiclesVisibility(visible: boolean): void {
    this.group.visible = visible;
  }

  public dispose(): void {
    this.factory.dispose();
    this.disposables.forEach((d) => {
      try {
        d.dispose();
      } catch (e) {
        // Ignore
      }
    });
  }
}
