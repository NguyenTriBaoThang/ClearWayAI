import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Box, LayoutDashboard, Cpu, ShieldCheck, Activity, ArrowRight, Database } from 'lucide-react';
import { fetchSystemStatus } from '../services/api';
import { SystemStatus } from '../types';

export const HomePage: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    fetchSystemStatus().then(setStatus);
  }, []);

  return (
    <div style={{ padding: '24px 32px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* Welcome Banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, #0d1b38 0%, #070d1e 100%)',
          border: '1px solid #1b2f5b',
          borderRadius: '12px',
          padding: '28px',
          marginBottom: '24px',
          boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
          <Activity size={22} color="#00f5d4" />
          <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '0.02em' }}>
            ClearWay AI
          </h1>
          <span
            style={{
              backgroundColor: 'rgba(0, 229, 255, 0.15)',
              color: '#00e5ff',
              fontSize: '0.72rem',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '12px',
              border: '1px solid rgba(0, 229, 255, 0.3)',
            }}
          >
            v0.1.0-alpha
          </span>
        </div>

        <p style={{ color: '#94a3b8', fontSize: '0.95rem', maxWidth: '800px', lineHeight: 1.6, marginBottom: '20px' }}>
          A high-fidelity 3D Digital Twin, Multi-Intersection Adaptive Signal Coordination, and Emergency Vehicle Pre-clearance platform.
          Central WebGL viewport synchronizes with SUMO microscopic traffic simulation and AI clearance estimation models.
        </p>

        {/* Safety & Provenance Box */}
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '12px',
            background: 'rgba(11, 21, 45, 0.7)',
            padding: '12px 16px',
            borderRadius: '8px',
            border: '1px solid #1e3a8a',
            fontSize: '0.8rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <ShieldCheck size={16} color="#06d6a0" />
            <span style={{ color: '#94a3b8' }}>Safety Gate:</span>
            <strong style={{ color: '#06d6a0' }}>{status?.mode || 'SIMULATION'} ONLY</strong>
          </div>
          <div style={{ color: '#334155' }}>|</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Database size={16} color="#ffd166" />
            <span style={{ color: '#94a3b8' }}>Data Provenance:</span>
            <strong style={{ color: '#ffd166' }}>{status?.data_provenance || 'DEMO_FIXTURE'}</strong>
          </div>
          <div style={{ color: '#334155' }}>|</div>
          <div style={{ color: '#cbd5e1' }}>
            Public Signal Override: <strong style={{ color: '#ef476f' }}>STRICTLY DISABLED</strong>
          </div>
        </div>
      </div>

      {/* Navigation Quick Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        <Link
          to="/dashboard"
          style={{
            backgroundColor: '#0d1b38',
            border: '1px solid #1b2f5b',
            borderRadius: '8px',
            padding: '20px',
            textDecoration: 'none',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            transition: 'border-color 0.2s',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
              <LayoutDashboard size={20} color="#00e5ff" />
              <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#f8fafc' }}>Operations Dashboard</h3>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.82rem', lineHeight: 1.5 }}>
              View the primary operations center matching the blueprint specification: V2X telemetry, phase timing table, adaptive queue chart, and 3D digital twin.
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#00e5ff', fontSize: '0.8rem', fontWeight: 600, marginTop: '16px' }}>
            Open Dashboard <ArrowRight size={14} />
          </div>
        </Link>

        <Link
          to="/digital-twin"
          style={{
            backgroundColor: '#0d1b38',
            border: '1px solid #1b2f5b',
            borderRadius: '8px',
            padding: '20px',
            textDecoration: 'none',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
              <Box size={20} color="#00f5d4" />
              <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#f8fafc' }}>3D Digital Twin</h3>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.82rem', lineHeight: 1.5 }}>
              Dedicated WebGL 3D isometric viewport. Interactive camera controls, road network geometry, and real Three.js rendering engine.
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#00f5d4', fontSize: '0.8rem', fontWeight: 600, marginTop: '16px' }}>
            Open 3D Viewer <ArrowRight size={14} />
          </div>
        </Link>

        <Link
          to="/simulation"
          style={{
            backgroundColor: '#0d1b38',
            border: '1px solid #1b2f5b',
            borderRadius: '8px',
            padding: '20px',
            textDecoration: 'none',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' }}>
              <Cpu size={20} color="#ffd166" />
              <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#f8fafc' }}>SUMO Simulation</h3>
            </div>
            <p style={{ color: '#94a3b8', fontSize: '0.82rem', lineHeight: 1.5 }}>
              Microscopic traffic simulator adapter, TraCI step controllers, multi-intersection demand generation, and priority corridors.
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ffd166', fontSize: '0.8rem', fontWeight: 600, marginTop: '16px' }}>
            View Simulation Module <ArrowRight size={14} />
          </div>
        </Link>
      </div>
    </div>
  );
};
