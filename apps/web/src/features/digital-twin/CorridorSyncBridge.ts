/**
 * ClearWayAI - SUMO-to-3D Corridor Synchronization Bridge (`CorridorSyncBridge.ts`)
 *
 * Bridges live simulation telemetry (WebSocket snapshots and REST step responses)
 * with the 3D WebGL Digital Twin scene:
 * 1. Synchronizes 3D mixed vehicle motion along the 1,000m arterial corridor (Nodes A–D)
 * 2. Synchronizes 16 physical signal poles (EW Green, Yellow, All-Red, NS Green)
 * 3. Enforces real-time emergency preemption green waves for AMB-339
 * 4. Animates dynamic 3D corridor ribbon, chevron flow, and billboard telemetry callout
 * 5. Provides seamless automatic failover from live SUMO streaming to deterministic fixture
 */

import * as THREE from 'three';
import { SceneEnvironment } from './SceneEnvironment';
import { SumoTrajectorySource, SumoTelemetrySnapshotInput } from './SumoTrajectorySource';
import { VehicleSnapshotFixture } from './VehicleSnapshotFixture';
import { CorridorMode, CorridorNodeStatus } from './CorridorOverlay3D';

export type SyncMode = 'LIVE_SUMO' | 'DEMO_FIXTURE';
export type SyncStatus = 'SYNCED' | 'INTERPOLATING' | 'FALLBACK_FIXTURE';

export interface SyncTelemetry {
  mode: SyncMode;
  status: SyncStatus;
  activeVehiclesCount: number;
  simTimeSec: number;
  lastPacketAgeMs: number;
  preemptionActive: boolean;
  activeNodePhases: Record<string, number>;
}

export class CorridorSyncBridge {
  public environment: SceneEnvironment;
  public sumoSource: SumoTrajectorySource;
  public fixtureSource: VehicleSnapshotFixture;

  public syncMode: SyncMode = 'LIVE_SUMO';
  public lastSnapshotWallTimeMs: number = 0;
  private readonly FALLBACK_TIMEOUT_MS: number = 3500;

  constructor(environment: SceneEnvironment) {
    this.environment = environment;
    this.sumoSource = new SumoTrajectorySource();
    this.fixtureSource = new VehicleSnapshotFixture();

    // Default to SumoTrajectorySource for live synchronization
    this.applyTrajectorySource(this.syncMode);
  }

  /**
   * Set operational synchronization mode ('LIVE_SUMO' or 'DEMO_FIXTURE')
   */
  public setSyncMode(mode: SyncMode): void {
    if (this.syncMode === mode) return;
    this.syncMode = mode;
    this.applyTrajectorySource(mode);
  }

  /**
   * Toggle between live SUMO synchronization and local demo fixture
   */
  public toggleSyncMode(): SyncMode {
    const nextMode: SyncMode = this.syncMode === 'LIVE_SUMO' ? 'DEMO_FIXTURE' : 'LIVE_SUMO';
    this.setSyncMode(nextMode);
    return nextMode;
  }

  private applyTrajectorySource(mode: SyncMode): void {
    if (!this.environment.vehicleManager) return;

    if (mode === 'LIVE_SUMO') {
      this.environment.vehicleManager.motionSystem.setTrajectorySource(this.sumoSource);
    } else {
      this.environment.vehicleManager.motionSystem.setTrajectorySource(this.fixtureSource);
    }
  }

  /**
   * Ingest live telemetry snapshot from WebSocket or REST simulation engine
   */
  public ingestSnapshot(snapshot: SumoTelemetrySnapshotInput | any): void {
    if (!snapshot) return;

    const wallNow = typeof performance !== 'undefined' ? performance.now() : Date.now();
    this.lastSnapshotWallTimeMs = wallNow;

    // 1. Ingest into SumoTrajectorySource
    this.sumoSource.ingestTelemetrySnapshot(snapshot);

    // 2. Synchronize 16 Physical Traffic Signal Poles across Nodes A–D
    this.syncTrafficSignals(snapshot);

    // 3. Synchronize Emergency Preemption Corridor & Ribbon
    this.syncEmergencyCorridor(snapshot);
  }

  /**
   * Synchronize traffic light phases across all 4 corridor intersections
   */
  private syncTrafficSignals(snapshot: SumoTelemetrySnapshotInput): void {
    if (!this.environment.multiSignals) return;

    // Default phases from snapshot or current phase
    let defaultPhase = 0;
    if (snapshot.signals && typeof snapshot.signals.current_phase === 'number') {
      defaultPhase = snapshot.signals.current_phase;
    }

    const nodeIds = ['node_a', 'node_b', 'node_c', 'node_d'];

    for (const nodeId of nodeIds) {
      let phaseToApply = defaultPhase;

      if (snapshot.traffic_lights && typeof snapshot.traffic_lights[nodeId] === 'number') {
        phaseToApply = snapshot.traffic_lights[nodeId];
      }

      this.environment.multiSignals.setNodePhase(nodeId, phaseToApply);
    }
  }

  /**
   * Synchronize 3D emergency priority ribbon, chevrons, and A–D node progression
   */
  private syncEmergencyCorridor(snapshot: SumoTelemetrySnapshotInput): void {
    if (!this.environment.corridorOverlay) return;

    // Locate active ambulance
    const vehList = snapshot.vehicles || [];
    const amb = vehList.find(
      (v: any) =>
        v.is_priority_vehicle ||
        v.vehicle_id.includes('AMB') ||
        v.vehicle_class === 'emergency_ambulance'
    );

    if (amb) {
      const ambX = amb.position_x;

      // Determine corridor mode based on ambulance position along 5th Ave
      let mode: CorridorMode = 'ACTIVE';
      if (ambX >= 850) {
        mode = 'COMPLETED'; // Reached Trauma Center
      } else if (ambX < -120) {
        mode = 'PLANNED'; // Approaching West Feeder Gate
      }

      this.environment.corridorOverlay.setMode(mode);

      // Compute A–D node chain statuses dynamically
      const nodeStatuses: CorridorNodeStatus[] = [
        {
          id: 'node_a',
          name: 'Node A (Maple St - 0m)',
          status: ambX > 25 ? 'COMPLETED' : 'ACTIVE',
          etaSec: Math.max(0, Math.round((0 - ambX) / Math.max(1, amb.speed_kmh / 3.6))),
          phaseWindow: ambX > 25 ? 'CLEARED' : 'PREEMPTION_GREEN',
        },
        {
          id: 'node_b',
          name: 'Node B (Oak St - 250m)',
          status: ambX > 275 ? 'COMPLETED' : ambX >= 0 ? 'ACTIVE' : 'PLANNED',
          etaSec: Math.max(0, Math.round((250 - ambX) / Math.max(1, amb.speed_kmh / 3.6))),
          phaseWindow: ambX > 275 ? 'CLEARED' : ambX >= 0 ? 'PREEMPTION_GREEN' : 'WINDOW_RESERVED',
        },
        {
          id: 'node_c',
          name: 'Node C (Pine St - 500m)',
          status: ambX > 525 ? 'COMPLETED' : ambX >= 250 ? 'ACTIVE' : 'PLANNED',
          etaSec: Math.max(0, Math.round((500 - ambX) / Math.max(1, amb.speed_kmh / 3.6))),
          phaseWindow: ambX > 525 ? 'CLEARED' : ambX >= 250 ? 'PREEMPTION_GREEN' : 'WINDOW_RESERVED',
        },
        {
          id: 'node_d',
          name: 'Node D (Elm St - 750m)',
          status: ambX > 775 ? 'COMPLETED' : ambX >= 500 ? 'ACTIVE' : 'PLANNED',
          etaSec: Math.max(0, Math.round((750 - ambX) / Math.max(1, amb.speed_kmh / 3.6))),
          phaseWindow: ambX > 775 ? 'CLEARED' : ambX >= 500 ? 'PREEMPTION_GREEN' : 'WINDOW_RESERVED',
        },
      ];

      // If preemption is active at an approaching intersection, enforce green hold in 3D
      if (this.environment.multiSignals && mode === 'ACTIVE') {
        if (ambX >= -100 && ambX <= 30) this.environment.multiSignals.setNodePhase('node_a', 0);
        if (ambX >= 150 && ambX <= 280) this.environment.multiSignals.setNodePhase('node_b', 0);
        if (ambX >= 400 && ambX <= 530) this.environment.multiSignals.setNodePhase('node_c', 0);
        if (ambX >= 650 && ambX <= 780) this.environment.multiSignals.setNodePhase('node_d', 0);
      }
    }
  }

  /**
   * Update dynamic frame ticks and execute failover watchdog
   */
  public update(timeMs: number): void {
    const wallNow = typeof performance !== 'undefined' ? performance.now() : Date.now();
    const packetAgeMs = this.lastSnapshotWallTimeMs > 0 ? wallNow - this.lastSnapshotWallTimeMs : Infinity;

    // Failover watchdog: if in LIVE_SUMO and packet stream is dead for > 3.5s, fallback to fixture
    if (this.syncMode === 'LIVE_SUMO') {
      if (packetAgeMs > this.FALLBACK_TIMEOUT_MS && this.lastSnapshotWallTimeMs > 0) {
        // Fallback transparently to deterministic fixture
        if (this.environment.vehicleManager.motionSystem.trajectorySource !== this.fixtureSource) {
          this.environment.vehicleManager.motionSystem.setTrajectorySource(this.fixtureSource);
        }
      } else {
        // Normal live sync: ensure SumoTrajectorySource is active
        if (this.environment.vehicleManager.motionSystem.trajectorySource !== this.sumoSource) {
          this.environment.vehicleManager.motionSystem.setTrajectorySource(this.sumoSource);
        }
      }
    }
  }

  /**
   * Return live telemetry diagnostics for HUD overlay
   */
  public getTelemetry(): SyncTelemetry {
    const wallNow = typeof performance !== 'undefined' ? performance.now() : Date.now();
    const packetAgeMs = this.lastSnapshotWallTimeMs > 0 ? Math.round(wallNow - this.lastSnapshotWallTimeMs) : 0;

    let status: SyncStatus = 'SYNCED';
    if (this.syncMode === 'DEMO_FIXTURE') {
      status = 'FALLBACK_FIXTURE';
    } else if (packetAgeMs > this.FALLBACK_TIMEOUT_MS) {
      status = 'FALLBACK_FIXTURE';
    } else if (packetAgeMs > 600) {
      status = 'INTERPOLATING';
    }

    const phasesObj: Record<string, number> = {};
    for (const [k, v] of this.sumoSource.nodePhases.entries()) {
      phasesObj[k] = v;
    }

    const count = this.syncMode === 'LIVE_SUMO'
      ? this.sumoSource.getActiveVehicleCount()
      : this.environment.vehicleManager.vehicles.size;

    return {
      mode: this.syncMode,
      status,
      activeVehiclesCount: count,
      simTimeSec: this.sumoSource.latestSimTimeSec,
      lastPacketAgeMs: packetAgeMs,
      preemptionActive: Boolean(this.sumoSource.activeMission),
      activeNodePhases: phasesObj,
    };
  }

  public dispose(): void {
    this.sumoSource.reset();
  }
}

