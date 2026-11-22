import React from 'react';
import { Sliders, TrendingDown, Layers } from 'lucide-react';

export const AdaptiveSignalCard: React.FC = () => {
  return (
    <div className="panel-card" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sliders size={14} color="#00e5ff" />
          <span>Adaptive Traffic Signal Control Dashboard</span>
        </div>
        <span style={{ fontSize: '0.68rem', color: '#06d6a0', fontWeight: 600 }}>● Active Logic</span>
      </div>

      <div style={{ padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: '8px', flex: 1, justifyContent: 'space-between' }}>
        {/* Top KPIs: Cycle, Current, Next Phase */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr 1.2fr', gap: '6px' }}>
          <div style={{ background: '#0a1128', padding: '6px 8px', borderRadius: '4px', border: '1px solid #162547' }}>
            <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>Cycle Time</div>
            <div style={{ fontSize: '0.88rem', fontWeight: 700, color: '#f8fafc', fontFamily: 'monospace' }}>120s</div>
          </div>
          <div style={{ background: '#0a1128', padding: '6px 8px', borderRadius: '4px', border: '1px solid #162547' }}>
            <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>Current Phase</div>
            <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#06d6a0', fontFamily: 'monospace' }}>P3 (E-W Thru)</div>
          </div>
          <div style={{ background: '#0a1128', padding: '6px 8px', borderRadius: '4px', border: '1px solid #162547' }}>
            <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>Next Phase</div>
            <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#38bdf8', fontFamily: 'monospace' }}>P4 (E-W Left)</div>
          </div>
        </div>

        {/* Phase Plan & Queue Length SVG Chart */}
        <div style={{ background: '#0a1128', padding: '6px', borderRadius: '4px', border: '1px solid #162547' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px', fontSize: '0.66rem' }}>
            <span style={{ color: '#94a3b8', fontWeight: 500 }}>Phase Plan & Queue Length</span>
            <div style={{ display: 'flex', gap: '8px', fontSize: '0.62rem' }}>
              <span style={{ color: '#00e5ff' }}>— Queue (veh)</span>
              <span style={{ color: '#ef476f' }}>--- Capacity</span>
              <span style={{ color: '#06d6a0', fontWeight: 600 }}>Occupancy: 76%</span>
            </div>
          </div>

          {/* Inline SVG Chart */}
          <svg viewBox="0 0 300 70" style={{ width: '100%', height: '55px', overflow: 'visible' }}>
            {/* Grid Lines */}
            <line x1="30" y1="10" x2="290" y2="10" stroke="#1e293b" strokeDasharray="2,2" />
            <line x1="30" y1="30" x2="290" y2="30" stroke="#1e293b" strokeDasharray="2,2" />
            <line x1="30" y1="50" x2="290" y2="50" stroke="#1e293b" strokeDasharray="2,2" />
            <line x1="30" y1="65" x2="290" y2="65" stroke="#334155" />

            {/* Capacity line (red stepped) */}
            <polyline
              points="30,60 80,60 90,20 210,20 220,60 290,60"
              fill="none"
              stroke="#ef476f"
              strokeWidth="1.5"
              strokeDasharray="4,2"
            />

            {/* Queue line (cyan curve) */}
            <polyline
              points="30,65 70,62 100,28 140,24 180,26 210,32 250,62 290,65"
              fill="none"
              stroke="#00e5ff"
              strokeWidth="2"
            />

            {/* Axis labels */}
            <text x="15" y="15" fill="#64748b" fontSize="8">120</text>
            <text x="15" y="35" fill="#64748b" fontSize="8">80</text>
            <text x="15" y="55" fill="#64748b" fontSize="8">40</text>
            <text x="75" y="69" fill="#64748b" fontSize="8">30</text>
            <text x="140" y="69" fill="#64748b" fontSize="8">60</text>
            <text x="205" y="69" fill="#64748b" fontSize="8">90</text>
            <text x="270" y="69" fill="#64748b" fontSize="8">120s</text>
          </svg>
        </div>

        {/* Bottom Optimization Metrics */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: '6px', fontSize: '0.72rem' }}>
          <div style={{ background: '#0a1128', padding: '5px 8px', borderRadius: '4px', border: '1px solid #162547' }}>
            <div style={{ fontSize: '0.62rem', color: '#94a3b8' }}>Phase Optimization</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#06d6a0', fontWeight: 700 }}>
              <TrendingDown size={14} /> -19% Delay
            </div>
            <div style={{ fontSize: '0.6rem', color: '#64748b' }}>(vs. fixed-time)</div>
          </div>

          <div style={{ background: '#0a1128', padding: '5px 8px', borderRadius: '4px', border: '1px solid #162547' }}>
            <div style={{ fontSize: '0.62rem', color: '#94a3b8' }}>Avg. Queue</div>
            <div style={{ color: '#00f5d4', fontWeight: 700, fontFamily: 'monospace' }}>87 m</div>
          </div>

          <div style={{ background: '#0a1128', padding: '5px 8px', borderRadius: '4px', border: '1px solid #162547' }}>
            <div style={{ fontSize: '0.62rem', color: '#94a3b8' }}>Backlog</div>
            <div style={{ color: '#ef476f', fontWeight: 700, fontFamily: 'monospace' }}>45 m</div>
          </div>
        </div>
      </div>
    </div>
  );
};
