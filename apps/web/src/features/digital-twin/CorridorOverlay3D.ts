import * as THREE from 'three';
import { DataProvenance } from '@clearway/shared';

export type CorridorMode = 'PLANNED' | 'ACTIVE' | 'COMPLETED' | 'BLOCKED';

export interface CorridorNodeStatus {
  id: string;
  name: string;
  status: 'PLANNED' | 'ACTIVE' | 'COMPLETED';
  etaSec: number;
  phaseWindow: string;
}

export interface CorridorPlanTelemetry {
  corridorId: string;
  missionId: string;
  mode: CorridorMode;
  targetVehicleId: string;
  nodes: CorridorNodeStatus[];
  clearanceDistanceM: number;
  preemptionLeadSec: number;
  reason: string;
  provenance: DataProvenance;
  timestamp: number;
}

/**
 * CorridorOverlay3D renders the 3D dynamic emergency corridor:
 * - Thick curved route ribbon with animated neon chevrons along 5th Ave
 * - Mode-driven styling: PLANNED (cyan/blue), ACTIVE (pulsing teal/cyan wave),
 *   COMPLETED (emerald green), BLOCKED (red hazard warning hatching)
 * - 3D dynamic floating callout sprite anchored above AMB-339
 * - Interactive raycast inspection with full A–D multi-intersection node chain
 */
export class CorridorOverlay3D {
  public group: THREE.Group;
  public ribbonMesh: THREE.Mesh;
  public borderLines: THREE.LineSegments;
  public chevronsGroup: THREE.Group;
  public calloutSprite: THREE.Sprite;

  public mode: CorridorMode = 'ACTIVE';
  public showCallouts: boolean = true;
  public provenance: DataProvenance = 'DEMO_FIXTURE';

  private ribbonMat: THREE.MeshStandardMaterial;
  private borderMat: THREE.LineBasicMaterial;
  private chevronMat: THREE.MeshBasicMaterial;
  private calloutCanvas: HTMLCanvasElement;
  private calloutTexture: THREE.CanvasTexture;
  private disposables: { dispose: () => void }[] = [];

  constructor() {
    this.group = new THREE.Group();
    this.group.name = 'CorridorOverlay3D';

    // 1. Thick 3D Emergency Route Ribbon (80m length along East-West, 3.8m wide)
    const ribbonGeo = new THREE.PlaneGeometry(80, 3.8, 40, 1);
    this.ribbonMat = new THREE.MeshStandardMaterial({
      color: 0x00f5d4,
      emissive: 0x00e5ff,
      emissiveIntensity: 0.6,
      transparent: true,
      opacity: 0.35,
      side: THREE.DoubleSide,
      roughness: 0.2,
      metalness: 0.1,
      polygonOffset: true,
      polygonOffsetFactor: -2,
      polygonOffsetUnits: -2,
    });
    this.ribbonMesh = new THREE.Mesh(ribbonGeo, this.ribbonMat);
    this.ribbonMesh.rotation.x = -Math.PI / 2;
    this.ribbonMesh.position.set(0, 0.042, 1.75); // Slightly raised above asphalt (y=0.042) to kill z-fighting
    this.ribbonMesh.receiveShadow = false;

    // Attach raycast inspection metadata
    this.ribbonMesh.userData = {
      isCorridor: true,
      corridorId: 'CORRIDOR-ALPHA-EAST',
    };

    this.group.add(this.ribbonMesh);
    this.disposables.push(ribbonGeo, this.ribbonMat);

    // 2. High-Visibility Pulsing Border Guide Lines
    const borderPoints: THREE.Vector3[] = [
      new THREE.Vector3(-40, 0.045, -0.15),
      new THREE.Vector3(40, 0.045, -0.15),
      new THREE.Vector3(-40, 0.045, 3.65),
      new THREE.Vector3(40, 0.045, 3.65),
    ];
    const borderGeo = new THREE.BufferGeometry().setFromPoints(borderPoints);
    this.borderMat = new THREE.LineBasicMaterial({
      color: 0x00f5d4,
      transparent: true,
      opacity: 0.9,
    });
    this.borderLines = new THREE.LineSegments(borderGeo, this.borderMat);
    this.group.add(this.borderLines);
    this.disposables.push(borderGeo, this.borderMat);

    // 3. Animated Directional Chevrons Group
    this.chevronsGroup = new THREE.Group();
    this.chevronsGroup.name = 'CorridorChevrons';
    this.chevronMat = new THREE.MeshBasicMaterial({
      color: 0x00e5ff,
      transparent: true,
      opacity: 0.85,
      side: THREE.DoubleSide,
    });
    this.disposables.push(this.chevronMat);

    this.buildChevronArrows();
    this.group.add(this.chevronsGroup);

    // 4. 3D Floating Vehicle Callout Sprite for AMB-339
    const { sprite, canvas, texture } = this.createCalloutSprite();
    this.calloutSprite = sprite;
    this.calloutCanvas = canvas;
    this.calloutTexture = texture;
    this.group.add(this.calloutSprite);
  }

  /**
   * Build chevron arrows along the corridor length
   */
  private buildChevronArrows(): void {
    // Standard chevron shape (two angled thick quad arms pointing East +X)
    const shape = new THREE.Shape();
    shape.moveTo(-0.8, -1.2);
    shape.lineTo(0.6, 0);
    shape.lineTo(-0.8, 1.2);
    shape.lineTo(-0.4, 1.2);
    shape.lineTo(1.0, 0);
    shape.lineTo(-0.4, -1.2);
    shape.closePath();

    const chevronGeo = new THREE.ShapeGeometry(shape);
    this.disposables.push(chevronGeo);

    // Place 14 chevrons evenly spaced across the 80m corridor
    for (let i = 0; i < 14; i++) {
      const mesh = new THREE.Mesh(chevronGeo, this.chevronMat);
      mesh.rotation.x = -Math.PI / 2;
      mesh.position.set(-36 + i * 5.6, 0.046, 1.75);
      mesh.scale.set(0.9, 0.9, 0.9);
      this.chevronsGroup.add(mesh);
    }
  }

  /**
   * Create high-res 2D billboard sprite for AMB-339 emergency callout
   */
  private createCalloutSprite(): {
    sprite: THREE.Sprite;
    canvas: HTMLCanvasElement;
    texture: THREE.CanvasTexture;
  } {
    const canvas = document.createElement('canvas');
    canvas.width = 320;
    canvas.height = 110;

    const texture = new THREE.CanvasTexture(canvas);
    texture.minFilter = THREE.LinearFilter;

    const spriteMat = new THREE.SpriteMaterial({
      map: texture,
      transparent: true,
      depthTest: false,
    });
    const sprite = new THREE.Sprite(spriteMat);
    sprite.scale.set(6.4, 2.2, 1);
    sprite.position.set(-18, 5.2, 1.75);

    this.disposables.push(spriteMat, texture);

    return { sprite, canvas, texture };
  }

  /**
   * Update dynamic corridor appearance, chevron scrolling, and vehicle callout
   */
  public update(timeMs: number, ambPosition?: THREE.Vector3): void {
    // 1. Update corridor styling based on operational mode
    switch (this.mode) {
      case 'ACTIVE': {
        const pulse = 0.35 + 0.15 * Math.sin(timeMs * 0.005);
        this.ribbonMat.color.setHex(0x00f5d4);
        this.ribbonMat.emissive.setHex(0x00e5ff);
        this.ribbonMat.opacity = pulse;
        this.borderMat.color.setHex(0x00f5d4);
        this.chevronMat.color.setHex(0x00e5ff);
        this.chevronMat.opacity = 0.9;
        break;
      }
      case 'PLANNED': {
        this.ribbonMat.color.setHex(0x0284c7);
        this.ribbonMat.emissive.setHex(0x0369a1);
        this.ribbonMat.opacity = 0.22;
        this.borderMat.color.setHex(0x38bdf8);
        this.chevronMat.color.setHex(0x38bdf8);
        this.chevronMat.opacity = 0.45;
        break;
      }
      case 'COMPLETED': {
        this.ribbonMat.color.setHex(0x059669);
        this.ribbonMat.emissive.setHex(0x047857);
        this.ribbonMat.opacity = 0.20;
        this.borderMat.color.setHex(0x10b981);
        this.chevronMat.color.setHex(0x10b981);
        this.chevronMat.opacity = 0.4;
        break;
      }
      case 'BLOCKED': {
        // Red hazard warning flashing
        const blink = Math.sin(timeMs * 0.008) > 0 ? 0.65 : 0.3;
        this.ribbonMat.color.setHex(0xef4444);
        this.ribbonMat.emissive.setHex(0xff1744);
        this.ribbonMat.opacity = blink;
        this.borderMat.color.setHex(0xf87171);
        this.chevronMat.color.setHex(0xf87171);
        this.chevronMat.opacity = blink;
        break;
      }
    }

    // 2. Animate Chevron Texture Scrolling along corridor
    const scrollOffset = (timeMs * 0.007) % 5.6;
    let idx = 0;
    this.chevronsGroup.children.forEach((child) => {
      const baseX = -36 + idx * 5.6;
      let newX = baseX + scrollOffset;
      if (newX > 38) newX -= 74;
      child.position.x = newX;
      idx++;
    });

    // 3. Update AMB-339 3D Callout position and contents
    if (ambPosition) {
      this.calloutSprite.position.set(ambPosition.x, 5.0, ambPosition.z);
    }

    this.calloutSprite.visible = this.showCallouts && this.mode === 'ACTIVE';
    if (this.calloutSprite.visible) {
      this.renderCalloutCanvas(timeMs, ambPosition);
    }
  }

  /**
   * Draw dynamic callout graphics on canvas
   */
  private renderCalloutCanvas(timeMs: number, ambPos?: THREE.Vector3): void {
    const ctx = this.calloutCanvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, 320, 110);

    // Dynamic ETA calculation based on distance to junction center (x=0)
    const currentX = ambPos ? ambPos.x : -18;
    const distToCenter = Math.max(0, -currentX);
    const speedMs = 17.2; // 62 km/h
    const etaSec = distToCenter > 0 ? (distToCenter / speedMs).toFixed(1) : 'PASSED';

    // Outer Callout Bubble with Cyber Glow
    ctx.fillStyle = 'rgba(7, 16, 38, 0.94)';
    ctx.beginPath();
    ctx.roundRect(4, 4, 312, 98, 8);
    ctx.fill();

    ctx.lineWidth = 2;
    ctx.strokeStyle = '#00f5d4';
    ctx.stroke();

    // Red Urgent Flashing Indicator Dot
    const dotBlink = Math.sin(timeMs * 0.01) > 0;
    ctx.fillStyle = dotBlink ? '#ff0055' : '#00f5d4';
    ctx.beginPath();
    ctx.arc(20, 24, 6, 0, Math.PI * 2);
    ctx.fill();

    // Top Header: Priority Mission Callout
    ctx.font = 'bold 15px monospace';
    ctx.fillStyle = '#f1f5f9';
    ctx.textAlign = 'left';
    ctx.fillText('AMB-339 • PREEMPTION ACTIVE', 34, 28);

    // Divider Line
    ctx.strokeStyle = '#1b325f';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(12, 40);
    ctx.lineTo(308, 40);
    ctx.stroke();

    // Sub-metrics: ETA and Corridor nodes
    ctx.font = '12px monospace';
    ctx.fillStyle = '#94a3b8';
    ctx.fillText(`ETA to INT-0457: `, 16, 62);
    ctx.fillStyle = '#06d6a0';
    ctx.font = 'bold 13px monospace';
    ctx.fillText(`${etaSec}${etaSec === 'PASSED' ? '' : 's'}`, 150, 62);

    ctx.font = '12px monospace';
    ctx.fillStyle = '#94a3b8';
    ctx.fillText(`Corridor Route: `, 16, 84);
    ctx.fillStyle = '#00e5ff';
    ctx.font = 'bold 12px monospace';
    ctx.fillText(`INT-0456 ➔ INT-0457 ➔ HOSP`, 140, 84);

    this.calloutTexture.needsUpdate = true;
  }

  /**
   * Raycast inspection: returns rich corridor telemetry when ribbon is clicked
   */
  public getCorridorTelemetry(timeMs: number): CorridorPlanTelemetry {
    return {
      corridorId: 'CORRIDOR-ALPHA-EAST',
      missionId: 'MISSION-AMB-339',
      mode: this.mode,
      targetVehicleId: 'AMB-339',
      clearanceDistanceM: 120,
      preemptionLeadSec: 18,
      reason: 'Emergency Level 1: Severe Trauma Inbound to Metropolitan General Hospital',
      provenance: this.provenance,
      timestamp: timeMs,
      nodes: [
        { id: 'INT-0456', name: 'Oak St & 4th Ave', status: 'COMPLETED', etaSec: 0, phaseWindow: 'CLEARED' },
        { id: 'INT-0457', name: 'Oak St & 5th Ave (Current)', status: 'ACTIVE', etaSec: 12.4, phaseWindow: 'PREEMPTION_GREEN' },
        { id: 'INT-0458', name: 'Oak St & 6th Ave', status: 'PLANNED', etaSec: 32.0, phaseWindow: 'WINDOW_RESERVED' },
        { id: 'INT-0459', name: 'Hospital Emergency Gate', status: 'PLANNED', etaSec: 54.0, phaseWindow: 'GATE_HOLD_OPEN' },
      ],
    };
  }

  public setMode(mode: CorridorMode): void {
    this.mode = mode;
  }

  public setVisibility(visible: boolean): void {
    this.group.visible = visible;
  }

  public setShowCallouts(show: boolean): void {
    this.showCallouts = show;
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
