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
        height: 'calc(100vh - 48px)',
        boxSizing: 'border-box',
        overflowY: 'auto',
      }}
    >
      {/* Top 3 Panels Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1.2fr 1fr 1.3fr',
          gap: '8px',
          minHeight: '170px',
        }}
      >
        <V2XHardwareCard />
        <PhaseTimingCard />
        <AdaptiveSignalCard />
      </div>

      {/* Center 3D Digital Twin Viewport */}
      <div
        style={{
          flex: 1,
          minHeight: '380px',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <DigitalTwinCanvas intersectionId="INT-0457" />
      </div>

      {/* Bottom 2 Panels Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1.2fr 1.3fr',
          gap: '8px',
          minHeight: '210px',
        }}
      >
        <IoTSensorsCard />
        <AnalyticsCard />
      </div>
    </div>
  );
};

