import * as THREE from 'three';
import { RoadNetworkMesh } from './RoadNetworkMesh';
import { CityEnvironmentMesh } from './CityEnvironmentMesh';
import { TrafficVehicleManager } from './TrafficVehicleManager';
import { TrafficSignal3D } from './TrafficSignal3D';
import { CorridorOverlay3D } from './CorridorOverlay3D';
import { FlowArrows3D } from './FlowArrows3D';
import { MultiIntersectionRoadNetwork } from './MultiIntersectionRoadNetwork';
import { CorridorCityEnvironment } from './CorridorCityEnvironment';
import { MultiSignalController } from './MultiSignalController';

/**
 * SceneEnvironment manages lighting, cyber grid, junction pedestal,
 * 3D road network geometry (asphalt, lanes, crosswalks, sidewalks),
 * 3D urban context (cyber towers, hospital facility, streetlights, trees, RSUs),
 * 3D traffic fleet (motorcycles, cars, SUVs, buses, trucks, AMB-339 ambulance, fire engine),
 * 3D traffic signal poles & heads (Red/Yellow/Green conflict-free), pedestrians,
 * 3D emergency corridor ribbons, directional flow arrows, conflict zone grid,
 * multi-intersection arterial corridor (Nodes A–D, Trauma Center), and visual overlays.
 */
export class SceneEnvironment {
  public scene: THREE.Scene;
  public roadNetwork: RoadNetworkMesh;
  public cityEnvironment: CityEnvironmentMesh;
  public vehicleManager: TrafficVehicleManager;
  public trafficSignals: TrafficSignal3D;
  public corridorOverlay: CorridorOverlay3D;
  public flowArrows: FlowArrows3D;

  // Multi-Intersection Arterial Corridor Components (Task 46)
  public corridorRoadNetwork: MultiIntersectionRoadNetwork;
  public corridorCity: CorridorCityEnvironment;
  public multiSignals: MultiSignalController;
  public isCorridorMode: boolean = true;

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

    // 5. 3D Emergency Priority Corridor Overlay (Multi-Segment Neon Chevrons)
    this.corridorOverlay = new CorridorOverlay3D();
    this.scene.add(this.corridorOverlay.group);

    // 6. 3D Flow Arrows, Conflict Zone Box, Sensor Footprints, and Queue Hotspots
    this.flowArrows = new FlowArrows3D();
    this.scene.add(this.flowArrows.group);

    // 7. Multi-Intersection Arterial Corridor (Nodes A, B, C, D + Trauma Center)
    this.corridorRoadNetwork = new MultiIntersectionRoadNetwork();
    this.scene.add(this.corridorRoadNetwork.group);

    this.corridorCity = new CorridorCityEnvironment();
    this.scene.add(this.corridorCity.group);

    this.multiSignals = new MultiSignalController();
    this.scene.add(this.multiSignals.group);

    this.setupCardinalMarkers();
    this.setupCorridorRibbon();

    // Default to Corridor View (1,000m 4-intersection model)
    this.setCorridorMode(true);
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

    // 5. Corridor-Wide Directional Lights (Arterial 1,000m span illumination)
    const corridorKey = new THREE.DirectionalLight(0x00f5d4, 0.9);
    corridorKey.position.set(375, 110, 75);
    this.scene.add(corridorKey);

    const corridorFill = new THREE.DirectionalLight(0xffd166, 0.45);
    corridorFill.position.set(375, 80, -75);
    this.scene.add(corridorFill);
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

    // Corridor Extended Ground Base Plane (spanning -200m to 1050m)
    const corridorGroundGeo = new THREE.PlaneGeometry(1400, 240);
    const corridorGround = new THREE.Mesh(corridorGroundGeo, groundMat);
    corridorGround.rotation.x = -Math.PI / 2;
    corridorGround.position.set(375, -0.31, 0);
    corridorGround.receiveShadow = true;
    this.scene.add(corridorGround);
    this.disposables.push(corridorGroundGeo);
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
   * Toggle between 1,000m multi-intersection arterial corridor and single-intersection view
   */
  public setCorridorMode(enabled: boolean): void {
    this.isCorridorMode = enabled;

    // Toggle multi-intersection arterial corridor
    if (this.corridorRoadNetwork) {
      this.corridorRoadNetwork.group.visible = enabled;
    }
    if (this.corridorCity) {
      this.corridorCity.group.visible = enabled;
    }
    if (this.multiSignals) {
      this.multiSignals.setSignalsVisibility(enabled);
    }

    // Toggle single-intersection standalone elements
    if (this.roadNetwork) {
      this.roadNetwork.group.visible = !enabled;
    }
    if (this.cityEnvironment) {
      this.cityEnvironment.group.visible = !enabled;
    }
    if (this.trafficSignals) {
      this.trafficSignals.setSignalsVisibility(!enabled);
    }
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

    let ambPos: THREE.Vector3 | undefined;
    if (this.vehicleManager) {
      const amb = this.vehicleManager.vehicles.get('AMB-339');
      if (amb) {
        ambPos = amb.bundle.group.position;
      }
    }

    // 5. Update 3D emergency corridor overlay (neon chevrons & vehicle callouts)
    if (this.corridorOverlay) {
      this.corridorOverlay.update(timeMs, ambPos);
    }

    // 6. Update 3D flow arrows, conflict zone pulsing, and sensor footprints
    if (this.flowArrows) {
      this.flowArrows.update(timeMs);
    }

    // 7. Update Corridor City (Beacon strobe) & Multi-Signal Controller
    if (this.corridorCity) {
      this.corridorCity.update(timeMs);
    }
    if (this.multiSignals) {
      this.multiSignals.update(timeMs);
    }

    if (ambPos) {
      return ambPos;
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
    if (this.corridorOverlay) {
      this.corridorOverlay.dispose();
    }
    if (this.flowArrows) {
      this.flowArrows.dispose();
    }
    if (this.corridorRoadNetwork) {
      this.corridorRoadNetwork.dispose();
    }
    if (this.corridorCity) {
      this.corridorCity.dispose();
    }
    if (this.multiSignals) {
      this.multiSignals.dispose();
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
