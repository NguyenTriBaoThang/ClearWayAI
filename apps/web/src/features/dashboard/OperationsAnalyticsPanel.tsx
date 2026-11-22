import React, { useState } from 'react';
import {
  BarChart3,
  AlertCircle,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  TrendingDown,
  Clock,
  Gauge,
  X,
  Info,
  Radio,
} from 'lucide-react';
import { PanelFrame } from '../../components/PanelFrame';
import { StatusPill } from '../../components/StatusPill';
import { TrafficAnalytics, DataProvenance } from '@clearway/shared';

export interface VolumeApproachData {
  approach: 'NB' | 'SB' | 'EB' | 'WB';
  name: string;
  volumeVehH: number;
  avg15MinVehH: number;
  heightPct: number;
  motorcyclePct: number;
  carPct: number;
  busPct: number;
}

export interface TravelTimeData {
  corridor: string;
  travelTimeMin: number;
  deltaPct: number;
  baselineMin: number;
}

export interface AnomalyAlert {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  timestamp: string;
  title: string;
  message: string;
}

const VOLUME_DATA: VolumeApproachData[] = [
  { approach: 'NB', name: 'Oak St. Northbound', volumeVehH: 1210, avg15MinVehH: 1180, heightPct: 55, motorcyclePct: 44, carPct: 46, busPct: 10 },
  { approach: 'SB', name: 'Oak St. Southbound', volumeVehH: 1438, avg15MinVehH: 1390, heightPct: 65, motorcyclePct: 48, carPct: 42, busPct: 10 },
  { approach: 'EB', name: '5th Ave. Eastbound (AMB Corridor)', volumeVehH: 2185, avg15MinVehH: 2050, heightPct: 98, motorcyclePct: 36, carPct: 52, busPct: 12 },
  { approach: 'WB', name: '5th Ave. Westbound', volumeVehH: 2061, avg15MinVehH: 1990, heightPct: 92, motorcyclePct: 38, carPct: 50, busPct: 12 },
];

const TRAVEL_TIMES: TravelTimeData[] = [
  { corridor: 'N → S', travelTimeMin: 2.6, deltaPct: -18, baselineMin: 3.2 },
  { corridor: 'S → N', travelTimeMin: 2.8, deltaPct: -17, baselineMin: 3.4 },
  { corridor: 'E → W', travelTimeMin: 3.9, deltaPct: 6, baselineMin: 3.7 },
  { corridor: 'W → E', travelTimeMin: 3.7, deltaPct: 4, baselineMin: 3.5 },
];

const INITIAL_ALERTS: AnomalyAlert[] = [
  {
    id: 'ALT-01',
    severity: 'critical',
    timestamp: '12s ago',
    title: 'Critical Corridor',
    message: 'AMB-339 priority corridor active (Approaching from West, ETA 42s)',
  },
  {
    id: 'ALT-02',
    severity: 'warning',
    timestamp: '48s ago',
    title: 'Queue Spillback',
    message: 'Oak St NB Queue > 80m (87m measured, spillback risk)',
  },
  {
    id: 'ALT-03',
    severity: 'info',
    timestamp: '2m ago',
    title: 'RSU Telemetry',
    message: 'RSU-0457 radio channel nominal (5.9 GHz, 0.2% packet loss)',
  },
];

export interface OperationsAnalyticsPanelProps {
  intersectionId?: string;
  className?: string;
  style?: React.CSSProperties;
}

export const OperationsAnalyticsPanel: React.FC<OperationsAnalyticsPanelProps> = ({
  intersectionId = 'INT-0457',
  className = '',
  style,
}) => {
  const [selectedApproach, setSelectedApproach] = useState<VolumeApproachData | null>(null);
  const [alerts, setAlerts] = useState<AnomalyAlert[]>(INITIAL_ALERTS);
  const [alertFilter, setAlertFilter] = useState<'all' | 'critical' | 'warning'>('all');

  const filteredAlerts = alerts.filter((a) => alertFilter === 'all' || a.severity === alertFilter);

  const dismissAlert = (id: string) => {
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  };

  const trafficAnalytics: TrafficAnalytics = {
    intersection_id: intersectionId,
    performance_index: 82,
    throughput_pct_change: 15.0,
    avg_delay_pct_change: -19.0,
    stops_per_veh_pct_change: -22.0,
    occupancy_pct: 76,
    avg_speed_kmh: 34.6,
    avg_queue_m: 87,
    backlog_m: 45,
    provenance: 'DEMO_FIXTURE' as DataProvenance,
  };

  return (
    <PanelFrame
      title="Traffic & Operations Analytics"
      icon={<BarChart3 size={15} color="#00e5ff" />}
      badge={
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <StatusPill label="Benchmarks" variant="cyan" size="xs" />
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
        <div style={{ display: 'flex', alignItems: 'center', gap: '3px', fontSize: '0.60rem' }}>
          <span style={{ color: '#64748b' }}>Index:</span>
          <span style={{ color: '#06d6a0', fontWeight: 700, fontFamily: 'monospace' }}>82/100</span>
        </div>
      }
      className={className}
      style={style}
    >
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1.25fr 1fr',
          gridTemplateRows: '1fr 1fr',
          gap: '6px',
          padding: '8px 10px',
          height: '100%',
          boxSizing: 'border-box',
        }}
      >
        {/* Quadrant 1 (Top-Left): Real-time Traffic Volume (veh/h) */}
        <div
          style={{
            background: '#0a1128',
            padding: '5px 8px',
            borderRadius: '4px',
            border: '1px solid #162547',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.64rem', marginBottom: '2px' }}>
            <span style={{ color: '#94a3b8', fontWeight: 500 }}>Real-time Volume (veh/h)</span>
            <div style={{ display: 'flex', gap: '6px', fontSize: '0.58rem' }}>
              <span style={{ color: '#00e5ff' }}>■ Current</span>
              <span style={{ color: '#64748b' }}>■ 15-min Avg</span>
            </div>
          </div>

          {/* Bar Chart Area */}
          <div
            style={{
              display: 'flex',
              alignItems: 'flex-end',
              justifyContent: 'space-around',
              height: '52px',
              paddingTop: '2px',
            }}
          >
            {VOLUME_DATA.map((v) => {
              const isSelected = selectedApproach?.approach === v.approach;
              return (
                <div
                  key={v.approach}
                  onClick={() => setSelectedApproach(isSelected ? null : v)}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '2px',
                    cursor: 'pointer',
                    padding: '2px 3px',
                    borderRadius: '3px',
                    backgroundColor: isSelected ? 'rgba(0, 229, 255, 0.15)' : 'transparent',
                  }}
                  title={`Click to inspect ${v.name} vehicle split`}
                >
                  <span style={{ fontSize: '0.55rem', color: isSelected ? '#00f5d4' : '#cbd5e1', fontFamily: 'monospace' }}>
                    {v.volumeVehH.toLocaleString()}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'flex-end', gap: '2px' }}>
                    {/* Current Volume Bar */}
                    <div
                      style={{
                        width: '12px',
                        height: `${Math.round((v.volumeVehH / 2200) * 44)}px`,
                        backgroundColor: '#00e5ff',
                        borderRadius: '2px 2px 0 0',
                        boxShadow: isSelected ? '0 0 6px #00e5ff' : 'none',
                        transition: 'height 0.3s ease',
                      }}
                    />
                    {/* 15-min Avg Bar */}
                    <div
                      style={{
                        width: '8px',
                        height: `${Math.round((v.avg15MinVehH / 2200) * 44)}px`,
                        backgroundColor: '#334155',
                        borderRadius: '2px 2px 0 0',
                      }}
                    />
                  </div>
                  <span style={{ fontSize: '0.60rem', color: '#64748b', fontWeight: 600 }}>{v.approach}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Quadrant 2 (Top-Right): Average Travel Time Horizontal Bars */}
        <div
          style={{
            background: '#0a1128',
            padding: '5px 8px',
            borderRadius: '4px',
            border: '1px solid #162547',
            fontSize: '0.66rem',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ color: '#94a3b8', fontSize: '0.62rem', marginBottom: '2px', display: 'flex', justifyContent: 'space-between' }}>
            <span>Avg Travel Time (zone)</span>
            <span style={{ color: '#64748b', fontSize: '0.58rem' }}>vs Baseline</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            {TRAVEL_TIMES.map((tt) => {
              const isImproved = tt.deltaPct < 0;
              return (
                <div key={tt.corridor} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ color: '#cbd5e1', fontSize: '0.64rem', fontFamily: 'monospace' }}>{tt.corridor}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <div
                      style={{
                        width: '42px',
                        height: '4px',
                        backgroundColor: '#162547',
                        borderRadius: '2px',
                        overflow: 'hidden',
                      }}
                    >
                      <div
                        style={{
                          width: `${Math.min(100, (tt.travelTimeMin / 4.5) * 100)}%`,
                          height: '100%',
                          backgroundColor: isImproved ? '#00e5ff' : '#ffd166',
                        }}
                      />
                    </div>
                    <span style={{ fontFamily: 'monospace', fontSize: '0.64rem', color: '#f1f5f9' }}>
                      {tt.travelTimeMin}m
                    </span>
                    <span
                      style={{
                        color: isImproved ? '#06d6a0' : '#ef476f',
                        fontSize: '0.58rem',
                        fontWeight: 600,
                        width: '35px',
                        textAlign: 'right',
                      }}
                    >
                      {isImproved ? '' : '+'}{tt.deltaPct}%
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Quadrant 3 (Bottom-Left): Radial Performance Index Gauge */}
        <div
          style={{
            background: '#0a1128',
            padding: '5px 8px',
            borderRadius: '4px',
            border: '1px solid #162547',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          {/* Radial Circular Progress Gauge */}
          <div
            style={{
              position: 'relative',
              width: '52px',
              height: '52px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <svg viewBox="0 0 36 36" style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)' }}>
              {/* Background Track */}
              <circle
                cx="18"
                cy="18"
                r="15.9155"
                fill="none"
                stroke="#162547"
                strokeWidth="3.4"
              />
              {/* Foreground Progress Ring */}
              <circle
                cx="18"
                cy="18"
                r="15.9155"
                fill="none"
                stroke="#06d6a0"
                strokeWidth="3.4"
                strokeDasharray="82, 100"
                strokeLinecap="round"
              />
            </svg>
            <div style={{ position: 'absolute', textAlign: 'center' }}>
              <div style={{ fontSize: '0.90rem', fontWeight: 800, color: '#06d6a0', fontFamily: 'monospace' }}>
                82
              </div>
              <div style={{ fontSize: '0.48rem', color: '#64748b' }}>/100</div>
            </div>
          </div>

          {/* Key KPI Deltas: Throughput, Avg Delay, Stops */}
          <div style={{ flex: 1, fontSize: '0.62rem', display: 'flex', flexDirection: 'column', gap: '2px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ color: '#94a3b8' }}>Throughput:</span>
              <span style={{ color: '#06d6a0', fontWeight: 600 }}>+15%</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ color: '#94a3b8' }}>Avg. Delay:</span>
              <span style={{ color: '#06d6a0', fontWeight: 600 }}>-19%</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ color: '#94a3b8' }}>Stops / Veh:</span>
              <span style={{ color: '#06d6a0', fontWeight: 600 }}>-22%</span>
            </div>
          </div>
        </div>

        {/* Quadrant 4 (Bottom-Right): Anomaly Alerts Feed */}
        <div
          style={{
            background: '#0a1128',
            padding: '4px 6px',
            borderRadius: '4px',
            border: '1px solid #162547',
            display: 'flex',
            flexDirection: 'column',
            gap: '2px',
            overflowY: 'auto',
            fontSize: '0.60rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #162547', paddingBottom: '2px' }}>
            <span style={{ color: '#94a3b8', fontWeight: 600 }}>Live Anomaly Feed</span>
            <div style={{ display: 'flex', gap: '3px' }}>
              <button
                type="button"
                onClick={() => setAlertFilter('all')}
                style={{
                  background: alertFilter === 'all' ? '#1b2f5b' : 'transparent',
                  border: 'none',
                  color: alertFilter === 'all' ? '#00e5ff' : '#64748b',
                  fontSize: '0.56rem',
                  cursor: 'pointer',
                  padding: '1px 3px',
                  borderRadius: '2px',
                }}
              >
                All
              </button>
              <button
                type="button"
                onClick={() => setAlertFilter('critical')}
                style={{
                  background: alertFilter === 'critical' ? '#1b2f5b' : 'transparent',
                  border: 'none',
                  color: alertFilter === 'critical' ? '#ef476f' : '#64748b',
                  fontSize: '0.56rem',
                  cursor: 'pointer',
                  padding: '1px 3px',
                  borderRadius: '2px',
                }}
              >
                Crit
              </button>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', marginTop: '2px' }}>
            {filteredAlerts.length === 0 ? (
              <div style={{ color: '#64748b', fontStyle: 'italic', textAlign: 'center', padding: '4px' }}>
                Zero active anomalies
              </div>
            ) : (
              filteredAlerts.map((alert) => (
                <div
                  key={alert.id}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '4px',
                    padding: '2px',
                    borderRadius: '2px',
                    backgroundColor: 'rgba(11, 21, 45, 0.4)',
                  }}
                >
                  {alert.severity === 'critical' ? (
                    <AlertCircle size={11} color="#ef476f" style={{ flexShrink: 0, marginTop: '1px' }} />
                  ) : alert.severity === 'warning' ? (
                    <AlertTriangle size={11} color="#ffd166" style={{ flexShrink: 0, marginTop: '1px' }} />
                  ) : (
                    <CheckCircle size={11} color="#00e5ff" style={{ flexShrink: 0, marginTop: '1px' }} />
                  )}
                  <div style={{ flex: 1, overflow: 'hidden' }}>
                    <span
                      style={{
                        color: alert.severity === 'critical' ? '#ef476f' : alert.severity === 'warning' ? '#ffd166' : '#00e5ff',
                        fontWeight: 700,
                      }}
                    >
                      {alert.title}:{' '}
                    </span>
                    <span style={{ color: '#cbd5e1' }}>{alert.message}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => dismissAlert(alert.id)}
                    style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', padding: 0 }}
                    title="Dismiss alert"
                  >
                    <X size={10} />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Selected Volume Approach Modal / Drawer */}
        {selectedApproach && (
          <div
            style={{
              gridColumn: 'span 2',
              backgroundColor: '#0a1428',
              border: '1px solid #00e5ff55',
              borderRadius: '4px',
              padding: '4px 8px',
              fontSize: '0.62rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <span style={{ color: '#00e5ff', fontWeight: 700 }}>{selectedApproach.name}</span>
              <span style={{ color: '#94a3b8', marginLeft: '6px' }}>
                Volume: <strong>{selectedApproach.volumeVehH} veh/h</strong> | Cars: {selectedApproach.carPct}% | Motos: {selectedApproach.motorcyclePct}% | Buses: {selectedApproach.busPct}%
              </span>
            </div>
            <button
              type="button"
              onClick={() => setSelectedApproach(null)}
              style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}
            >
              <X size={12} />
            </button>
          </div>
        )}
      </div>
    </PanelFrame>
  );
};

export default OperationsAnalyticsPanel;

