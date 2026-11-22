import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

export type CameraPresetType = 'iso' | 'top' | 'close' | 'chase';
export type ProjectionMode = 'perspective' | 'orthographic';

export interface CameraStateMetrics {
  position: { x: number; y: number; z: number };
  target: { x: number; y: number; z: number };
  distance: number;
  pitchDeg: number;
  yawDeg: number;
  projection: ProjectionMode;
  preset: CameraPresetType;
  autoRotate: boolean;
}

/**
 * SceneController governs the dual camera system (Perspective & Orthographic),
 * OrbitControls, smooth transitions between camera presets, and real-time telemetry.
 */
export class SceneController {
  public domElement: HTMLElement;
  public perspectiveCamera: THREE.PerspectiveCamera;
  public orthographicCamera: THREE.OrthographicCamera;
  public activeCamera: THREE.Camera;
  public controls: OrbitControls;

  public projectionMode: ProjectionMode = 'perspective';
  public currentPreset: CameraPresetType = 'iso';
  public autoRotate: boolean = false;
  public autoRotateSpeed: number = 0.5;

  // Preset definition coordinates
  private readonly PRESETS: Record<CameraPresetType, { pos: THREE.Vector3; target: THREE.Vector3 }> = {
    iso: {
      pos: new THREE.Vector3(46, 50, 46),
      target: new THREE.Vector3(0, 0, 0),
    },
    top: {
      pos: new THREE.Vector3(0, 80, 0.01),
      target: new THREE.Vector3(0, 0, 0),
    },
    close: {
      pos: new THREE.Vector3(18, 14, 18),
      target: new THREE.Vector3(0, 1, 0),
    },
    chase: {
      pos: new THREE.Vector3(-18, 8, 10),
      target: new THREE.Vector3(-18, 0.8, 0),
    },
  };

  private targetCamPos: THREE.Vector3 = new THREE.Vector3().copy(this.PRESETS.iso.pos);
  private targetControlsTarget: THREE.Vector3 = new THREE.Vector3().copy(this.PRESETS.iso.target);
  private isTransitioning: boolean = false;
  private transitionAlpha: number = 0;

  constructor(domElement: HTMLElement, width: number, height: number) {
    this.domElement = domElement;

    // 1. Perspective Camera - Low FOV (38°) for isometric-like depth without distortion
    const aspect = width / height;
    this.perspectiveCamera = new THREE.PerspectiveCamera(38, aspect, 0.1, 1000);
    this.perspectiveCamera.position.copy(this.PRESETS.iso.pos);

    // 2. Orthographic Camera - True axonometric parallel projection
    const frustumSize = 50;
    this.orthographicCamera = new THREE.OrthographicCamera(
      (-frustumSize * aspect) / 2,
      (frustumSize * aspect) / 2,
      frustumSize / 2,
      -frustumSize / 2,
      0.1,
      1000
    );
    this.orthographicCamera.position.copy(this.PRESETS.iso.pos);
    this.orthographicCamera.zoom = 1.0;

    // Default to perspective with isometric orientation
    this.activeCamera = this.perspectiveCamera;

    // 3. OrbitControls setup
    this.controls = new OrbitControls(this.activeCamera, this.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    this.controls.enablePan = true;
    this.controls.enableZoom = true;
    this.controls.enableRotate = true;

    // Strict boundary gates: never flip camera underground
    this.controls.maxPolarAngle = Math.PI / 2.05; // ~87.7 deg
    this.controls.minDistance = 15;
    this.controls.maxDistance = 180;
    this.controls.target.copy(this.PRESETS.iso.target);
    this.controls.update();

    // Disable autoRotate if user interacts with controls
    this.controls.addEventListener('start', () => {
      this.isTransitioning = false;
    });
  }

  /**
   * Switch between Perspective and Orthographic projection modes
   */
  public setProjectionMode(mode: ProjectionMode, width: number, height: number): void {
    if (this.projectionMode === mode) return;

    const prevPos = this.activeCamera.position.clone();
    const prevTarget = this.controls.target.clone();

    this.projectionMode = mode;
    if (mode === 'orthographic') {
      this.updateOrthographicFrustum(width, height);
      this.orthographicCamera.position.copy(prevPos);
      this.activeCamera = this.orthographicCamera;
    } else {
      this.perspectiveCamera.position.copy(prevPos);
      this.activeCamera = this.perspectiveCamera;
    }

    // Rebind controls to the active camera
    this.controls.object = this.activeCamera;
    this.controls.target.copy(prevTarget);
    this.controls.update();
  }

  /**
   * Set active camera preset and initiate smooth lerp transition
   */
  public setPreset(preset: CameraPresetType): void {
    this.currentPreset = preset;
    const p = this.PRESETS[preset];
    this.targetCamPos.copy(p.pos);
    this.targetControlsTarget.copy(p.target);
    this.isTransitioning = true;
    this.transitionAlpha = 0;
  }

  /**
   * Update controller state every animation frame
   */
  public update(chaseTargetPos?: THREE.Vector3): void {
    // 1. If in Chase mode, dynamically update target position based on vehicle waypoint
    if (this.currentPreset === 'chase' && chaseTargetPos) {
      this.targetControlsTarget.copy(chaseTargetPos);
      this.targetCamPos.set(chaseTargetPos.x - 12, chaseTargetPos.y + 6, chaseTargetPos.z + 10);
      this.activeCamera.position.lerp(this.targetCamPos, 0.08);
      this.controls.target.lerp(this.targetControlsTarget, 0.08);
      this.controls.update();
      return;
    }

    // 2. Smooth Lerp transition towards preset target
    if (this.isTransitioning) {
      this.transitionAlpha += 0.04;
      this.activeCamera.position.lerp(this.targetCamPos, 0.1);
      this.controls.target.lerp(this.targetControlsTarget, 0.1);

      if (this.activeCamera.position.distanceTo(this.targetCamPos) < 0.2 && this.transitionAlpha >= 1) {
        this.activeCamera.position.copy(this.targetCamPos);
        this.controls.target.copy(this.targetControlsTarget);
        this.isTransitioning = false;
      }
    }

    // 3. Optional Turntable Auto-Rotation
    if (this.autoRotate && !this.isTransitioning) {
      this.controls.autoRotate = true;
      this.controls.autoRotateSpeed = this.autoRotateSpeed;
    } else {
      this.controls.autoRotate = false;
    }

    this.controls.update();
  }

  /**
   * Handle resize event
   */
  public handleResize(width: number, height: number): void {
    const aspect = width / height;

    // Update perspective aspect ratio
    this.perspectiveCamera.aspect = aspect;
    this.perspectiveCamera.updateProjectionMatrix();

    // Update orthographic frustum
    this.updateOrthographicFrustum(width, height);
  }

  private updateOrthographicFrustum(width: number, height: number): void {
    const aspect = width / height;
    const frustumSize = 48;
    this.orthographicCamera.left = (-frustumSize * aspect) / 2;
    this.orthographicCamera.right = (frustumSize * aspect) / 2;
    this.orthographicCamera.top = frustumSize / 2;
    this.orthographicCamera.bottom = -frustumSize / 2;
    this.orthographicCamera.updateProjectionMatrix();
  }

  /**
   * Get live telemetry metrics for HUD overlay
   */
  public getMetrics(): CameraStateMetrics {
    const pos = this.activeCamera.position;
    const target = this.controls.target;
    const distance = pos.distanceTo(target);

    // Compute Pitch (elevation angle above horizontal) & Yaw (azimuth)
    const dx = pos.x - target.x;
    const dy = pos.y - target.y;
    const dz = pos.z - target.z;
    const horizontalDist = Math.sqrt(dx * dx + dz * dz);
    const pitchDeg = Math.round(Math.atan2(dy, horizontalDist) * (180 / Math.PI));
    const yawDeg = Math.round(Math.atan2(dx, dz) * (180 / Math.PI));

    return {
      position: { x: Math.round(pos.x), y: Math.round(pos.y), z: Math.round(pos.z) },
      target: { x: Math.round(target.x), y: Math.round(target.y), z: Math.round(target.z) },
      distance: Math.round(distance),
      pitchDeg,
      yawDeg,
      projection: this.projectionMode,
      preset: this.currentPreset,
      autoRotate: this.autoRotate,
    };
  }

  public reset(): void {
    this.setPreset('iso');
  }

  public dispose(): void {
    this.controls.dispose();
  }
}

