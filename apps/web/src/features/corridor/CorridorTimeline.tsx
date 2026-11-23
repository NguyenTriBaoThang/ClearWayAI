/**
 * ClearWayAI Corridor Moving-Horizon Coordination Timeline (`apps/web/src/features/corridor/CorridorTimeline.tsx`)
 *
 * Visualizes the arterial green-wave progression, JIT pre-clearance actuation intervals,
 * AMB-339 vehicle arrival trajectory, and post-clearance recovery debt amortization.
 */

import React, { useState } from 'react';
import {
  Clock,
  Activity,
  ShieldAlert,
  Sliders,
  CheckCircle,
  TrendingDown,
  RotateCcw,
} from 'lucide-react';
import { useOperations } from '../dashboard/OperationsContext';

interface NodeTimelineBar {
  nodeId: string;
  label: string;
  offsetSec: number;
  triggerLeadSec: number;
  holdDurationSec: number;
  arrivalSec: number;
  recoverySec: number;
  state: 'MONITORING' | 'ARMED' | 'TRANSITIONING' | 'HOLDING_GREEN' | 'EV_PASSING' | 'RECOVERY';
}

const DEFAULT_TIMELINE_NODES: NodeTimelineBar[] = [
  {
    nodeId: 'node_a',
    label: 'Node A (Maple)',
    offsetSec: 0.0,
    triggerLeadSec: 14.2,
    holdDurationSec: 22.0,
    arrivalSec: 8.1,
    recoverySec: 18.0,
    state: 'EV_PASSING',
  },
  {
    nodeId: 'node_b',
    label: 'Node B (Oak)',
    offsetSec: 13.5,
    triggerLeadSec: 16.5,
    holdDurationSec: 24.0,
    arrivalSec: 21.6,
    recoverySec: 20.0,
    state: 'HOLDING_GREEN',
  },
  {
    nodeId: 'node_c',
    label: 'Node C (Pine)',
    offsetSec: 27.0,
    triggerLeadSec: 15.0,
    holdDurationSec: 20.0,
    arrivalSec: 35.1,
    recoverySec: 16.0,
    state: 'ARMED',
  },
  {
    nodeId: 'node_d',
    label: 'Node D (Elm)',
    offsetSec: 40.5,
    triggerLeadSec: 14.0,
    holdDurationSec: 22.0,
    arrivalSec: 48.6,
    recoverySec: 18.0,
    state: 'MONITORING',
  },
];

export interface CorridorTimelineProps {
  className?: string;
  style?: React.CSSProperties;
}

export const CorridorTimeline: React.FC<CorridorTimelineProps> = ({
  className = '',
  style,
}) => {
  const { multiNodeETA, simTimeSec } = useOperations();
  const [selectedTimelineNode, setSelectedTimelineNode] = useState<string>('node_b');

  // Time window: 0s -> 60s
  const MAX_TIME_SEC = 60.0;
  const timeToPercent = (sec: number) => Math.max(0, Math.min(100, (sec / MAX_TIME_SEC) * 100));

  const getNodeStateColor = (state: string) => {
    switch (state) {
      case 'EV_PASSING':
        return '#00e5ff';
      case 'HOLDING_GREEN':
        return '#06d6a0';
      case 'TRANSITIONING':
      case 'ARMED':
        return '#ffd166';
      case 'RECOVERY':
        return '#a855f7';
      default:
        return '#64748b';
    }
  };

  return (
    <div
      className={`panel-card cyber-corner ${className}`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#0a1428',
        border: '1px solid #1b2f5b',
        borderRadius: '8px',
        overflow: 'hidden',
        color: '#f8fafc',
        boxShadow: '0 4px 24px rgba(0, 0, 0, 0.5)',
        ...style,
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 14px',
          backgroundColor: '#0d1b38',
          borderBottom: '1px solid #162547',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '24px',
              height: '24px',
              borderRadius: '5px',
              backgroundColor: 'rgba(6, 214, 160, 0.15)',
              border: '1px solid rgba(6, 214, 160, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#06d6a0',
            }}
          >
            <Clock size={14} />
          </div>
          <span style={{ fontSize: '0.82rem', fontWeight: 700, letterSpacing: '0.04em', color: '#06d6a0' }}>
            MOVING-HORIZON COORDINATION TIMELINE
          </span>
          <span style={{ fontSize: '0.70rem', color: '#94a3b8' }}>
            (Cascading Pre-clearance Offsets & Green-Wave Trajectory)
          </span>
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.68rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '2px', backgroundColor: '#ffd166' }} />
            <span style={{ color: '#94a3b8' }}>JIT Trigger</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '2px', backgroundColor: '#06d6a0' }} />
            <span style={{ color: '#94a3b8' }}>Green Hold</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '2px', backgroundColor: '#a855f7' }} />
            <span style={{ color: '#94a3b8' }}>Recovery Amortization</span>
          </div>
        </div>
      </div>

      {/* Gantt Chart Matrix */}
      <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {/* Horizontal Time Scale Header */}
        <div style={{ display: 'flex', alignItems: 'center', paddingLeft: '110px', fontSize: '0.68rem', color: '#64748b' }}>
          {[0, 10, 20, 30, 40, 50, 60].map((sec) => (
            <div key={sec} style={{ flex: 1, textAlign: sec === 0 ? 'left' : sec === 60 ? 'right' : 'center', fontFamily: 'monospace' }}>
              +{sec}s
            </div>
          ))}
        </div>

        {/* Node Rows */}
        {DEFAULT_TIMELINE_NODES.map((node) => {
          const eta = multiNodeETA?.etas_by_node?.[node.nodeId];
          const arrivalSec = eta ? eta.eta_seconds : node.arrivalSec;
          const isSelected = selectedTimelineNode === node.nodeId;

          // Band boundaries
          const triggerStart = Math.max(0, arrivalSec - node.triggerLeadSec);
          const holdEnd = arrivalSec + 6.0;
          const recoveryEnd = holdEnd + node.recoverySec;

          return (
            <div
              key={node.nodeId}
              onClick={() => setSelectedTimelineNode(node.nodeId)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                cursor: 'pointer',
                padding: '4px 6px',
                borderRadius: '6px',
                backgroundColor: isSelected ? 'rgba(0, 229, 255, 0.08)' : 'transparent',
                border: isSelected ? '1px solid rgba(0, 229, 255, 0.3)' : '1px solid transparent',
              }}
            >
              {/* Row Label */}
              <div style={{ width: '100px', display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '0.74rem', fontWeight: 700, color: isSelected ? '#00e5ff' : '#f8fafc' }}>
                  {node.label}
                </span>
                <span
                  style={{
                    fontSize: '0.62rem',
                    fontWeight: 600,
                    color: getNodeStateColor(node.state),
                    fontFamily: 'monospace',
                  }}
                >
                  {node.state}
                </span>
              </div>

              {/* Timeline Track */}
              <div
                style={{
                  flex: 1,
                  height: '24px',
                  backgroundColor: '#070e22',
                  borderRadius: '4px',
                  position: 'relative',
                  border: '1px solid #162547',
                  overflow: 'hidden',
                }}
              >
                {/* 10s Vertical Grid Lines */}
                {[0, 10, 20, 30, 40, 50, 60].map((s) => (
                  <div
                    key={s}
                    style={{
                      position: 'absolute',
                      left: `${timeToPercent(s)}%`,
                      top: 0,
                      bottom: 0,
                      width: '1px',
                      backgroundColor: 'rgba(22, 37, 71, 0.6)',
                    }}
                  />
                ))}

                {/* Pre-clearance Trigger Buffer Band */}
                <div
                  title="JIT Pre-clearance Actuation Window"
                  style={{
                    position: 'absolute',
                    left: `${timeToPercent(triggerStart)}%`,
                    width: `${timeToPercent(arrivalSec) - timeToPercent(triggerStart)}%`,
                    top: '2px',
                    bottom: '2px',
                    backgroundColor: 'rgba(255, 209, 102, 0.25)',
                    border: '1px dashed #ffd166',
                    borderRadius: '3px 0 0 3px',
                  }}
                />

                {/* Green Hold Preemption Band */}
                <div
                  title="Active Preemption Green Hold"
                  style={{
                    position: 'absolute',
                    left: `${timeToPercent(triggerStart)}%`,
                    width: `${timeToPercent(holdEnd) - timeToPercent(triggerStart)}%`,
                    top: '4px',
                    bottom: '4px',
                    backgroundColor: 'rgba(6, 214, 160, 0.45)',
                    border: '1px solid #06d6a0',
                    borderRadius: '3px',
                  }}
                />

                {/* Post-Transit Recovery Band */}
                <div
                  title="Cross-Street Green Debt Amortization"
                  style={{
                    position: 'absolute',
                    left: `${timeToPercent(holdEnd)}%`,
                    width: `${timeToPercent(recoveryEnd) - timeToPercent(holdEnd)}%`,
                    top: '6px',
                    bottom: '6px',
                    backgroundColor: 'rgba(168, 85, 247, 0.25)',
                    border: '1px solid #a855f7',
                    borderRadius: '0 3px 3px 0',
                  }}
                />

                {/* AMB-339 Projected Arrival Marker Line */}
                <div
                  title={`Projected EV Passage: +${arrivalSec.toFixed(1)}s`}
                  style={{
                    position: 'absolute',
                    left: `${timeToPercent(arrivalSec)}%`,
                    top: 0,
                    bottom: 0,
                    width: '3px',
                    backgroundColor: '#ef476f',
                    boxShadow: '0 0 8px #ef476f',
                    zIndex: 10,
                  }}
                />
              </div>

              {/* Arrival Countdown Pill */}
              <div
                style={{
                  width: '55px',
                  textAlign: 'right',
                  fontSize: '0.72rem',
                  fontWeight: 700,
                  fontFamily: 'monospace',
                  color: '#00e5ff',
                }}
              >
                +{arrivalSec.toFixed(0)}s
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Node Recovery & Debt Status Footer */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 16px',
          backgroundColor: '#070e22',
          borderTop: '1px solid #162547',
          fontSize: '0.70rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <RotateCcw size={13} color="#a855f7" />
          <span style={{ color: '#94a3b8' }}>
            Recovery Controller Strategy:
          </span>
          <strong style={{ color: '#a855f7' }}>
            3-Cycle Quadratic Debt Amortization (Max +15s Cross-Green Bonus)
          </strong>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle size={13} color="#06d6a0" />
          <span style={{ color: '#06d6a0', fontWeight: 600 }}>
            Master Clock Resync: 100% Deterministic (Zero Drift)
          </span>
        </div>
      </div>
    </div>
  );
};

export default CorridorTimeline;

