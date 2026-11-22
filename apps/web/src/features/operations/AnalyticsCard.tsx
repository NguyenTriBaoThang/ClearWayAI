import React from 'react';
import { BarChart3, AlertTriangle, AlertCircle, ArrowUpRight, ArrowDownRight } from 'lucide-react';

export const AnalyticsCard: React.FC = () => {
  return (
    <div className="panel-card" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <BarChart3 size={14} color="#00e5ff" />
          <span>Traffic & Operations Analytics</span>
        </div>
        <span style={{ fontSize: '0.68rem', color: '#64748b' }}>Cross-Approach Benchmarks</span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1.2fr 1fr',
          gridTemplateRows: '1fr 1fr',
          gap: '8px',
          padding: '10px',
          flex: 1,
        }}
      >
        {/* Top-Left: Real-time Traffic Volume Bar Chart */}
        <div style={{ background: '#0a1128', padding: '6px 8px', borderRadius: '4px', border: '1px solid #162547' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.66rem', marginBottom: '4px' }}>
            <span style={{ color: '#94a3b8' }}>Real-time Traffic Volume (veh/h)</span>
            <div style={{ display: 'flex', gap: '6px', fontSize: '0.6rem' }}>
              <span style={{ color: '#00e5ff' }}>■ Current</span>
              <span style={{ color: '#64748b' }}>■ 15-min Avg</span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-around', height: '55px', paddingTop: '4px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px' }}>
              <span style={{ fontSize: '0.55rem', color: '#cbd5e1' }}>1,210</span>
              <div style={{ width: '16px', height: '30px', backgroundColor: '#00e5ff', borderRadius: '2px 2px 0 0' }} />
              <span style={{ fontSize: '0.62rem', color: '#64748b' }}>NB</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px' }}>
              <span style={{ fontSize: '0.55rem', color: '#cbd5e1' }}>1,438</span>
              <div style={{ width: '16px', height: '36px', backgroundColor: '#00e5ff', borderRadius: '2px 2px 0 0' }} />
              <span style={{ fontSize: '0.62rem', color: '#64748b' }}>SB</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px' }}>
              <span style={{ fontSize: '0.55rem', color: '#cbd5e1' }}>2,185</span>
              <div style={{ width: '16px', height: '48px', backgroundColor: '#00e5ff', borderRadius: '2px 2px 0 0' }} />
              <span style={{ fontSize: '0.62rem', color: '#64748b' }}>EB</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px' }}>
              <span style={{ fontSize: '0.55rem', color: '#cbd5e1' }}>2,061</span>
              <div style={{ width: '16px', height: '45px', backgroundColor: '#00e5ff', borderRadius: '2px 2px 0 0' }} />
              <span style={{ fontSize: '0.62rem', color: '#64748b' }}>WB</span>
            </div>
          </div>
        </div>

        {/* Top-Right: Avg Travel Time Horizontal Bars */}
        <div style={{ background: '#0a1128', padding: '6px 8px', borderRadius: '4px', border: '1px solid #162547', fontSize: '0.68rem' }}>
          <div style={{ color: '#94a3b8', fontSize: '0.66rem', marginBottom: '6px' }}>Avg Travel Time (zone)</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ color: '#cbd5e1' }}>N → S</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <div style={{ width: '45px', height: '6px', background: '#00e5ff', borderRadius: '3px' }} />
                <span style={{ fontFamily: 'monospace' }}>2.6m</span>
                <span style={{ color: '#06d6a0', fontSize: '0.6rem' }}>(-18%)</span>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ color: '#cbd5e1' }}>S → N</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <div style={{ width: '50px', height: '6px', background: '#00e5ff', borderRadius: '3px' }} />
                <span style={{ fontFamily: 'monospace' }}>2.8m</span>
                <span style={{ color: '#06d6a0', fontSize: '0.6rem' }}>(-17%)</span>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ color: '#cbd5e1' }}>E → W</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <div style={{ width: '70px', height: '6px', background: '#38bdf8', borderRadius: '3px' }} />
                <span style={{ fontFamily: 'monospace' }}>3.9m</span>
                <span style={{ color: '#ef476f', fontSize: '0.6rem' }}>(+6%)</span>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ color: '#cbd5e1' }}>W → E</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <div style={{ width: '65px', height: '6px', background: '#38bdf8', borderRadius: '3px' }} />
                <span style={{ fontFamily: 'monospace' }}>3.7m</span>
                <span style={{ color: '#ef476f', fontSize: '0.6rem' }}>(+4%)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom-Left: Intersection Performance Index Gauge */}
        <div style={{ background: '#0a1128', padding: '6px 8px', borderRadius: '4px', border: '1px solid #162547', display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Circular Indicator */}
          <div style={{ position: 'relative', width: '56px', height: '56px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg viewBox="0 0 36 36" style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)' }}>
              <path
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#162547"
                strokeWidth="3.5"
              />
              <path
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#06d6a0"
                strokeWidth="3.5"
                strokeDasharray="82, 100"
              />
            </svg>
            <div style={{ position: 'absolute', textAlign: 'center' }}>
              <div style={{ fontSize: '0.95rem', fontWeight: 800, color: '#06d6a0', fontFamily: 'monospace' }}>82</div>
              <div style={{ fontSize: '0.5rem', color: '#64748b' }}>/100</div>
            </div>
          </div>

          {/* Performance Deltas */}
          <div style={{ flex: 1, fontSize: '0.65rem', display: 'flex', flexDirection: 'column', gap: '3px' }}>
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

        {/* Bottom-Right: Anomaly Detection & Alerts */}
        <div style={{ background: '#0a1128', padding: '6px 8px', borderRadius: '4px', border: '1px solid #162547', display: 'flex', flexDirection: 'column', gap: '4px', overflowY: 'auto', fontSize: '0.64rem' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '5px' }}>
            <AlertCircle size={13} color="#ef476f" style={{ flexShrink: 0, marginTop: '1px' }} />
            <div>
              <span style={{ color: '#ef476f', fontWeight: 700 }}>Critical: </span>
              <span style={{ color: '#cbd5e1' }}>Emergency vehicle AMB-339 active priority.</span>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '5px' }}>
            <AlertTriangle size={13} color="#ffd166" style={{ flexShrink: 0, marginTop: '1px' }} />
            <div>
              <span style={{ color: '#ffd166', fontWeight: 700 }}>Warning: </span>
              <span style={{ color: '#cbd5e1' }}>Rising queue on 5th Ave. (EB) (87m).</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
