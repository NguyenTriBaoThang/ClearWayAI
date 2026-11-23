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
import { CorridorOperationsView } from '../features/corridor/CorridorOperationsView';
import { OperationsProvider, useOperations } from '../features/dashboard/OperationsContext';

const DashboardContent: React.FC = () => {
  const [isMissionDrawerOpen, setIsMissionDrawerOpen] = useState<boolean>(false);
  const [isInspectorOpen, setIsInspectorOpen] = useState<boolean>(false);
  const [viewportMode, setViewportMode] = useState<'3D' | 'CORRIDOR_2D'>('3D');
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

      {/* Center Viewport Switcher & Primary Display */}
      <div
        style={{
          flex: '1 1 auto',
          minHeight: '440px',
          display: 'flex',
          flexDirection: 'column',
          position: 'relative',
        }}
      >
        {/* Viewport Mode Switcher Pill */}
        <div
          style={{
            position: 'absolute',
            top: '12px',
            right: '16px',
            zIndex: 35,
            display: 'flex',
            alignItems: 'center',
            backgroundColor: 'rgba(10, 20, 45, 0.9)',
            border: '1px solid #1b2f5b',
            borderRadius: '6px',
            padding: '2px',
            gap: '2px',
          }}
        >
          <button
            onClick={() => setViewportMode('3D')}
            style={{
              padding: '4px 10px',
              fontSize: '0.68rem',
              fontWeight: 700,
              borderRadius: '4px',
              cursor: 'pointer',
              border: viewportMode === '3D' ? '1px solid #00e5ff' : '1px solid transparent',
              backgroundColor: viewportMode === '3D' ? '#1b2f5b' : 'transparent',
              color: viewportMode === '3D' ? '#00e5ff' : '#94a3b8',
            }}
          >
            3D DIGITAL TWIN
          </button>
          <button
            onClick={() => setViewportMode('CORRIDOR_2D')}
            style={{
              padding: '4px 10px',
              fontSize: '0.68rem',
              fontWeight: 700,
              borderRadius: '4px',
              cursor: 'pointer',
              border: viewportMode === 'CORRIDOR_2D' ? '1px solid #06d6a0' : '1px solid transparent',
              backgroundColor: viewportMode === 'CORRIDOR_2D' ? '#1b2f5b' : 'transparent',
              color: viewportMode === 'CORRIDOR_2D' ? '#06d6a0' : '#94a3b8',
            }}
          >
            2D CORRIDOR MAP & TIMELINE
          </button>
        </div>

        {viewportMode === '3D' ? (
          <DigitalTwinCanvas intersectionId="INT-0457" />
        ) : (
          <div style={{ flex: 1, padding: '4px 0', overflowY: 'auto' }}>
            <CorridorOperationsView />
          </div>
        )}

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
