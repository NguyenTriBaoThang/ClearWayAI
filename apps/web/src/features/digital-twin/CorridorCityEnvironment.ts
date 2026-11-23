/**
 * ClearWayAI Corridor-Wide 3D City Environment (`apps/web/src/features/digital-twin/CorridorCityEnvironment.ts`)
 *
 * Generates the complete 3D urban context along the 1,000m arterial corridor:
 * - Commercial & corporate cyber towers distributed across inter-node city blocks
 * - Metropolitan General Trauma Center at x = 850m with emergency bay, helipad, and glowing beacon
 * - V2X RSU transceiver nodes at all 4 intersections (RSU-01 through RSU-04)
 * - Boulevard streetlights and low-poly urban trees at regular spacing
 * - West Feeder Gate gateway portal structure at x = -150m
 */

import * as THREE from 'three';
import { ARTERIAL_NODES } from './MultiIntersectionRoadNetwork';
import { VMSBoardStatusInput, VMSOverheadGantryMesh } from './VMSOverheadGantryMesh';

export class CorridorCityEnvironment {
  public group: THREE.Group;
  public buildingsGroup: THREE.Group;
  public hospitalGroup: THREE.Group;
  public streetlightsGroup: THREE.Group;
  public treesGroup: THREE.Group;
  public rsuPolesGroup: THREE.Group;
  public vmsGantriesGroup: THREE.Group;
  public vmsGantries: VMSOverheadGantryMesh[] = [];

  private disposables: { dispose: () => void }[] = [];
  private beaconMaterial?: THREE.MeshBasicMaterial;

  constructor() {
    this.group = new THREE.Group();
    this.group.name = 'CorridorCityEnvironment';

    this.buildingsGroup = new THREE.Group();
    this.buildingsGroup.name = 'CorridorBuildings';
    this.hospitalGroup = new THREE.Group();
    this.hospitalGroup.name = 'TraumaCenterHospital';
    this.streetlightsGroup = new THREE.Group();
    this.streetlightsGroup.name = 'Streetlights';
    this.treesGroup = new THREE.Group();
    this.treesGroup.name = 'BoulevardTrees';
    this.rsuPolesGroup = new THREE.Group();
    this.rsuPolesGroup.name = 'V2XRSUPoles';
    this.vmsGantriesGroup = new THREE.Group();
    this.vmsGantriesGroup.name = 'VMSOverheadGantries';

    this.group.add(this.buildingsGroup);
    this.group.add(this.hospitalGroup);
    this.group.add(this.streetlightsGroup);
    this.group.add(this.treesGroup);
    this.group.add(this.rsuPolesGroup);
    this.group.add(this.vmsGantriesGroup);

    this.buildCityBlockBuildings();
    this.buildTraumaCenterHospital();
    this.buildV2XRSUNodes();
    this.buildStreetlights();
    this.buildBoulevardTrees();
    this.buildWestFeederPortal();
    this.buildVMSGantries();
  }

  /**
   * 1. Cyber Commercial Towers Distributed Along the 1,000m Corridor
   */
  private buildCityBlockBuildings(): void {
    // Inter-node block building clusters (North & South of 5th Ave)
    const buildingPositions = [
      // Block 1 (West of Node A: x = -100 to -30)
      { x: -80, z: -25, w: 20, d: 20, h: 32, color: 0x0c1b3a, trim: 0x00e5ff },
      { x: -80, z: 25, w: 20, d: 20, h: 28, color: 0x0e1f42, trim: 0x06d6a0 },
      { x: -40, z: -25, w: 18, d: 18, h: 36, color: 0x0c1b3a, trim: 0x00f5d4 },
      { x: -40, z: 25, w: 18, d: 18, h: 26, color: 0x0e1f42, trim: 0xffd166 },

      // Block 2 (Between Node A and Node B: x = 30 to 220)
      { x: 80, z: -25, w: 22, d: 20, h: 42, color: 0x0c1b3a, trim: 0x00e5ff },
      { x: 80, z: 25, w: 22, d: 20, h: 30, color: 0x0e1f42, trim: 0x06d6a0 },
      { x: 140, z: -25, w: 24, d: 20, h: 48, color: 0x0c1b3a, trim: 0x00f5d4 },
      { x: 140, z: 25, w: 24, d: 20, h: 34, color: 0x0e1f42, trim: 0x38bdf8 },
      { x: 190, z: -25, w: 20, d: 20, h: 38, color: 0x0c1b3a, trim: 0x00e5ff },
      { x: 190, z: 25, w: 20, d: 20, h: 28, color: 0x0e1f42, trim: 0x06d6a0 },

      // Block 3 (Between Node B and Node C: x = 280 to 470)
      { x: 330, z: -25, w: 22, d: 20, h: 45, color: 0x0c1b3a, trim: 0x00e5ff },
      { x: 330, z: 25, w: 22, d: 20, h: 32, color: 0x0e1f42, trim: 0x06d6a0 },
      { x: 390, z: -25, w: 24, d: 20, h: 52, color: 0x0c1b3a, trim: 0x00f5d4 },
      { x: 390, z: 25, w: 24, d: 20, h: 35, color: 0x0e1f42, trim: 0x38bdf8 },
      { x: 440, z: -25, w: 20, d: 20, h: 40, color: 0x0c1b3a, trim: 0x00e5ff },
      { x: 440, z: 25, w: 20, d: 20, h: 28, color: 0x0e1f42, trim: 0x06d6a0 },

      // Block 4 (Between Node C and Node D: x = 530 to 720)
      { x: 580, z: -25, w: 22, d: 20, h: 38, color: 0x0c1b3a, trim: 0x00e5ff },
      { x: 580, z: 25, w: 22, d: 20, h: 30, color: 0x0e1f42, trim: 0x06d6a0 },
      { x: 640, z: -25, w: 24, d: 20, h: 44, color: 0x0c1b3a, trim: 0x00f5d4 },
      { x: 640, z: 25, w: 24, d: 20, h: 32, color: 0x0e1f42, trim: 0x38bdf8 },
      { x: 690, z: -25, w: 20, d: 20, h: 36, color: 0x0c1b3a, trim: 0x00e5ff },
      { x: 690, z: 25, w: 20, d: 20, h: 26, color: 0x0e1f42, trim: 0x06d6a0 },
    ];

    for (const b of buildingPositions) {
      this.createTower(b.x, b.z, b.w, b.d, b.h, b.color, b.trim);
    }
  }

  private createTower(x: number, z: number, w: number, d: number, h: number, bodyColor: number, trimColor: number): void {
    const bodyMat = new THREE.MeshStandardMaterial({
      color: bodyColor,
      roughness: 0.35,
      metalness: 0.75,
    });
    const trimMat = new THREE.MeshBasicMaterial({ color: trimColor });
    this.disposables.push(bodyMat, trimMat);

    // Tower Body
    const geo = new THREE.BoxGeometry(w, h, d);
    const mesh = new THREE.Mesh(geo, bodyMat);
    mesh.position.set(x, h / 2, z);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    this.buildingsGroup.add(mesh);

    // Rooftop Accent Frame
    const roofGeo = new THREE.BoxGeometry(w + 0.4, 0.4, d + 0.4);
    const roof = new THREE.Mesh(roofGeo, trimMat);
    roof.position.set(x, h + 0.2, z);
    this.buildingsGroup.add(roof);

    // Rooftop Spire / Antenna
    const spireGeo = new THREE.CylinderGeometry(0.1, 0.3, 5, 8);
    const spire = new THREE.Mesh(spireGeo, trimMat);
    spire.position.set(x, h + 2.5, z);
    this.buildingsGroup.add(spire);
  }

  /**
   * 2. Metropolitan Trauma Center Hospital at x = 850m
   */
  private buildTraumaCenterHospital(): void {
    const hospX = 850.0;
    const hospZ = -26.0;

    const hospMat = new THREE.MeshStandardMaterial({
      color: 0x0f2747,
      roughness: 0.4,
      metalness: 0.6,
    });
    const cyanTrimMat = new THREE.MeshBasicMaterial({ color: 0x00e5ff });
    const redCrossMat = new THREE.MeshBasicMaterial({ color: 0xef476f });
    this.disposables.push(hospMat, cyanTrimMat, redCrossMat);

    // Main Hospital Block (34m wide x 24m high x 26m deep)
    const mainGeo = new THREE.BoxGeometry(34, 24, 26);
    const mainMesh = new THREE.Mesh(mainGeo, hospMat);
    mainMesh.position.set(hospX, 12, hospZ);
    this.hospitalGroup.add(mainMesh);

    // Emergency Ambulance Arrival Bay Canopy
    const canopyGeo = new THREE.BoxGeometry(18, 1, 10);
    const canopy = new THREE.Mesh(canopyGeo, cyanTrimMat);
    canopy.position.set(hospX, 4.5, hospZ + 16);
    this.hospitalGroup.add(canopy);

    // Rooftop Helipad
    const padGeo = new THREE.CylinderGeometry(6.5, 6.5, 0.4, 32);
    const padMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.8 });
    const pad = new THREE.Mesh(padGeo, padMat);
    pad.position.set(hospX, 24.2, hospZ);
    this.hospitalGroup.add(pad);

    // Helipad "H" Marking
    const hLineMat = new THREE.MeshBasicMaterial({ color: 0xffd166 });
    const h1 = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.05, 5.0), hLineMat);
    h1.position.set(hospX - 2.0, 24.45, hospZ);
    this.hospitalGroup.add(h1);

    const h2 = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.05, 5.0), hLineMat);
    h2.position.set(hospX + 2.0, 24.45, hospZ);
    this.hospitalGroup.add(h2);

    const hMid = new THREE.Mesh(new THREE.BoxGeometry(4.0, 0.05, 0.8), hLineMat);
    hMid.position.set(hospX, 24.45, hospZ);
    this.hospitalGroup.add(hMid);

    // Glowing Medical Beacon
    const beaconGeo = new THREE.SphereGeometry(1.0, 16, 16);
    this.beaconMaterial = new THREE.MeshBasicMaterial({ color: 0xef476f });
    const beacon = new THREE.Mesh(beaconGeo, this.beaconMaterial);
    beacon.position.set(hospX, 27.0, hospZ);
    this.hospitalGroup.add(beacon);
  }

  /**
   * 3. V2X RSU Transceiver Nodes at Nodes A, B, C, D
   */
  private buildV2XRSUNodes(): void {
    const poleMat = new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.8 });
    const rsuBoxMat = new THREE.MeshBasicMaterial({ color: 0x00f5d4 });
    this.disposables.push(poleMat, rsuBoxMat);

    for (const node of ARTERIAL_NODES) {
      // Mast Pole
      const poleGeo = new THREE.CylinderGeometry(0.12, 0.16, 6.0, 12);
      const pole = new THREE.Mesh(poleGeo, poleMat);
      pole.position.set(node.xMeters + 8.5, 3.0, -8.5);
      this.rsuPolesGroup.add(pole);

      // Transceiver Box
      const boxGeo = new THREE.BoxGeometry(0.8, 0.8, 0.8);
      const box = new THREE.Mesh(boxGeo, rsuBoxMat);
      box.position.set(node.xMeters + 8.5, 6.2, -8.5);
      this.rsuPolesGroup.add(box);
    }
  }

  /**
   * 4. Boulevard Streetlights Spaced Every 40m Along 5th Ave
   */
  private buildStreetlights(): void {
    const poleMat = new THREE.MeshStandardMaterial({ color: 0x475569, metalness: 0.7 });
    const lightGlowMat = new THREE.MeshBasicMaterial({ color: 0x00e5ff });
    this.disposables.push(poleMat, lightGlowMat);

    for (let x = -130; x <= 870; x += 40) {
      // Avoid intersection junctions (Nodes A, B, C, D at x=0, 250, 500, 750)
      if ([0, 250, 500, 750].some((nx) => Math.abs(x - nx) < 18)) continue;

      // North sidewalk streetlight
      const poleGeo = new THREE.CylinderGeometry(0.08, 0.12, 5.5, 8);
      const poleN = new THREE.Mesh(poleGeo, poleMat);
      poleN.position.set(x, 2.75, -7.8);
      this.streetlightsGroup.add(poleN);

      const headGeo = new THREE.BoxGeometry(0.6, 0.15, 0.4);
      const headN = new THREE.Mesh(headGeo, lightGlowMat);
      headN.position.set(x, 5.5, -7.5);
      this.streetlightsGroup.add(headN);

      // South sidewalk streetlight
      const poleS = new THREE.Mesh(poleGeo, poleMat);
      poleS.position.set(x, 2.75, 7.8);
      this.streetlightsGroup.add(poleS);

      const headS = new THREE.Mesh(headGeo, lightGlowMat);
      headS.position.set(x, 5.5, 7.5);
      this.streetlightsGroup.add(headS);
    }
  }

  /**
   * 5. Boulevard Stylized Urban Trees
   */
  private buildBoulevardTrees(): void {
    const trunkMat = new THREE.MeshStandardMaterial({ color: 0x27272a, roughness: 0.9 });
    const foliageMat = new THREE.MeshStandardMaterial({
      color: 0x064e3b,
      roughness: 0.6,
      emissive: 0x065f46,
      emissiveIntensity: 0.2,
    });
    this.disposables.push(trunkMat, foliageMat);

    for (let x = -110; x <= 850; x += 40) {
      if ([0, 250, 500, 750].some((nx) => Math.abs(x - nx) < 22)) continue;

      // North side tree
      const trunkN = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.18, 1.8, 6), trunkMat);
      trunkN.position.set(x, 0.9, -10.5);
      this.treesGroup.add(trunkN);

      const foliageN = new THREE.Mesh(new THREE.ConeGeometry(1.6, 3.8, 7), foliageMat);
      foliageN.position.set(x, 3.5, -10.5);
      this.treesGroup.add(foliageN);

      // South side tree
      const trunkS = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.18, 1.8, 6), trunkMat);
      trunkS.position.set(x, 0.9, 10.5);
      this.treesGroup.add(trunkS);

      const foliageS = new THREE.Mesh(new THREE.ConeGeometry(1.6, 3.8, 7), foliageMat);
      foliageS.position.set(x, 3.5, 10.5);
      this.treesGroup.add(foliageS);
    }
  }

  /**
   * 6. West Feeder Gate Portal at x = -150m
   */
  private buildWestFeederPortal(): void {
    const portalMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.8 });
    const cyanLightMat = new THREE.MeshBasicMaterial({ color: 0x00e5ff });
    this.disposables.push(portalMat, cyanLightMat);

    // Left Arch Leg
    const legL = new THREE.Mesh(new THREE.BoxGeometry(1.2, 8.0, 1.2), portalMat);
    legL.position.set(-150, 4.0, -8.0);
    this.buildingsGroup.add(legL);

    // Right Arch Leg
    const legR = new THREE.Mesh(new THREE.BoxGeometry(1.2, 8.0, 1.2), portalMat);
    legR.position.set(-150, 4.0, 8.0);
    this.buildingsGroup.add(legR);

    // Overhead Arch Beam
    const beam = new THREE.Mesh(new THREE.BoxGeometry(1.4, 1.2, 17.2), portalMat);
    beam.position.set(-150, 8.0, 0);
    this.buildingsGroup.add(beam);

    // Cyan Status Line across beam
    const line = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.2, 16.0), cyanLightMat);
    line.position.set(-149.8, 8.0, 0);
    this.buildingsGroup.add(line);
  }

  /**
   * 7. Overhead Variable Message Signs (VMS) Gantries Ahead of Intersections A-D
   */
  private buildVMSGantries(): void {
    const gantryConfigs = [
      { boardId: 'VMS-A', nodeId: 'node_a', xMeters: -80.0 },
      { boardId: 'VMS-B', nodeId: 'node_b', xMeters: 170.0 },
      { boardId: 'VMS-C', nodeId: 'node_c', xMeters: 420.0 },
      { boardId: 'VMS-D', nodeId: 'node_d', xMeters: 670.0 },
    ];

    for (const cfg of gantryConfigs) {
      const gantry = new VMSOverheadGantryMesh(cfg.boardId, cfg.nodeId, cfg.xMeters, 14.0);
      this.vmsGantries.push(gantry);
      this.vmsGantriesGroup.add(gantry.group);
      this.disposables.push(gantry);
    }
  }

  public updateVMS(
    advisories?: Record<string, VMSBoardStatusInput>,
    timeSec: number = 0,
  ): void {
    for (const gantry of this.vmsGantries) {
      if (advisories && advisories[gantry.nodeId]) {
        gantry.updateAdvisory(advisories[gantry.nodeId], timeSec);
      } else {
        // Default nominal advisory
        gantry.updateAdvisory(
          {
            board_id: gantry.boardId,
            node_id: gantry.nodeId,
            gantry_x_m: gantry.gantryX,
            target_stopline_x: gantry.gantryX + 80.0,
            mode: 'NOMINAL',
            message_line_1_vi: 'CHÚC QUÝ KHÁCH BÌNH AN',
            message_line_2_en: 'SPEED LIMIT 50 KM/H',
            recommended_speed_kmh: 50,
            flashing_strobe: false,
            chevron_direction: 'NONE',
          },
          timeSec,
        );
      }
    }
  }

  public update(timeMs: number): void {
    if (this.beaconMaterial) {
      const pulse = Math.sin(timeMs * 0.008);
      this.beaconMaterial.color.setHex(pulse > 0 ? 0xef476f : 0x7f1d1d);
    }
    this.updateVMS(undefined, timeMs / 1000.0);
  }

  public setBuildingsVisibility(visible: boolean): void {
    this.buildingsGroup.visible = visible;
    this.hospitalGroup.visible = visible;
  }

  public setStreetFurnitureVisibility(visible: boolean): void {
    this.streetlightsGroup.visible = visible;
    this.rsuPolesGroup.visible = visible;
    this.vmsGantriesGroup.visible = visible;
  }

  public setTreesVisibility(visible: boolean): void {
    this.treesGroup.visible = visible;
  }

  public dispose(): void {
    for (const g of this.vmsGantries) {
      g.dispose();
    }
    for (const d of this.disposables) {
      d.dispose();
    }
  }
}
