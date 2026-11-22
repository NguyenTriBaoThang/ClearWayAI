import React, { useState } from 'react';
import {
  Search,
  Car,
  Activity,
  Radio,
  Sliders,
  X,
  Crosshair,
  RefreshCw,
  Download,
  CheckCircle,
  Eye,
} from 'lucide-react';
import { StatusPill } from '../../components/StatusPill';

export type InspectorTab = 'vehicles' | 'signals' | 'sensors' | 'intersection';

export interface UnifiedInspectorProps {
  isOpen: boolean;
  onClose: () => void;
  onTrackEntity?: (entityId: string, type: string) => void;
}

export const UnifiedInspector: React.FC<UnifiedInspectorProps> = ({
  isOpen,
  onClose,
  onTrackEntity,
}) => {
  const [activeTab, setActiveTab] = useState<InspectorTab>('vehicles');
  const [selectedEntityId, setSelectedEntityId] = useState<string>('AMB-339');
  const [pingResult, setPingResult] = useState<string | null>(null);

  if (!isOpen) return null;

  const handlePing = () => {
    setPingResult('Pinging entity telemetry channel...');
    setTimeout(() => {
      setPingResult(`ECHO_REPLY from ${selectedEntityId}: latency=1.8ms, packet_loss=0%, status=NOMINAL`);
    }, 350);
  };

  const handleExportJson = () => {
    const data = {
      entity_id: selectedEntityId,
      category: activeTab,
      timestamp: new Date().toISOString(),
      provenance: 'DEMO_FIXTURE',
      intersection_id: 'INT-0457',
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `telemetry-${selectedEntityId.toLowerCase()}.json`;
    a.click();
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: '48px',
        right: '0',
        width: '400px',
        height: 'calc(100vh - 48px)',
        backgroundColor: '#0a1428',
        borderLeft: '1px solid #1b2f5b',
        boxShadow: '-8px 0 30px rgba(0, 0, 0, 0.7)',
        zIndex: 100,
        display: 'flex',
        flexDirection: 'column',
        boxSizing: 'border-box',
        overflowY: 'auto',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 16px',
          borderBottom: '1px solid #1b2f5b',
          backgroundColor: '#070d1e',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '6px',
              backgroundColor: 'rgba(0, 229, 255, 0.15)',
              border: '1px solid #00e5ff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#00e5ff',
            }}
          >
            <Search size={16} />
          </div>
          <div>
            <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#f1f5f9' }}>
              Unified Object Inspector
            </div>
            <div style={{ fontSize: '0.62rem', color: '#94a3b8' }}>
              Real-time Entity Diagnostics & Telemetry
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={onClose}
          style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '4px' }}
          title="Close Inspector [ESC]"
        >
          <X size={18} />
        </button>
      </div>

      {/* Tabs Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          borderBottom: '1px solid #1b2f5b',
          backgroundColor: '#070d1e',
        }}
      >
        <button
          type="button"
          onClick={() => { setActiveTab('vehicles'); setSelectedEntityId('AMB-339'); }}
          style={{
            padding: '8px 4px',
            backgroundColor: activeTab === 'vehicles' ? '#0d1b38' : 'transparent',
            border: 'none',
            borderBottom: `2px solid ${activeTab === 'vehicles' ? '#00e5ff' : 'transparent'}`,
            color: activeTab === 'vehicles' ? '#00e5ff' : '#94a3b8',
            fontSize: '0.65rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Vehicles
        </button>

        <button
          type="button"
          onClick={() => { setActiveTab('signals'); setSelectedEntityId('POLE-SW'); }}
          style={{
            padding: '8px 4px',
            backgroundColor: activeTab === 'signals' ? '#0d1b38' : 'transparent',
            border: 'none',
            borderBottom: `2px solid ${activeTab === 'signals' ? '#00e5ff' : 'transparent'}`,
            color: activeTab === 'signals' ? '#00e5ff' : '#94a3b8',
            fontSize: '0.65rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Signals
        </button>

        <button
          type="button"
          onClick={() => { setActiveTab('sensors'); setSelectedEntityId('RSU-0457-A'); }}
          style={{
            padding: '8px 4px',
            backgroundColor: activeTab === 'sensors' ? '#0d1b38' : 'transparent',
            border: 'none',
            borderBottom: `2px solid ${activeTab === 'sensors' ? '#00e5ff' : 'transparent'}`,
            color: activeTab === 'sensors' ? '#00e5ff' : '#94a3b8',
            fontSize: '0.65rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Sensors
        </button>

        <button
          type="button"
          onClick={() => { setActiveTab('intersection'); setSelectedEntityId('INT-0457'); }}
          style={{
            padding: '8px 4px',
            backgroundColor: activeTab === 'intersection' ? '#0d1b38' : 'transparent',
            border: 'none',
            borderBottom: `2px solid ${activeTab === 'intersection' ? '#00e5ff' : 'transparent'}`,
            color: activeTab === 'intersection' ? '#00e5ff' : '#94a3b8',
            fontSize: '0.65rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Node
        </button>
      </div>

      {/* Body Content */}
      <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {/* Entity Selector Dropdown */}
        <div>
          <label style={{ fontSize: '0.64rem', color: '#64748b', display: 'block', marginBottom: '3px' }}>
            Select Target Entity
          </label>
          <select
            value={selectedEntityId}
            onChange={(e) => { setSelectedEntityId(e.target.value); setPingResult(null); }}
            style={{
              width: '100%',
              backgroundColor: '#070d1e',
              border: '1px solid #1b2f5b',
              color: '#00f5d4',
              borderRadius: '4px',
              padding: '6px 8px',
              fontSize: '0.72rem',
              outline: 'none',
              cursor: 'pointer',
            }}
          >
            {activeTab === 'vehicles' && (
              <>
                <option value="AMB-339">AMB-339 (Class 1 Ambulance - Priority)</option>
                <option value="CAR-102">CAR-102 (Electric Sedan - 5th Ave EB)</option>
                <option value="MOTO-088">MOTO-088 (Motorcycle Scooter - Oak St NB)</option>
                <option value="BUS-14">BUS-14 (Transit Bus - Route 45)</option>
              </>
            )}
            {activeTab === 'signals' && (
              <>
                <option value="POLE-SW">POLE-SW (Master Controller Mast - Phase 2 & 4)</option>
                <option value="POLE-NE">POLE-NE (Secondary Dual-Head Mast - Phase 6 & 8)</option>
                <option value="POLE-SE">POLE-SE (Eastbound Pedestrian Mast)</option>
              </>
            )}
            {activeTab === 'sensors' && (
              <>
                <option value="RSU-0457-A">RSU-0457-A (5.9 GHz DSRC / C-V2X)</option>
                <option value="CAM-457-4K">CAM-457-4K (Northbound Video Detector)</option>
                <option value="LOOP-D2-EB">LOOP-D2-EB (Inductive Loop Stopline 5th Ave)</option>
              </>
            )}
            {activeTab === 'intersection' && (
              <>
                <option value="INT-0457">INT-0457 (Oak St & 5th Ave - Core Digital Twin)</option>
                <option value="INT-0456">INT-0456 (Cedar St & 5th Ave - Pre-clearance Wave)</option>
              </>
            )}
          </select>
        </div>

        {/* Diagnostic Properties Card */}
        <div
          style={{
            backgroundColor: '#0d1b38',
            border: '1px solid #1b2f5b',
            borderRadius: '6px',
            padding: '10px 12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#f1f5f9' }}>
              {selectedEntityId} Telemetry Profile
            </span>
            <StatusPill label="NOMINAL" variant="green" size="xs" />
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '6px',
              fontSize: '0.64rem',
              color: '#94a3b8',
            }}
          >
            <div>Type: <strong style={{ color: '#00f5d4' }}>{activeTab.toUpperCase()}</strong></div>
            <div>Status: <strong style={{ color: '#06d6a0' }}>Online (Active)</strong></div>
            <div>Coordinates: <strong style={{ color: '#f1f5f9', fontFamily: 'monospace' }}>[X: -14.2, Y: 0.0, Z: 8.5]</strong></div>
            <div>Speed / Rate: <strong style={{ color: '#ffd166', fontFamily: 'monospace' }}>58.2 km/h</strong></div>
            <div>Heading: <strong style={{ color: '#f1f5f9', fontFamily: 'monospace' }}>89.5° (Eastbound)</strong></div>
            <div>Latency: <strong style={{ color: '#00f5d4', fontFamily: 'monospace' }}>11.4 ms</strong></div>
          </div>
        </div>

        {/* Action Buttons: Track Camera, Ping, Export */}
        <div style={{ display: 'flex', gap: '6px' }}>
          <button
            type="button"
            onClick={() => onTrackEntity && onTrackEntity(selectedEntityId, activeTab)}
            style={{
              flex: 1,
              padding: '6px 8px',
              backgroundColor: 'rgba(0, 229, 255, 0.15)',
              border: '1px solid #00e5ff',
              color: '#00e5ff',
              borderRadius: '4px',
              fontSize: '0.66rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '4px',
            }}
          >
            <Crosshair size={12} />
            <span>Track Camera</span>
          </button>

          <button
            type="button"
            onClick={handlePing}
            style={{
              flex: 1,
              padding: '6px 8px',
              backgroundColor: 'rgba(6, 214, 160, 0.15)',
              border: '1px solid #06d6a0',
              color: '#06d6a0',
              borderRadius: '4px',
              fontSize: '0.66rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '4px',
            }}
          >
            <RefreshCw size={12} />
            <span>Ping Entity</span>
          </button>

          <button
            type="button"
            onClick={handleExportJson}
            style={{
              padding: '6px 8px',
              backgroundColor: 'rgba(30, 41, 59, 0.6)',
              border: '1px solid #1e293b',
              color: '#94a3b8',
              borderRadius: '4px',
              fontSize: '0.66rem',
              cursor: 'pointer',
            }}
            title="Export Telemetry to JSON"
          >
            <Download size={12} />
          </button>
        </div>

        {/* Ping Log Output */}
        {pingResult && (
          <div
            style={{
              padding: '6px 8px',
              backgroundColor: '#050a18',
              border: '1px solid #06d6a044',
              borderRadius: '4px',
              fontSize: '0.60rem',
              fontFamily: 'monospace',
              color: '#06d6a0',
            }}
          >
            {pingResult}
          </div>
        )}

        {/* Provenance Footer */}
        <div
          style={{
            marginTop: 'auto',
            padding: '6px 8px',
            backgroundColor: '#070d1e',
            borderRadius: '4px',
            border: '1px dashed #1b2f5b',
            fontSize: '0.60rem',
            color: '#64748b',
          }}
        >
          <strong style={{ color: '#00f5d4' }}>PROVENANCE: DEMO_FIXTURE</strong> — All telemetry reflects synchronized digital twin state machine.
        </div>
      </div>
    </div>
  );
};

export default UnifiedInspector;

