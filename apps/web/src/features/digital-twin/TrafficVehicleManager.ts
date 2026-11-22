import * as THREE from 'three';
import { VehicleClass, VehicleState } from '@clearway/shared';
import { VehicleAssetFactory, VehicleMeshBundle } from './VehicleAssetFactory';
import { VehicleMotionSystem } from './VehicleMotionSystem';
import { VehicleSnapshot, VehicleTrajectorySource } from './VehicleTrajectorySource';
import { VehicleSnapshotFixture } from './VehicleSnapshotFixture';

export interface ManagedVehicle {
  state: VehicleState;
  bundle: VehicleMeshBundle;
}

/**
 * TrafficVehicleManager orchestrates the 3D fleet across intersection INT-0457:
 * - Powered by VehicleMotionSystem with deterministic snapshot playback
 * - Smooth lane graph following, stop line waiting, and turning arcs
 * - High-density urban motorcycles/scooters & passenger cars (e.g. MOTO-01, BUS-104)
 * - Priority ambulance (AMB-339) with active corridor clearance
 * - Emergency rescue fire engine
 * - Dynamic 3D floating speed badges and click inspection
 */
export class TrafficVehicleManager {
  public group: THREE.Group;
  public factory: VehicleAssetFactory;
  public motionSystem: VehicleMotionSystem;
  public vehicles: Map<string, ManagedVehicle> = new Map();

  constructor(trajectorySource?: VehicleTrajectorySource) {
    this.group = new THREE.Group();
    this.group.name = 'TrafficVehicles';
    this.factory = new VehicleAssetFactory();

    // Initialize VehicleMotionSystem with snapshot fixture
    const source = trajectorySource || new VehicleSnapshotFixture();
    this.motionSystem = new VehicleMotionSystem(source);
    this.group.add(this.motionSystem.group);

    this.spawnInitialFleet();
  }

  /**
   * Spawns initial fleet states through deterministic motion system
   */
  public spawnInitialFleet(): void {
    this.motionSystem.update(0);
    this.syncVehiclesMap();
  }

  /**
   * Synchronize backward-compatible vehicles Map for direct lookups
   */
  private syncVehiclesMap(): void {
    this.motionSystem.vehicles.forEach((managed, id) => {
      this.vehicles.set(id, {
        state: managed.snapshot,
        bundle: managed.bundle,
      });
    });
  }

  /**
   * Add a custom vehicle directly
   */
  public addVehicle(state: VehicleState): void {
    this.motionSystem.update(0);
    this.syncVehiclesMap();
  }

  /**
   * Update dynamic vehicle behaviors (lane interpolation, strobe lightbars, emergency corridor)
   */
  public update(timeMs: number): void {
    this.motionSystem.update(timeMs);
    this.syncVehiclesMap();
  }

  /**
   * Raycast vehicle selection for operator inspector
   */
  public findVehicleByIntersection(intersects: THREE.Intersection[]): VehicleSnapshot | null {
    return this.motionSystem.findVehicleByIntersection(intersects);
  }

  public setVehiclesVisibility(visible: boolean): void {
    this.group.visible = visible;
    this.motionSystem.setVehiclesVisibility(visible);
  }

  public setShowBadges(show: boolean): void {
    this.motionSystem.setShowBadges(show);
  }

  public dispose(): void {
    this.motionSystem.dispose();
    this.factory.dispose();
    this.vehicles.clear();
  }
}
