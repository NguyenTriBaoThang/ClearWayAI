import React, { useState } from 'react';
import { Camera, Radio, Disc, Cpu, Compass, Layers } from 'lucide-react';

export const IoTSensorsCard: React.FC = () => {
  const [layers, setLayers] = useState({
    trafficFlow: true,
    sensorCoverage: true,
    v2xNetwork: true,
    incidentEvent: true,
    emergencyCorridor: true,
    parkingOccupancy: false,
  });

  const toggleLayer = (key: keyof typeof layers) => {
    setLayers(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="panel-card" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Radio size={14} color="#00e5ff" />
          <span>IoT Sensor Network & City Map Overview</span>
        </div>
        <span style={{ fontSize: '0.68rem', color: '#64748b' }}>Simulated Telemetry Topology</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '170px 1fr', gap: '10px', padding: '10px', flex: 1 }}>
        {/* Left: Sensor Inventory & Layer Controls */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.72rem' }}>
          {/* Sensor Devices */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Camera size={13} color="#ef476f" />
              <div style={{ flex: 1, color: '#e2e8f0' }}>Traffic Cameras</div>
              <div style={{ color: '#06d6a0', fontWeight: 600, fontFamily: 'monospace' }}>112/112</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Radio size={13} color="#00e5ff" />
              <div style={{ flex: 1, color: '#e2e8f0' }}>LiDAR Sensors</div>
              <div style={{ color: '#06d6a0', fontWeight: 600, fontFamily: 'monospace' }}>48/48</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Disc size={13} color="#38bdf8" />
              <div style={{ flex: 1, color: '#e2e8f0' }}>Loop Detectors</div>
              <div style={{ color: '#06d6a0', fontWeight: 600, fontFamily: 'monospace' }}>96/96</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Radio size={13} color="#ffd166" />
              <div style={{ flex: 1, color: '#e2e8f0' }}>RSUs (V2I)</div>
              <div style={{ color: '#06d6a0', fontWeight: 600, fontFamily: 'monospace' }}>42/42</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Cpu size={13} color="#06d6a0" />
              <div style={{ flex: 1, color: '#e2e8f0' }}>Signal Controllers</div>
              <div style={{ color: '#06d6a0', fontWeight: 600, fontFamily: 'monospace' }}>8/8</div>
            </div>
          </div>

          <div style={{ height: '1px', backgroundColor: '#1b2f5b' }} />

          {/* Layer Checkboxes */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '0.68rem', color: '#94a3b8', fontWeight: 600 }}>Data Layers (City)</span>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: '#cbd5e1' }}>
              <input type="checkbox" checked={layers.trafficFlow} onChange={() => toggleLayer('trafficFlow')} />
              <span>Traffic Flow</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: '#cbd5e1' }}>
              <input type="checkbox" checked={layers.sensorCoverage} onChange={() => toggleLayer('sensorCoverage')} />
              <span>Sensor Coverage</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: '#cbd5e1' }}>
              <input type="checkbox" checked={layers.v2xNetwork} onChange={() => toggleLayer('v2xNetwork')} />
              <span>V2X Network</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: '#cbd5e1' }}>
              <input type="checkbox" checked={layers.incidentEvent} onChange={() => toggleLayer('incidentEvent')} />
              <span>Incident / Event</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: '#cbd5e1' }}>
              <input type="checkbox" checked={layers.emergencyCorridor} onChange={() => toggleLayer('emergencyCorridor')} />
              <span style={{ color: '#00f5d4' }}>Emergency Corridor</span>
            </label>
          </div>
        </div>

        {/* Right: Mini City Map Representation */}
        <div
          style={{
            position: 'relative',
            backgroundColor: '#070d1e',
            borderRadius: '6px',
            border: '1px solid #1b2f5b',
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {/* Vector Map Diagram */}
          <svg viewBox="0 0 240 180" style={{ width: '100%', height: '100%' }}>
            {/* Map Roads Grid */}
            <rect width="240" height="180" fill="#070d1e" />
            <path d="M 0 90 L 240 90" stroke="#162547" strokeWidth="8" />
            <path d="M 120 0 L 120 180" stroke="#162547" strokeWidth="8" />
            <path d="M 40 0 L 40 180" stroke="#12203e" strokeWidth="4" />
            <path d="M 200 0 L 200 180" stroke="#12203e" strokeWidth="4" />
            <path d="M 0 40 L 240 40" stroke="#12203e" strokeWidth="4" />
            <path d="M 0 140 L 240 140" stroke="#12203e" strokeWidth="4" />

            {/* Emergency Corridor (Blue dotted route) */}
            <path
              d="M 40 90 L 120 90 L 200 90"
              stroke="#00e5ff"
              strokeWidth="3"
              strokeDasharray="4,3"
            />

            {/* Nodes and Sensors */}
            <circle cx="120" cy="90" r="14" fill="rgba(0, 229, 255, 0.2)" stroke="#00e5ff" strokeWidth="1.5" />
            <circle cx="120" cy="90" r="5" fill="#ffd166" />

            <circle cx="40" cy="90" r="4" fill="#06d6a0" />
            <circle cx="200" cy="90" r="4" fill="#06d6a0" />
            <circle cx="120" cy="40" r="4" fill="#06d6a0" />
            <circle cx="120" cy="140" r="4" fill="#06d6a0" />

            {/* Hospital Marker */}
            <rect x="200" y="30" width="16" height="16" rx="3" fill="#1e293b" stroke="#38bdf8" />
            <text x="204" y="42" fill="#38bdf8" fontSize="10" fontWeight="bold">H</text>

            {/* Scale Bar */}
            <line x1="20" y1="165" x2="80" y2="165" stroke="#94a3b8" strokeWidth="1.5" />
            <line x1="20" y1="162" x2="20" y2="168" stroke="#94a3b8" strokeWidth="1.5" />
            <line x1="80" y1="162" x2="80" y2="168" stroke="#94a3b8" strokeWidth="1.5" />
            <text x="28" y="162" fill="#64748b" fontSize="7">0 250 500m</text>
          </svg>

          {/* Compass Rose */}
          <div
            style={{
              position: 'absolute',
              top: '8px',
              right: '8px',
              backgroundColor: 'rgba(11, 21, 45, 0.85)',
              padding: '3px 6px',
              borderRadius: '4px',
              border: '1px solid #1b2f5b',
              fontSize: '0.62rem',
              color: '#94a3b8',
              display: 'flex',
              alignItems: 'center',
              gap: '2px',
            }}
          >
            <Compass size={12} color="#00e5ff" />
            <span>N</span>
          </div>
        </div>
      </div>
    </div>
  );
};

