import React from 'react';
import { Wifi, Radio, Server, Cpu, CheckCircle } from 'lucide-react';

export const V2XHardwareCard: React.FC = () => {
  return (
    <div className="panel-card" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Wifi size={14} color="#00e5ff" />
          <span>V2I/V2V Communication & Hardware Status</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '0.68rem', color: '#64748b' }}>Network ID:</span>
          <span style={{ fontSize: '0.72rem', color: '#00f5d4', fontFamily: 'monospace', fontWeight: 600 }}>
            RM-INT-0457
          </span>
        </div>
      </div>

      <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '12px', flex: 1, justifyContent: 'space-between' }}>
        {/* Hardware Flow Diagram */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '8px',
            background: 'rgba(11, 21, 45, 0.6)',
            padding: '10px 6px',
            borderRadius: '6px',
            border: '1px solid #1b2f5b',
            textAlign: 'center',
          }}
        >
          {/* Node 1: On-Board Units */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
            <Cpu size={16} color="#00e5ff" />
            <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>On-Board Units (Vehicles)</div>
            <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#06d6a0' }}>1,842 Online</div>
            <div style={{ fontSize: '0.62rem', color: '#64748b' }}>(99.2%)</div>
          </div>

          {/* Node 2: RSU */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
            <Radio size={16} color="#00f5d4" />
            <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>RSU (Roadside Unit)</div>
            <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#06d6a0' }}>42 Online</div>
            <div style={{ fontSize: '0.62rem', color: '#64748b' }}>(100%)</div>
          </div>

          {/* Node 3: Edge Controller */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
            <Server size={16} color="#00e5ff" />
            <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>Edge Controller (Intersection)</div>
            <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#06d6a0' }}>Online</div>
            <div style={{ fontSize: '0.62rem', color: '#64748b' }}>(Primary)</div>
          </div>

          {/* Node 4: Signal Controller */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
            <ActivityIcon size={16} color="#ffd166" />
            <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>Signal Controller (8 Phases)</div>
            <div style={{ fontSize: '0.78rem', fontWeight: 700, color: '#06d6a0' }}>Online</div>
            <div style={{ fontSize: '0.62rem', color: '#64748b' }}>(V2I C-V2X / DSRC)</div>
          </div>
        </div>

        {/* Telemetry Metrics Footer */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '6px 10px',
            backgroundColor: '#0a1128',
            borderRadius: '6px',
            border: '1px solid #162547',
            fontSize: '0.72rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <CheckCircle size={13} color="#06d6a0" />
            <span style={{ color: '#94a3b8' }}>V2X Status:</span>
            <span style={{ color: '#06d6a0', fontWeight: 600 }}>Active (Simulated)</span>
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
    </div>
  );
};

const ActivityIcon: React.FC<{ size: number; color: string }> = ({ size, color }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
  </svg>
);

