import React, { useState } from 'react';
import { Layers, Zap } from 'lucide-react';
import { DigitalTwinCanvas } from '../features/digital-twin/DigitalTwinCanvas';
import { DualSimulationComparison } from '../features/digital-twin/DualSimulationComparison';

export const DigitalTwinPage: React.FC = () => {
  const [viewMode, setViewMode] = useState<'SINGLE' | 'SPLIT_COMPARISON'>('SINGLE');

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - 48px)',
        padding: '12px',
        boxSizing: 'border-box',
        backgroundColor: '#070d1e',
      }}
    >
      <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc' }}>
            Full-Screen 3D Digital Twin View
          </h2>
          <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
            Interactive WebGL 3D scene inspecting junction INT-0457 & 1,000m arterial corridor (5th Ave).
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* Viewport Mode Switcher */}
          <div
            style={{
              backgroundColor: '#0d1b38',
              border: '1px solid #1b2f5b',
              borderRadius: '6px',
              padding: '2px',
              display: 'flex',
              gap: '2px',
            }}
          >
            <button
              onClick={() => setViewMode('SINGLE')}
              style={{
                backgroundColor: viewMode === 'SINGLE' ? 'rgba(0, 229, 255, 0.2)' : 'transparent',
                border: viewMode === 'SINGLE' ? '1px solid #00e5ff' : '1px solid transparent',
                color: viewMode === 'SINGLE' ? '#00e5ff' : '#94a3b8',
                borderRadius: '4px',
                padding: '3px 8px',
                fontSize: '0.68rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <Layers size={11} />
              <span>SINGLE VIEW</span>
            </button>

            <button
              onClick={() => setViewMode('SPLIT_COMPARISON')}
              style={{
                backgroundColor: viewMode === 'SPLIT_COMPARISON' ? 'rgba(0, 245, 212, 0.2)' : 'transparent',
                border: viewMode === 'SPLIT_COMPARISON' ? '1px solid #00f5d4' : '1px solid transparent',
                color: viewMode === 'SPLIT_COMPARISON' ? '#00f5d4' : '#94a3b8',
                borderRadius: '4px',
                padding: '3px 8px',
                fontSize: '0.68rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <Zap size={11} />
              <span>SPLIT COMPARISON (B0 vs AI)</span>
            </button>
          </div>

          <div
            style={{
              backgroundColor: '#0d1b38',
              border: '1px solid #1b2f5b',
              padding: '4px 10px',
              borderRadius: '6px',
              fontSize: '0.72rem',
              color: '#00f5d4',
            }}
          >
            Model Coordinates: Meters (SI) | 1,000m Corridor
          </div>
        </div>
      </div>

      <div style={{ flex: 1, minHeight: '500px' }}>
        {viewMode === 'SINGLE' ? (
          <DigitalTwinCanvas intersectionId="INT-0457" />
        ) : (
          <DualSimulationComparison onClose={() => setViewMode('SINGLE')} />
        )}
      </div>
    </div>
  );
};

