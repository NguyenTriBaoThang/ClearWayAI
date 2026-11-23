import React, { useState, useEffect } from 'react';
import { Activity, Bell, Settings, ShieldCheck, ChevronDown, Radio, Flame } from 'lucide-react';
import { StatusPill } from '../components/StatusPill';

interface TopBarProps {
  simulationTime?: string;
  isSimulatedMode?: boolean;
  connectionStatus?: 'CONNECTED' | 'CONNECTING' | 'DISCONNECTED' | 'SIMULATED';
  latencyMs?: number;
}

export const TopBar: React.FC<TopBarProps> = ({
  simulationTime = '2025-01-15 14:27:36',
  isSimulatedMode = true,
  connectionStatus = 'CONNECTED',
  latencyMs = 11,
}) => {
  const [realTime, setRealTime] = useState<string>('');
  const [simSeconds, setSimSeconds] = useState<number>(36);
  const [selectedIntersection, setSelectedIntersection] = useState<string>('INT-0457');
  const [isEmergencyActive, setIsEmergencyActive] = useState<boolean>(true);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setRealTime(now.toTimeString().split(' ')[0]);
      setSimSeconds((prev) => (prev + 1) % 60);
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const formattedSimTime = `${simulationTime.slice(0, 17)}${simSeconds < 10 ? '0' + simSeconds : simSeconds}`;

  return (
    <header
      style={{
        height: '48px',
        backgroundColor: '#0a1128',
        borderBottom: '1px solid #1b2f5b',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 16px',
        color: '#f8fafc',
        zIndex: 50,
        flexShrink: 0,
      }}
    >
      {/* Left: Brand, Suite Title, and Intersection Selector */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '6px',
              backgroundColor: 'rgba(0, 229, 255, 0.15)',
              border: '1px solid rgba(0, 229, 255, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#00e5ff',
            }}
          >
            <Activity size={16} />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span
              style={{
                fontSize: '0.90rem',
                fontWeight: 800,
                letterSpacing: '0.04em',
                color: '#00e5ff',
                lineHeight: 1.1,
              }}
            >
              CLEARWAY AI
            </span>
            <span
              style={{
                fontSize: '0.62rem',
                color: '#94a3b8',
                fontWeight: 600,
                letterSpacing: '0.08em',
              }}
            >
              DIGITAL TWIN OPS
            </span>
          </div>
        </div>

        <div style={{ height: '18px', width: '1px', backgroundColor: '#1b2f5b' }} />

        {/* Intersection Quick Switcher */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            backgroundColor: '#0d1b38',
            border: '1px solid #1b2f5b',
            padding: '3px 10px',
            borderRadius: '6px',
            fontSize: '0.72rem',
            cursor: 'pointer',
          }}
          title="Active Monitored Intersection"
        >
          <span
            style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              backgroundColor: '#00e5ff',
              display: 'inline-block',
            }}
          />
          <span style={{ color: '#94a3b8' }}>Target:</span>
          <span style={{ color: '#f8fafc', fontWeight: 600, fontFamily: 'monospace' }}>
            {selectedIntersection}
          </span>
          <span style={{ color: '#cbd5e1' }}>(Oak St & 5th Ave)</span>
          <ChevronDown size={13} color="#64748b" />
        </div>
      </div>

      {/* Center: Safety Gate, Active Phase, and Emergency Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {/* Safety Gate Provenance Badge */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: 'rgba(11, 21, 45, 0.8)',
            padding: '3px 10px',
            borderRadius: '14px',
            border: '1px solid #1b2f5b',
            fontSize: '0.72rem',
          }}
        >
          <ShieldCheck size={14} color="#06d6a0" />
          <span style={{ color: '#94a3b8' }}>Safety Gate:</span>
          <span style={{ color: '#06d6a0', fontWeight: 700 }}>SIMULATION ONLY</span>
          <span style={{ color: '#64748b' }}>|</span>
          <span style={{ color: '#ffd166', fontWeight: 600 }}>DEMO FIXTURE</span>
        </div>

        {/* Active Phase Pill */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            backgroundColor: 'rgba(6, 214, 160, 0.12)',
            border: '1px solid rgba(6, 214, 160, 0.35)',
            padding: '3px 8px',
            borderRadius: '12px',
            fontSize: '0.70rem',
          }}
        >
          <span
            className="live-pulse-green"
            style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#06d6a0' }}
          />
          <span style={{ color: '#94a3b8' }}>Signal:</span>
          <span style={{ color: '#06d6a0', fontWeight: 700, fontFamily: 'monospace' }}>
            P3 E-W Thru (24s)
          </span>
        </div>

        {/* Emergency Corridor Status Indicator */}
        <button
          onClick={() => setIsEmergencyActive(!isEmergencyActive)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            backgroundColor: isEmergencyActive ? 'rgba(239, 71, 111, 0.15)' : 'rgba(100, 116, 139, 0.15)',
            border: `1px solid ${isEmergencyActive ? 'rgba(239, 71, 111, 0.4)' : '#334155'}`,
            color: isEmergencyActive ? '#ef476f' : '#94a3b8',
            padding: '3px 8px',
            borderRadius: '12px',
            fontSize: '0.70rem',
            cursor: 'pointer',
            fontWeight: 600,
          }}
          title="Click to toggle Emergency Vehicle Pre-emption demonstration"
        >
          <Flame size={12} color={isEmergencyActive ? '#ef476f' : '#94a3b8'} />
          <span>EV Corridor: {isEmergencyActive ? 'AMB-339 (PRIORITY)' : 'STANDBY'}</span>
        </button>
      </div>

      {/* Right: Telemetry Tickers, Timestamps, and User Avatar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {/* Telemetry Pills: FPS & Latency */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <StatusPill label="60 FPS" variant="green" size="xs" />
          <StatusPill label={`${latencyMs}ms`} variant="cyan" size="xs" />
          <StatusPill
            label={
              connectionStatus === 'CONNECTED'
                ? 'WS ONLINE'
                : connectionStatus === 'SIMULATED'
                ? 'WS SIMULATED'
                : 'WS CONNECTING'
            }
            variant={
              connectionStatus === 'CONNECTED'
                ? 'green'
                : connectionStatus === 'SIMULATED'
                ? 'amber'
                : 'cyan'
            }
            size="xs"
            pulse={connectionStatus === 'CONNECTED'}
          />
        </div>

        {/* Timestamps: Simulation vs Wall Clock */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', fontSize: '0.70rem' }}>
          <div style={{ fontFamily: 'monospace', color: '#00e5ff', fontWeight: 600 }}>
            {formattedSimTime} <span style={{ color: '#38bdf8', fontSize: '0.65rem' }}>[SIM]</span>
          </div>
          <div style={{ fontFamily: 'monospace', color: '#64748b', fontSize: '0.64rem' }}>
            Host UTC: {realTime || '14:27:36'}
          </div>
        </div>

        {/* Icons & Avatar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#94a3b8' }}>
          <div style={{ position: 'relative', cursor: 'pointer' }} title="Alerts & Incidents (4 active)">
            <Bell size={16} />
            <span
              style={{
                position: 'absolute',
                top: '-4px',
                right: '-4px',
                width: '12px',
                height: '12px',
                backgroundColor: '#ef476f',
                borderRadius: '50%',
                fontSize: '0.55rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                fontWeight: 700,
              }}
            >
              4
            </span>
          </div>

          <div style={{ cursor: 'pointer' }} title="Simulation & Twin Settings">
            <Settings size={16} />
          </div>

          <div
            title="Logged in as Operator: Traffic Control Specialist"
            style={{
              width: '26px',
              height: '26px',
              borderRadius: '50%',
              backgroundColor: '#122347',
              border: '1px solid #00e5ff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '0.70rem',
              fontWeight: 700,
              color: '#00e5ff',
              cursor: 'pointer',
            }}
          >
            OP
          </div>
        </div>
      </div>
    </header>
  );
};
