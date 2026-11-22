import React, { useState, useEffect } from 'react';
import { Activity, Bell, Settings, ShieldCheck } from 'lucide-react';

interface TopBarProps {
  simulationTime?: string;
  isSimulatedMode?: boolean;
}

export const TopBar: React.FC<TopBarProps> = ({
  simulationTime = '2025-01-15 14:27:36',
  isSimulatedMode = true,
}) => {
  const [realTime, setRealTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setRealTime(now.toTimeString().split(' ')[0]);
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

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
      }}
    >
      {/* Left Brand and Suite Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <span style={{ fontSize: '0.8rem', color: '#94a3b8', fontWeight: 500, letterSpacing: '0.04em' }}>
          Smart City Operations Suite
        </span>
        <div style={{ height: '14px', width: '1px', backgroundColor: '#334155' }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={18} color="#00f5d4" />
          <span style={{ fontSize: '0.95rem', fontWeight: 700, letterSpacing: '0.02em', color: '#00e5ff' }}>
            ClearWay AI
          </span>
          <span style={{ fontSize: '0.85rem', color: '#cbd5e1', fontWeight: 500 }}>
            — Traffic Control Digital Twin
          </span>
        </div>
      </div>

      {/* Center Provenance Notice */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'rgba(15, 23, 42, 0.8)',
          padding: '3px 12px',
          borderRadius: '20px',
          border: '1px solid #1e293b',
          fontSize: '0.75rem',
        }}
      >
        <ShieldCheck size={14} color="#06d6a0" />
        <span style={{ color: '#94a3b8' }}>Safety Gate:</span>
        <span style={{ color: '#06d6a0', fontWeight: 600 }}>SIMULATION ONLY</span>
        <span style={{ color: '#64748b' }}>|</span>
        <span style={{ color: '#f59e0b', fontWeight: 500 }}>DEMO FIXTURE</span>
      </div>

      {/* Right Controls, Clock, and Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* Mode Pill */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            backgroundColor: isSimulatedMode ? 'rgba(6, 214, 160, 0.12)' : 'rgba(239, 71, 111, 0.12)',
            color: isSimulatedMode ? '#06d6a0' : '#ef476f',
            border: `1px solid ${isSimulatedMode ? 'rgba(6, 214, 160, 0.3)' : 'rgba(239, 71, 111, 0.3)'}`,
            padding: '2px 10px',
            borderRadius: '12px',
            fontSize: '0.75rem',
            fontWeight: 700,
          }}
        >
          <span style={{ width: '7px', height: '7px', borderRadius: '50%', backgroundColor: '#06d6a0' }} />
          LIVE SIM
        </div>

        {/* Timestamps: Simulation vs Wall Clock */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', fontSize: '0.72rem' }}>
          <div style={{ fontFamily: 'monospace', color: '#e2e8f0', fontWeight: 600 }}>
            {simulationTime} <span style={{ color: '#38bdf8' }}>(SIM)</span>
          </div>
          <div style={{ fontFamily: 'monospace', color: '#64748b', fontSize: '0.68rem' }}>
            Host UTC: {realTime || '14:27:36'}
          </div>
        </div>

        {/* Icons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: '#94a3b8' }}>
          <div style={{ position: 'relative', cursor: 'pointer' }}>
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
          <div style={{ cursor: 'pointer' }}>
            <Settings size={16} />
          </div>
          <div
            style={{
              width: '26px',
              height: '26px',
              borderRadius: '50%',
              backgroundColor: '#1b2f5b',
              border: '1px solid #38bdf8',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '0.72rem',
              fontWeight: 600,
              color: '#38bdf8',
            }}
          >
            OP
          </div>
        </div>
      </div>
    </header>
  );
};

