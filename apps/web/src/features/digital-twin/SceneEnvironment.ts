import * as THREE from 'three';
import { RoadNetworkMesh } from './RoadNetworkMesh';
import { CityEnvironmentMesh } from './CityEnvironmentMesh';
import { TrafficVehicleManager } from './TrafficVehicleManager';
import { TrafficSignal3D } from './TrafficSignal3D';

/**
 * SceneEnvironment manages lighting, cyber grid, junction pedestal,
 * 3D road network geometry (asphalt, lanes, crosswalks, sidewalks),
 * 3D urban context (cyber towers, hospital facility, streetlights, trees, RSUs),
 * 3D traffic fleet (motorcycles, cars, SUVs, buses, trucks, AMB-339 ambulance, fire engine),
 * 3D traffic signal poles & heads (Red/Yellow/Green conflict-free), pedestrians,
 * cardinal markers, and visual corridor ribbons for ClearWayAI.
 */
export class SceneEnvironment {
  public scene: THREE.Scene;
  public roadNetwork: RoadNetworkMesh;
  public cityEnvironment: CityEnvironmentMesh;
  public vehicleManager: TrafficVehicleManager;
  public trafficSignals: TrafficSignal3D;

  public keyLight!: THREE.DirectionalLight;
  public fillLight!: THREE.DirectionalLight;
  public ambientLight!: THREE.AmbientLight;
  public hemiLight!: THREE.HemisphereLight;

  private disposables: { dispose: () => void }[] = [];
  private corridorMaterial?: THREE.MeshBasicMaterial;

  constructor(scene: THREE.Scene) {
    this.scene = scene;
    this.setupLighting();
    this.setupGroundAndGrid();

    // 1. Procedural Road Network (Asphalt, Lanes, Markings, Crosswalks, Sidewalks)
    this.roadNetwork = new RoadNetworkMesh();
    this.scene.add(this.roadNetwork.group);

    // 2. Procedural City Environment (Towers, Hospital, Streetlights, Trees, RSUs)
    this.cityEnvironment = new CityEnvironmentMesh();
    this.scene.add(this.cityEnvironment.group);

    // 3. 3D Mixed Traffic Fleet (Vietnamese Motorcycles, Cars, Buses, Trucks, AMB-339)
    this.vehicleManager = new TrafficVehicleManager();
    this.scene.add(this.vehicleManager.group);

    // 4. 3D Traffic Signals & Pedestrians (Conflict-Free Multi-Phase Heads)
    this.trafficSignals = new TrafficSignal3D();
    this.scene.add(this.trafficSignals.group);

    this.setupCardinalMarkers();
    this.setupCorridorRibbon();
  }

  private setupLighting(): void {
    // 1. Ambient Light - deep navy cyber glow
    this.ambientLight = new THREE.AmbientLight(0x0d1b38, 0.85);
    this.scene.add(this.ambientLight);

    // 2. Key Light - strong cyan/teal directional light from upper-left
    this.keyLight = new THREE.DirectionalLight(0x00f5d4, 1.4);
    this.keyLight.position.set(38, 62, 28);
    this.keyLight.castShadow = true;
    this.scene.add(this.keyLight);

    // 3. Fill Light - warm amber/gold directional light from opposite side
    this.fillLight = new THREE.DirectionalLight(0xffd166, 0.55);
    this.fillLight.position.set(-36, 32, -26);
    this.scene.add(this.fillLight);

    // 4. Hemisphere Light - cyan sky to deep navy ground
    this.hemiLight = new THREE.HemisphereLight(0x00e5ff, 0x070d1e, 0.45);
    this.scene.add(this.hemiLight);
  }

  private setupGroundAndGrid(): void {
    // Ground Base Plane (dark navy cyber floor)
    const groundGeo = new THREE.PlaneGeometry(160, 160);
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x070d1e,
      roughness: 0.9,
      metalness: 0.1,
    });
    const ground = new THREE.Mesh(groundGeo, groundMat);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -0.3;
    ground.receiveShadow = true;
    this.scene.add(ground);
    this.disposables.push(groundGeo, groundMat);

    // Dual-tier Cyber Grid:
    // 1. Primary Cyan Grid (80x80 units, 40 divisions)
    const primaryGrid = new THREE.GridHelper(80, 40, 0x00e5ff, 0x1b2f5b);
    primaryGrid.position.y = -0.28;
    this.scene.add(primaryGrid);
    this.disposables.push(primaryGrid.geometry, primaryGrid.material as any);

    // 2. Fine Micro Grid (120x120 units, 120 divisions)
    const fineGrid = new THREE.GridHelper(120, 120, 0x162547, 0x0f1c3f);
    fineGrid.position.y = -0.29;
    this.scene.add(fineGrid);
    this.disposables.push(fineGrid.geometry, fineGrid.material as any);
  }

  private setupCardinalMarkers(): void {
    // 3D Cardinal Orientation Markers (N, S, E, W)
    const directions = [
      { label: 'NORTH (Oak St. NB)', pos: new THREE.Vector3(0, 0.1, -22), color: 0x00e5ff },
      { label: 'SOUTH (Oak St. SB)', pos: new THREE.Vector3(0, 0.1, 22), color: 0x00e5ff },
      { label: 'EAST (5th Ave. EB)', pos: new THREE.Vector3(22, 0.1, 0), color: 0x00f5d4 },
      { label: 'WEST (5th Ave. WB)', pos: new THREE.Vector3(-22, 0.1, 0), color: 0x00f5d4 },
    ];

    directions.forEach((dir) => {
      const pinGeo = new THREE.CylinderGeometry(0.5, 0.5, 0.2, 16);
      const pinMat = new THREE.MeshBasicMaterial({ color: dir.color });
      const pinMesh = new THREE.Mesh(pinGeo, pinMat);
      pinMesh.position.copy(dir.pos);
      this.scene.add(pinMesh);
      this.disposables.push(pinGeo, pinMat);
    });
  }

  private setupCorridorRibbon(): void {
    // Emergency Priority Corridor Visual Ribbon (East-West path through junction)
    const corridorGeo = new THREE.PlaneGeometry(80, 3.8);
    this.corridorMaterial = new THREE.MeshBasicMaterial({
      color: 0x00e5ff,
      transparent: true,
      opacity: 0.18,
      side: THREE.DoubleSide,
      wireframe: false,
    });
    const corridorMesh = new THREE.Mesh(corridorGeo, this.corridorMaterial);
    corridorMesh.rotation.x = -Math.PI / 2;
    corridorMesh.position.set(0, 0.032, 1.75); // Centered over East-West incoming lane
    this.scene.add(corridorMesh);
    this.disposables.push(corridorGeo, this.corridorMaterial);

    // Glowing border line guides for the corridor
    const lineGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(-40, 0.035, -0.15),
      new THREE.Vector3(40, 0.035, -0.15),
      new THREE.Vector3(-40, 0.035, 3.65),
      new THREE.Vector3(40, 0.035, 3.65),
    ]);
    const lineMat = new THREE.LineBasicMaterial({ color: 0x00f5d4 });
    const corridorLines = new THREE.LineSegments(lineGeo, lineMat);
    this.scene.add(corridorLines);
    this.disposables.push(lineGeo, lineMat);
  }

  /**
   * Update dynamic scene effects on animation frame
   */
  public update(timeMs: number): THREE.Vector3 {
    // 1. Subtle pulsing on emergency corridor ribbon
    if (this.corridorMaterial) {
      this.corridorMaterial.opacity = 0.16 + 0.1 * Math.sin(timeMs * 0.003);
    }

    // 2. Update dynamic urban effects (Hospital medical strobe, RSU LEDs)
    if (this.cityEnvironment) {
      this.cityEnvironment.update(timeMs);
    }

    // 3. Update 3D traffic vehicles (strobes & corridor traversal)
    if (this.vehicleManager) {
      this.vehicleManager.update(timeMs);
    }

    // 4. Update 3D traffic signals and pedestrians
    if (this.trafficSignals) {
      this.trafficSignals.update(timeMs);
    }

    if (this.vehicleManager) {
      const amb = this.vehicleManager.vehicles.get('AMB-339');
      if (amb) {
        return amb.bundle.group.position;
      }
    }

    return new THREE.Vector3(0, 0, 0);
  }

  public dispose(): void {
    if (this.roadNetwork) {
      this.roadNetwork.dispose();
    }
    if (this.cityEnvironment) {
      this.cityEnvironment.dispose();
    }
    if (this.vehicleManager) {
      this.vehicleManager.dispose();
    }
    if (this.trafficSignals) {
      this.trafficSignals.dispose();
    }
    this.disposables.forEach((item) => {
      try {
        item.dispose();
      } catch (e) {
        // Ignore dispose error
      }
    });
  }
}
