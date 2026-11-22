import * as THREE from 'three';

/**
 * FlowArrows3D creates:
 * 1. Directional Traffic Flow Arrows on lane approaches
 * 2. Intersection Conflict Zone (Yellow Box Junction cross-hatched grid)
 * 3. Dynamic Queue Hotspots indicating approach congestion
 * 4. 3D Sensor Footprints (RSU V2X range circles & LiDAR/Camera detector frustums)
 */
export class FlowArrows3D {
  public group: THREE.Group;
  public flowArrowsGroup: THREE.Group;
  public conflictZoneGroup: THREE.Group;
  public queueHotspotsGroup: THREE.Group;
  public sensorFootprintsGroup: THREE.Group;

  private disposables: { dispose: () => void }[] = [];

  constructor() {
    this.group = new THREE.Group();
    this.group.name = 'FlowArrows3D';

    this.flowArrowsGroup = new THREE.Group();
    this.flowArrowsGroup.name = 'FlowArrows';
    this.group.add(this.flowArrowsGroup);

    this.conflictZoneGroup = new THREE.Group();
    this.conflictZoneGroup.name = 'ConflictZone';
    this.group.add(this.conflictZoneGroup);

    this.queueHotspotsGroup = new THREE.Group();
    this.queueHotspotsGroup.name = 'QueueHotspots';
    this.group.add(this.queueHotspotsGroup);

    this.sensorFootprintsGroup = new THREE.Group();
    this.sensorFootprintsGroup.name = 'SensorFootprints';
    this.group.add(this.sensorFootprintsGroup);

    this.buildFlowArrows();
    this.buildConflictZoneBox();
    this.buildQueueHotspots();
    this.buildSensorFootprints();
  }

  /**
   * 1. Build 3D Directional Flow Arrows along approach lanes
   */
  private buildFlowArrows(): void {
    const arrowMat = new THREE.MeshBasicMaterial({
      color: 0x06d6a0,
      transparent: true,
      opacity: 0.85,
      side: THREE.DoubleSide,
    });
    this.disposables.push(arrowMat);

    // Thick arrowhead geometry
    const shape = new THREE.Shape();
    shape.moveTo(-0.45, -0.6);
    shape.lineTo(0, 0.6);
    shape.lineTo(0.45, -0.6);
    shape.lineTo(0.18, -0.4);
    shape.lineTo(0, -0.1);
    shape.lineTo(-0.18, -0.4);
    shape.closePath();

    const arrowGeo = new THREE.ShapeGeometry(shape);
    this.disposables.push(arrowGeo);

    // Positions across 4 approach directions
    const arrowConfigs: { x: number; z: number; rotY: number; scale?: number }[] = [
      // Eastbound straight arrows
      { x: -26, z: 1.75, rotY: -Math.PI / 2 },
      { x: -16, z: 1.75, rotY: -Math.PI / 2 },
      { x: -26, z: 5.25, rotY: -Math.PI / 2 },
      { x: -16, z: 5.25, rotY: -Math.PI / 2 },

      // Westbound straight arrows
      { x: 26, z: -1.75, rotY: Math.PI / 2 },
      { x: 16, z: -1.75, rotY: Math.PI / 2 },
      { x: 26, z: -5.25, rotY: Math.PI / 2 },
      { x: 16, z: -5.25, rotY: Math.PI / 2 },

      // Northbound straight arrows
      { x: -1.75, z: 26, rotY: 0 },
      { x: -1.75, z: 16, rotY: 0 },
      { x: -5.25, z: 26, rotY: 0 },
      { x: -5.25, z: 16, rotY: 0 },

      // Southbound straight arrows
      { x: 1.75, z: -26, rotY: Math.PI },
      { x: 1.75, z: -16, rotY: Math.PI },
      { x: 5.25, z: -26, rotY: Math.PI },
      { x: 5.25, z: -16, rotY: Math.PI },
    ];

    arrowConfigs.forEach((cfg) => {
      const mesh = new THREE.Mesh(arrowGeo, arrowMat);
      mesh.rotation.x = -Math.PI / 2;
      mesh.rotation.z = cfg.rotY;
      mesh.position.set(cfg.x, 0.041, cfg.z);
      mesh.scale.set(1.4, 1.4, 1.4);
      this.flowArrowsGroup.add(mesh);
    });
  }

  /**
   * 2. Build Conflict Zone (Yellow Box Junction cross-hatched grid)
   */
  private buildConflictZoneBox(): void {
    // 14m x 14m intersection center conflict area
    const boxSize = 14;
    const half = boxSize / 2;
    const y = 0.039;

    const points: THREE.Vector3[] = [];

    // Perimeter border
    points.push(new THREE.Vector3(-half, y, -half), new THREE.Vector3(half, y, -half));
    points.push(new THREE.Vector3(half, y, -half), new THREE.Vector3(half, y, half));
    points.push(new THREE.Vector3(half, y, half), new THREE.Vector3(-half, y, half));
    points.push(new THREE.Vector3(-half, y, half), new THREE.Vector3(-half, y, -half));

    // Diagonal criss-cross lines (Yellow Box grid spacing = 1.75m)
    const step = 1.75;
    for (let offset = -boxSize; offset <= boxSize; offset += step) {
      // Diagonal 1 (slope = +1)
      const p1x = Math.max(-half, Math.min(half, -half + offset));
      const p1z = Math.max(-half, Math.min(half, -half - offset + boxSize));
      const p2x = Math.max(-half, Math.min(half, half + offset));
      const p2z = Math.max(-half, Math.min(half, half - offset + boxSize));

      if (Math.abs(p1x - p2x) > 0.1 && Math.abs(p1z - p2z) > 0.1) {
        points.push(new THREE.Vector3(p1x, y, p1z), new THREE.Vector3(p2x, y, p2z));
      }

      // Diagonal 2 (slope = -1)
      const p3x = Math.max(-half, Math.min(half, -half + offset));
      const p3z = Math.max(-half, Math.min(half, half + offset));
      const p4x = Math.max(-half, Math.min(half, half + offset));
      const p4z = Math.max(-half, Math.min(half, -half + offset));

      if (Math.abs(p3x - p4x) > 0.1 && Math.abs(p3z - p4z) > 0.1) {
        points.push(new THREE.Vector3(p3x, y, p3z), new THREE.Vector3(p4x, y, p4z));
      }
    }

    const boxGeo = new THREE.BufferGeometry().setFromPoints(points);
    const boxMat = new THREE.LineBasicMaterial({
      color: 0xffd166,
      transparent: true,
      opacity: 0.75,
    });

    const boxLines = new THREE.LineSegments(boxGeo, boxMat);
    boxLines.userData = { isConflictZone: true };
    this.conflictZoneGroup.add(boxLines);
    this.disposables.push(boxGeo, boxMat);
  }

  /**
   * 3. Build Dynamic Queue Hotspots along queued approaches
   */
  private buildQueueHotspots(): void {
    const queueGeo = new THREE.PlaneGeometry(16, 6.8);
    const queueMat = new THREE.MeshBasicMaterial({
      color: 0xef4444,
      transparent: true,
      opacity: 0.22,
      side: THREE.DoubleSide,
    });
    this.disposables.push(queueGeo, queueMat);

    // Northbound approach queue hotspot
    const nbQueue = new THREE.Mesh(queueGeo, queueMat);
    nbQueue.rotation.x = -Math.PI / 2;
    nbQueue.rotation.z = Math.PI / 2;
    nbQueue.position.set(-3.5, 0.038, 22);
    this.queueHotspotsGroup.add(nbQueue);

    // Southbound approach queue hotspot
    const sbQueue = new THREE.Mesh(queueGeo, queueMat);
    sbQueue.rotation.x = -Math.PI / 2;
    sbQueue.rotation.z = Math.PI / 2;
    sbQueue.position.set(3.5, 0.038, -22);
    this.queueHotspotsGroup.add(sbQueue);
  }

  /**
   * 4. Build 3D Sensor Footprints (RSU range circles & LiDAR cones)
   */
  private buildSensorFootprints(): void {
    // 4 Corner RSU V2X communication projection rings (radius = 16m)
    const rsuPositions = [
      { x: -11.5, z: -11.5 },
      { x: 11.5, z: 11.5 },
      { x: 11.5, z: -11.5 },
      { x: -11.5, z: 11.5 },
    ];

    const ringGeo = new THREE.RingGeometry(15.8, 16.0, 32);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0x00e5ff,
      transparent: true,
      opacity: 0.35,
      side: THREE.DoubleSide,
    });
    this.disposables.push(ringGeo, ringMat);

    rsuPositions.forEach((pos) => {
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.rotation.x = -Math.PI / 2;
      ring.position.set(pos.x, 0.037, pos.z);
      this.sensorFootprintsGroup.add(ring);
    });

    // Optical Camera / LiDAR Detector Frustum Cones
    const coneGeo = new THREE.ConeGeometry(4.2, 5.5, 4, 1, true);
    const coneMat = new THREE.MeshBasicMaterial({
      color: 0x00e5ff,
      transparent: true,
      opacity: 0.12,
      wireframe: true,
    });
    this.disposables.push(coneGeo, coneMat);

    rsuPositions.forEach((pos) => {
      const cone = new THREE.Mesh(coneGeo, coneMat);
      cone.position.set(pos.x, 2.8, pos.z);
      cone.rotation.x = Math.PI;
      this.sensorFootprintsGroup.add(cone);
    });
  }

  /**
   * Dynamic update on animation ticks (pulsing effects)
   */
  public update(timeMs: number): void {
    // Subtle breathing glow on sensor footprints
    const sensorAlpha = 0.25 + 0.1 * Math.sin(timeMs * 0.003);
    this.sensorFootprintsGroup.children.forEach((child) => {
      if ((child as THREE.Mesh).material) {
        ((child as THREE.Mesh).material as THREE.Material).opacity = sensorAlpha;
      }
    });

    // Subtle pulsing on conflict zone
    const boxAlpha = 0.70 + 0.15 * Math.sin(timeMs * 0.004);
    this.conflictZoneGroup.children.forEach((child) => {
      if ((child as THREE.LineSegments).material) {
        ((child as THREE.LineSegments).material as THREE.Material).opacity = boxAlpha;
      }
    });
  }

  public setFlowArrowsVisibility(visible: boolean): void {
    this.flowArrowsGroup.visible = visible;
  }

  public setConflictZoneVisibility(visible: boolean): void {
    this.conflictZoneGroup.visible = visible;
  }

  public setQueueHotspotsVisibility(visible: boolean): void {
    this.queueHotspotsGroup.visible = visible;
  }

  public setSensorFootprintsVisibility(visible: boolean): void {
    this.sensorFootprintsGroup.visible = visible;
  }

  public dispose(): void {
    this.disposables.forEach((item) => {
      try {
        item.dispose();
      } catch (e) {
        // Ignore
      }
    });
  }
}

