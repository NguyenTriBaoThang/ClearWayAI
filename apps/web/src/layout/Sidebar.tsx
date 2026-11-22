import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Box,
  Cpu,
  BarChart2,
  Sliders,
  Home,
  HelpCircle,
  FileText,
  Shield,
  Zap,
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const navItems = [
    { to: '/', icon: Home, label: 'System Overview' },
    { to: '/dashboard', icon: LayoutDashboard, label: 'Digital Twin Operations Dashboard' },
    { to: '/digital-twin', icon: Box, label: '3D Scene Viewport & Instancing' },
    { to: '/simulation', icon: Cpu, label: 'SUMO TraCI & Adaptive Controllers' },
    { to: '/experiments', icon: BarChart2, label: 'RL Benchmarks & Emissions Analytics' },
    { to: '/settings', icon: Sliders, label: 'System Configuration & Safety Locks' },
  ];

  return (
    <aside
      style={{
        width: '56px',
        backgroundColor: '#070d1e',
        borderRight: '1px solid #1b2f5b',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '12px 0',
        zIndex: 40,
        justifyContent: 'space-between',
        flexShrink: 0,
      }}
    >
      {/* Primary Navigation Icons */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', alignItems: 'center' }}>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            title={item.label}
            style={({ isActive }) => ({
              width: '40px',
              height: '40px',
              borderRadius: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: isActive ? '#00e5ff' : '#64748b',
              backgroundColor: isActive ? 'rgba(0, 229, 255, 0.12)' : 'transparent',
              border: isActive ? '1px solid rgba(0, 229, 255, 0.35)' : '1px solid transparent',
              boxShadow: isActive ? '0 0 10px rgba(0, 229, 255, 0.2)' : 'none',
              transition: 'all 0.2s ease',
              textDecoration: 'none',
              position: 'relative',
            })}
          >
            {({ isActive }) => (
              <>
                <item.icon size={20} />
                {isActive && (
                  <span
                    style={{
                      position: 'absolute',
                      left: '-8px',
                      top: '10px',
                      width: '3px',
                      height: '20px',
                      borderRadius: '0 2px 2px 0',
                      backgroundColor: '#00e5ff',
                      boxShadow: '0 0 8px #00e5ff',
                    }}
                  />
                )}
              </>
            )}
          </NavLink>
        ))}
      </div>

      {/* Bottom Status Indicators & Documentation Links */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', alignItems: 'center' }}>
        {/* Safety Interlock Guard Pill */}
        <div
          title="Safety Interlock: ACTIVE (All-Red/Yellow Guarded, No direct public override)"
          style={{
            width: '34px',
            height: '34px',
            borderRadius: '6px',
            backgroundColor: 'rgba(6, 214, 160, 0.12)',
            border: '1px solid rgba(6, 214, 160, 0.35)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#06d6a0',
            cursor: 'help',
          }}
        >
          <Shield size={16} />
        </div>

        {/* SUMO Engine Standby Indicator */}
        <div
          title="Micro-simulation Engine: SUMO TraCI Bridge (Standby/Fixture Mode)"
          style={{
            width: '34px',
            height: '34px',
            borderRadius: '6px',
            backgroundColor: 'rgba(0, 229, 255, 0.10)',
            border: '1px solid rgba(0, 229, 255, 0.25)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#00e5ff',
            cursor: 'help',
          }}
        >
          <Zap size={15} />
        </div>

        <div style={{ width: '28px', height: '1px', backgroundColor: '#1b2f5b', margin: '4px 0' }} />

        {/* OpenAPI Documentation Link */}
        <a
          href="/docs"
          target="_blank"
          rel="noreferrer"
          title="API Documentation (FastAPI OpenAPI)"
          style={{
            width: '34px',
            height: '34px',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#64748b',
            textDecoration: 'none',
            transition: 'color 0.2s',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = '#00e5ff')}
          onMouseLeave={(e) => (e.currentTarget.style.color = '#64748b')}
        >
          <FileText size={17} />
        </a>

        {/* Quick Help Modal Trigger */}
        <div
          title="ClearWay AI System Architecture & Shortcuts"
          style={{
            width: '34px',
            height: '34px',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#64748b',
            cursor: 'pointer',
            transition: 'color 0.2s',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = '#00e5ff')}
          onMouseLeave={(e) => (e.currentTarget.style.color = '#64748b')}
        >
          <HelpCircle size={17} />
        </div>
      </div>
    </aside>
  );
};
