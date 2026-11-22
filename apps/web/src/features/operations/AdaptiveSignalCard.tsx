import React from 'react';
import { Sliders, TrendingDown } from 'lucide-react';
import { PanelFrame } from '../../components/PanelFrame';
import { StatusPill } from '../../components/StatusPill';

export const AdaptiveSignalCard: React.FC = () => {
  return (
    <PanelFrame
      title="Adaptive Signal Control (RL Agent)"
      icon={<Sliders size={15} />}
      badge={<StatusPill label="Active Logic" variant="cyan" size="xs" pulse />}
    >
      <div
        style={{
          padding: '8px 10px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          height: '100%',
          justifyContent: 'space-between',
        }}
      >
        {/* Top KPIs: Cycle, Current, Next Phase */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.25fr 1.25fr', gap: '6px' }}>
          <div style={{ background: '#0a1128', padding: '5px 8px', borderRadius: '4px', border: '1px solid #162547' }}>
            <div style={{ fontSize: '0.62rem', color: '#94a3b8' }}>Cycle Time</div>
            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f8fafc', fontFamily: 'monospace' }}>
              120s
            </div>
          </div>
          <div style={{ background: '#0a1128', padding: '5px 8px', borderRadius: '4px', border: '1px solid #162547' }}>
            <div style={{ fontSize: '0.62rem', color: '#94a3b8' }}>Current Phase</div>
            <div style={{ fontSize: '0.76rem', fontWeight: 700, color: '#06d6a0', fontFamily: 'monospace' }}>
              P3 (E-W Thru)
            </div>
          </div>
          <div style={{ background: '#0a1128', padding: '5px 8px', borderRadius: '4px', border: '1px solid #162547' }}>
            <div style={{ fontSize: '0.62rem', color: '#94a3b8' }}>Next Phase</div>
            <div style={{ fontSize: '0.76rem', fontWeight: 700, color: '#38bdf8', fontFamily: 'monospace' }}>
              P4 (E-W Left)
            </div>
          </div>
        </div>

        {/* Phase Plan & Queue Length SVG Chart */}
        <div style={{ background: '#0a1128', padding: '5px 8px', borderRadius: '4px', border: '1px solid #162547' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2px', fontSize: '0.64rem' }}>
            <span style={{ color: '#94a3b8', fontWeight: 500 }}>Phase Plan & Queue Length</span>
            <div style={{ display: 'flex', gap: '8px', fontSize: '0.60rem' }}>
              <span style={{ color: '#00e5ff' }}>— Queue (veh)</span>
              <span style={{ color: '#ef476f' }}>--- Capacity</span>
              <span style={{ color: '#06d6a0', fontWeight: 600 }}>Occupancy: 76%</span>
            </div>
          </div>

          {/* Inline SVG Chart */}
          <svg viewBox="0 0 300 65" style={{ width: '100%', height: '50px', overflow: 'visible' }}>
            {/* Grid Lines */}
            <line x1="30" y1="10" x2="290" y2="10" stroke="#1e293b" strokeDasharray="2,2" />
            <line x1="30" y1="28" x2="290" y2="28" stroke="#1e293b" strokeDasharray="2,2" />
            <line x1="30" y1="46" x2="290" y2="46" stroke="#1e293b" strokeDasharray="2,2" />
            <line x1="30" y1="60" x2="290" y2="60" stroke="#334155" />

            {/* Capacity line (red stepped) */}
            <polyline
              points="30,55 80,55 90,18 210,18 220,55 290,55"
              fill="none"
              stroke="#ef476f"
              strokeWidth="1.5"
              strokeDasharray="4,2"
            />

            {/* Queue line (cyan curve) */}
            <polyline
              points="30,58 70,56 100,24 140,20 180,22 210,28 250,56 290,58"
              fill="none"
              stroke="#00e5ff"
              strokeWidth="2"
            />

            {/* Axis labels */}
            <text x="12" y="14" fill="#64748b" fontSize="7">120</text>
            <text x="12" y="32" fill="#64748b" fontSize="7">80</text>
            <text x="12" y="50" fill="#64748b" fontSize="7">40</text>
            <text x="75" y="64" fill="#64748b" fontSize="7">30</text>
            <text x="140" y="64" fill="#64748b" fontSize="7">60</text>
            <text x="205" y="64" fill="#64748b" fontSize="7">90</text>
            <text x="270" y="64" fill="#64748b" fontSize="7">120s</text>
          </svg>
        </div>

        {/* Bottom Optimization Metrics */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: '6px', fontSize: '0.70rem' }}>
          <div style={{ background: '#0a1128', padding: '4px 6px', borderRadius: '4px', border: '1px solid #162547' }}>
            <div style={{ fontSize: '0.60rem', color: '#94a3b8' }}>Optimization</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '3px', color: '#06d6a0', fontWeight: 700 }}>
              <TrendingDown size={13} /> -19% Delay
            </div>
          </div>

          <div style={{ background: '#0a1128', padding: '4px 6px', borderRadius: '4px', border: '1px solid #162547' }}>
            <div style={{ fontSize: '0.60rem', color: '#94a3b8' }}>Avg. Queue</div>
            <div style={{ color: '#00f5d4', fontWeight: 700, fontFamily: 'monospace' }}>87 m</div>
          </div>

          <div style={{ background: '#0a1128', padding: '4px 6px', borderRadius: '4px', border: '1px solid #162547' }}>
            <div style={{ fontSize: '0.60rem', color: '#94a3b8' }}>Backlog</div>
            <div style={{ color: '#ef476f', fontWeight: 700, fontFamily: 'monospace' }}>45 m</div>
          </div>
        </div>
      </div>
    </PanelFrame>
  );
};
