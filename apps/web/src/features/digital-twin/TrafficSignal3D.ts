import * as THREE from 'three';
import { SignalPhaseController, SignalLightColor, PedestrianPhase, SignalCycleSnapshot } from './SignalPhaseController';

export interface SignalHeadBundle {
  housing: THREE.Mesh;
  redLens: THREE.Mesh;
  yellowLens: THREE.Mesh;
  greenLens: THREE.Mesh;
  redMat: THREE.MeshStandardMaterial;
  yellowMat: THREE.MeshStandardMaterial;
  greenMat: THREE.MeshStandardMaterial;
  currentLit: SignalLightColor | 'none';
}

export interface PedestrianHeadBundle {
  housing: THREE.Mesh;
  dontWalkLens: THREE.Mesh;
  walkLens: THREE.Mesh;
  dontWalkMat: THREE.MeshStandardMaterial;
  walkMat: THREE.MeshStandardMaterial;
  currentLit: PedestrianPhase;
}

export interface SignalPoleBundle {
  id: string;
  approach: 'EAST_WEST' | 'NORTH_SOUTH';
  group: THREE.Group;
  primaryHead: SignalHeadBundle;
  secondaryHead: SignalHeadBundle;
  pedestrianHead: PedestrianHeadBundle;
}

export interface PedestrianAgent {
  id: string;
  crosswalk: 'NORTH' | 'SOUTH' | 'EAST' | 'WEST';
  group: THREE.Group;
  baseX: number;
  baseZ: number;
  walkAxis: 'X' | 'Z';
  color: number;
}

export interface InspectedSignalPole {
  poleId: string;
  approachName: string;
  vehicularPhase: SignalLightColor;
  pedestrianPhase: PedestrianPhase;
  countdownSec: number;
  nextPhase: string;
  conflictFreeStatus: string;
  provenance: string;
  timestamp: number;
}

/**
 * TrafficSignal3D creates and updates physical 3D traffic light mast poles,
 * emissive signal heads with strict single-lens illumination, pedestrian signals,
 * and animated crossing pedestrians in WebGL.
 */
export class TrafficSignal3D {
  public group: THREE.Group;
  public signalsGroup: THREE.Group;
  public pedestriansGroup: THREE.Group;
  public controller: SignalPhaseController;

  public poles: SignalPoleBundle[] = [];
  public pedestrians: PedestrianAgent[] = [];

  private disposables: { dispose: () => void }[] = [];

  constructor(controller?: SignalPhaseController) {
    this.group = new THREE.Group();
    this.group.name = 'TrafficSignal3D';

    this.signalsGroup = new THREE.Group();
    this.signalsGroup.name = 'SignalPoles';
    this.group.add(this.signalsGroup);

    this.pedestriansGroup = new THREE.Group();
    this.pedestriansGroup.name = 'Pedestrians';
    this.group.add(this.pedestriansGroup);

    this.controller = controller || new SignalPhaseController();

    this.buildSignalPoles();
    this.buildPedestrianAgents();
  }

  /**
   * Build 4 Master Signal Poles at the 4 intersection corners
   */
  private buildSignalPoles(): void {
    // 1. North Approach Pole (NW Corner) - Controls Southbound traffic on Oak St
    const northPole = this.createMasterPole(
      'SIG-POLE-N',
      'NORTH_SOUTH',
      new THREE.Vector3(-11.5, 0, -11.5),
      Math.PI / 2, // Arm points East towards +X
      0 // Heads face North (-Z)
    );
    this.poles.push(northPole);
    this.signalsGroup.add(northPole.group);

    // 2. South Approach Pole (SE Corner) - Controls Northbound traffic on Oak St
    const southPole = this.createMasterPole(
      'SIG-POLE-S',
      'NORTH_SOUTH',
      new THREE.Vector3(11.5, 0, 11.5),
      -Math.PI / 2, // Arm points West towards -X
      Math.PI // Heads face South (+Z)
    );
    this.poles.push(southPole);
    this.signalsGroup.add(southPole.group);

    // 3. East Approach Pole (NE Corner) - Controls Westbound traffic on 5th Ave
    const eastPole = this.createMasterPole(
      'SIG-POLE-E',
      'EAST_WEST',
      new THREE.Vector3(11.5, 0, -11.5),
      Math.PI, // Arm points South towards +Z
      Math.PI / 2 // Heads face East (+X)
    );
    this.poles.push(eastPole);
    this.signalsGroup.add(eastPole.group);

    // 4. West Approach Pole (SW Corner) - Controls Eastbound traffic on 5th Ave
    const westPole = this.createMasterPole(
      'SIG-POLE-W',
      'EAST_WEST',
      new THREE.Vector3(-11.5, 0, 11.5),
      0, // Arm points North towards -Z
      -Math.PI / 2 // Heads face West (-X)
    );
    this.poles.push(westPole);
    this.signalsGroup.add(westPole.group);
  }

  /**
   * Create a single steel mast pole with cantilever arm and dual signal heads
   */
  private createMasterPole(
    id: string,
    approach: 'EAST_WEST' | 'NORTH_SOUTH',
    position: THREE.Vector3,
    armRotationY: number,
    headsFacingY: number
  ): SignalPoleBundle {
    const poleGroup = new THREE.Group();
    poleGroup.name = id;
    poleGroup.position.copy(position);

    // Metadata for raycast inspection
    poleGroup.userData = {
      isSignalPole: true,
      poleId: id,
      approach,
    };

    const steelMat = new THREE.MeshStandardMaterial({
      color: 0x242d3d,
      roughness: 0.4,
      metalness: 0.8,
    });
    this.disposables.push(steelMat);

    // 1. Vertical Post (6.4m tall, 0.16m radius)
    const postGeo = new THREE.CylinderGeometry(0.14, 0.18, 6.4, 16);
    const post = new THREE.Mesh(postGeo, steelMat);
    post.position.y = 3.2;
    post.castShadow = true;
    post.receiveShadow = true;
    poleGroup.add(post);
    this.disposables.push(postGeo);

    // Base flanged collar
    const baseCollarGeo = new THREE.CylinderGeometry(0.28, 0.32, 0.4, 16);
    const baseCollar = new THREE.Mesh(baseCollarGeo, steelMat);
    baseCollar.position.y = 0.2;
    poleGroup.add(baseCollar);
    this.disposables.push(baseCollarGeo);

    // 2. Horizontal Cantilever Arm (Arm extends 7.2m out over roadway)
    const armGroup = new THREE.Group();
    armGroup.position.y = 5.8;
    armGroup.rotation.y = armRotationY;

    const armGeo = new THREE.CylinderGeometry(0.10, 0.13, 7.2, 16);
    const arm = new THREE.Mesh(armGeo, steelMat);
    arm.rotation.z = Math.PI / 2;
    arm.position.x = 3.6;
    arm.castShadow = true;
    armGroup.add(arm);
    poleGroup.add(armGroup);
    this.disposables.push(armGeo);

    // Diagonal support gusset
    const braceGeo = new THREE.CylinderGeometry(0.05, 0.05, 2.2, 12);
    const brace = new THREE.Mesh(braceGeo, steelMat);
    brace.rotation.z = Math.PI / 4;
    brace.position.set(0.8, -0.6, 0);
    armGroup.add(brace);
    this.disposables.push(braceGeo);

    // 3. Primary Overhead Vehicular Signal Head (Suspended at 5.4m near lane center)
    const primaryHead = this.createSignalHead(headsFacingY);
    primaryHead.housing.position.set(5.5, -0.4, 0);
    armGroup.add(primaryHead.housing);

    // 4. Secondary Post-Mounted Vehicular Signal Head (Mounted on vertical mast at 3.2m)
    const secondaryHead = this.createSignalHead(headsFacingY);
    secondaryHead.housing.position.set(0, 3.2, 0);
    secondaryHead.housing.scale.set(0.85, 0.85, 0.85);
    poleGroup.add(secondaryHead.housing);

    // 5. Pedestrian Signal Head (Crosswalk signal at 2.4m height)
    const pedestrianHead = this.createPedestrianHead(headsFacingY + Math.PI / 2);
    pedestrianHead.housing.position.set(0, 2.4, 0);
    poleGroup.add(pedestrianHead.housing);

    return {
      id,
      approach,
      group: poleGroup,
      primaryHead,
      secondaryHead,
      pedestrianHead,
    };
  }

  /**
   * Create a 3-lens vehicular traffic light head (Red, Yellow, Green)
   */
  private createSignalHead(facingRotationY: number): SignalHeadBundle {
    const headGroup = new THREE.Group();
    headGroup.rotation.y = facingRotationY;

    // Housing body (black polycarbonate casing)
    const housingMat = new THREE.MeshStandardMaterial({
      color: 0x0f172a,
      roughness: 0.6,
      metalness: 0.3,
    });
    this.disposables.push(housingMat);

    const bodyGeo = new THREE.BoxGeometry(0.42, 1.25, 0.32);
    const body = new THREE.Mesh(bodyGeo, housingMat);
    body.castShadow = true;
    headGroup.add(body);
    this.disposables.push(bodyGeo);

    // High-contrast backplate border (yellow/black border for highway visibility)
    const backplateGeo = new THREE.BoxGeometry(0.56, 1.38, 0.02);
    const backplateMat = new THREE.MeshBasicMaterial({ color: 0x0a0f1d });
    const backplate = new THREE.Mesh(backplateGeo, backplateMat);
    backplate.position.z = -0.16;
    headGroup.add(backplate);
    this.disposables.push(backplateGeo, backplateMat);

    // Lens Geometries & Materials
    const lensGeo = new THREE.CylinderGeometry(0.12, 0.12, 0.08, 16);
    this.disposables.push(lensGeo);

    // Red Lens (Top)
    const redMat = new THREE.MeshStandardMaterial({
      color: 0x330005,
      roughness: 0.2,
      metalness: 0.1,
      emissive: 0x000000,
      emissiveIntensity: 0.0,
    });
    const redLens = new THREE.Mesh(lensGeo, redMat);
    redLens.rotation.x = Math.PI / 2;
    redLens.position.set(0, 0.38, 0.16);
    headGroup.add(redLens);

    // Yellow Lens (Middle)
    const yellowMat = new THREE.MeshStandardMaterial({
      color: 0x332b00,
      roughness: 0.2,
      metalness: 0.1,
      emissive: 0x000000,
      emissiveIntensity: 0.0,
    });
    const yellowLens = new THREE.Mesh(lensGeo, yellowMat);
    yellowLens.rotation.x = Math.PI / 2;
    yellowLens.position.set(0, 0, 0.16);
    headGroup.add(yellowLens);

    // Green Lens (Bottom)
    const greenMat = new THREE.MeshStandardMaterial({
      color: 0x003314,
      roughness: 0.2,
      metalness: 0.1,
      emissive: 0x000000,
      emissiveIntensity: 0.0,
    });
    const greenLens = new THREE.Mesh(lensGeo, greenMat);
    greenLens.rotation.x = Math.PI / 2;
    greenLens.position.set(0, -0.38, 0.16);
    headGroup.add(greenLens);

    this.disposables.push(redMat, yellowMat, greenMat);

    return {
      housing: headGroup as any,
      redLens,
      yellowLens,
      greenLens,
      redMat,
      yellowMat,
      greenMat,
      currentLit: 'none',
    };
  }

  /**
   * Create a 2-lens pedestrian crosswalk signal head (Don't Walk Red / Walk Green)
   */
  private createPedestrianHead(facingRotationY: number): PedestrianHeadBundle {
    const headGroup = new THREE.Group();
    headGroup.rotation.y = facingRotationY;

    const housingMat = new THREE.MeshStandardMaterial({
      color: 0x111827,
      roughness: 0.6,
      metalness: 0.2,
    });
    this.disposables.push(housingMat);

    const bodyGeo = new THREE.BoxGeometry(0.32, 0.65, 0.22);
    const body = new THREE.Mesh(bodyGeo, housingMat);
    headGroup.add(body);
    this.disposables.push(bodyGeo);

    const lensGeo = new THREE.BoxGeometry(0.22, 0.22, 0.04);
    this.disposables.push(lensGeo);

    // Don't Walk Lens (Top - Red Hand)
    const dontWalkMat = new THREE.MeshStandardMaterial({
      color: 0x3b0707,
      emissive: 0x000000,
      emissiveIntensity: 0.0,
    });
    const dontWalkLens = new THREE.Mesh(lensGeo, dontWalkMat);
    dontWalkLens.position.set(0, 0.14, 0.11);
    headGroup.add(dontWalkLens);

    // Walk Lens (Bottom - Green Walking Figure)
    const walkMat = new THREE.MeshStandardMaterial({
      color: 0x032e15,
      emissive: 0x000000,
      emissiveIntensity: 0.0,
    });
    const walkLens = new THREE.Mesh(lensGeo, walkMat);
    walkLens.position.set(0, -0.14, 0.11);
    headGroup.add(walkLens);

    this.disposables.push(dontWalkMat, walkMat);

    return {
      housing: headGroup as any,
      dontWalkLens,
      walkLens,
      dontWalkMat,
      walkMat,
      currentLit: 'DONT_WALK',
    };
  }

  /**
   * Build 8 Low-Poly 3D Pedestrians on the 4 Crosswalks
   */
  private buildPedestrianAgents(): void {
    const crosswalkConfigs: {
      crosswalk: PedestrianAgent['crosswalk'];
      baseX: number;
      baseZ: number;
      walkAxis: 'X' | 'Z';
      colors: number[];
    }[] = [
      { crosswalk: 'NORTH', baseX: 0, baseZ: -14, walkAxis: 'X', colors: [0x38bdf8, 0xffd166] },
      { crosswalk: 'SOUTH', baseX: 0, baseZ: 14, walkAxis: 'X', colors: [0x06d6a0, 0xf43f5e] },
      { crosswalk: 'EAST', baseX: 14, baseZ: 0, walkAxis: 'Z', colors: [0xa855f7, 0x00e5ff] },
      { crosswalk: 'WEST', baseX: -14, baseZ: 0, walkAxis: 'Z', colors: [0xfbbf24, 0x64748b] },
    ];

    crosswalkConfigs.forEach((cfg, idx) => {
      cfg.colors.forEach((col, pIdx) => {
        const id = `PED-${cfg.crosswalk}-${pIdx + 1}`;
        const group = this.createPedestrianFigure(col);
        group.position.set(cfg.baseX, 0, cfg.baseZ);
        this.pedestriansGroup.add(group);

        this.pedestrians.push({
          id,
          crosswalk: cfg.crosswalk,
          group,
          baseX: cfg.baseX + (pIdx === 0 ? -1.5 : 1.5),
          baseZ: cfg.baseZ + (pIdx === 0 ? -0.8 : 0.8),
          walkAxis: cfg.walkAxis,
          color: col,
        });
      });
    });
  }

  /**
   * Create stylized low-poly human figure (head, torso, legs)
   */
  private createPedestrianFigure(clothingColor: number): THREE.Group {
    const figure = new THREE.Group();

    // Torso (Jacket/Shirt)
    const torsoGeo = new THREE.CylinderGeometry(0.18, 0.16, 0.65, 8);
    const torsoMat = new THREE.MeshStandardMaterial({ color: clothingColor, roughness: 0.8 });
    const torso = new THREE.Mesh(torsoGeo, torsoMat);
    torso.position.y = 0.95;
    torso.castShadow = true;
    figure.add(torso);

    // Head
    const headGeo = new THREE.SphereGeometry(0.12, 8, 8);
    const skinMat = new THREE.MeshStandardMaterial({ color: 0xfcd34d, roughness: 0.6 });
    const head = new THREE.Mesh(headGeo, skinMat);
    head.position.y = 1.42;
    figure.add(head);

    // Legs / Pants
    const legGeo = new THREE.CylinderGeometry(0.06, 0.06, 0.65, 6);
    const pantsMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.9 });
    const legL = new THREE.Mesh(legGeo, pantsMat);
    legL.position.set(-0.08, 0.32, 0);
    legL.castShadow = true;
    figure.add(legL);

    const legR = new THREE.Mesh(legGeo, pantsMat);
    legR.position.set(0.08, 0.32, 0);
    legR.castShadow = true;
    figure.add(legR);

    this.disposables.push(torsoGeo, torsoMat, headGeo, skinMat, legGeo, pantsMat);

    return figure;
  }

  /**
   * Synchronize 3D signal head illumination and pedestrian motion with cycle clock
   */
  public update(timeMs: number): SignalCycleSnapshot {
    const snap = this.controller.getSnapshotAtTime(timeMs);

    // 1. Update 4 Signal Poles & Heads
    for (const pole of this.poles) {
      const approachStatus = pole.approach === 'EAST_WEST' ? snap.eastWest : snap.northSouth;
      this.updateSignalHead(pole.primaryHead, approachStatus.vehicularPhase);
      this.updateSignalHead(pole.secondaryHead, approachStatus.vehicularPhase);
      this.updatePedestrianHead(pole.pedestrianHead, approachStatus.pedestrianPhase, timeMs);
    }

    // 2. Update Pedestrian Walking Animations
    for (const ped of this.pedestrians) {
      const isEW = ped.crosswalk === 'NORTH' || ped.crosswalk === 'SOUTH';
      const pedPhase = isEW ? snap.eastWest.pedestrianPhase : snap.northSouth.pedestrianPhase;

      if (pedPhase === 'WALK') {
        // Pedestrian is actively crossing zebra stripes (-5.5m to +5.5m)
        const walkCycle = ((timeMs * 0.0016) % 11) - 5.5;
        const bob = Math.abs(Math.sin(timeMs * 0.008)) * 0.06;

        if (ped.walkAxis === 'X') {
          ped.group.position.x = ped.baseX + walkCycle;
          ped.group.position.z = ped.baseZ;
          ped.group.rotation.y = walkCycle > 0 ? Math.PI / 2 : -Math.PI / 2;
        } else {
          ped.group.position.x = ped.baseX;
          ped.group.position.z = ped.baseZ + walkCycle;
          ped.group.rotation.y = walkCycle > 0 ? 0 : Math.PI;
        }
        ped.group.position.y = bob;
      } else {
        // Safe standby on sidewalk
        ped.group.position.set(ped.baseX, 0, ped.baseZ);
      }
    }

    return snap;
  }

  /**
   * Update emissive lens states for a vehicular signal head
   * Strict physical interlock: ONLY the active color illuminates!
   */
  private updateSignalHead(head: SignalHeadBundle, targetColor: SignalLightColor): void {
    if (head.currentLit === targetColor) return;

    // Reset all 3 lenses to unlit dark glass
    head.redMat.emissive.setHex(0x000000);
    head.redMat.emissiveIntensity = 0.0;
    head.redMat.color.setHex(0x330005);

    head.yellowMat.emissive.setHex(0x000000);
    head.yellowMat.emissiveIntensity = 0.0;
    head.yellowMat.color.setHex(0x332b00);

    head.greenMat.emissive.setHex(0x000000);
    head.greenMat.emissiveIntensity = 0.0;
    head.greenMat.color.setHex(0x003314);

    // Illuminate strictly one target lens
    if (targetColor === 'red') {
      head.redMat.emissive.setHex(0xff0033);
      head.redMat.emissiveIntensity = 2.8;
      head.redMat.color.setHex(0xff1744);
    } else if (targetColor === 'yellow') {
      head.yellowMat.emissive.setHex(0xffb300);
      head.yellowMat.emissiveIntensity = 2.8;
      head.yellowMat.color.setHex(0xffea00);
    } else if (targetColor === 'green') {
      head.greenMat.emissive.setHex(0x00c853);
      head.greenMat.emissiveIntensity = 3.0;
      head.greenMat.color.setHex(0x00e676);
    }

    head.currentLit = targetColor;
  }

  /**
   * Update emissive lens states for a pedestrian crosswalk signal head
   */
  private updatePedestrianHead(head: PedestrianHeadBundle, phase: PedestrianPhase, timeMs: number): void {
    head.dontWalkMat.emissive.setHex(0x000000);
    head.dontWalkMat.emissiveIntensity = 0.0;
    head.walkMat.emissive.setHex(0x000000);
    head.walkMat.emissiveIntensity = 0.0;

    if (phase === 'WALK') {
      head.walkMat.emissive.setHex(0x00c853);
      head.walkMat.emissiveIntensity = 2.5;
      head.walkMat.color.setHex(0x00e676);
    } else if (phase === 'FLASHING') {
      // Flashing clearance hand
      const isFlashOn = Math.floor(timeMs / 400) % 2 === 0;
      if (isFlashOn) {
        head.dontWalkMat.emissive.setHex(0xff0033);
        head.dontWalkMat.emissiveIntensity = 2.5;
        head.dontWalkMat.color.setHex(0xff1744);
      }
    } else {
      // Solid Don't Walk Red hand
      head.dontWalkMat.emissive.setHex(0xff0033);
      head.dontWalkMat.emissiveIntensity = 2.5;
      head.dontWalkMat.color.setHex(0xff1744);
    }

    head.currentLit = phase;
  }

  /**
   * Raycast inspection for Signal Poles
   */
  public findSignalPoleByIntersection(intersects: THREE.Intersection[], timeMs: number): InspectedSignalPole | null {
    const snap = this.controller.getSnapshotAtTime(timeMs);

    for (const hit of intersects) {
      let obj: THREE.Object3D | null = hit.object;
      while (obj && obj !== this.group) {
        if (obj.userData && obj.userData.isSignalPole) {
          const poleId = obj.userData.poleId as string;
          const approach = obj.userData.approach as 'EAST_WEST' | 'NORTH_SOUTH';
          const approachStatus = approach === 'EAST_WEST' ? snap.eastWest : snap.northSouth;

          return {
            poleId,
            approachName: approachStatus.name,
            vehicularPhase: approachStatus.vehicularPhase,
            pedestrianPhase: approachStatus.pedestrianPhase,
            countdownSec: approachStatus.countdownSec,
            nextPhase: snap.nextPhaseName,
            conflictFreeStatus: snap.conflictFreeVerified ? 'CONFLICT_FREE_VERIFIED' : 'SAFETY_FAULT',
            provenance: snap.provenance,
            timestamp: timeMs,
          };
        }
        obj = obj.parent;
      }
    }
    return null;
  }

  public setSignalsVisibility(visible: boolean): void {
    this.signalsGroup.visible = visible;
  }

  public setPedestriansVisibility(visible: boolean): void {
    this.pedestriansGroup.visible = visible;
  }

  public dispose(): void {
    this.disposables.forEach((item) => {
      try {
        item.dispose();
      } catch (e) {
        // Ignore
      }
    });
    this.poles = [];
    this.pedestrians = [];
  }
}
