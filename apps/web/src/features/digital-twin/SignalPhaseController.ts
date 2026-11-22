import { SignalState, SignalApproachTiming, DataProvenance } from '@clearway/shared';

export type SignalLightColor = 'red' | 'yellow' | 'green';
export type PedestrianPhase = 'WALK' | 'FLASHING' | 'DONT_WALK';

export interface ApproachSignalStatus {
  approachId: 'EAST_WEST' | 'NORTH_SOUTH';
  name: string;
  vehicularPhase: SignalLightColor;
  pedestrianPhase: PedestrianPhase;
  countdownSec: number;
  phaseDurationSec: number;
}

export interface SignalCycleSnapshot {
  cycleTimeSec: number;
  currentPhaseName: string;
  nextPhaseName: string;
  timeToNextPhaseSec: number;
  eastWest: ApproachSignalStatus;
  northSouth: ApproachSignalStatus;
  conflictFreeVerified: boolean;
  provenance: DataProvenance;
  timestamp: number;
}

/**
 * SignalPhaseController governs the 60-second NEMA-standard multi-phase signal sequence
 * for intersection INT-0457 with strict conflict-free safety validation,
 * green minimum constraints, yellow change intervals, all-red clearance intervals,
 * and synchronized pedestrian walk logic.
 */
export class SignalPhaseController {
  public readonly cycleTotalSec = 60;
  public readonly provenance: DataProvenance = 'DEMO_FIXTURE';

  // Timing parameters
  private readonly EW_GREEN_END = 25; // 0s - 25s (25s Green)
  private readonly EW_YELLOW_END = 28; // 25s - 28s (3s Yellow)
  private readonly ALL_RED_1_END = 30; // 28s - 30s (2s All-Red Clearance)
  private readonly NS_GREEN_END = 55; // 30s - 55s (25s Green)
  private readonly NS_YELLOW_END = 58; // 55s - 58s (3s Yellow)
  private readonly ALL_RED_2_END = 60; // 58s - 60s (2s All-Red Clearance)

  /**
   * Safety Conflict Matrix Validator
   * Asserts that conflicting vehicular approaches are NEVER green or yellow simultaneously.
   */
  public validateConflictFree(ew: SignalLightColor, ns: SignalLightColor): boolean {
    if ((ew === 'green' || ew === 'yellow') && (ns === 'green' || ns === 'yellow')) {
      return false; // Critical Safety Violation: Concurrent conflicting rights-of-way
    }
    return true;
  }

  /**
   * Evaluate exact signal status across both approaches at any simulation time
   */
  public getSnapshotAtTime(timeMs: number): SignalCycleSnapshot {
    const cycleTimeSec = (timeMs / 1000) % this.cycleTotalSec;
    let ewColor: SignalLightColor = 'red';
    let nsColor: SignalLightColor = 'red';
    let ewPed: PedestrianPhase = 'DONT_WALK';
    let nsPed: PedestrianPhase = 'DONT_WALK';
    let currentPhaseName = '';
    let nextPhaseName = '';
    let timeToNextPhase = 0;
    let ewCountdown = 0;
    let nsCountdown = 0;
    let ewDuration = 0;
    let nsDuration = 0;

    if (cycleTimeSec < this.EW_GREEN_END) {
      // Phase 1: East-West Green (25s) | North-South Red
      ewColor = 'green';
      nsColor = 'red';
      ewPed = cycleTimeSec < 20 ? 'WALK' : 'FLASHING';
      nsPed = 'DONT_WALK';
      currentPhaseName = 'PHASE_1_EW_GREEN';
      nextPhaseName = 'PHASE_2_EW_YELLOW';
      timeToNextPhase = this.EW_GREEN_END - cycleTimeSec;
      ewCountdown = Math.ceil(this.EW_GREEN_END - cycleTimeSec);
      nsCountdown = Math.ceil(this.ALL_RED_1_END - cycleTimeSec);
      ewDuration = 25;
      nsDuration = 30;
    } else if (cycleTimeSec < this.EW_YELLOW_END) {
      // Phase 2: East-West Yellow (3s) | North-South Red
      ewColor = 'yellow';
      nsColor = 'red';
      ewPed = 'DONT_WALK';
      nsPed = 'DONT_WALK';
      currentPhaseName = 'PHASE_2_EW_YELLOW';
      nextPhaseName = 'PHASE_3_ALL_RED_CLEARANCE';
      timeToNextPhase = this.EW_YELLOW_END - cycleTimeSec;
      ewCountdown = Math.ceil(this.EW_YELLOW_END - cycleTimeSec);
      nsCountdown = Math.ceil(this.ALL_RED_1_END - cycleTimeSec);
      ewDuration = 3;
      nsDuration = 30;
    } else if (cycleTimeSec < this.ALL_RED_1_END) {
      // Phase 3: All-Red Clearance Interval (2s)
      ewColor = 'red';
      nsColor = 'red';
      ewPed = 'DONT_WALK';
      nsPed = 'DONT_WALK';
      currentPhaseName = 'PHASE_3_ALL_RED_CLEARANCE';
      nextPhaseName = 'PHASE_4_NS_GREEN';
      timeToNextPhase = this.ALL_RED_1_END - cycleTimeSec;
      ewCountdown = Math.ceil(this.ALL_RED_2_END - cycleTimeSec);
      nsCountdown = Math.ceil(this.ALL_RED_1_END - cycleTimeSec);
      ewDuration = 32;
      nsDuration = 2;
    } else if (cycleTimeSec < this.NS_GREEN_END) {
      // Phase 4: North-South Green (25s) | East-West Red
      ewColor = 'red';
      nsColor = 'green';
      ewPed = 'DONT_WALK';
      nsPed = cycleTimeSec < 50 ? 'WALK' : 'FLASHING';
      currentPhaseName = 'PHASE_4_NS_GREEN';
      nextPhaseName = 'PHASE_5_NS_YELLOW';
      timeToNextPhase = this.NS_GREEN_END - cycleTimeSec;
      ewCountdown = Math.ceil(this.ALL_RED_2_END - cycleTimeSec);
      nsCountdown = Math.ceil(this.NS_GREEN_END - cycleTimeSec);
      ewDuration = 30;
      nsDuration = 25;
    } else if (cycleTimeSec < this.NS_YELLOW_END) {
      // Phase 5: North-South Yellow (3s) | East-West Red
      ewColor = 'red';
      nsColor = 'yellow';
      ewPed = 'DONT_WALK';
      nsPed = 'DONT_WALK';
      currentPhaseName = 'PHASE_5_NS_YELLOW';
      nextPhaseName = 'PHASE_6_ALL_RED_CLEARANCE';
      timeToNextPhase = this.NS_YELLOW_END - cycleTimeSec;
      ewCountdown = Math.ceil(this.ALL_RED_2_END - cycleTimeSec);
      nsCountdown = Math.ceil(this.NS_YELLOW_END - cycleTimeSec);
      ewDuration = 30;
      nsDuration = 3;
    } else {
      // Phase 6: All-Red Clearance Interval (2s)
      ewColor = 'red';
      nsColor = 'red';
      ewPed = 'DONT_WALK';
      nsPed = 'DONT_WALK';
      currentPhaseName = 'PHASE_6_ALL_RED_CLEARANCE';
      nextPhaseName = 'PHASE_1_EW_GREEN';
      timeToNextPhase = this.ALL_RED_2_END - cycleTimeSec;
      ewCountdown = Math.ceil(this.ALL_RED_2_END - cycleTimeSec);
      nsCountdown = Math.ceil(this.cycleTotalSec + this.ALL_RED_1_END - cycleTimeSec);
      ewDuration = 2;
      nsDuration = 32;
    }

    // Safety Interlock Validation
    const isConflictFree = this.validateConflictFree(ewColor, nsColor);
    if (!isConflictFree) {
      // Fail-safe fallback to All-Red
      ewColor = 'red';
      nsColor = 'red';
      ewPed = 'DONT_WALK';
      nsPed = 'DONT_WALK';
      currentPhaseName = 'FAILSAFE_ALL_RED';
    }

    return {
      cycleTimeSec: Math.round(cycleTimeSec * 10) / 10,
      currentPhaseName,
      nextPhaseName,
      timeToNextPhaseSec: Math.round(timeToNextPhase * 10) / 10,
      conflictFreeVerified: isConflictFree,
      provenance: this.provenance,
      timestamp: timeMs,
      eastWest: {
        approachId: 'EAST_WEST',
        name: '5th Ave (EB/WB Corridor)',
        vehicularPhase: ewColor,
        pedestrianPhase: ewPed,
        countdownSec: Math.max(1, ewCountdown),
        phaseDurationSec: ewDuration,
      },
      northSouth: {
        approachId: 'NORTH_SOUTH',
        name: 'Oak St (NB/SB Arterial)',
        vehicularPhase: nsColor,
        pedestrianPhase: nsPed,
        countdownSec: Math.max(1, nsCountdown),
        phaseDurationSec: nsDuration,
      },
    };
  }

  /**
   * Convert to shared domain SignalState contract
   */
  public toSharedSignalState(timeMs: number): SignalState {
    const snap = this.getSnapshotAtTime(timeMs);

    const approaches: SignalApproachTiming[] = [
      {
        approach: '5th Ave Eastbound (EB)',
        red_s: 32,
        yellow_s: 3,
        green_s: 25,
        cycle_s: 60,
        split_pct: 42,
        current_phase: snap.eastWest.vehicularPhase,
      },
      {
        approach: '5th Ave Westbound (WB)',
        red_s: 32,
        yellow_s: 3,
        green_s: 25,
        cycle_s: 60,
        split_pct: 42,
        current_phase: snap.eastWest.vehicularPhase,
      },
      {
        approach: 'Oak St Northbound (NB)',
        red_s: 32,
        yellow_s: 3,
        green_s: 25,
        cycle_s: 60,
        split_pct: 42,
        current_phase: snap.northSouth.vehicularPhase,
      },
      {
        approach: 'Oak St Southbound (SB)',
        red_s: 32,
        yellow_s: 3,
        green_s: 25,
        cycle_s: 60,
        split_pct: 42,
        current_phase: snap.northSouth.vehicularPhase,
      },
    ];

    return {
      intersection_id: 'INT-0457',
      intersection_name: 'Oak St & 5th Ave',
      cycle_time_s: this.cycleTotalSec,
      current_phase_name: snap.currentPhaseName,
      next_phase_name: snap.nextPhaseName,
      approaches,
      provenance: this.provenance,
    };
  }
}
