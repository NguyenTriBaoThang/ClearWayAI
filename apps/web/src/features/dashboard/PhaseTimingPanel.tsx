import React, { useState, useEffect } from 'react';
import {
  Clock,
  Radio,
  AlertTriangle,
  Flame,
  CheckCircle,
  X,
  Sliders,
  Shield,
  Activity,
  ArrowRight,
} from 'lucide-react';
import { PanelFrame } from '../../components/PanelFrame';
import { StatusPill } from '../../components/StatusPill';
import { SignalApproachTiming, SignalState, DataProvenance } from '@clearway/shared';

export type SignalLightColor = 'red' | 'yellow' | 'green';

export interface DetailedApproachTiming extends SignalApproachTiming {
  name: string;
  direction: 'N' | 'S' | 'E' | 'W';
  nemaPhase: string;
  minGreenSec: number;
  maxGreenSec: number;
  yellowChangeSec: number;
  redClearanceSec: number;
  pedestrianWalkSec: number;
  pedestrianClearSec: number;
  detectorStatus: string;
  preemptionWeight: number;
}

const DEFAULT_APPROACHES: DetailedApproachTiming[] = [
  {
    approach: 'N - Oak St. (NB)',
    name: 'Northbound Oak Street',
    direction: 'N',
    nemaPhase: 'Phase 4 (NB Thru/Right)',
    red_s: 67,
    yellow_s: 4,
    green_s: 49,
    cycle_s: 120,
    split_pct: 41,
    current_phase: 'red',
    minGreenSec: 10,
    maxGreenSec: 55,
    yellowChangeSec: 4,
    redClearanceSec: 2,
    pedestrianWalkSec: 15,
    pedestrianClearSec: 18,
    detectorStatus: 'Loop D4-NB: Active (8 veh queue)',
    preemptionWeight: 1,
  },
  {
    approach: 'S - Oak St. (SB)',
    name: 'Southbound Oak Street',
    direction: 'S',
    nemaPhase: 'Phase 8 (SB Thru/Right)',
    red_s: 67,
    yellow_s: 4,
    green_s: 49,
    cycle_s: 120,
    split_pct: 41,
    current_phase: 'red',
    minGreenSec: 10,
    maxGreenSec: 55,
    yellowChangeSec: 4,
    redClearanceSec: 2,
    pedestrianWalkSec: 15,
    pedestrianClearSec: 18,
    detectorStatus: 'Loop D8-SB: Active (6 veh queue)',
    preemptionWeight: 1,
  },
  {
    approach: 'E - 5th Ave. (EB)',
    name: 'Eastbound 5th Avenue (AMB Corridor)',
    direction: 'E',
    nemaPhase: 'Phase 2 (EB Thru/Right - Priority)',
    red_s: 49,
    yellow_s: 4,
    green_s: 67,
    cycle_s: 120,
    split_pct: 56,
    current_phase: 'green',
    minGreenSec: 15,
    maxGreenSec: 75,
    yellowChangeSec: 4,
    redClearanceSec: 2,
    pedestrianWalkSec: 18,
    pedestrianClearSec: 22,
    detectorStatus: 'Loop D2-EB: Active (V2X Corridor Pre-clearance)',
    preemptionWeight: 5,
  },
  {
    approach: 'W - 5th Ave. (WB)',
    name: 'Westbound 5th Avenue',
    direction: 'W',
    nemaPhase: 'Phase 6 (WB Thru/Right)',
    red_s: 49,
    yellow_s: 4,
    green_s: 67,
    cycle_s: 120,
    split_pct: 56,
    current_phase: 'green',
    minGreenSec: 15,
    maxGreenSec: 75,
    yellowChangeSec: 4,
    redClearanceSec: 2,
    pedestrianWalkSec: 18,
    pedestrianClearSec: 22,
    detectorStatus: 'Loop D6-WB: Active (4 veh queue)',
    preemptionWeight: 3,
  },
];

export interface PhaseTimingPanelProps {
  intersectionId?: string;
  intersectionName?: string;
  className?: string;
  style?: React.CSSProperties;
}

export const PhaseTimingPanel: React.FC<PhaseTimingPanelProps> = ({
  intersectionId = 'INT-0457',
  intersectionName = 'Oak St. & 5th Ave',
  className = '',
  style,
}) => {
  const [cycleElapsed, setCycleElapsed] = useState<number>(18);
  const [preemptionActive, setPreemptionActive] = useState<boolean>(false);
  const [selectedApproach, setSelectedApproach] = useState<DetailedApproachTiming | null>(null);

  // Synchronized 120s signal cycle ticker
  useEffect(() => {
    const timer = setInterval(() => {
      setCycleElapsed((prev) => (prev + 1) % 120);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Compute live phase and remaining countdown for each approach
  const computedApproaches = DEFAULT_APPROACHES.map((app) => {
    let currentPhase: SignalLightColor = 'red';
    let countdown = 0;
    let red_s = app.red_s;
    let green_s = app.green_s;
    let split_pct = app.split_pct;

    if (preemptionActive) {
      // Emergency Corridor Pre-emption: East-West holds extended green
      if (app.direction === 'E' || app.direction === 'W') {
        currentPhase = 'green';
        countdown = 45;
        green_s = 88;
        red_s = 28;
        split_pct = 73;
      } else {
        currentPhase = 'red';
        countdown = 45;
        green_s = 24;
        red_s = 92;
        split_pct = 20;
      }
    } else {
      // Normal 120s Cycle:
      // 0 <= t < 67: East-West Green, North-South Red
      // 67 <= t < 71: East-West Yellow, North-South Red
      // 71 <= t < 120: North-South Green, East-West Red
      if (app.direction === 'E' || app.direction === 'W') {
        if (cycleElapsed < 67) {
          currentPhase = 'green';
          countdown = 67 - cycleElapsed;
        } else if (cycleElapsed < 71) {
          currentPhase = 'yellow';
          countdown = 71 - cycleElapsed;
        } else {
          currentPhase = 'red';
          countdown = 120 - cycleElapsed;
        }
      } else {
        if (cycleElapsed < 67) {
          currentPhase = 'red';
          countdown = 71 - cycleElapsed;
        } else if (cycleElapsed < 71) {
          currentPhase = 'red';
          countdown = 71 - cycleElapsed;
        } else {
          currentPhase = 'green';
          countdown = 120 - cycleElapsed;
        }
      }
    }

    return {
      ...app,
      red_s,
      green_s,
      split_pct,
      current_phase: currentPhase,
      countdownSec: Math.max(1, countdown),
    };
  });

  // Construct shared domain SignalState contract
  const signalState: SignalState = {
    intersection_id: intersectionId,
    intersection_name: intersectionName,
    cycle_time_s: 120,
    current_phase_name: preemptionActive
      ? 'EMERGENCY_CORRIDOR_PREEMPTION'
      : cycleElapsed < 67
      ? 'P2_P6_EW_GREEN'
      : cycleElapsed < 71
      ? 'P2_P6_EW_YELLOW'
      : 'P4_P8_NS_GREEN',
    next_phase_name: cycleElapsed < 67 ? 'P2_P6_EW_YELLOW' : cycleElapsed < 71 ? 'P4_P8_NS_GREEN' : 'P2_P6_EW_GREEN',
    approaches: computedApproaches.map((a) => ({
      approach: a.approach,
      red_s: a.red_s,
      yellow_s: a.yellow_s,
      green_s: a.green_s,
      cycle_s: a.cycle_s,
      split_pct: a.split_pct,
      current_phase: a.current_phase,
    })),
    provenance: 'DEMO_FIXTURE' as DataProvenance,
  };

  return (
    <PanelFrame
      title={`${intersectionName} (${intersectionId})`}
      icon={<Clock size={15} color="#00e5ff" />}
      badge={
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <StatusPill label="Split Timing" variant="amber" size="xs" />
          <span style={{ fontSize: '0.64rem', color: '#64748b', fontFamily: 'monospace' }}>
            Cycle: <strong style={{ color: '#00f5d4' }}>120s</strong> ({cycleElapsed}s)
          </span>
        </div>
      }
      headerActions={
        <button
          type="button"
          onClick={() => setPreemptionActive(!preemptionActive)}
          title={preemptionActive ? 'Disable Emergency Pre-emption' : 'Trigger AMB-339 Corridor Pre-emption'}
          style={{
            background: preemptionActive ? 'rgba(239, 71, 111, 0.25)' : 'rgba(15, 23, 42, 0.6)',
            color: preemptionActive ? '#ef476f' : '#94a3b8',
            border: `1px solid ${preemptionActive ? '#ef476f' : '#1e293b'}`,
            borderRadius: '4px',
            padding: '2px 6px',
            fontSize: '0.62rem',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            fontWeight: 600,
          }}
        >
          <Flame size={11} color={preemptionActive ? '#ef476f' : '#64748b'} />
          {preemptionActive ? 'Pre-empt ON' : 'Test Pre-empt'}
        </button>
      }
      className={className}
      style={style}
    >
      <div
        style={{
          padding: '6px 10px',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          gap: '6px',
          boxSizing: 'border-box',
        }}
      >
        {/* Pre-emption Alert Banner when active */}
        {preemptionActive && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '3px 8px',
              backgroundColor: 'rgba(239, 71, 111, 0.15)',
              border: '1px solid rgba(239, 71, 111, 0.4)',
              borderRadius: '4px',
              fontSize: '0.65rem',
              color: '#ef476f',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <Flame size={12} color="#ef476f" className="live-pulse-red" />
              <span>
                <strong>CORRIDOR PRE-EMPTION ACTIVE:</strong> AMB-339 Priority Route (5th Ave E-W Green Extended)
              </span>
            </div>
            <span style={{ fontFamily: 'monospace', fontWeight: 700 }}>HOLD GREEN</span>
          </div>
        )}

        {/* Approach Split Timing Table */}
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.71rem', textAlign: 'left' }}>
            <thead>
              <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1b2f5b', fontSize: '0.64rem' }}>
                <th style={{ padding: '3px 4px', fontWeight: 500 }}>Approach</th>
                <th style={{ padding: '3px 4px', color: '#ef476f', textAlign: 'center', fontWeight: 600 }}>Red</th>
                <th style={{ padding: '3px 4px', color: '#ffd166', textAlign: 'center', fontWeight: 600 }}>Yellow</th>
                <th style={{ padding: '3px 4px', color: '#06d6a0', textAlign: 'center', fontWeight: 600 }}>Green</th>
                <th style={{ padding: '3px 4px', textAlign: 'center', fontWeight: 500 }}>Cycle</th>
                <th style={{ padding: '3px 4px', textAlign: 'center', fontWeight: 500 }}>Split</th>
              </tr>
            </thead>
            <tbody>
              {computedApproaches.map((app) => {
                const isSelected = selectedApproach?.approach === app.approach;
                return (
                  <tr
                    key={app.approach}
                    onClick={() => setSelectedApproach(isSelected ? null : app)}
                    style={{
                      borderBottom: '1px solid rgba(27, 47, 91, 0.4)',
                      backgroundColor: isSelected ? 'rgba(0, 229, 255, 0.08)' : 'transparent',
                      cursor: 'pointer',
                      transition: 'background-color 0.15s ease',
                    }}
                    title={`Click to inspect ${app.name} (${app.nemaPhase})`}
                  >
                    {/* Approach Name with Signal Head Lens Status */}
                    <td style={{ padding: '4px 3px', fontWeight: 500 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                        {/* Mini Signal Head Indicator: 3 lenses */}
                        <div
                          style={{
                            display: 'flex',
                            gap: '2px',
                            backgroundColor: '#050a18',
                            padding: '2px 3px',
                            borderRadius: '3px',
                            border: '1px solid #162547',
                          }}
                        >
                          <span
                            style={{
                              width: '5px',
                              height: '5px',
                              borderRadius: '50%',
                              backgroundColor: app.current_phase === 'red' ? '#ef476f' : 'rgba(239, 71, 111, 0.2)',
                              boxShadow: app.current_phase === 'red' ? '0 0 5px #ef476f' : 'none',
                            }}
                          />
                          <span
                            style={{
                              width: '5px',
                              height: '5px',
                              borderRadius: '50%',
                              backgroundColor: app.current_phase === 'yellow' ? '#ffd166' : 'rgba(255, 209, 102, 0.2)',
                              boxShadow: app.current_phase === 'yellow' ? '0 0 5px #ffd166' : 'none',
                            }}
                          />
                          <span
                            style={{
                              width: '5px',
                              height: '5px',
                              borderRadius: '50%',
                              backgroundColor: app.current_phase === 'green' ? '#06d6a0' : 'rgba(6, 214, 160, 0.2)',
                              boxShadow: app.current_phase === 'green' ? '0 0 5px #06d6a0' : 'none',
                            }}
                          />
                        </div>

                        <span style={{ color: isSelected ? '#00f5d4' : '#e2e8f0', fontSize: '0.69rem' }}>
                          {app.approach}
                        </span>
                      </div>
                    </td>

                    {/* Red Duration & Countdown */}
                    <td
                      style={{
                        padding: '4px 3px',
                        textAlign: 'center',
                        color: app.current_phase === 'red' ? '#ef476f' : '#64748b',
                        fontFamily: 'monospace',
                        fontWeight: 700,
                      }}
                    >
                      {app.current_phase === 'red' ? `${app.countdownSec}s*` : `${app.red_s}s`}
                    </td>

                    {/* Yellow Duration & Countdown */}
                    <td
                      style={{
                        padding: '4px 3px',
                        textAlign: 'center',
                        color: app.current_phase === 'yellow' ? '#ffd166' : '#64748b',
                        fontFamily: 'monospace',
                        fontWeight: 700,
                      }}
                    >
                      {app.current_phase === 'yellow' ? `${app.countdownSec}s*` : `${app.yellow_s}s`}
                    </td>

                    {/* Green Duration & Countdown */}
                    <td
                      style={{
                        padding: '4px 3px',
                        textAlign: 'center',
                        color: app.current_phase === 'green' ? '#06d6a0' : '#64748b',
                        fontFamily: 'monospace',
                        fontWeight: 700,
                      }}
                    >
                      {app.current_phase === 'green' ? `${app.countdownSec}s*` : `${app.green_s}s`}
                    </td>

                    {/* Total Cycle */}
                    <td style={{ padding: '4px 3px', textAlign: 'center', fontFamily: 'monospace', color: '#94a3b8' }}>
                      {app.cycle_s}s
                    </td>

                    {/* Split Percentage with mini visual bar */}
                    <td style={{ padding: '4px 3px', textAlign: 'center' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px' }}>
                        <span style={{ color: '#38bdf8', fontFamily: 'monospace', fontWeight: 600 }}>
                          {app.split_pct}%
                        </span>
                        <div
                          style={{
                            width: '32px',
                            height: '3px',
                            backgroundColor: '#162547',
                            borderRadius: '2px',
                            overflow: 'hidden',
                          }}
                        >
                          <div
                            style={{
                              width: `${app.split_pct}%`,
                              height: '100%',
                              backgroundColor: app.current_phase === 'green' ? '#06d6a0' : '#38bdf8',
                            }}
                          />
                        </div>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Selected Approach Detailed Phase Inspector */}
        {selectedApproach && (
          <div
            style={{
              backgroundColor: '#0a1428',
              border: '1px solid #1b2f5b',
              borderRadius: '5px',
              padding: '6px 8px',
              fontSize: '0.64rem',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderBottom: '1px solid #162547',
                paddingBottom: '3px',
                marginBottom: '4px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <Sliders size={12} color="#00f5d4" />
                <span style={{ fontWeight: 700, color: '#f1f5f9' }}>{selectedApproach.name}</span>
                <span style={{ color: '#64748b', fontFamily: 'monospace' }}>({selectedApproach.nemaPhase})</span>
              </div>
              <button
                type="button"
                onClick={() => setSelectedApproach(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#94a3b8',
                  cursor: 'pointer',
                  padding: '1px',
                }}
              >
                <X size={12} />
              </button>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '3px 6px',
                color: '#94a3b8',
              }}
            >
              <div>
                <span style={{ color: '#64748b' }}>Min/Max Green: </span>
                <span style={{ color: '#06d6a0', fontFamily: 'monospace' }}>
                  {selectedApproach.minGreenSec}s / {selectedApproach.maxGreenSec}s
                </span>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>Yellow / Red Clr: </span>
                <span style={{ color: '#ffd166', fontFamily: 'monospace' }}>
                  {selectedApproach.yellowChangeSec}s / {selectedApproach.redClearanceSec}s
                </span>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>Ped Walk / Clr: </span>
                <span style={{ color: '#38bdf8', fontFamily: 'monospace' }}>
                  {selectedApproach.pedestrianWalkSec}s / {selectedApproach.pedestrianClearSec}s
                </span>
              </div>
              <div style={{ gridColumn: 'span 3', color: '#64748b' }}>
                <span>Detectors: </span>
                <span style={{ color: '#f1f5f9', fontFamily: 'monospace' }}>{selectedApproach.detectorStatus}</span>
              </div>
            </div>
          </div>
        )}

        {/* Footer Status Bar: Safety Interlock & Provenance */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '3px 6px',
            backgroundColor: '#0a1128',
            borderRadius: '4px',
            border: '1px solid #162547',
            fontSize: '0.62rem',
            color: '#64748b',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <CheckCircle size={11} color="#06d6a0" />
            <span>NEMA TS2 Controller In-Sync</span>
            <span style={{ color: '#1b2f5b' }}>|</span>
            <span style={{ color: '#94a3b8' }}>MMU Conflict-Free Verified</span>
          </div>
          <div>
            <span style={{ color: '#00f5d4', fontWeight: 600 }}>DEMO_FIXTURE</span>
          </div>
        </div>
      </div>
    </PanelFrame>
  );
};

export default PhaseTimingPanel;

