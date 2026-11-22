import React, { useState } from 'react';
import {
  Sliders,
  TrendingDown,
  Brain,
  ShieldCheck,
  Zap,
  Info,
  X,
  Activity,
  Layers,
} from 'lucide-react';
import { PanelFrame } from '../../components/PanelFrame';
import { StatusPill } from '../../components/StatusPill';
import { TrafficAnalytics, DataProvenance } from '@clearway/shared';

export type SignalControlMode = 'rl_adaptive' | 'actuated' | 'fixed_time';

export interface ChartDataPoint {
  timeSec: number;
  queueVeh: number;
  capacityVeh: number;
  phase: string;
}

const BASE_CHART_DATA: ChartDataPoint[] = [
  { timeSec: 0, queueVeh: 12, capacityVeh: 20, phase: 'P1' },
  { timeSec: 15, queueVeh: 22, capacityVeh: 20, phase: 'P1' },
  { timeSec: 30, queueVeh: 48, capacityVeh: 20, phase: 'P2' },
  { timeSec: 45, queueVeh: 78, capacityVeh: 110, phase: 'P3 (E-W Thru)' },
  { timeSec: 60, queueVeh: 92, capacityVeh: 110, phase: 'P3 (E-W Thru)' },
  { timeSec: 75, queueVeh: 84, capacityVeh: 110, phase: 'P3 (E-W Thru)' },
  { timeSec: 90, queueVeh: 46, capacityVeh: 20, phase: 'P4 (E-W Left)' },
  { timeSec: 105, queueVeh: 24, capacityVeh: 20, phase: 'P4 (E-W Left)' },
  { timeSec: 120, queueVeh: 14, capacityVeh: 20, phase: 'P1' },
];

export interface AdaptiveSignalPanelProps {
  intersectionId?: string;
  initialMode?: SignalControlMode;
  className?: string;
  style?: React.CSSProperties;
}

export const AdaptiveSignalPanel: React.FC<AdaptiveSignalPanelProps> = ({
  intersectionId = 'INT-0457',
  initialMode = 'rl_adaptive',
  className = '',
  style,
}) => {
  const [controlMode, setControlMode] = useState<SignalControlMode>(initialMode);
  const [hoveredPoint, setHoveredPoint] = useState<ChartDataPoint | null>(null);
  const [showDiagnostics, setShowDiagnostics] = useState<boolean>(false);

  // Compute metrics based on active control mode
  const metrics = {
    rl_adaptive: {
      delayReduction: '-19%',
      avgQueueM: '87 m',
      backlogM: '45 m',
      occupancyPct: 76,
      currentPhase: 'P3 (E-W Thru)',
      nextPhase: 'P4 (E-W Left)',
      agentStatus: 'Active Logic (PPO)',
      badgeVariant: 'cyan' as const,
    },
    actuated: {
      delayReduction: '-11%',
      avgQueueM: '102 m',
      backlogM: '61 m',
      occupancyPct: 84,
      currentPhase: 'P3 (E-W Thru)',
      nextPhase: 'P4 (E-W Left)',
      agentStatus: 'Actuated (Webster)',
      badgeVariant: 'amber' as const,
    },
    fixed_time: {
      delayReduction: '0% (Baseline)',
      avgQueueM: '138 m',
      backlogM: '92 m',
      occupancyPct: 93,
      currentPhase: 'P3 (E-W Thru)',
      nextPhase: 'P4 (E-W Left)',
      agentStatus: 'Pre-timed Fixed',
      badgeVariant: 'neutral' as const,
    },
  }[controlMode];

  const trafficAnalytics: TrafficAnalytics = {
    intersection_id: intersectionId,
    performance_index: controlMode === 'rl_adaptive' ? 94.2 : controlMode === 'actuated' ? 82.0 : 68.5,
    throughput_pct_change: controlMode === 'rl_adaptive' ? 14.8 : controlMode === 'actuated' ? 7.2 : 0.0,
    avg_delay_pct_change: controlMode === 'rl_adaptive' ? -19.0 : controlMode === 'actuated' ? -11.0 : 0.0,
    stops_per_veh_pct_change: controlMode === 'rl_adaptive' ? -22.4 : controlMode === 'actuated' ? -12.0 : 0.0,
    occupancy_pct: metrics.occupancyPct,
    avg_speed_kmh: controlMode === 'rl_adaptive' ? 34.6 : controlMode === 'actuated' ? 29.1 : 22.4,
    avg_queue_m: parseInt(metrics.avgQueueM, 10),
    backlog_m: parseInt(metrics.backlogM, 10),
    provenance: 'DEMO_FIXTURE' as DataProvenance,
  };

  // Convert data points to SVG coordinate space
  // SVG box: 300 width, 65 height
  // X: 30 to 290 (span 260px for 0-120s)
  // Y: 10 to 58 (span 48px for 120-0 veh)
  const mapX = (t: number) => 30 + (t / 120) * 260;
  const mapY = (q: number) => 58 - (Math.min(120, q) / 120) * 48;

  // Build cyan curve path
  const curvePoints = BASE_CHART_DATA.map((d) => `${mapX(d.timeSec)},${mapY(d.queueVeh)}`).join(' ');
  const areaPath = `M ${mapX(0)},58 L ${curvePoints} L ${mapX(120)},58 Z`;

  // Build red stepped capacity line: 0-35s capacity 20, 35-85s capacity 110, 85-120s capacity 20
  const capStepPoints = [
    `${mapX(0)},${mapY(20)}`,
    `${mapX(38)},${mapY(20)}`,
    `${mapX(40)},${mapY(110)}`,
    `${mapX(84)},${mapY(110)}`,
    `${mapX(86)},${mapY(20)}`,
    `${mapX(120)},${mapY(20)}`,
  ].join(' ');

  return (
    <PanelFrame
      title="Adaptive Signal Control (RL Agent)"
      icon={<Sliders size={15} color="#00e5ff" />}
      badge={
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <StatusPill label={metrics.agentStatus} variant={metrics.badgeVariant} size="xs" pulse />
          <span
            style={{
              fontSize: '0.62rem',
              color: '#00f5d4',
              fontFamily: 'monospace',
              backgroundColor: '#122347',
              padding: '1px 5px',
              borderRadius: '3px',
              border: '1px solid #1b2f5b',
            }}
          >
            DEMO_FIXTURE
          </span>
        </div>
      }
      headerActions={
        <div style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
          <button
            type="button"
            onClick={() => setControlMode('rl_adaptive')}
            title="PPO Reinforcement Learning Policy"
            style={{
              background: controlMode === 'rl_adaptive' ? 'rgba(0, 229, 255, 0.25)' : 'rgba(15, 23, 42, 0.6)',
              color: controlMode === 'rl_adaptive' ? '#00e5ff' : '#64748b',
              border: `1px solid ${controlMode === 'rl_adaptive' ? '#00e5ff' : '#1e293b'}`,
              borderRadius: '3px',
              padding: '2px 5px',
              fontSize: '0.60rem',
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            RL (PPO)
          </button>
          <button
            type="button"
            onClick={() => setControlMode('actuated')}
            title="Actuated Webster Dynamic Split"
            style={{
              background: controlMode === 'actuated' ? 'rgba(255, 209, 102, 0.25)' : 'rgba(15, 23, 42, 0.6)',
              color: controlMode === 'actuated' ? '#ffd166' : '#64748b',
              border: `1px solid ${controlMode === 'actuated' ? '#ffd166' : '#1e293b'}`,
              borderRadius: '3px',
              padding: '2px 5px',
              fontSize: '0.60rem',
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            Actuated
          </button>
          <button
            type="button"
            onClick={() => setControlMode('fixed_time')}
            title="Fixed-Time Pre-timed Baseline"
            style={{
              background: controlMode === 'fixed_time' ? 'rgba(148, 163, 184, 0.25)' : 'rgba(15, 23, 42, 0.6)',
              color: controlMode === 'fixed_time' ? '#f1f5f9' : '#64748b',
              border: `1px solid ${controlMode === 'fixed_time' ? '#94a3b8' : '#1e293b'}`,
              borderRadius: '3px',
              padding: '2px 5px',
              fontSize: '0.60rem',
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            Fixed
          </button>
        </div>
      }
      className={className}
      style={style}
    >
      <div
        style={{
          padding: '8px 10px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          height: '100%',
          justifyContent: 'space-between',
          boxSizing: 'border-box',
        }}
      >
        {/* Top KPIs: Cycle Time, Current Phase, Next Phase */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.25fr 1.25fr', gap: '6px' }}>
          {/* Cycle Time */}
          <div
            style={{
              background: '#0a1128',
              padding: '5px 8px',
              borderRadius: '4px',
              border: '1px solid #162547',
            }}
          >
            <div style={{ fontSize: '0.60rem', color: '#94a3b8' }}>Cycle Time</div>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f8fafc', fontFamily: 'monospace' }}>
              120s
            </div>
          </div>

          {/* Current Phase */}
          <div
            style={{
              background: '#0a1128',
              padding: '5px 8px',
              borderRadius: '4px',
              border: '1px solid #162547',
            }}
          >
            <div style={{ fontSize: '0.60rem', color: '#94a3b8' }}>Current Phase</div>
            <div
              style={{
                fontSize: '0.74rem',
                fontWeight: 700,
                color: '#06d6a0',
                fontFamily: 'monospace',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {metrics.currentPhase}
            </div>
          </div>

          {/* Next Phase */}
          <div
            style={{
              background: '#0a1128',
              padding: '5px 8px',
              borderRadius: '4px',
              border: '1px solid #162547',
            }}
          >
            <div style={{ fontSize: '0.60rem', color: '#94a3b8' }}>Next Phase</div>
            <div
              style={{
                fontSize: '0.74rem',
                fontWeight: 700,
                color: '#38bdf8',
                fontFamily: 'monospace',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {metrics.nextPhase}
            </div>
          </div>
        </div>

        {/* Phase Plan & Queue Length Vector Chart */}
        <div
          style={{
            background: '#0a1128',
            padding: '5px 8px',
            borderRadius: '4px',
            border: '1px solid #162547',
            position: 'relative',
          }}
        >
          {/* Header Row of Chart */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '3px',
              fontSize: '0.64rem',
            }}
          >
            <span style={{ color: '#94a3b8', fontWeight: 500 }}>Phase Plan & Queue Length</span>
            <div style={{ display: 'flex', gap: '8px', fontSize: '0.58rem' }}>
              <span style={{ color: '#00e5ff' }}>— Queue (veh)</span>
              <span style={{ color: '#ef476f' }}>--- Capacity</span>
              <span style={{ color: '#06d6a0', fontWeight: 600 }}>Occupancy: {metrics.occupancyPct}%</span>
            </div>
          </div>

          {/* Inline Interactive SVG Chart */}
          <div style={{ position: 'relative' }}>
            <svg
              viewBox="0 0 300 68"
              style={{ width: '100%', height: '54px', overflow: 'visible', cursor: 'crosshair' }}
              onMouseLeave={() => setHoveredPoint(null)}
            >
              <defs>
                <linearGradient id="queueGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#00e5ff" stopOpacity="0.25" />
                  <stop offset="100%" stopColor="#00e5ff" stopOpacity="0.0" />
                </linearGradient>
              </defs>

              {/* Grid Lines */}
              <line x1="30" y1="10" x2="290" y2="10" stroke="#1e293b" strokeDasharray="2,2" />
              <line x1="30" y1="26" x2="290" y2="26" stroke="#1e293b" strokeDasharray="2,2" />
              <line x1="30" y1="42" x2="290" y2="42" stroke="#1e293b" strokeDasharray="2,2" />
              <line x1="30" y1="58" x2="290" y2="58" stroke="#334155" />

              {/* Gradient fill under queue curve */}
              <polygon points={`30,58 ${curvePoints} 290,58`} fill="url(#queueGradient)" />

              {/* Red dashed stepped line: Capacity */}
              <polyline
                points={capStepPoints}
                fill="none"
                stroke="#ef476f"
                strokeWidth="1.6"
                strokeDasharray="4,2"
              />

              {/* Cyan curve: Queue Length */}
              <polyline points={curvePoints} fill="none" stroke="#00e5ff" strokeWidth="2.0" />

              {/* Interactive Data Point Dots */}
              {BASE_CHART_DATA.map((pt, idx) => (
                <circle
                  key={idx}
                  cx={mapX(pt.timeSec)}
                  cy={mapY(pt.queueVeh)}
                  r={hoveredPoint?.timeSec === pt.timeSec ? 4 : 2}
                  fill="#00e5ff"
                  stroke="#070d1e"
                  strokeWidth="1"
                  style={{ transition: 'r 0.15s ease' }}
                  onMouseEnter={() => setHoveredPoint(pt)}
                />
              ))}

              {/* Hover crosshair guide line */}
              {hoveredPoint && (
                <line
                  x1={mapX(hoveredPoint.timeSec)}
                  y1="10"
                  x2={mapX(hoveredPoint.timeSec)}
                  y2="58"
                  stroke="#00e5ff"
                  strokeWidth="1"
                  strokeDasharray="2,2"
                />
              )}

              {/* Y-Axis tick labels */}
              <text x="12" y="13" fill="#64748b" fontSize="7" fontFamily="monospace">120</text>
              <text x="12" y="29" fill="#64748b" fontSize="7" fontFamily="monospace">80</text>
              <text x="12" y="45" fill="#64748b" fontSize="7" fontFamily="monospace">40</text>

              {/* X-Axis tick labels */}
              <text x="30" y="66" fill="#64748b" fontSize="7" fontFamily="monospace">0</text>
              <text x="95" y="66" fill="#64748b" fontSize="7" fontFamily="monospace">30</text>
              <text x="160" y="66" fill="#64748b" fontSize="7" fontFamily="monospace">60</text>
              <text x="225" y="66" fill="#64748b" fontSize="7" fontFamily="monospace">90</text>
              <text x="280" y="66" fill="#64748b" fontSize="7" fontFamily="monospace">120s</text>
            </svg>

            {/* Hover Tooltip Popup */}
            {hoveredPoint && (
              <div
                style={{
                  position: 'absolute',
                  top: '2px',
                  left: `${Math.min(200, Math.max(30, (hoveredPoint.timeSec / 120) * 260))}px`,
                  backgroundColor: 'rgba(7, 13, 30, 0.95)',
                  border: '1px solid #00e5ff',
                  borderRadius: '3px',
                  padding: '2px 5px',
                  fontSize: '0.58rem',
                  color: '#f1f5f9',
                  pointerEvents: 'none',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.5)',
                  zIndex: 10,
                }}
              >
                <div><strong>t={hoveredPoint.timeSec}s:</strong> {hoveredPoint.phase}</div>
                <div>Queue: <span style={{ color: '#00e5ff' }}>{hoveredPoint.queueVeh} veh</span> | Cap: <span style={{ color: '#ef476f' }}>{hoveredPoint.capacityVeh}</span></div>
              </div>
            )}
          </div>
        </div>

        {/* Bottom Optimization Metrics Row: -19% Delay, 87m Avg Queue, 45m Backlog */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: '6px', fontSize: '0.70rem' }}>
          {/* Optimization KPI */}
          <div
            style={{
              background: '#0a1128',
              padding: '4px 6px',
              borderRadius: '4px',
              border: '1px solid #162547',
            }}
          >
            <div style={{ fontSize: '0.60rem', color: '#94a3b8' }}>Optimization</div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '3px',
                color: controlMode === 'fixed_time' ? '#94a3b8' : '#06d6a0',
                fontWeight: 700,
                fontSize: '0.74rem',
              }}
            >
              <TrendingDown size={13} color={controlMode === 'fixed_time' ? '#94a3b8' : '#06d6a0'} />
              <span>{metrics.delayReduction} Delay</span>
            </div>
          </div>

          {/* Avg. Queue */}
          <div
            style={{
              background: '#0a1128',
              padding: '4px 6px',
              borderRadius: '4px',
              border: '1px solid #162547',
            }}
          >
            <div style={{ fontSize: '0.60rem', color: '#94a3b8' }}>Avg. Queue</div>
            <div style={{ color: '#00f5d4', fontWeight: 700, fontFamily: 'monospace', fontSize: '0.76rem' }}>
              {metrics.avgQueueM}
            </div>
          </div>

          {/* Backlog */}
          <div
            style={{
              background: '#0a1128',
              padding: '4px 6px',
              borderRadius: '4px',
              border: '1px solid #162547',
            }}
          >
            <div style={{ fontSize: '0.60rem', color: '#94a3b8' }}>Backlog</div>
            <div style={{ color: '#ef476f', fontWeight: 700, fontFamily: 'monospace', fontSize: '0.76rem' }}>
              {metrics.backlogM}
            </div>
          </div>
        </div>

        {/* Diagnostics & Safety Guard Button / Expansion */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.60rem' }}>
          <button
            type="button"
            onClick={() => setShowDiagnostics(!showDiagnostics)}
            style={{
              background: 'none',
              border: 'none',
              color: '#00e5ff',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '3px',
              fontSize: '0.60rem',
              padding: 0,
            }}
          >
            <Brain size={11} />
            {showDiagnostics ? 'Hide RL Architecture' : 'View RL Diagnostics & Safety Envelope'}
          </button>
          <span style={{ color: '#64748b' }}>vs. Fixed-time baseline</span>
        </div>

        {/* RL Diagnostics Drawer */}
        {showDiagnostics && (
          <div
            style={{
              backgroundColor: '#0a1428',
              border: '1px solid #1b2f5b',
              borderRadius: '4px',
              padding: '5px 8px',
              fontSize: '0.62rem',
              color: '#94a3b8',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                borderBottom: '1px solid #162547',
                paddingBottom: '2px',
                marginBottom: '4px',
                color: '#f1f5f9',
                fontWeight: 600,
              }}
            >
              <span>Reinforcement Learning Model Envelope</span>
              <button
                type="button"
                onClick={() => setShowDiagnostics(false)}
                style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}
              >
                <X size={11} />
              </button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3px 6px' }}>
              <div>Model: <span style={{ color: '#00f5d4', fontFamily: 'monospace' }}>PPO Actor-Critic</span></div>
              <div>Safety MMU: <span style={{ color: '#06d6a0', fontFamily: 'monospace' }}>NEMA Hardware Interlocked</span></div>
              <div>Min Green: <span style={{ color: '#f1f5f9', fontFamily: 'monospace' }}>10.0s (Hard Limit)</span></div>
              <div>Max Green: <span style={{ color: '#f1f5f9', fontFamily: 'monospace' }}>75.0s (Hard Limit)</span></div>
              <div style={{ gridColumn: 'span 2' }}>
                Reward: <span style={{ color: '#38bdf8', fontFamily: 'monospace' }}>-(0.5·delay + 0.3·stops + 0.2·queue_var)</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </PanelFrame>
  );
};

export default AdaptiveSignalPanel;

