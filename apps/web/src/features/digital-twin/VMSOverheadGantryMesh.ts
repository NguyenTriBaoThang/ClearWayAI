/**
 * ClearWayAI 3D Variable Message Sign (VMS) Overhead Gantry Mesh
 * (`apps/web/src/features/digital-twin/VMSOverheadGantryMesh.ts`)
 *
 * Implements realistic overhead cantilever / portal truss gantries spanning 5th Avenue (14m width):
 * - Two vertical structural steel lattice columns at z = -8.5m and z = +8.5m (height 6.5m)
 * - Overhead horizontal steel crossbeam spanning across roadway at height 5.8m (clearance 5.2m)
 * - Large electronic LED matrix display board (8.0m wide x 1.8m high x 0.35m deep)
 * - Dynamic HTML5 1024x256 Canvas Texture with bilingual advisory rendering:
 *   * Line 1: Vietnamese alert ("NHƯỜNG ĐƯỜNG XE CẤP CỨU", "ĐANG GIẢI TỎA DÒNG XE", etc.)
 *   * Line 2: English actionable command ("MERGE RIGHT >>> AMB-339", "SPEED LIMIT 50 KM/H")
 *   * High-contrast LED matrix styling with amber/red cyber glow
 * - Dual corner flashing warning strobe beacons (modulating pulse in EMERGENCY/PRE_CLEARANCE modes)
 */

import * as THREE from 'three';

export interface VMSBoardStatusInput {
  board_id: string;
  node_id: string;
  gantry_x_m: number;
  target_stopline_x: number;
  mode: 'NOMINAL' | 'PRE_CLEARANCE' | 'EMERGENCY_CORRIDOR' | 'CAUTION_RECOVERY' | string;
  message_line_1_vi: string;
  message_line_2_en: string;
  recommended_speed_kmh: number;
  flashing_strobe: boolean;
  chevron_direction: 'RIGHT' | 'NONE' | 'BOTH' | string;
  ev_distance_m?: number | null;
  ev_eta_sec?: number | null;
}

export class VMSOverheadGantryMesh {
  public group: THREE.Group;
  public readonly boardId: string;
  public readonly nodeId: string;
  public readonly gantryX: number;

  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D | null;
  private ledTexture: THREE.CanvasTexture;
  private boardMaterial: THREE.MeshBasicMaterial;
  private strobeMaterialLeft: THREE.MeshBasicMaterial;
  private strobeMaterialRight: THREE.MeshBasicMaterial;

  private lastMode: string = '';
  private lastLine1: string = '';
  private lastLine2: string = '';
  private disposables: { dispose: () => void }[] = [];

  constructor(
    boardId: string,
    nodeId: string,
    gantryX: number,
    roadWidthMeters: number = 14.0,
  ) {
    this.boardId = boardId;
    this.nodeId = nodeId;
    this.gantryX = gantryX;

    this.group = new THREE.Group();
    this.group.name = `VMSGantry_${boardId}`;
    this.group.position.set(gantryX, 0, 0);

    // 1. Create Dynamic Canvas & Texture (1024 x 256 px)
    this.canvas = document.createElement('canvas');
    this.canvas.width = 1024;
    this.canvas.height = 256;
    this.ctx = this.canvas.getContext('2d');

    this.ledTexture = new THREE.CanvasTexture(this.canvas);
    this.ledTexture.minFilter = THREE.LinearFilter;
    this.ledTexture.magFilter = THREE.LinearFilter;
    this.disposables.push(this.ledTexture);

    this.boardMaterial = new THREE.MeshBasicMaterial({
      map: this.ledTexture,
      toneMapped: false,
    });
    this.disposables.push(this.boardMaterial);

    this.strobeMaterialLeft = new THREE.MeshBasicMaterial({ color: 0xffaa00 });
    this.strobeMaterialRight = new THREE.MeshBasicMaterial({ color: 0xffaa00 });
    this.disposables.push(this.strobeMaterialLeft, this.strobeMaterialRight);

    // 2. Build 3D Steel Gantry Structure
    this.buildGantryStructure(roadWidthMeters);

    // 3. Render Initial Nominal Advisory
    this.drawCanvasAdvisory({
      board_id: boardId,
      node_id: nodeId,
      gantry_x_m: gantryX,
      target_stopline_x: gantryX + 80.0,
      mode: 'NOMINAL',
      message_line_1_vi: 'CHÚC QUÝ KHÁCH BÌNH AN',
      message_line_2_en: 'SPEED LIMIT 50 KM/H',
      recommended_speed_kmh: 50,
      flashing_strobe: false,
      chevron_direction: 'NONE',
    });
  }

  private buildGantryStructure(roadWidth: number): void {
    const columnHeight = 6.8;
    const spanZ = roadWidth / 2 + 1.8; // z = +/- 8.8m
    const steelMat = new THREE.MeshStandardMaterial({
      color: 0x333b4d,
      roughness: 0.6,
      metalness: 0.7,
    });
    this.disposables.push(steelMat);

    // Vertical Steel Columns (Left & Right of roadway)
    const colGeom = new THREE.BoxGeometry(0.5, columnHeight, 0.5);
    this.disposables.push(colGeom);

    const leftCol = new THREE.Mesh(colGeom, steelMat);
    leftCol.position.set(0, columnHeight / 2, -spanZ);
    leftCol.castShadow = true;
    this.group.add(leftCol);

    const rightCol = new THREE.Mesh(colGeom, steelMat);
    rightCol.position.set(0, columnHeight / 2, spanZ);
    rightCol.castShadow = true;
    this.group.add(rightCol);

    // Overhead Crossbeam Truss
    const beamLength = spanZ * 2 + 1.0;
    const beamGeom = new THREE.BoxGeometry(0.7, 0.8, beamLength);
    this.disposables.push(beamGeom);

    const crossbeam = new THREE.Mesh(beamGeom, steelMat);
    crossbeam.position.set(0, columnHeight - 0.4, 0);
    crossbeam.castShadow = true;
    this.group.add(crossbeam);

    // Overhead LED Display Housing Box
    const boardWidth = 8.6;
    const boardHeight = 2.1;
    const boardDepth = 0.4;
    const housingGeom = new THREE.BoxGeometry(boardDepth, boardHeight, boardWidth);
    const housingMat = new THREE.MeshStandardMaterial({
      color: 0x111622,
      roughness: 0.8,
      metalness: 0.3,
    });
    this.disposables.push(housingGeom, housingMat);

    const housing = new THREE.Mesh(housingGeom, housingMat);
    housing.position.set(0, columnHeight - 0.5, 0);
    this.group.add(housing);

    // LED Display Face (Faces Westward toward approaching traffic, heading East)
    const faceGeom = new THREE.PlaneGeometry(boardWidth - 0.2, boardHeight - 0.2);
    this.disposables.push(faceGeom);

    const displayFace = new THREE.Mesh(faceGeom, this.boardMaterial);
    // Orient face toward -X (Westbound direction, facing traffic moving Eastbound)
    displayFace.position.set(-boardDepth / 2 - 0.02, columnHeight - 0.5, 0);
    displayFace.rotation.y = -Math.PI / 2;
    this.group.add(displayFace);

    // Corner Warning Strobe Beacons
    const beaconGeom = new THREE.SphereGeometry(0.18, 12, 12);
    this.disposables.push(beaconGeom);

    const beaconLeft = new THREE.Mesh(beaconGeom, this.strobeMaterialLeft);
    beaconLeft.position.set(-boardDepth / 2 - 0.05, columnHeight + 0.6, -boardWidth / 2 + 0.4);
    this.group.add(beaconLeft);

    const beaconRight = new THREE.Mesh(beaconGeom, this.strobeMaterialRight);
    beaconRight.position.set(-boardDepth / 2 - 0.05, columnHeight + 0.6, boardWidth / 2 - 0.4);
    this.group.add(beaconRight);
  }

  /**
   * Render dynamic matrix LED pixels to HTML5 Canvas
   */
  public drawCanvasAdvisory(status: VMSBoardStatusInput): void {
    if (!this.ctx) return;
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;

    // 1. Dark Matrix Background
    ctx.fillStyle = '#060a12';
    ctx.fillRect(0, 0, w, h);

    // Subtle LED Grid Dot Pattern
    ctx.fillStyle = 'rgba(255, 255, 255, 0.04)';
    for (let x = 8; x < w; x += 16) {
      for (let y = 8; y < h; y += 16) {
        ctx.fillRect(x, y, 2, 2);
      }
    }

    // Border Glow based on Advisory Mode
    let primaryColor = '#ffb700'; // Amber (Nominal / Pre-clearance)
    let headerText = `${status.board_id} • ARTERIAL CORRIDOR ADVISORY`;
    let isEmergency = false;

    if (status.mode === 'EMERGENCY_CORRIDOR') {
      primaryColor = '#ff2b2b'; // Emergency Red
      headerText = `🚨 ${status.board_id} • CẢNH BÁO XE CẤP CỨU KHẨN CẤP / PRIORITY PREEMPTION`;
      isEmergency = true;
    } else if (status.mode === 'PRE_CLEARANCE') {
      primaryColor = '#ffaa00'; // Amber warning
      headerText = `⚡ ${status.board_id} • ĐIỀU PHỐI GIẢI TỎA DÒNG XE / PRE-CLEARANCE ACTIVE`;
    } else if (status.mode === 'CAUTION_RECOVERY') {
      primaryColor = '#00d2ff'; // Cyan recovery
      headerText = `ℹ️ ${status.board_id} • GIAO LỘ ĐANG ĐIỀU TIẾT / SMOOTH RECOVERY`;
    }

    ctx.strokeStyle = primaryColor;
    ctx.lineWidth = 6;
    ctx.strokeRect(6, 6, w - 12, h - 12);

    // 2. Header Status Strip
    ctx.fillStyle = primaryColor;
    ctx.font = 'bold 22px "Consolas", "Courier New", monospace';
    ctx.textAlign = 'left';
    ctx.fillText(headerText, 24, 38);

    // Speed Limit Badge on top right
    ctx.textAlign = 'right';
    ctx.fillText(`MAX: ${status.recommended_speed_kmh} KM/H`, w - 24, 38);

    // Divider Line
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(24, 52);
    ctx.lineTo(w - 24, 52);
    ctx.stroke();

    // 3. Line 1: Vietnamese Message (Large Bold)
    ctx.fillStyle = isEmergency ? '#ff4d4d' : '#ffc400';
    ctx.font = 'bold 50px "Segoe UI", Arial, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(status.message_line_1_vi, w / 2, 122);

    // 4. Line 2: English / Action Directive
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 44px "Consolas", monospace';
    ctx.fillText(status.message_line_2_en, w / 2, 195);

    // 5. Chevron Direction Indicators if applicable
    if (status.chevron_direction === 'RIGHT') {
      ctx.fillStyle = primaryColor;
      ctx.font = 'bold 48px monospace';
      ctx.fillText('>>>', w - 90, 195);
      ctx.fillText('>>>', 90, 195);
    }

    // Footer info
    ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
    ctx.font = '16px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('CLEARWAY AI • AUTOMATED DRIVER GUIDANCE SYSTEM', w / 2, 238);

    this.ledTexture.needsUpdate = true;
    this.lastMode = status.mode;
    this.lastLine1 = status.message_line_1_vi;
    this.lastLine2 = status.message_line_2_en;
  }

  /**
   * Update advisory state and modulate warning strobe flashers
   */
  public updateAdvisory(status: VMSBoardStatusInput, timeSec: number): void {
    // Check if canvas redraw is needed
    if (
      status.mode !== this.lastMode ||
      status.message_line_1_vi !== this.lastLine1 ||
      status.message_line_2_en !== this.lastLine2
    ) {
      this.drawCanvasAdvisory(status);
    }

    // Warning Strobe Flasher Modulation
    if (status.flashing_strobe) {
      const pulse = (Math.sin(timeSec * 10.0) + 1.0) / 2.0; // 5 Hz pulse
      const isRed = status.mode === 'EMERGENCY_CORRIDOR';
      const col = isRed ? new THREE.Color(1.0, 0.1 * pulse, 0.1 * pulse) : new THREE.Color(1.0, 0.7 * pulse, 0.0);
      this.strobeMaterialLeft.color.copy(col);
      this.strobeMaterialRight.color.copy(col);
    } else {
      this.strobeMaterialLeft.color.setHex(0x332200);
      this.strobeMaterialRight.color.setHex(0x332200);
    }
  }

  public dispose(): void {
    for (const d of this.disposables) {
      d.dispose();
    }
  }
}

