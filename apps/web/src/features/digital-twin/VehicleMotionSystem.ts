import * as THREE from 'three';
import { VehicleAssetFactory, VehicleMeshBundle } from './VehicleAssetFactory';
import { VehicleSnapshot, VehicleTrajectorySource, VehicleMotionStatus } from './VehicleTrajectorySource';
import { VehicleSnapshotFixture } from './VehicleSnapshotFixture';

export interface ManagedMotionVehicle {
  snapshot: VehicleSnapshot;
  prevSnapshot?: VehicleSnapshot;
  bundle: VehicleMeshBundle;
  badgeSprite?: THREE.Sprite;
  badgeCanvas?: HTMLCanvasElement;
  badgeTexture?: THREE.CanvasTexture;
  lastUpdatedMs: number;
  interpolatedX: number;
  interpolatedY: number;
  interpolatedZ: number;
  interpolatedHeading: number;
}

/**
 * Shortest angular path interpolation in degrees [0, 360).
 */
export function lerpAngleDeg(fromDeg: number, toDeg: number, t: number): number {
  const diff = ((toDeg - fromDeg + 540) % 360) - 180;
  return ((fromDeg + diff * t) % 360 + 360) % 360;
}

/**
 * VehicleMotionSystem governs:
 * 1. Persistent vehicle instance mapping (vehicle_id -> 3D Mesh)
 * 2. Deterministic snapshot ingestion & smooth tick interpolation
 * 3. Bounded extrapolation with STALE status when frames are dropped (>1.5s)
 * 4. Dynamic 3D floating speed badges and ID overlays
 * 5. Raycasting vehicle inspection with live telemetry metrics
 */
export class VehicleMotionSystem {
  public group: THREE.Group;
  public factory: VehicleAssetFactory;
  public trajectorySource: VehicleTrajectorySource;
  public vehicles: Map<string, ManagedMotionVehicle> = new Map();

  public showBadges: boolean = true;
  private readonly STALE_THRESHOLD_MS = 1500;
  private readonly MAX_TELEPORT_DELTA_M = 15.0;

  private disposables: { dispose: () => void }[] = [];

  constructor(trajectorySource?: VehicleTrajectorySource) {
    this.group = new THREE.Group();
    this.group.name = 'VehicleMotionSystem';
    this.factory = new VehicleAssetFactory();
    this.trajectorySource = trajectorySource || new VehicleSnapshotFixture();
  }

  /**
   * Set or switch trajectory source (e.g. from fixture playback to live SUMO stream)
   */
  public setTrajectorySource(source: VehicleTrajectorySource): void {
    this.trajectorySource = source;
  }

  /**
   * Ingest snapshots at current simulation timestamp and interpolate smoothly
   */
  public update(timeMs: number): void {
    const snapshots = this.trajectorySource.getSnapshotsAtTime(timeMs);

    // Track active vehicles in this snapshot tick
    const activeIds = new Set<string>();

    for (const snap of snapshots) {
      activeIds.add(snap.id);
      let managed = this.vehicles.get(snap.id);

      if (!managed) {
        // Instantiate new 3D vehicle bundle from factory
        managed = this.createVehicleInstance(snap);
        this.vehicles.set(snap.id, managed);
        this.group.add(managed.bundle.group);
      }

      // Check for frame staleness or time jump
      const dt = (timeMs - managed.lastUpdatedMs) / 1000;
      managed.prevSnapshot = { ...managed.snapshot };
      managed.snapshot = snap;
      managed.lastUpdatedMs = timeMs;

      // Handle bounded extrapolation / interpolation
      if (dt > 0 && dt < 1.0) {
        // Check for teleport anomaly
        const dx = snap.x - managed.interpolatedX;
        const dz = snap.z - managed.interpolatedZ;
        const dist = Math.sqrt(dx * dx + dz * dz);

        if (dist > this.MAX_TELEPORT_DELTA_M && managed.prevSnapshot) {
          // Clamp to maximum reasonable speed displacement to prevent clipping
          const clampAlpha = this.MAX_TELEPORT_DELTA_M / dist;
          managed.interpolatedX += dx * clampAlpha;
          managed.interpolatedZ += dz * clampAlpha;
        } else {
          // Smooth easing lerp
          managed.interpolatedX += (snap.x - managed.interpolatedX) * 0.45;
          managed.interpolatedZ += (snap.z - managed.interpolatedZ) * 0.45;
        }

        managed.interpolatedHeading = lerpAngleDeg(managed.interpolatedHeading, snap.heading, 0.4);
      } else {
        // Immediate sync on reset or first tick
        managed.interpolatedX = snap.x;
        managed.interpolatedY = snap.y || 0;
        managed.interpolatedZ = snap.z;
        managed.interpolatedHeading = snap.heading;
      }

      // Apply coordinates to Three.js Object3D
      managed.bundle.group.position.set(managed.interpolatedX, managed.interpolatedY, managed.interpolatedZ);
      managed.bundle.group.rotation.y = (managed.interpolatedHeading * Math.PI) / 180;

      // Update dynamic strobes/lights
      if (managed.bundle.update) {
        managed.bundle.update(timeMs);
      }

      // Update 3D Speed Badge Billboard
      this.updateSpeedBadge(managed);
    }

    // Check for dropped / stale vehicles that were not in this snapshot
    this.vehicles.forEach((managed, id) => {
      if (!activeIds.has(id)) {
        const timeSinceUpdate = timeMs - managed.lastUpdatedMs;
        if (timeSinceUpdate > this.STALE_THRESHOLD_MS) {
          managed.snapshot.status = 'STALE';
          this.updateSpeedBadge(managed);
        }
      }
    });
  }

  /**
   * Instantiate persistent 3D bundle and speed badge for a vehicle
   */
  private createVehicleInstance(snap: VehicleSnapshot): ManagedMotionVehicle {
    let bundle: VehicleMeshBundle;

    switch (snap.vehicle_class) {
      case 'motorcycle':
        bundle = this.factory.createMotorcycle(snap.id, 0x00e5ff);
        break;
      case 'passenger_car':
        bundle = this.factory.createPassengerCar(snap.id, 0x38bdf8);
        break;
      case 'suv':
        bundle = this.factory.createSUV(snap.id, 0x06d6a0);
        break;
      case 'bus':
        bundle = this.factory.createBus(snap.id, 0x00e5ff);
        break;
      case 'truck':
        bundle = this.factory.createTruck(snap.id, 0xffd166);
        break;
      case 'emergency_ambulance':
        bundle = this.factory.createEmergencyAmbulance(snap.id);
        break;
      case 'emergency_fire':
        bundle = this.factory.createEmergencyFireEngine(snap.id);
        break;
      default:
        bundle = this.factory.createPassengerCar(snap.id, 0x94a3b8);
    }

    // Attach custom user data for raycasting inspection
    bundle.group.userData = {
      vehicleId: snap.id,
      vehicleClass: snap.vehicle_class,
      isPriority: snap.is_priority_vehicle,
      missionId: snap.mission_id,
    };

    // Create 3D Floating Speed Badge (Canvas billboard sprite)
    const { sprite, canvas, texture } = this.createSpeedBadgeSprite(snap);
    bundle.group.add(sprite);

    return {
      snapshot: snap,
      bundle,
      badgeSprite: sprite,
      badgeCanvas: canvas,
      badgeTexture: texture,
      lastUpdatedMs: snap.timestamp,
      interpolatedX: snap.x,
      interpolatedY: snap.y || 0,
      interpolatedZ: snap.z,
      interpolatedHeading: snap.heading,
    };
  }

  /**
   * Generates a high-res 2D Canvas billboard sprite floating above vehicle
   */
  private createSpeedBadgeSprite(snap: VehicleSnapshot): {
    sprite: THREE.Sprite;
    canvas: HTMLCanvasElement;
    texture: THREE.CanvasTexture;
  } {
    const canvas = document.createElement('canvas');
    canvas.width = 160;
    canvas.height = 48;

    const texture = new THREE.CanvasTexture(canvas);
    texture.minFilter = THREE.LinearFilter;
    const spriteMat = new THREE.SpriteMaterial({
      map: texture,
      transparent: true,
      depthTest: false,
    });

    const sprite = new THREE.Sprite(spriteMat);
    // Vertical offset based on vehicle height
    const heightOffset = snap.vehicle_class === 'bus' || snap.vehicle_class === 'truck' ? 4.2 : 2.5;
    sprite.position.set(0, heightOffset, 0);
    sprite.scale.set(2.4, 0.72, 1);
    sprite.visible = this.showBadges;

    this.disposables.push(spriteMat, texture);

    return { sprite, canvas, texture };
  }

  /**
   * Draw dynamic badge text on canvas (ID | Speed km/h)
   */
  private updateSpeedBadge(managed: ManagedMotionVehicle): void {
    if (!managed.badgeSprite || !managed.badgeCanvas || !managed.badgeTexture) return;

    managed.badgeSprite.visible = this.showBadges;
    if (!this.showBadges) return;

    const ctx = managed.badgeCanvas.getContext('2d');
    if (!ctx) return;

    const snap = managed.snapshot;
    const isPriority = snap.is_priority_vehicle;
    const isStale = snap.status === 'STALE';

    ctx.clearRect(0, 0, 160, 48);

    // Background capsule
    ctx.fillStyle = isStale
      ? 'rgba(239, 68, 68, 0.90)'
      : isPriority
      ? 'rgba(10, 25, 47, 0.92)'
      : 'rgba(15, 23, 42, 0.85)';

    ctx.beginPath();
    ctx.roundRect(4, 4, 152, 40, 8);
    ctx.fill();

    // Border
    ctx.lineWidth = 2;
    ctx.strokeStyle = isStale
      ? '#f87171'
      : isPriority
      ? '#00e5ff'
      : '#38bdf8';
    ctx.stroke();

    // Vehicle ID text
    ctx.font = 'bold 15px monospace';
    ctx.fillStyle = isStale ? '#ffffff' : isPriority ? '#00e5ff' : '#f8fafc';
    ctx.textAlign = 'left';
    ctx.fillText(snap.id, 12, 28);

    // Speed text in km/h
    ctx.font = 'bold 13px monospace';
    ctx.fillStyle = isStale ? '#fecaca' : isPriority ? '#ff0055' : '#06d6a0';
    ctx.textAlign = 'right';
    const speedText = isStale ? 'STALE' : `${Math.round(snap.speed_kmh)}k`;
    ctx.fillText(speedText, 148, 28);

    managed.badgeTexture.needsUpdate = true;
  }

  /**
   * Raycast vehicle selection for operator inspector
   */
  public findVehicleByIntersection(intersects: THREE.Intersection[]): VehicleSnapshot | null {
    for (const hit of intersects) {
      let obj: THREE.Object3D | null = hit.object;
      while (obj && obj !== this.group) {
        if (obj.userData && obj.userData.vehicleId) {
          const v = this.vehicles.get(obj.userData.vehicleId);
          if (v) return v.snapshot;
        }
        obj = obj.parent;
      }
    }
    return null;
  }

  public getVehicleSnapshot(vehicleId: string): VehicleSnapshot | null {
    const v = this.vehicles.get(vehicleId);
    return v ? v.snapshot : null;
  }

  public setShowBadges(show: boolean): void {
    this.showBadges = show;
    this.vehicles.forEach((v) => {
      if (v.badgeSprite) {
        v.badgeSprite.visible = show;
      }
    });
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
    this.vehicles.clear();
  }
}
