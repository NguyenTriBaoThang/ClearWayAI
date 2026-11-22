import * as THREE from 'three';

/**
 * CityEnvironmentMesh generates the detailed 3D urban context surrounding the intersection:
 * - 4 corner city quadrant blocks with high-tech cyber buildings & towers
 * - Metropolitan General Hospital in the NE quadrant (directly tied to the emergency ambulance corridor)
 * - Smart City Traffic Operations Center with communications spire in SW quadrant
 * - Emissive window matrices, rooftop HVAC units, and glowing roofline trims
 * - Urban street furniture: Streetlights along sidewalks, stylized low-poly trees, and V2X RSU poles
 */
export class CityEnvironmentMesh {
  public group: THREE.Group;

  // Subgroups for selective HUD layer toggles
  public buildingsGroup: THREE.Group;
  public hospitalGroup: THREE.Group;
  public streetFurnitureGroup: THREE.Group;
  public treesGroup: THREE.Group;
  public rsuPolesGroup: THREE.Group;

  private disposables: { dispose: () => void }[] = [];
  private beaconMaterial?: THREE.MeshBasicMaterial;
  private rsuLedMaterial?: THREE.MeshBasicMaterial;

  constructor() {
    this.group = new THREE.Group();
    this.group.name = 'CityEnvironment';

    this.buildingsGroup = new THREE.Group();
    this.buildingsGroup.name = 'Buildings';
    this.hospitalGroup = new THREE.Group();
    this.hospitalGroup.name = 'HospitalFacility';
    this.streetFurnitureGroup = new THREE.Group();
    this.streetFurnitureGroup.name = 'StreetFurniture';
    this.treesGroup = new THREE.Group();
    this.treesGroup.name = 'UrbanTrees';
    this.rsuPolesGroup = new THREE.Group();
    this.rsuPolesGroup.name = 'RSUNodes';

    this.group.add(this.buildingsGroup);
    this.group.add(this.hospitalGroup);
    this.group.add(this.streetFurnitureGroup);
    this.group.add(this.treesGroup);
    this.group.add(this.rsuPolesGroup);

    this.buildBuildingsNW();
    this.buildHospitalFacilityNE();
    this.buildSmartCityHubSW();
    this.buildResidentialTowersSE();
    this.buildStreetlights();
    this.buildUrbanTrees();
    this.buildV2XRSUPoles();
  }

  /**
   * 1. North-West Quadrant: Commercial Towers & Corporate Glass Blocks
   */
  private buildBuildingsNW(): void {
    // Tower NW1: High-rise Glass Tower
    this.createOfficeTower({
      x: -22,
      z: -22,
      width: 14,
      depth: 14,
      height: 38,
      bodyColor: 0x0c1b3a,
      trimColor: 0x00e5ff,
      windowColor: 0x00f5d4,
      name: 'Tower_NW1',
    });

    // Tower NW2: Mid-rise Commercial Building
    this.createOfficeTower({
      x: -34,
      z: -18,
      width: 11,
      depth: 13,
      height: 26,
      bodyColor: 0x0e2046,
      trimColor: 0x00e5ff,
      windowColor: 0x38bdf8,
      name: 'Tower_NW2',
    });

    // Substation NW3: Low-rise edge computing & power facility
    this.createSimpleBuilding({
      x: -18,
      z: -34,
      width: 12,
      depth: 10,
      height: 14,
      bodyColor: 0x102450,
      trimColor: 0x06d6a0,
      name: 'Facility_NW3',
    });
  }

  /**
   * 2. North-East Quadrant: Metropolitan General Hospital (AMB-339 Destination)
   */
  private buildHospitalFacilityNE(): void {
    // Main Hospital Tower with Rooftop Helipad & Emergency Medical Beacon
    const hospitalX = 24;
    const hospitalZ = -24;
    const hospitalW = 16;
    const hospitalD = 16;
    const hospitalH = 32;

    const hospitalMat = new THREE.MeshStandardMaterial({
      color: 0x122550,
      roughness: 0.6,
      metalness: 0.3,
    });
    this.disposables.push(hospitalMat);

    // Main Hospital Structure
    const mainGeo = new THREE.BoxGeometry(hospitalW, hospitalH, hospitalD);
    const mainMesh = new THREE.Mesh(mainGeo, hospitalMat);
    mainMesh.position.set(hospitalX, hospitalH / 2 + 0.2, hospitalZ);
    mainMesh.castShadow = true;
    mainMesh.receiveShadow = true;
    this.hospitalGroup.add(mainMesh);
    this.disposables.push(mainGeo);

    // Glowing Cyan Roofline Trim
    const roofEdges = new THREE.EdgesGeometry(mainGeo);
    const roofTrimMat = new THREE.LineBasicMaterial({ color: 0x00f5d4, linewidth: 2 });
    const roofLines = new THREE.LineSegments(roofEdges, roofTrimMat);
    roofLines.position.copy(mainMesh.position);
    this.hospitalGroup.add(roofLines);
    this.disposables.push(roofEdges, roofTrimMat);

    // Emergency Receiving Wing (Lower Annex facing the emergency corridor)
    const wingGeo = new THREE.BoxGeometry(12, 14, 10);
    const wingMesh = new THREE.Mesh(wingGeo, hospitalMat);
    wingMesh.position.set(hospitalX + 11, 7 + 0.2, hospitalZ);
    wingMesh.castShadow = true;
    this.hospitalGroup.add(wingMesh);
    this.disposables.push(wingGeo);

    // Helipad Platform on Roof
    const helipadGeo = new THREE.CylinderGeometry(5.0, 5.0, 0.4, 24);
    const helipadMat = new THREE.MeshStandardMaterial({
      color: 0x1a3366,
      roughness: 0.5,
      metalness: 0.4,
    });
    const helipad = new THREE.Mesh(helipadGeo, helipadMat);
    helipad.position.set(hospitalX, hospitalH + 0.4, hospitalZ);
    this.hospitalGroup.add(helipad);
    this.disposables.push(helipadGeo, helipadMat);

    // Helipad "H" Marker
    const hBar1Geo = new THREE.PlaneGeometry(0.8, 4.0);
    const hBar2Geo = new THREE.PlaneGeometry(0.8, 4.0);
    const hCrossGeo = new THREE.PlaneGeometry(2.4, 0.8);
    const hMat = new THREE.MeshBasicMaterial({ color: 0x00e5ff });
    this.disposables.push(hBar1Geo, hBar2Geo, hCrossGeo, hMat);

    const m1 = new THREE.Mesh(hBar1Geo, hMat);
    m1.rotation.x = -Math.PI / 2;
    m1.position.set(hospitalX - 1.2, hospitalH + 0.65, hospitalZ);

    const m2 = new THREE.Mesh(hBar2Geo, hMat);
    m2.rotation.x = -Math.PI / 2;
    m2.position.set(hospitalX + 1.2, hospitalH + 0.65, hospitalZ);

    const mCross = new THREE.Mesh(hCrossGeo, hMat);
    mCross.rotation.x = -Math.PI / 2;
    mCross.position.set(hospitalX, hospitalH + 0.65, hospitalZ);

    this.hospitalGroup.add(m1, m2, mCross);

    // Emergency Red/Cyan Medical Beacon Mast
    const mastGeo = new THREE.CylinderGeometry(0.15, 0.2, 5.0, 8);
    const mastMat = new THREE.MeshStandardMaterial({ color: 0x64748b, metalness: 0.9 });
    const mast = new THREE.Mesh(mastGeo, mastMat);
    mast.position.set(hospitalX + 5, hospitalH + 2.5, hospitalZ + 5);
    this.hospitalGroup.add(mast);

    this.beaconMaterial = new THREE.MeshBasicMaterial({ color: 0xef476f });
    const beaconGeo = new THREE.SphereGeometry(0.45, 12, 12);
    const beacon = new THREE.Mesh(beaconGeo, this.beaconMaterial);
    beacon.position.set(hospitalX + 5, hospitalH + 5.2, hospitalZ + 5);
    this.hospitalGroup.add(beacon);

    this.disposables.push(mastGeo, mastMat, beaconGeo, this.beaconMaterial);
  }

  /**
   * 3. South-West Quadrant: Smart City Traffic Operations Hub & Antenna Spire
   */
  private buildSmartCityHubSW(): void {
    const hubX = -24;
    const hubZ = 24;
    const hubW = 15;
    const hubD = 15;
    const hubH = 28;

    this.createOfficeTower({
      x: hubX,
      z: hubZ,
      width: hubW,
      depth: hubD,
      height: hubH,
      bodyColor: 0x0a1633,
      trimColor: 0x00e5ff,
      windowColor: 0x00f5d4,
      name: 'TrafficOperations_SW1',
    });

    // Tall V2X Master Communications Spire
    const spireGeo = new THREE.CylinderGeometry(0.12, 0.35, 12.0, 8);
    const spireMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.8 });
    const spire = new THREE.Mesh(spireGeo, spireMat);
    spire.position.set(hubX, hubH + 6.0, hubZ);
    this.buildingsGroup.add(spire);

    // Glowing tip on antenna
    const tipGeo = new THREE.SphereGeometry(0.35, 12, 12);
    const tipMat = new THREE.MeshBasicMaterial({ color: 0x00e5ff });
    const tip = new THREE.Mesh(tipGeo, tipMat);
    tip.position.set(hubX, hubH + 12.1, hubZ);
    this.buildingsGroup.add(tip);

    this.disposables.push(spireGeo, spireMat, tipGeo, tipMat);

    // Annex Building SW2
    this.createSimpleBuilding({
      x: -18,
      z: 35,
      width: 11,
      depth: 11,
      height: 18,
      bodyColor: 0x0f2249,
      trimColor: 0x38bdf8,
      name: 'Annex_SW2',
    });
  }

  /**
   * 4. South-East Quadrant: Residential & Retail Cyber Towers
   */
  private buildResidentialTowersSE(): void {
    // Tower SE1
    this.createOfficeTower({
      x: 24,
      z: 24,
      width: 14,
      depth: 13,
      height: 35,
      bodyColor: 0x0d1e40,
      trimColor: 0xffd166,
      windowColor: 0xffd166,
      name: 'Tower_SE1',
    });

    // Tower SE2: Stepped Urban Tower
    this.createOfficeTower({
      x: 35,
      z: 22,
      width: 11,
      depth: 11,
      height: 24,
      bodyColor: 0x0b1a38,
      trimColor: 0x00e5ff,
      windowColor: 0x00e5ff,
      name: 'Tower_SE2',
    });

    // Low Pavilion SE3
    this.createSimpleBuilding({
      x: 22,
      z: 35,
      width: 10,
      depth: 9,
      height: 15,
      bodyColor: 0x12244f,
      trimColor: 0x06d6a0,
      name: 'Pavilion_SE3',
    });
  }

  /**
   * 5. Urban Streetlights (Cột đèn chiếu sáng đường)
   */
  private buildStreetlights(): void {
    const poleMat = new THREE.MeshStandardMaterial({
      color: 0x1e293b,
      metalness: 0.8,
      roughness: 0.3,
    });
    const lampMat = new THREE.MeshBasicMaterial({ color: 0x00f5d4 });
    this.disposables.push(poleMat, lampMat);

    const poleGeo = new THREE.CylinderGeometry(0.08, 0.1, 7.0, 8);
    const armGeo = new THREE.CylinderGeometry(0.05, 0.05, 2.2, 8);
    const headGeo = new THREE.BoxGeometry(0.3, 0.15, 0.5);
    this.disposables.push(poleGeo, armGeo, headGeo);

    // Positions for streetlights along the curb edges:
    // Placed at curb offset (~7.8m from center road lines)
    const positions = [
      // Along North Road (Oak St)
      { x: -7.8, z: -15, rotY: 0 },
      { x: -7.8, z: -27, rotY: 0 },
      { x: 7.8, z: -15, rotY: Math.PI },
      { x: 7.8, z: -27, rotY: Math.PI },

      // Along South Road (Oak St)
      { x: -7.8, z: 15, rotY: 0 },
      { x: -7.8, z: 27, rotY: 0 },
      { x: 7.8, z: 15, rotY: Math.PI },
      { x: 7.8, z: 27, rotY: Math.PI },

      // Along East Road (5th Ave)
      { x: 15, z: -7.8, rotY: -Math.PI / 2 },
      { x: 27, z: -7.8, rotY: -Math.PI / 2 },
      { x: 15, z: 7.8, rotY: Math.PI / 2 },
      { x: 27, z: 7.8, rotY: Math.PI / 2 },

      // Along West Road (5th Ave)
      { x: -15, z: -7.8, rotY: -Math.PI / 2 },
      { x: -27, z: -7.8, rotY: -Math.PI / 2 },
      { x: -15, z: 7.8, rotY: Math.PI / 2 },
      { x: -27, z: 7.8, rotY: Math.PI / 2 },
    ];

    positions.forEach((p) => {
      const group = new THREE.Group();

      // Vertical pole
      const pole = new THREE.Mesh(poleGeo, poleMat);
      pole.position.y = 3.5;
      group.add(pole);

      // Horizontal arm reaching out towards road
      const arm = new THREE.Mesh(armGeo, poleMat);
      arm.rotation.z = Math.PI / 2;
      arm.position.set(0.9, 6.9, 0);
      group.add(arm);

      // Glowing lamp head
      const head = new THREE.Mesh(headGeo, lampMat);
      head.position.set(1.9, 6.8, 0);
      group.add(head);

      group.position.set(p.x, 0.22, p.z);
      group.rotation.y = p.rotY;
      this.streetFurnitureGroup.add(group);
    });
  }

  /**
   * 6. Stylized Low-Poly Urban Trees
   */
  private buildUrbanTrees(): void {
    const trunkMat = new THREE.MeshStandardMaterial({
      color: 0x1f293d,
      roughness: 0.9,
    });
    const foliageMat = new THREE.MeshStandardMaterial({
      color: 0x06d6a0,
      emissive: 0x06d6a0,
      emissiveIntensity: 0.15,
      roughness: 0.7,
      flatShading: true,
    });
    this.disposables.push(trunkMat, foliageMat);

    const trunkGeo = new THREE.CylinderGeometry(0.18, 0.25, 2.2, 6);
    const foliageGeo = new THREE.ConeGeometry(1.6, 3.8, 6);
    this.disposables.push(trunkGeo, foliageGeo);

    // Tree positions along sidewalk boulevards
    const treePositions = [
      // NW Sidewalk
      { x: -11.5, z: -16 },
      { x: -11.5, z: -25 },
      { x: -16, z: -11.5 },
      { x: -25, z: -11.5 },

      // NE Sidewalk
      { x: 11.5, z: -16 },
      { x: 11.5, z: -25 },
      { x: 16, z: -11.5 },
      { x: 25, z: -11.5 },

      // SW Sidewalk
      { x: -11.5, z: 16 },
      { x: -11.5, z: 25 },
      { x: -16, z: 11.5 },
      { x: -25, z: 11.5 },

      // SE Sidewalk
      { x: 11.5, z: 16 },
      { x: 11.5, z: 25 },
      { x: 16, z: 11.5 },
      { x: 25, z: 11.5 },
    ];

    treePositions.forEach((pos) => {
      const tree = new THREE.Group();

      const trunk = new THREE.Mesh(trunkGeo, trunkMat);
      trunk.position.y = 1.1;
      trunk.castShadow = true;
      tree.add(trunk);

      const foliage = new THREE.Mesh(foliageGeo, foliageMat);
      foliage.position.y = 3.6;
      foliage.castShadow = true;
      tree.add(foliage);

      tree.position.set(pos.x, 0.22, pos.z);
      this.treesGroup.add(tree);
    });
  }

  /**
   * 7. V2X RSU (Roadside Unit) Nodes at the 4 Corners
   */
  private buildV2XRSUPoles(): void {
    const rsuMat = new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.7 });
    this.rsuLedMaterial = new THREE.MeshBasicMaterial({ color: 0x00f5d4 });
    this.disposables.push(rsuMat, this.rsuLedMaterial);

    const poleGeo = new THREE.CylinderGeometry(0.08, 0.08, 4.5, 8);
    const boxGeo = new THREE.BoxGeometry(0.5, 0.7, 0.4);
    const antennaGeo = new THREE.CylinderGeometry(0.02, 0.02, 1.2, 6);
    const ledGeo = new THREE.SphereGeometry(0.08, 8, 8);
    this.disposables.push(poleGeo, boxGeo, antennaGeo, ledGeo);

    // 4 Corner RSU Posts placed right at crosswalk intersection zones
    const rsuCorners = [
      { x: -8.5, z: -8.5, name: 'RSU_NW' },
      { x: 8.5, z: -8.5, name: 'RSU_NE' },
      { x: -8.5, z: 8.5, name: 'RSU_SW' },
      { x: 8.5, z: 8.5, name: 'RSU_SE' },
    ];

    rsuCorners.forEach((corner) => {
      const rsu = new THREE.Group();

      const pole = new THREE.Mesh(poleGeo, rsuMat);
      pole.position.y = 2.25;
      rsu.add(pole);

      const rsuBox = new THREE.Mesh(boxGeo, rsuMat);
      rsuBox.position.set(0, 4.0, 0);
      rsu.add(rsuBox);

      const antenna = new THREE.Mesh(antennaGeo, rsuMat);
      antenna.position.set(0, 4.8, 0);
      rsu.add(antenna);

      const led = new THREE.Mesh(ledGeo, this.rsuLedMaterial!);
      led.position.set(0, 4.2, 0.22);
      rsu.add(led);

      rsu.position.set(corner.x, 0.22, corner.z);
      this.rsuPolesGroup.add(rsu);
    });
  }

  /**
   * Helper: Build Multi-story Cyber Office Tower with Windows & Glowing Edges
   */
  private createOfficeTower(opts: {
    x: number;
    z: number;
    width: number;
    depth: number;
    height: number;
    bodyColor: number;
    trimColor: number;
    windowColor: number;
    name: string;
  }): void {
    const geo = new THREE.BoxGeometry(opts.width, opts.height, opts.depth);
    const mat = new THREE.MeshStandardMaterial({
      color: opts.bodyColor,
      roughness: 0.6,
      metalness: 0.35,
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(opts.x, opts.height / 2 + 0.2, opts.z);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    this.buildingsGroup.add(mesh);

    // Glowing Cyber Edge Trims
    const edges = new THREE.EdgesGeometry(geo);
    const trimMat = new THREE.LineBasicMaterial({ color: opts.trimColor });
    const edgeLines = new THREE.LineSegments(edges, trimMat);
    edgeLines.position.copy(mesh.position);
    this.buildingsGroup.add(edgeLines);

    // Rooftop HVAC unit
    const hvacGeo = new THREE.BoxGeometry(opts.width * 0.45, 1.8, opts.depth * 0.45);
    const hvacMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.8 });
    const hvac = new THREE.Mesh(hvacGeo, hvacMat);
    hvac.position.set(opts.x, opts.height + 0.9 + 0.2, opts.z);
    this.buildingsGroup.add(hvac);

    this.disposables.push(geo, mat, edges, trimMat, hvacGeo, hvacMat);
  }

  private createSimpleBuilding(opts: {
    x: number;
    z: number;
    width: number;
    depth: number;
    height: number;
    bodyColor: number;
    trimColor: number;
    name: string;
  }): void {
    const geo = new THREE.BoxGeometry(opts.width, opts.height, opts.depth);
    const mat = new THREE.MeshStandardMaterial({
      color: opts.bodyColor,
      roughness: 0.7,
      metalness: 0.25,
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(opts.x, opts.height / 2 + 0.2, opts.z);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    this.buildingsGroup.add(mesh);

    const edges = new THREE.EdgesGeometry(geo);
    const trimMat = new THREE.LineBasicMaterial({ color: opts.trimColor });
    const edgeLines = new THREE.LineSegments(edges, trimMat);
    edgeLines.position.copy(mesh.position);
    this.buildingsGroup.add(edgeLines);

    this.disposables.push(geo, mat, edges, trimMat);
  }

  /**
   * Update animation frame dynamic effects (beacon strobe, RSU LEDs)
   */
  public update(timeMs: number): void {
    // 1. Hospital Emergency Medical Beacon Flashing (Amber/Red pulse)
    if (this.beaconMaterial) {
      const flash = (Math.sin(timeMs * 0.008) + 1) / 2;
      this.beaconMaterial.color.setRGB(0.9 + 0.1 * flash, 0.2 * flash, 0.3 * flash);
    }

    // 2. RSU C-V2X Communication Link status blink
    if (this.rsuLedMaterial) {
      const blink = Math.sin(timeMs * 0.005) > 0 ? 1 : 0.3;
      this.rsuLedMaterial.opacity = blink;
    }
  }

  /**
   * Layer Visibility Controls
   */
  public setBuildingsVisibility(visible: boolean): void {
    this.buildingsGroup.visible = visible;
    this.hospitalGroup.visible = visible;
  }

  public setStreetFurnitureVisibility(visible: boolean): void {
    this.streetFurnitureGroup.visible = visible;
    this.rsuPolesGroup.visible = visible;
  }

  public setTreesVisibility(visible: boolean): void {
    this.treesGroup.visible = visible;
  }

  public dispose(): void {
    this.disposables.forEach((d) => {
      try {
        d.dispose();
      } catch (e) {
        // Ignore
      }
    });
  }
}

