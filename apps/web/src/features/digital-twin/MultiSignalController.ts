/**
 * ClearWayAI Multi-Intersection 3D Signal Controller (`apps/web/src/features/digital-twin/MultiSignalController.ts`)
 *
 * Controls physical 3D traffic light mast poles and emissive single-lens heads across
 * all 4 intersections along the 1,000m arterial corridor (Node A, Node B, Node C, Node D).
 */

import * as THREE from 'three';
import { ARTERIAL_NODES, CorridorNodeTopology } from './MultiIntersectionRoadNetwork';

export interface NodeSignalGroup {
  nodeId: string;
  group: THREE.Group;
  ewPoles: THREE.Mesh[];
  nsPoles: THREE.Mesh[];
  ewGreenLenses: THREE.MeshBasicMaterial[];
  ewYellowLenses: THREE.MeshBasicMaterial[];
  ewRedLenses: THREE.MeshBasicMaterial[];
  nsGreenLenses: THREE.MeshBasicMaterial[];
  nsYellowLenses: THREE.MeshBasicMaterial[];
  nsRedLenses: THREE.MeshBasicMaterial[];
  currentPhase: number;
}

export class MultiSignalController {
  public group: THREE.Group;
  public nodeSignals: Map<string, NodeSignalGroup> = new Map();
  private disposables: { dispose: () => void }[] = [];

  constructor() {
    this.group = new THREE.Group();
    this.group.name = 'MultiSignalController';

    for (const node of ARTERIAL_NODES) {
      this.buildNodeSignals(node);
    }
  }

  private buildNodeSignals(node: CorridorNodeTopology): void {
    const nodeGroup = new THREE.Group();
    nodeGroup.name = `Signals_${node.id}`;

    const poleMat = new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.85, roughness: 0.3 });
    const housingMat = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.8 });
    this.disposables.push(poleMat, housingMat);

    const ewGreenLenses: THREE.MeshBasicMaterial[] = [];
    const ewYellowLenses: THREE.MeshBasicMaterial[] = [];
    const ewRedLenses: THREE.MeshBasicMaterial[] = [];
    const nsGreenLenses: THREE.MeshBasicMaterial[] = [];
    const nsYellowLenses: THREE.MeshBasicMaterial[] = [];
    const nsRedLenses: THREE.MeshBasicMaterial[] = [];

    // 4 Mast Poles per Intersection: NE, NW, SE, SW
    const poleOffsets = [
      { x: 9.5, z: -9.5, isEW: true },  // NE
      { x: -9.5, z: -9.5, isEW: false }, // NW
      { x: -9.5, z: 9.5, isEW: true },   // SW
      { x: 9.5, z: 9.5, isEW: false },   // SE
    ];

    for (const offset of poleOffsets) {
      const poleX = node.xMeters + offset.x;
      const poleZ = node.zMeters + offset.z;

      // Vertical Mast
      const mastGeo = new THREE.CylinderGeometry(0.12, 0.16, 6.5, 12);
      const mast = new THREE.Mesh(mastGeo, poleMat);
      mast.position.set(poleX, 3.25, poleZ);
      nodeGroup.add(mast);

      // Horizontal Mast Arm
      const armGeo = new THREE.CylinderGeometry(0.08, 0.08, 5.0, 8);
      const arm = new THREE.Mesh(armGeo, poleMat);
      arm.rotation.z = Math.PI / 2;
      arm.position.set(poleX - (offset.x > 0 ? 2.5 : -2.5), 6.2, poleZ);
      nodeGroup.add(arm);

      // 3-Lens Signal Head Housing
      const headGeo = new THREE.BoxGeometry(0.5, 1.4, 0.4);
      const head = new THREE.Mesh(headGeo, housingMat);
      head.position.set(poleX - (offset.x > 0 ? 3.5 : -3.5), 5.6, poleZ);
      nodeGroup.add(head);

      // Lenses: Red (top), Yellow (mid), Green (bot)
      const redMat = new THREE.MeshBasicMaterial({ color: 0xef476f });
      const yellowMat = new THREE.MeshBasicMaterial({ color: 0x475569 }); // dark when off
      const greenMat = new THREE.MeshBasicMaterial({ color: 0x06d6a0 });
      this.disposables.push(redMat, yellowMat, greenMat);

      const lensGeo = new THREE.CircleGeometry(0.16, 16);

      const redLens = new THREE.Mesh(lensGeo, redMat);
      redLens.position.set(head.position.x, 6.0, head.position.z + 0.21);
      nodeGroup.add(redLens);

      const yellowLens = new THREE.Mesh(lensGeo, yellowMat);
      yellowLens.position.set(head.position.x, 5.6, head.position.z + 0.21);
      nodeGroup.add(yellowLens);

      const greenLens = new THREE.Mesh(lensGeo, greenMat);
      greenLens.position.set(head.position.x, 5.2, head.position.z + 0.21);
      nodeGroup.add(greenLens);

      if (offset.isEW) {
        ewGreenLenses.push(greenMat);
        ewYellowLenses.push(yellowMat);
        ewRedLenses.push(redMat);
      } else {
        nsGreenLenses.push(greenMat);
        nsYellowLenses.push(yellowMat);
        nsRedLenses.push(redMat);
      }
    }

    this.nodeSignals.set(node.id, {
      nodeId: node.id,
      group: nodeGroup,
      ewPoles: [],
      nsPoles: [],
      ewGreenLenses,
      ewYellowLenses,
      ewRedLenses,
      nsGreenLenses,
      nsYellowLenses,
      nsRedLenses,
      currentPhase: 0,
    });

    this.group.add(nodeGroup);
    // Initialize Node A–D to Phase 0 (Eastbound Green)
    this.setNodePhase(node.id, 0);
  }

  /**
   * Sets phase for an individual intersection node:
   * 0: EW Green, NS Red
   * 1: EW Yellow, NS Red
   * 2: All Red
   * 3: NS Green, EW Red
   * 4: NS Yellow, EW Red
   * 5: All Red
   */
  public setNodePhase(nodeId: string, phase: number): void {
    const nodeSignal = this.nodeSignals.get(nodeId);
    if (!nodeSignal) return;

    nodeSignal.currentPhase = phase;

    const litRed = 0xef476f;
    const litYellow = 0xffd166;
    const litGreen = 0x06d6a0;
    const darkColor = 0x1e293b;

    if (phase === 0) {
      // EW Green, NS Red
      nodeSignal.ewGreenLenses.forEach((m) => m.color.setHex(litGreen));
      nodeSignal.ewYellowLenses.forEach((m) => m.color.setHex(darkColor));
      nodeSignal.ewRedLenses.forEach((m) => m.color.setHex(darkColor));

      nodeSignal.nsGreenLenses.forEach((m) => m.color.setHex(darkColor));
      nodeSignal.nsYellowLenses.forEach((m) => m.color.setHex(darkColor));
      nodeSignal.nsRedLenses.forEach((m) => m.color.setHex(litRed));
    } else if (phase === 1) {
      // EW Yellow, NS Red
      nodeSignal.ewGreenLenses.forEach((m) => m.color.setHex(darkColor));
      nodeSignal.ewYellowLenses.forEach((m) => m.color.setHex(litYellow));
      nodeSignal.ewRedLenses.forEach((m) => m.color.setHex(darkColor));

      nodeSignal.nsGreenLenses.forEach((m) => m.color.setHex(darkColor));
      nodeSignal.nsYellowLenses.forEach((m) => m.color.setHex(darkColor));
      nodeSignal.nsRedLenses.forEach((m) => m.color.setHex(litRed));
    } else if (phase === 3) {
      // NS Green, EW Red
      nodeSignal.ewGreenLenses.forEach((m) => m.color.setHex(darkColor));
      nodeSignal.ewYellowLenses.forEach((m) => m.color.setHex(darkColor));
      nodeSignal.ewRedLenses.forEach((m) => m.color.setHex(litRed));

      nodeSignal.nsGreenLenses.forEach((m) => m.color.setHex(litGreen));
      nodeSignal.nsYellowLenses.forEach((m) => m.color.setHex(darkColor));
      nodeSignal.nsRedLenses.forEach((m) => m.color.setHex(darkColor));
    } else if (phase === 4) {
      // NS Yellow, EW Red
      nodeSignal.ewGreenLenses.forEach((m) => m.color.setHex(darkColor));
      nodeSignal.ewYellowLenses.forEach((m) => m.color.setHex(darkColor));
      nodeSignal.ewRedLenses.forEach((m) => m.color.setHex(litRed));

      nodeSignal.nsGreenLenses.forEach((m) => m.color.setHex(darkColor));
      nodeSignal.nsYellowLenses.forEach((m) => m.color.setHex(litYellow));
      nodeSignal.nsRedLenses.forEach((m) => m.color.setHex(darkColor));
    } else {
      // All-Red (phase 2 or 5)
      nodeSignal.ewGreenLenses.forEach((m) => m.color.setHex(darkColor));
      nodeSignal.ewYellowLenses.forEach((m) => m.color.setHex(darkColor));
      nodeSignal.ewRedLenses.forEach((m) => m.color.setHex(litRed));

      nodeSignal.nsGreenLenses.forEach((m) => m.color.setHex(darkColor));
      nodeSignal.nsYellowLenses.forEach((m) => m.color.setHex(darkColor));
      nodeSignal.nsRedLenses.forEach((m) => m.color.setHex(litRed));
    }
  }

  public update(timeMs: number): void {
    // Dynamic lens pulsing or countdown indicators if needed
    // Default maintains setNodePhase state
  }

  public setSignalsVisibility(visible: boolean): void {
    this.group.visible = visible;
  }

  public dispose(): void {
    for (const d of this.disposables) {
      d.dispose();
    }
  }
}
