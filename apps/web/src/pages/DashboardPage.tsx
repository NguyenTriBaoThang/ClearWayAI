import React from 'react';
import { V2XHardwareCard } from '../features/operations/V2XHardwareCard';
import { PhaseTimingCard } from '../features/operations/PhaseTimingCard';
import { AdaptiveSignalCard } from '../features/operations/AdaptiveSignalCard';
import { IoTSensorsCard } from '../features/operations/IoTSensorsCard';
import { AnalyticsCard } from '../features/operations/AnalyticsCard';
import { DigitalTwinCanvas } from '../features/digital-twin/DigitalTwinCanvas';

export const DashboardPage: React.FC = () => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        padding: '8px',
        minHeight: 'calc(100vh - 48px)',
        boxSizing: 'border-box',
        backgroundColor: '#070d1e',
      }}
    >
      {/* Top 3 Panels Row: 1.25fr 1fr 1.35fr */}
      <div className="dashboard-grid-top">
        <V2XHardwareCard />
        <PhaseTimingCard />
        <AdaptiveSignalCard />
      </div>

      {/* Center 3D Digital Twin Viewport: Occupies ~55-60% of vertical height */}
      <div
        style={{
          flex: '1 1 auto',
          minHeight: '440px',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <DigitalTwinCanvas intersectionId="INT-0457" />
      </div>

      {/* Bottom 2 Panels Row: 1.2fr 1.3fr */}
      <div className="dashboard-grid-bottom">
        <IoTSensorsCard />
        <AnalyticsCard />
      </div>
    </div>
  );
};
