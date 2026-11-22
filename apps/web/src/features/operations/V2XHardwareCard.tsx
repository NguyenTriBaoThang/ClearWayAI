import React from 'react';
import { Wifi, Radio, Server, Cpu, CheckCircle } from 'lucide-react';
import { PanelFrame } from '../../components/PanelFrame';
import { StatusPill } from '../../components/StatusPill';

export const V2XHardwareCard: React.FC = () => {
  return (
    <PanelFrame
      title="V2I/V2V Communication & Hardware Status"
      icon={<Wifi size={15} />}
      badge={
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '0.66rem', color: '#64748b' }}>Network ID:</span>
          <span style={{ fontSize: '0.70rem', color: '#00f5d4', fontFamily: 'monospace', fontWeight: 600 }}>
            RM-INT-0457
          </span>
        </div>
      }
    >
      <div
        style={{
          padding: '10px 12px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          height: '100%',
          gap: '8px',
        }}
      >
        {/* Hardware Flow Diagram / Nodes Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '6px',
            backgroundColor: 'rgba(11, 21, 45, 0.6)',
            padding: '8px 4px',
            borderRadius: '6px',
            border: '1px solid #1b2f5b',
            textAlign: 'center',
          }}
        >
          {/* Node 1: On-Board Units */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px' }}>
            <Cpu size={15} color="#00e5ff" />
            <div style={{ fontSize: '0.62rem', color: '#94a3b8' }}>On-Board Units (Veh)</div>
            <div style={{ fontSize: '0.76rem', fontWeight: 700, color: '#06d6a0', fontFamily: 'monospace' }}>
              1,842 Online
            </div>
            <div style={{ fontSize: '0.60rem', color: '#64748b' }}>(99.2%)</div>
          </div>

          {/* Node 2: RSU */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px' }}>
            <Radio size={15} color="#00f5d4" />
            <div style={{ fontSize: '0.62rem', color: '#94a3b8' }}>RSU (Roadside Unit)</div>
            <div style={{ fontSize: '0.76rem', fontWeight: 700, color: '#06d6a0', fontFamily: 'monospace' }}>
              42 Online
            </div>
            <div style={{ fontSize: '0.60rem', color: '#64748b' }}>(100%)</div>
          </div>

          {/* Node 3: Edge Controller */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px' }}>
            <Server size={15} color="#00e5ff" />
            <div style={{ fontSize: '0.62rem', color: '#94a3b8' }}>Edge Controller</div>
            <div style={{ fontSize: '0.76rem', fontWeight: 700, color: '#06d6a0', fontFamily: 'monospace' }}>
              Online
            </div>
            <div style={{ fontSize: '0.60rem', color: '#64748b' }}>(Primary)</div>
          </div>

          {/* Node 4: Signal Controller */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px' }}>
            <ActivitySvg size={15} color="#ffd166" />
            <div style={{ fontSize: '0.62rem', color: '#94a3b8' }}>Signal Controller</div>
            <div style={{ fontSize: '0.76rem', fontWeight: 700, color: '#06d6a0', fontFamily: 'monospace' }}>
              Online
            </div>
            <div style={{ fontSize: '0.60rem', color: '#64748b' }}>(C-V2X / DSRC)</div>
          </div>
        </div>

        {/* Telemetry Metrics Footer */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '5px 8px',
            backgroundColor: '#0a1128',
            borderRadius: '4px',
            border: '1px solid #162547',
            fontSize: '0.70rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <CheckCircle size={13} color="#06d6a0" />
            <span style={{ color: '#94a3b8' }}>V2X Link:</span>
            <StatusPill label="Active (Simulated)" variant="green" size="xs" />
          </div>
          <div>
            <span style={{ color: '#94a3b8' }}>Latency: </span>
            <span style={{ color: '#00f5d4', fontWeight: 600, fontFamily: 'monospace' }}>11 ms</span>
          </div>
          <div>
            <span style={{ color: '#94a3b8' }}>Packet Loss: </span>
            <span style={{ color: '#06d6a0', fontWeight: 600, fontFamily: 'monospace' }}>0.2%</span>
          </div>
        </div>
      </div>
    </PanelFrame>
  );
};

const ActivitySvg: React.FC<{ size: number; color: string }> = ({ size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
  </svg>
);
