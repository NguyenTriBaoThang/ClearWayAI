import React from 'react';
import { DigitalTwinCanvas } from '../features/digital-twin/DigitalTwinCanvas';

export const DigitalTwinPage: React.FC = () => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - 48px)',
        padding: '12px',
        boxSizing: 'border-box',
      }}
    >
      <div style={{ marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc' }}>
            Full-Screen 3D Digital Twin View
          </h2>
          <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
            Interactive WebGL 3D scene inspecting junction INT-0457 (Oak St. & 5th Ave).
          </p>
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
          Model Coordinates: Meters (SI) | Camera: Isometric Perspective
        </div>
      </div>

      <div style={{ flex: 1, minHeight: '500px' }}>
        <DigitalTwinCanvas intersectionId="INT-0457" />
      </div>
    </div>
  );
};

