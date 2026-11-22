import React, { useState } from 'react';
import {
  Camera,
  Radio,
  Disc,
  Cpu,
  Compass,
  AlertTriangle,
  Flame,
  CheckCircle,
  X,
  Layers,
  MapPin,
  Eye,
  Activity,
} from 'lucide-react';
import { PanelFrame } from '../../components/PanelFrame';
import { StatusPill } from '../../components/StatusPill';
import { DataProvenance } from '@clearway/shared';

export interface IntersectionMapNode {
  id: string;
  name: string;
  x: number;
  y: number;
  status: 'ONLINE' | 'COORDINATED' | 'PREEMPTED';
  activePhase: string;
  queueM: number;
  rsuChannel: string;
  camera: string;
}

const MAP_NODES: IntersectionMapNode[] = [
  {
    id: 'INT-0455',
    name: 'Maple St & 5th Ave',
    x: 45,
    y: 100,
    status: 'COORDINATED',
    activePhase: 'P2 (E-W Thru)',
    queueM: 28,
    rsuChannel: 'RSU-0455 (5.9 GHz Ch 178)',
    camera: 'CAM-455-HD (Live)',
  },
  {
    id: 'INT-0456',
    name: 'Cedar St & 5th Ave',
    x: 90,
    y: 100,
    status: 'COORDINATED',
    activePhase: 'P2 (E-W Thru)',
    queueM: 34,
    rsuChannel: 'RSU-0456 (5.9 GHz Ch 178)',
    camera: 'CAM-456-HD (Live)',
  },
  {
    id: 'INT-0457',
    name: 'Oak St & 5th Ave (Digital Twin Core)',
    x: 135,
    y: 100,
    status: 'PREEMPTED',
    activePhase: 'P3 (E-W Thru Priority)',
    queueM: 87,
    rsuChannel: 'RSU-0457-MAST-1 (5.9 GHz Ch 180)',
    camera: 'CAM-457-4K (Dual-Lens)',
  },
  {
    id: 'INT-0458',
    name: 'Pine St & 5th Ave',
    x: 215,
    y: 100,
    status: 'COORDINATED',
    activePhase: 'P2 (E-W Thru)',
    queueM: 22,
    rsuChannel: 'RSU-0458 (5.9 GHz Ch 178)',
    camera: 'CAM-458-HD (Live)',
  },
];

export interface IoTSensorsPanelProps {
  className?: string;
  style?: React.CSSProperties;
}

export const IoTSensorsPanel: React.FC<IoTSensorsPanelProps> = ({
  className = '',
  style,
}) => {
  const [layers, setLayers] = useState({
    trafficFlow: true,
    sensorCoverage: true,
    v2xNetwork: true,
    incidentEvent: true,
    emergencyCorridor: true,
    parkingOccupancy: false,
  });

  const [activeFilter, setActiveFilter] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<IntersectionMapNode | null>(MAP_NODES[2]); // Default to INT-0457

  const toggleLayer = (key: keyof typeof layers) => {
    setLayers((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <PanelFrame
      title="IoT Sensor Network & City Map Overview"
      icon={<Radio size={15} color="#00e5ff" />}
      badge={
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <StatusPill label="Topology" variant="cyan" size="xs" />
          <span
            style={{
              fontSize: '0.62rem',
              color: '#00f5d4',
              fontFamily: 'monospace',
              backgroundColor: '#122347',
              padding: '1px 5px',
              borderRadius: '3px',
              border: '1px solid #1b2f5b',
            }}
          >
            DEMO_FIXTURE
          </span>
        </div>
      }
      headerActions={
        <div style={{ fontSize: '0.62rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Activity size={11} color="#06d6a0" />
          <span style={{ color: '#06d6a0', fontWeight: 600 }}>306/306 Online</span>
        </div>
      }
      className={className}
      style={style}
    >
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '175px 1fr',
          gap: '8px',
          padding: '8px 10px',
          height: '100%',
          boxSizing: 'border-box',
        }}
      >
        {/* Left Column: Sensor Inventory & Data Layers */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            fontSize: '0.70rem',
            gap: '6px',
          }}
        >
          {/* Sensor Devices Inventory (5 categories) */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <div
              style={{
                fontSize: '0.62rem',
                color: '#64748b',
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                marginBottom: '1px',
              }}
            >
              Sensor Inventory
            </div>

            {/* 1. Traffic Cameras */}
            <div
              onClick={() => setActiveFilter(activeFilter === 'camera' ? null : 'camera')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '2px 4px',
                borderRadius: '4px',
                backgroundColor: activeFilter === 'camera' ? 'rgba(239, 71, 111, 0.15)' : 'transparent',
                cursor: 'pointer',
              }}
              title="Click to filter camera coverage"
            >
              <Camera size={12} color="#ef476f" />
              <div style={{ flex: 1, color: '#e2e8f0', fontSize: '0.68rem' }}>Traffic Cameras</div>
              <div style={{ color: '#06d6a0', fontWeight: 700, fontFamily: 'monospace' }}>112 / 112</div>
            </div>

            {/* 2. LiDAR Sensors */}
            <div
              onClick={() => setActiveFilter(activeFilter === 'lidar' ? null : 'lidar')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '2px 4px',
                borderRadius: '4px',
                backgroundColor: activeFilter === 'lidar' ? 'rgba(0, 229, 255, 0.15)' : 'transparent',
                cursor: 'pointer',
              }}
              title="Click to filter LiDAR coverage"
            >
              <Radio size={12} color="#00e5ff" />
              <div style={{ flex: 1, color: '#e2e8f0', fontSize: '0.68rem' }}>LiDAR Sensors</div>
              <div style={{ color: '#06d6a0', fontWeight: 700, fontFamily: 'monospace' }}>48 / 48</div>
            </div>

            {/* 3. Loop Detectors */}
            <div
              onClick={() => setActiveFilter(activeFilter === 'loop' ? null : 'loop')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '2px 4px',
                borderRadius: '4px',
                backgroundColor: activeFilter === 'loop' ? 'rgba(56, 189, 248, 0.15)' : 'transparent',
                cursor: 'pointer',
              }}
              title="Click to filter inductive loops"
            >
              <Disc size={12} color="#38bdf8" />
              <div style={{ flex: 1, color: '#e2e8f0', fontSize: '0.68rem' }}>Loop Detectors</div>
              <div style={{ color: '#06d6a0', fontWeight: 700, fontFamily: 'monospace' }}>96 / 96</div>
            </div>

            {/* 4. RSUs (V2I) */}
            <div
              onClick={() => setActiveFilter(activeFilter === 'rsu' ? null : 'rsu')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '2px 4px',
                borderRadius: '4px',
                backgroundColor: activeFilter === 'rsu' ? 'rgba(255, 209, 102, 0.15)' : 'transparent',
                cursor: 'pointer',
              }}
              title="Click to filter V2I RSUs"
            >
              <Radio size={12} color="#ffd166" />
              <div style={{ flex: 1, color: '#e2e8f0', fontSize: '0.68rem' }}>RSUs (V2I)</div>
              <div style={{ color: '#06d6a0', fontWeight: 700, fontFamily: 'monospace' }}>42 / 42</div>
            </div>

            {/* 5. Signal Controllers */}
            <div
              onClick={() => setActiveFilter(activeFilter === 'controller' ? null : 'controller')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '2px 4px',
                borderRadius: '4px',
                backgroundColor: activeFilter === 'controller' ? 'rgba(6, 214, 160, 0.15)' : 'transparent',
                cursor: 'pointer',
              }}
              title="Click to filter signal controllers"
            >
              <Cpu size={12} color="#06d6a0" />
              <div style={{ flex: 1, color: '#e2e8f0', fontSize: '0.68rem' }}>Signal Controllers</div>
              <div style={{ color: '#06d6a0', fontWeight: 700, fontFamily: 'monospace' }}>8 / 8</div>
            </div>
          </div>

          <div style={{ height: '1px', backgroundColor: '#1b2f5b', margin: '2px 0' }} />

          {/* Data Layers Checkboxes (6 layers) */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
            <span style={{ fontSize: '0.62rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Data Layers (City)
            </span>

            <label style={{ display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer', color: '#cbd5e1', fontSize: '0.66rem' }}>
              <input type="checkbox" checked={layers.trafficFlow} onChange={() => toggleLayer('trafficFlow')} />
              <span>Traffic Flow</span>
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer', color: '#cbd5e1', fontSize: '0.66rem' }}>
              <input type="checkbox" checked={layers.sensorCoverage} onChange={() => toggleLayer('sensorCoverage')} />
              <span>Sensor Coverage</span>
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer', color: '#cbd5e1', fontSize: '0.66rem' }}>
              <input type="checkbox" checked={layers.v2xNetwork} onChange={() => toggleLayer('v2xNetwork')} />
              <span>V2X Network</span>
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer', color: '#cbd5e1', fontSize: '0.66rem' }}>
              <input type="checkbox" checked={layers.incidentEvent} onChange={() => toggleLayer('incidentEvent')} />
              <span>Incident / Event</span>
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer', color: '#cbd5e1', fontSize: '0.66rem' }}>
              <input type="checkbox" checked={layers.emergencyCorridor} onChange={() => toggleLayer('emergencyCorridor')} />
              <span style={{ color: '#00f5d4', fontWeight: 600 }}>Emergency Corridor</span>
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer', color: '#94a3b8', fontSize: '0.66rem' }}>
              <input type="checkbox" checked={layers.parkingOccupancy} onChange={() => toggleLayer('parkingOccupancy')} />
              <span>Parking Occupancy</span>
            </label>
          </div>
        </div>

        {/* Right Column: Mini Vector City Map Viewport */}
        <div
          style={{
            position: 'relative',
            backgroundColor: '#070d1e',
            borderRadius: '6px',
            border: '1px solid #1b2f5b',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Vector Map Diagram */}
          <svg viewBox="0 0 280 185" style={{ width: '100%', height: '100%', display: 'block' }}>
            <rect width="280" height="185" fill="#070d1e" />

            {/* Base Street Grid */}
            {/* Horizontal streets */}
            <path d="M 0 50 L 280 50" stroke="#12203e" strokeWidth="4" />
            <path d="M 0 100 L 280 100" stroke="#162547" strokeWidth="9" />
            <path d="M 0 150 L 280 150" stroke="#12203e" strokeWidth="4" />

            {/* Vertical streets */}
            <path d="M 45 0 L 45 185" stroke="#12203e" strokeWidth="4" />
            <path d="M 135 0 L 135 185" stroke="#162547" strokeWidth="9" />
            <path d="M 215 0 L 215 185" stroke="#12203e" strokeWidth="4" />

            {/* Street Names */}
            <text x="6" y="96" fill="#475569" fontSize="6.5" fontFamily="monospace">5th Ave (Corridor)</text>
            <text x="140" y="16" fill="#475569" fontSize="6.5" fontFamily="monospace">Oak St</text>

            {/* Layer: Traffic Flow Heatlines */}
            {layers.trafficFlow && (
              <g opacity="0.85">
                {/* 5th Ave EB Flow: green */}
                <line x1="10" y1="98" x2="110" y2="98" stroke="#06d6a0" strokeWidth="2.5" />
                {/* 5th Ave near core: amber queue */}
                <line x1="110" y1="98" x2="135" y2="98" stroke="#ffd166" strokeWidth="2.5" />
                {/* Oak St NB: green */}
                <line x1="133" y1="180" x2="133" y2="120" stroke="#06d6a0" strokeWidth="2.5" />
                {/* Oak St core queue: red */}
                <line x1="133" y1="120" x2="133" y2="105" stroke="#ef476f" strokeWidth="2.5" />
              </g>
            )}

            {/* Layer: Sensor Coverage Fooprints */}
            {layers.sensorCoverage && (
              <g>
                {/* Radar footprints for intersections */}
                <circle cx="135" cy="100" r="28" fill="rgba(0, 229, 255, 0.08)" stroke="#00e5ff" strokeWidth="1" strokeDasharray="3,2" />
                <circle cx="45" cy="100" r="18" fill="rgba(0, 229, 255, 0.05)" stroke="#00e5ff55" strokeWidth="0.8" strokeDasharray="2,2" />
                <circle cx="90" cy="100" r="18" fill="rgba(0, 229, 255, 0.05)" stroke="#00e5ff55" strokeWidth="0.8" strokeDasharray="2,2" />
                <circle cx="215" cy="100" r="18" fill="rgba(0, 229, 255, 0.05)" stroke="#00e5ff55" strokeWidth="0.8" strokeDasharray="2,2" />
              </g>
            )}

            {/* Layer: V2X Wireless Mesh Links */}
            {layers.v2xNetwork && (
              <g>
                <line x1="45" y1="100" x2="90" y2="100" stroke="#ffd166" strokeWidth="1.2" strokeDasharray="3,3" />
                <line x1="90" y1="100" x2="135" y2="100" stroke="#ffd166" strokeWidth="1.2" strokeDasharray="3,3" />
                <line x1="135" y1="100" x2="215" y2="100" stroke="#ffd166" strokeWidth="1.2" strokeDasharray="3,3" />
                <line x1="215" y1="100" x2="245" y2="40" stroke="#ffd166" strokeWidth="1.2" strokeDasharray="3,3" />
              </g>
            )}

            {/* Layer: Emergency Corridor Route */}
            {layers.emergencyCorridor && (
              <g>
                {/* Ribbon path to hospital */}
                <path
                  d="M 20 100 L 215 100 L 245 48"
                  fill="none"
                  stroke="#00f5d4"
                  strokeWidth="3.2"
                  strokeDasharray="4,3"
                />
                {/* Ambulance moving icon indicator */}
                <circle cx="115" cy="100" r="4.5" fill="#ef476f" stroke="#ffffff" strokeWidth="1" />
                <text x="110" y="93" fill="#00f5d4" fontSize="6" fontWeight="bold">AMB-339</text>
              </g>
            )}

            {/* Layer: Incident / Event Marker */}
            {layers.incidentEvent && (
              <g>
                <polygon points="175,93 182,107 168,107" fill="#ef476f" stroke="#ffd166" strokeWidth="1" />
                <text x="172" y="105" fill="#ffffff" fontSize="7" fontWeight="bold">!</text>
                <text x="162" y="116" fill="#ef476f" fontSize="5.5" fontFamily="monospace">INC-092</text>
              </g>
            )}

            {/* Layer: Parking Occupancy */}
            {layers.parkingOccupancy && (
              <g>
                <rect x="70" y="60" width="16" height="12" rx="2" fill="#1b2f5b" stroke="#38bdf8" />
                <text x="74" y="69" fill="#38bdf8" fontSize="6.5" fontWeight="bold">P</text>
                <text x="90" y="69" fill="#06d6a0" fontSize="5.5">84%</text>

                <rect x="155" y="125" width="16" height="12" rx="2" fill="#1b2f5b" stroke="#38bdf8" />
                <text x="159" y="134" fill="#38bdf8" fontSize="6.5" fontWeight="bold">P</text>
                <text x="175" y="134" fill="#ffd166" fontSize="5.5">42%</text>
              </g>
            )}

            {/* Intersection Nodes (Clickable) */}
            {MAP_NODES.map((node) => {
              const isSelected = selectedNode?.id === node.id;
              const isCore = node.id === 'INT-0457';
              return (
                <g
                  key={node.id}
                  onClick={() => setSelectedNode(node)}
                  style={{ cursor: 'pointer' }}
                >
                  {/* Outer pulse ring for selected node */}
                  {isSelected && (
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r={isCore ? 12 : 9}
                      fill="none"
                      stroke="#00e5ff"
                      strokeWidth="1.5"
                    />
                  )}
                  {/* Node dot */}
                  <circle
                    cx={node.x}
                    cy={node.y}
                    r={isCore ? 6 : 4.5}
                    fill={isCore ? '#ffd166' : '#06d6a0'}
                    stroke="#070d1e"
                    strokeWidth="1.5"
                  />
                  <text
                    x={node.x - 14}
                    y={node.y + 14}
                    fill={isSelected ? '#00f5d4' : '#94a3b8'}
                    fontSize="6"
                    fontFamily="monospace"
                  >
                    {node.id}
                  </text>
                </g>
              );
            })}

            {/* Metropolitan Hospital Facility Marker */}
            <g>
              <rect x="235" y="28" width="22" height="20" rx="3" fill="#0c2340" stroke="#00e5ff" strokeWidth="1.5" />
              <text x="242" y="42" fill="#00e5ff" fontSize="11" fontWeight="bold">H</text>
              <text x="220" y="24" fill="#38bdf8" fontSize="5.8" fontWeight="bold">Metro Hospital</text>
            </g>

            {/* Metric Scale Bar: 0 250 500 1,000 m */}
            <g>
              <line x1="20" y1="172" x2="100" y2="172" stroke="#94a3b8" strokeWidth="1.2" />
              <line x1="20" y1="169" x2="20" y2="175" stroke="#94a3b8" strokeWidth="1.2" />
              <line x1="40" y1="170" x2="40" y2="174" stroke="#64748b" strokeWidth="1" />
              <line x1="60" y1="170" x2="60" y2="174" stroke="#64748b" strokeWidth="1" />
              <line x1="100" y1="169" x2="100" y2="175" stroke="#94a3b8" strokeWidth="1.2" />
              <text x="18" y="167" fill="#64748b" fontSize="5.5" fontFamily="monospace">0</text>
              <text x="35" y="167" fill="#64748b" fontSize="5.5" fontFamily="monospace">250</text>
              <text x="55" y="167" fill="#64748b" fontSize="5.5" fontFamily="monospace">500</text>
              <text x="92" y="167" fill="#64748b" fontSize="5.5" fontFamily="monospace">1,000 m</text>
            </g>
          </svg>

          {/* Compass Rose Indicator */}
          <div
            style={{
              position: 'absolute',
              top: '5px',
              right: '5px',
              backgroundColor: 'rgba(11, 21, 45, 0.85)',
              padding: '2px 5px',
              borderRadius: '3px',
              border: '1px solid #1b2f5b',
              fontSize: '0.58rem',
              color: '#94a3b8',
              display: 'flex',
              alignItems: 'center',
              gap: '2px',
              pointerEvents: 'none',
            }}
          >
            <Compass size={11} color="#00e5ff" />
            <span style={{ fontWeight: 700, color: '#f1f5f9' }}>N</span>
          </div>

          {/* Interactive Node Telemetry Inspector Sub-bar */}
          {selectedNode && (
            <div
              style={{
                backgroundColor: 'rgba(10, 20, 40, 0.95)',
                borderTop: '1px solid #1b2f5b',
                padding: '4px 8px',
                fontSize: '0.62rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                color: '#94a3b8',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <MapPin size={11} color="#00e5ff" />
                <span style={{ color: '#f1f5f9', fontWeight: 700 }}>{selectedNode.id}</span>
                <span style={{ color: '#64748b' }}>({selectedNode.name})</span>
                <span
                  style={{
                    backgroundColor: selectedNode.status === 'PREEMPTED' ? 'rgba(239, 71, 111, 0.2)' : 'rgba(6, 214, 160, 0.2)',
                    color: selectedNode.status === 'PREEMPTED' ? '#ef476f' : '#06d6a0',
                    padding: '0 4px',
                    borderRadius: '2px',
                    fontFamily: 'monospace',
                    fontSize: '0.58rem',
                    fontWeight: 600,
                  }}
                >
                  {selectedNode.status}
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span>Phase: <strong style={{ color: '#00f5d4' }}>{selectedNode.activePhase}</strong></span>
                <span>Queue: <strong style={{ color: '#ffd166' }}>{selectedNode.queueM}m</strong></span>
                <button
                  type="button"
                  onClick={() => setSelectedNode(null)}
                  style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', padding: 0 }}
                  title="Close Inspector"
                >
                  <X size={11} />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </PanelFrame>
  );
};

export default IoTSensorsPanel;

