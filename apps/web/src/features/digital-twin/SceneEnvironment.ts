import * as THREE from 'three';

/**
 * SceneEnvironment manages lighting, cyber grid, junction pedestal,
 * cardinal markers, and visual corridor ribbons for the ClearWayAI 3D Digital Twin.
 */
export class SceneEnvironment {
  public scene: THREE.Scene;
  public keyLight!: THREE.DirectionalLight;
  public fillLight!: THREE.DirectionalLight;
  public ambientLight!: THREE.AmbientLight;
  public hemiLight!: THREE.HemisphereLight;

  private disposables: { dispose: () => void }[] = [];
  private corridorMaterial?: THREE.MeshBasicMaterial;
  private waypointsMesh?: THREE.Mesh;

  constructor(scene: THREE.Scene) {
    this.scene = scene;
    this.setupLighting();
    this.setupGroundAndGrid();
    this.setupJunctionPlatform();
    this.setupCardinalMarkers();
    this.setupCorridorRibbon();
    this.setupWaypointMarker();
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

  private setupJunctionPlatform(): void {
    // Main elevated intersection pedestal
    const platformGeo = new THREE.BoxGeometry(26, 0.4, 26);
    const platformMat = new THREE.MeshStandardMaterial({
      color: 0x0b1836,
      roughness: 0.7,
      metalness: 0.3,
    });
    const platform = new THREE.Mesh(platformGeo, platformMat);
    platform.position.y = -0.1;
    this.scene.add(platform);
    this.disposables.push(platformGeo, platformMat);

    // Glowing cyan edges for the pedestal
    const edgesGeo = new THREE.EdgesGeometry(platformGeo);
    const edgesMat = new THREE.LineBasicMaterial({ color: 0x00e5ff, linewidth: 2 });
    const edgeLines = new THREE.LineSegments(edgesGeo, edgesMat);
    edgeLines.position.copy(platform.position);
    this.scene.add(edgeLines);
    this.disposables.push(edgesGeo, edgesMat);

    // Conflict zone central platform (the inner intersection box)
    const innerBoxGeo = new THREE.BoxGeometry(16, 0.42, 16);
    const innerBoxMat = new THREE.MeshStandardMaterial({
      color: 0x0e2046,
      roughness: 0.6,
      metalness: 0.4,
    });
    const innerBox = new THREE.Mesh(innerBoxGeo, innerBoxMat);
    innerBox.position.y = -0.09;
    this.scene.add(innerBox);
    this.disposables.push(innerBoxGeo, innerBoxMat);

    const innerEdgesGeo = new THREE.EdgesGeometry(innerBoxGeo);
    const innerEdgesMat = new THREE.LineBasicMaterial({ color: 0x00f5d4, linewidth: 1 });
    const innerEdgeLines = new THREE.LineSegments(innerEdgesGeo, innerEdgesMat);
    innerEdgeLines.position.copy(innerBox.position);
    this.scene.add(innerEdgeLines);
    this.disposables.push(innerEdgesGeo, innerEdgesMat);

    // Center Coordinate Axis Helper
    const axesHelper = new THREE.AxesHelper(7);
    axesHelper.position.set(0, 0.15, 0);
    this.scene.add(axesHelper);
    this.disposables.push(axesHelper.geometry, axesHelper.material as any);
  }

  private setupCardinalMarkers(): void {
    // 3D Cardinal Orientation Markers (N, S, E, W)
    const directions = [
      { label: 'NORTH (Oak St. NB)', pos: new THREE.Vector3(0, 0.1, -16), color: 0x00e5ff },
      { label: 'SOUTH (Oak St. SB)', pos: new THREE.Vector3(0, 0.1, 16), color: 0x00e5ff },
      { label: 'EAST (5th Ave. EB)', pos: new THREE.Vector3(16, 0.1, 0), color: 0x00f5d4 },
      { label: 'WEST (5th Ave. WB)', pos: new THREE.Vector3(-16, 0.1, 0), color: 0x00f5d4 },
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
    const corridorGeo = new THREE.PlaneGeometry(50, 4.5);
    this.corridorMaterial = new THREE.MeshBasicMaterial({
      color: 0x00e5ff,
      transparent: true,
      opacity: 0.22,
      side: THREE.DoubleSide,
      wireframe: false,
    });
    const corridorMesh = new THREE.Mesh(corridorGeo, this.corridorMaterial);
    corridorMesh.rotation.x = -Math.PI / 2;
    corridorMesh.position.set(0, 0.02, 0);
    this.scene.add(corridorMesh);
    this.disposables.push(corridorGeo, this.corridorMaterial);

    // Border line guides for the corridor
    const lineGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(-25, 0.05, -2.25),
      new THREE.Vector3(25, 0.05, -2.25),
      new THREE.Vector3(-25, 0.05, 2.25),
      new THREE.Vector3(25, 0.05, 2.25),
    ]);
    const lineMat = new THREE.LineBasicMaterial({ color: 0x00f5d4 });
    const corridorLines = new THREE.LineSegments(lineGeo, lineMat);
    this.scene.add(corridorLines);
    this.disposables.push(lineGeo, lineMat);
  }

  private setupWaypointMarker(): void {
    // Dynamic vehicle waypoint marker (represents emergency ambulance AMB-339)
    const markerGeo = new THREE.BoxGeometry(4.2, 1.6, 2.0);
    const markerMat = new THREE.MeshStandardMaterial({
      color: 0xef476f,
      emissive: 0xef476f,
      emissiveIntensity: 0.6,
      roughness: 0.3,
      metalness: 0.8,
    });
    this.waypointsMesh = new THREE.Mesh(markerGeo, markerMat);
    this.waypointsMesh.position.set(-18, 0.8, 0);
    this.scene.add(this.waypointsMesh);
    this.disposables.push(markerGeo, markerMat);
  }

  /**
   * Update dynamic scene effects on animation frame
   */
  public update(timeMs: number): THREE.Vector3 {
    // 1. Subtle pulsing on emergency corridor ribbon
    if (this.corridorMaterial) {
      this.corridorMaterial.opacity = 0.18 + 0.1 * Math.sin(timeMs * 0.003);
    }

    // 2. Animate ambulance waypoint traversing East-West along corridor (-22m to +22m)
    if (this.waypointsMesh) {
      const progress = ((timeMs * 0.006) % 44) - 22;
      this.waypointsMesh.position.x = progress;
      return this.waypointsMesh.position;
    }

    return new THREE.Vector3(0, 0, 0);
  }

  public dispose(): void {
    this.disposables.forEach((item) => {
      try {
        item.dispose();
      } catch (e) {
        // Ignore dispose error
      }
    });
  }
}

