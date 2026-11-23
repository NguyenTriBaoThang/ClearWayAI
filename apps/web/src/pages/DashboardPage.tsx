import React, { useState } from 'react';
import { V2XHardwareCard } from '../features/operations/V2XHardwareCard';
import { PhaseTimingCard } from '../features/operations/PhaseTimingCard';
import { AdaptiveSignalCard } from '../features/operations/AdaptiveSignalCard';
import { IoTSensorsCard } from '../features/operations/IoTSensorsCard';
import { AnalyticsCard } from '../features/operations/AnalyticsCard';
import { DigitalTwinCanvas } from '../features/digital-twin/DigitalTwinCanvas';
import { SimulationControls } from '../features/operations/SimulationControls';
import { MissionDrawer } from '../features/operations/MissionDrawer';
import { UnifiedInspector } from '../features/operations/UnifiedInspector';
import { OperationsProvider, useOperations } from '../features/dashboard/OperationsContext';

const DashboardContent: React.FC = () => {
  const [isMissionDrawerOpen, setIsMissionDrawerOpen] = useState<boolean>(false);
  const [isInspectorOpen, setIsInspectorOpen] = useState<boolean>(false);
  const operations = useOperations();

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
        position: 'relative',
      }}
    >
      {/* Top 3 Panels Row: 1.25fr 1fr 1.35fr */}
      <div className="dashboard-grid-top">
        <V2XHardwareCard />
        <PhaseTimingCard />
        <AdaptiveSignalCard />
      </div>

      {/* Center 3D Digital Twin Viewport & Floating Simulation Controls */}
      <div
        style={{
          flex: '1 1 auto',
          minHeight: '440px',
          display: 'flex',
          flexDirection: 'column',
          position: 'relative',
        }}
      >
        <DigitalTwinCanvas intersectionId="INT-0457" />

        {/* Floating Simulation Controls Toolbar */}
        <div
          style={{
            position: 'absolute',
            bottom: '12px',
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 30,
            maxWidth: '95%',
          }}
        >
          <SimulationControls
            onTogglePlay={operations.togglePlay}
            onStep={() => operations.stepSimulation(0.1)}
            onChangeSpeed={operations.setPlaybackSpeed}
            onOpenMissionDrawer={() => setIsMissionDrawerOpen(true)}
            onOpenInspector={() => setIsInspectorOpen(true)}
          />
        </div>
      </div>

      {/* Bottom 2 Panels Row: 1.2fr 1.3fr */}
      <div className="dashboard-grid-bottom">
        <IoTSensorsCard />
        <AnalyticsCard />
      </div>

      {/* Interactive Operational Drawers */}
      <MissionDrawer
        isOpen={isMissionDrawerOpen}
        onClose={() => setIsMissionDrawerOpen(false)}
      />

      <UnifiedInspector
        isOpen={isInspectorOpen}
        onClose={() => setIsInspectorOpen(false)}
      />
    </div>
  );
};

export const DashboardPage: React.FC = () => {
  return (
    <OperationsProvider>
      <DashboardContent />
    </OperationsProvider>
  );
};

export default DashboardPage;
