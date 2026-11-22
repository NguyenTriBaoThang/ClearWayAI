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
  FileText
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const navItems = [
    { to: '/', icon: Home, label: 'Overview' },
    { to: '/dashboard', icon: LayoutDashboard, label: 'Digital Twin Dashboard' },
    { to: '/digital-twin', icon: Box, label: '3D Scene Viewer' },
    { to: '/simulation', icon: Cpu, label: 'SUMO Simulation & TraCI' },
    { to: '/experiments', icon: BarChart2, label: 'Benchmark & Experiments' },
    { to: '/settings', icon: Sliders, label: 'System Configuration' },
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
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'center' }}>
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
              border: isActive ? '1px solid rgba(0, 229, 255, 0.3)' : '1px solid transparent',
              transition: 'all 0.2s ease',
              textDecoration: 'none',
            })}
          >
            <item.icon size={20} />
          </NavLink>
        ))}
      </div>

      {/* Bottom Documentation & Help Icons */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', alignItems: 'center' }}>
        <a
          href="/docs"
          target="_blank"
          rel="noreferrer"
          title="API Documentation (FastAPI OpenAPI)"
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#64748b',
            textDecoration: 'none',
          }}
        >
          <FileText size={18} />
        </a>
        <div
          title="ClearWay AI Help & Specifications"
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#64748b',
            cursor: 'pointer',
          }}
        >
          <HelpCircle size={18} />
        </div>
      </div>
    </aside>
  );
};
