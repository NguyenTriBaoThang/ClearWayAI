import React, { useState, useEffect } from 'react';
import {
  Wifi,
  Radio,
  Server,
  Cpu,
  CheckCircle,
  AlertTriangle,
  WifiOff,
  Activity,
  X,
  RefreshCw,
  Terminal,
  ShieldAlert,
} from 'lucide-react';
import { PanelFrame } from '../../components/PanelFrame';
import { StatusPill } from '../../components/StatusPill';
import { HardwareStatus, DataProvenance } from '@clearway/shared';

export type V2XNodeId = 'obu' | 'rsu' | 'edge' | 'signal';
export type SimulationLinkMode = 'nominal' | 'degraded' | 'offline';

export interface V2XDeviceInfo {
  id: V2XNodeId;
  shortName: string;
  fullName: string;
  stationId: string;
  role: string;
  iconType: 'obu' | 'rsu' | 'edge' | 'signal';
  primaryMetric: string;
  subMetric: string;
  protocol: string;
  standard: string;
  ipMac: string;
  firmware: string;
  frequency: string;
  nominalRttMs: number;
  heartbeat: string;
  statusText: string;
  provenanceNote: string;
}

const DEVICE_PROFILES: Record<V2XNodeId, V2XDeviceInfo> = {
  obu: {
    id: 'obu',
    shortName: 'On-Board Units',
    fullName: 'Vehicle On-Board Units (OBU Fleet)',
    stationId: 'OBU-SUBNET-457',
    role: 'Vehicle-to-Infrastructure broadcast (BSM/CAM telemetry at 10 Hz)',
    iconType: 'obu',
    primaryMetric: '1,842 Online',
    subMetric: '(99.2% Adoption)',
    protocol: 'SAE J2735 / ETSI ITS-G5',
    standard: 'IEEE 802.11p / 3GPP Rel-16 PC5 direct mode',
    ipMac: '10.45.7.0/24 (Dynamic Ad-hoc Mesh)',
    firmware: 'v2.8.4-c-v2x-fleet',
    frequency: '5.9 GHz (DSRC Ch 178)',
    nominalRttMs: 8.4,
    heartbeat: '12ms ago',
    statusText: 'Broadcasting BSM',
    provenanceNote: 'DEMO_FIXTURE: Synthetic vehicle kinematics generated via SUMO micro-simulation.',
  },
  rsu: {
    id: 'rsu',
    shortName: 'RSU (Roadside Unit)',
    fullName: 'Intersection Roadside Unit Cluster (RSU-0457)',
    stationId: 'RSU-0457-MAST-1',
    role: 'Physical RF Transceiver mounted on signal mast arm; aggregates vehicle packets',
    iconType: 'rsu',
    primaryMetric: '42 Online',
    subMetric: '(100% Corridor)',
    protocol: 'IEEE 802.11p / C-V2X PC5 & Uu',
    standard: 'SAE J2945/1 / ETSI EN 302 665',
    ipMac: '192.168.10.42 / 00:1B:44:11:3A:B7',
    firmware: 'v3.4.1-rc2-clearway',
    frequency: '5.895 - 5.925 GHz (Ch 180)',
    nominalRttMs: 4.1,
    heartbeat: '5ms ago',
    statusText: '4 Units In-Range',
    provenanceNote: 'DEMO_FIXTURE: Virtual roadside station receiver emulating 5.9 GHz RF spectrum.',
  },
  edge: {
    id: 'edge',
    shortName: 'Edge Controller',
    fullName: 'ClearWay Edge AI Computing Unit (EACU-0457)',
    stationId: 'EDGE-0457-PRI',
    role: 'Real-time multi-modal AI edge inference (YOLOv8 + SUMO micro-fusion)',
    iconType: 'edge',
    primaryMetric: 'Online',
    subMetric: '(Primary / Standby)',
    protocol: 'NVIDIA TensorRT / ZeroMQ IPC / gRPC Telemetry',
    standard: 'ISO/TS 19321 (IVI) / ISO 19091',
    ipMac: '192.168.10.2 (Master) / 192.168.10.3 (Backup)',
    firmware: 'v1.4.0-edge-orin-rt',
    frequency: 'Gigabit Fiber Uplink (Local Bus)',
    nominalRttMs: 1.8,
    heartbeat: '2ms ago',
    statusText: 'Nominal (Inference 4.2ms)',
    provenanceNote: 'DEMO_FIXTURE: Emulated edge computing host executing local queue arbitration logic.',
  },
  signal: {
    id: 'signal',
    shortName: 'Signal Controller',
    fullName: 'NEMA TS2 Type 1 / 2070 Signal Controller',
    stationId: 'SIG-0457-NEMA',
    role: 'Hardware signal phase state machine with Malfunction Management Unit (MMU)',
    iconType: 'signal',
    primaryMetric: 'Online',
    subMetric: '(C-V2X / DSRC SPaT)',
    protocol: 'NTCIP 1202 Standard / SPaT & MAP broadcast',
    standard: 'NEMA TS2 / ATC 5201 Standard',
    ipMac: '192.168.10.100 (RS-485 / Ethernet)',
    firmware: 'v4.1.9-nema-safe',
    frequency: 'Hardwired NEMA Bus / Opto-Isolated',
    nominalRttMs: 1.2,
    heartbeat: '3ms ago',
    statusText: '8 Phases Coordinated',
    provenanceNote: 'DEMO_FIXTURE: Simulated NEMA TS2 controller with safety interlock enforcement.',
  },
};

export interface V2XHardwarePanelProps {
  networkId?: string;
  initialMode?: SimulationLinkMode;
  onSelectNode?: (nodeId: V2XNodeId) => void;
  className?: string;
  style?: React.CSSProperties;
}

export const V2XHardwarePanel: React.FC<V2XHardwarePanelProps> = ({
  networkId = 'RM-INT-0457',
  initialMode = 'nominal',
  onSelectNode,
  className = '',
  style,
}) => {
  const [simMode, setSimMode] = useState<SimulationLinkMode>(initialMode);
  const [activeNode, setActiveNode] = useState<V2XNodeId | null>(null);
  const [pinging, setPinging] = useState<boolean>(false);
  const [pingLog, setPingLog] = useState<string | null>(null);
  const [jitter, setJitter] = useState<{ latency: number; loss: number }>({
    latency: 11.2,
    loss: 0.2,
  });

  // Dynamic telemetry jitter to simulate authentic network polling
  useEffect(() => {
    const timer = setInterval(() => {
      if (simMode === 'nominal') {
        const delta = (Math.random() - 0.5) * 1.2;
        setJitter({
          latency: Number(Math.max(9.8, Math.min(13.4, 11.2 + delta)).toFixed(1)),
          loss: Number(Math.max(0.1, Math.min(0.3, 0.2 + (Math.random() - 0.5) * 0.1)).toFixed(1)),
        });
      } else if (simMode === 'degraded') {
        const delta = (Math.random() - 0.5) * 8.0;
        setJitter({
          latency: Number(Math.max(68.0, Math.min(88.0, 78.4 + delta)).toFixed(1)),
          loss: Number(Math.max(3.8, Math.min(6.2, 4.8 + (Math.random() - 0.5) * 0.8)).toFixed(1)),
        });
      } else {
        setJitter({ latency: 999.0, loss: 100.0 });
      }
    }, 2500);

    return () => clearInterval(timer);
  }, [simMode]);

  const handleSelectNode = (nodeId: V2XNodeId) => {
    const next = activeNode === nodeId ? null : nodeId;
    setActiveNode(next);
    setPingLog(null);
    if (onSelectNode && next) {
      onSelectNode(next);
    }
  };

  const handlePingDevice = (node: V2XDeviceInfo) => {
    setPinging(true);
    setPingLog(null);
    setTimeout(() => {
      setPinging(false);
      if (simMode === 'offline') {
        setPingLog(`PING ${node.ipMac.split(' ')[0]}: Destination Host Unreachable (100% packet loss)`);
      } else {
        const rtt = simMode === 'degraded' ? (node.nominalRttMs * 6.5).toFixed(1) : node.nominalRttMs.toFixed(1);
        setPingLog(
          `64 bytes from ${node.stationId} (${node.ipMac.split(' ')[0]}): icmp_seq=1 ttl=64 time=${rtt} ms [STATUS: OK]`
        );
      }
    }, 450);
  };

  // Determine channel telemetry from simulation mode
  const hardwareStatus: HardwareStatus = {
    network_id: networkId,
    obu_vehicles_online: simMode === 'offline' ? 0 : 1842,
    obu_pct: simMode === 'offline' ? 0.0 : 99.2,
    rsu_online: simMode === 'offline' ? 0 : simMode === 'degraded' ? 38 : 42,
    rsu_pct: simMode === 'offline' ? 0.0 : simMode === 'degraded' ? 90.5 : 100.0,
    edge_controllers_online: simMode === 'offline' ? 0 : 2,
    signal_controllers_online: simMode === 'offline' ? 0 : 4,
    v2x_status: simMode === 'nominal' ? 'Active' : simMode === 'degraded' ? 'Degraded' : 'Offline',
    latency_ms: jitter.latency,
    packet_loss_pct: jitter.loss,
    provenance: 'DEMO_FIXTURE' as DataProvenance,
  };

  const activeDevice = activeNode ? DEVICE_PROFILES[activeNode] : null;

  return (
    <PanelFrame
      title="V2I/V2X Communication & Hardware Status"
      icon={<Wifi size={15} color={simMode === 'offline' ? '#ef476f' : '#00f5d4'} />}
      badge={
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.66rem', color: '#64748b' }}>Network ID:</span>
          <span
            style={{
              fontSize: '0.70rem',
              color: '#00f5d4',
              fontFamily: 'monospace',
              fontWeight: 600,
            }}
          >
            {networkId}
          </span>
          <StatusPill
            label="Simulated V2X Network"
            variant="cyan"
            size="xs"
            title="DEMO_FIXTURE: Pure synthetic testbed. No real live RSUs claimed."
          />
        </div>
      }
      headerActions={
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <button
            type="button"
            onClick={() => setSimMode('nominal')}
            title="Nominal V2X Link (Low latency, 0.2% loss)"
            style={{
              background: simMode === 'nominal' ? 'rgba(6, 214, 160, 0.25)' : 'rgba(15, 23, 42, 0.6)',
              color: simMode === 'nominal' ? '#06d6a0' : '#64748b',
              border: `1px solid ${simMode === 'nominal' ? '#06d6a0' : '#1e293b'}`,
              borderRadius: '4px',
              padding: '2px 6px',
              fontSize: '0.62rem',
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            Nominal
          </button>
          <button
            type="button"
            onClick={() => setSimMode('degraded')}
            title="Simulate High Jitter / Interference"
            style={{
              background: simMode === 'degraded' ? 'rgba(255, 209, 102, 0.25)' : 'rgba(15, 23, 42, 0.6)',
              color: simMode === 'degraded' ? '#ffd166' : '#64748b',
              border: `1px solid ${simMode === 'degraded' ? '#ffd166' : '#1e293b'}`,
              borderRadius: '4px',
              padding: '2px 6px',
              fontSize: '0.62rem',
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            Degraded
          </button>
          <button
            type="button"
            onClick={() => setSimMode('offline')}
            title="Simulate Complete V2X Severance"
            style={{
              background: simMode === 'offline' ? 'rgba(239, 71, 111, 0.25)' : 'rgba(15, 23, 42, 0.6)',
              color: simMode === 'offline' ? '#ef476f' : '#64748b',
              border: `1px solid ${simMode === 'offline' ? '#ef476f' : '#1e293b'}`,
              borderRadius: '4px',
              padding: '2px 6px',
              fontSize: '0.62rem',
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            Offline
          </button>
        </div>
      }
      className={className}
      style={style}
    >
      <div
        style={{
          padding: '10px 12px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          height: '100%',
          gap: '8px',
          boxSizing: 'border-box',
        }}
      >
        {/* Degraded / Severed Warning Alerts */}
        {simMode === 'degraded' && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 8px',
              backgroundColor: 'rgba(255, 209, 102, 0.12)',
              border: '1px solid rgba(255, 209, 102, 0.35)',
              borderRadius: '4px',
              fontSize: '0.66rem',
              color: '#ffd166',
            }}
          >
            <AlertTriangle size={13} color="#ffd166" style={{ flexShrink: 0 }} />
            <span>
              <strong>V2X Link Degraded:</strong> Jitter spike detected (
              {jitter.latency}ms). Fallback to local inductive loops & radar sensors active.
            </span>
          </div>
        )}

        {simMode === 'offline' && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 8px',
              backgroundColor: 'rgba(239, 71, 111, 0.12)',
              border: '1px solid rgba(239, 71, 111, 0.35)',
              borderRadius: '4px',
              fontSize: '0.66rem',
              color: '#ef476f',
            }}
          >
            <ShieldAlert size={13} color="#ef476f" style={{ flexShrink: 0 }} />
            <span>
              <strong>V2X Link Severed:</strong> DSRC/C-V2X carrier dropped. Signal controller switched to autonomous
              isolated coordination.
            </span>
          </div>
        )}

        {/* Pipeline Architecture Diagram: Vehicle ➔ RSU ➔ Edge Controller ➔ Signal Controller */}
        <div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '4px',
            }}
          >
            <span style={{ fontSize: '0.65rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              V2X Hardware Pipeline (Click node to inspect)
            </span>
            <span style={{ fontSize: '0.62rem', color: '#00f5d4', fontFamily: 'monospace' }}>
              {activeNode ? `Inspecting: ${activeDevice?.shortName}` : '4 Connected Nodes'}
            </span>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: '6px',
              backgroundColor: 'rgba(11, 21, 45, 0.65)',
              padding: '8px 6px',
              borderRadius: '6px',
              border: '1px solid #1b2f5b',
              position: 'relative',
            }}
          >
            {/* Node 1: Vehicle (On-Board Units) */}
            <PipelineNodeCard
              profile={DEVICE_PROFILES.obu}
              isSelected={activeNode === 'obu'}
              simMode={simMode}
              onClick={() => handleSelectNode('obu')}
            />

            {/* Connecting Pulse 1 */}
            <PipelinePulseConnector simMode={simMode} />

            {/* Node 2: RSU (Roadside Unit) */}
            <PipelineNodeCard
              profile={DEVICE_PROFILES.rsu}
              isSelected={activeNode === 'rsu'}
              simMode={simMode}
              onClick={() => handleSelectNode('rsu')}
            />

            {/* Connecting Pulse 2 */}
            <PipelinePulseConnector simMode={simMode} />

            {/* Node 3: Edge Controller */}
            <PipelineNodeCard
              profile={DEVICE_PROFILES.edge}
              isSelected={activeNode === 'edge'}
              simMode={simMode}
              onClick={() => handleSelectNode('edge')}
            />

            {/* Connecting Pulse 3 */}
            <PipelinePulseConnector simMode={simMode} />

            {/* Node 4: Signal Controller */}
            <PipelineNodeCard
              profile={DEVICE_PROFILES.signal}
              isSelected={activeNode === 'signal'}
              simMode={simMode}
              onClick={() => handleSelectNode('signal')}
            />
          </div>
        </div>

        {/* Interactive Device Inspector Drawer / Modal */}
        {activeDevice && (
          <div
            style={{
              backgroundColor: '#0a1428',
              border: '1px solid #00e5ff55',
              borderRadius: '6px',
              padding: '8px 10px',
              boxShadow: '0 4px 12px rgba(0, 229, 255, 0.1)',
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                borderBottom: '1px solid #162547',
                paddingBottom: '4px',
                marginBottom: '6px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Terminal size={13} color="#00e5ff" />
                <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#f1f5f9' }}>
                  {activeDevice.fullName}
                </span>
                <span
                  style={{
                    fontSize: '0.62rem',
                    color: '#64748b',
                    fontFamily: 'monospace',
                    backgroundColor: '#122347',
                    padding: '1px 4px',
                    borderRadius: '3px',
                  }}
                >
                  {activeDevice.stationId}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setActiveNode(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#94a3b8',
                  cursor: 'pointer',
                  padding: '2px',
                  display: 'flex',
                  alignItems: 'center',
                }}
                title="Close Inspector"
              >
                <X size={14} />
              </button>
            </div>

            {/* Inspector Key-Value Diagnostics */}
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '4px 8px',
                fontSize: '0.64rem',
                color: '#94a3b8',
                marginBottom: '6px',
              }}
            >
              <div>
                <span style={{ color: '#64748b' }}>Protocol: </span>
                <span style={{ color: '#00f5d4', fontFamily: 'monospace' }}>{activeDevice.protocol}</span>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>RF / Standard: </span>
                <span style={{ color: '#f1f5f9', fontFamily: 'monospace' }}>{activeDevice.frequency}</span>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>Station IP/MAC: </span>
                <span style={{ color: '#f1f5f9', fontFamily: 'monospace' }}>{activeDevice.ipMac}</span>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>Firmware: </span>
                <span style={{ color: '#06d6a0', fontFamily: 'monospace' }}>{activeDevice.firmware}</span>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>Nominal RTT: </span>
                <span style={{ color: '#00f5d4', fontFamily: 'monospace' }}>
                  {simMode === 'offline' ? 'TIMEOUT' : `${activeDevice.nominalRttMs} ms`}
                </span>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>Last Heartbeat: </span>
                <span style={{ color: simMode === 'offline' ? '#ef476f' : '#f1f5f9' }}>
                  {simMode === 'offline' ? 'STALE (>60s)' : activeDevice.heartbeat}
                </span>
              </div>
            </div>

            {/* Honest Provenance Disclaimer */}
            <div
              style={{
                fontSize: '0.60rem',
                color: '#64748b',
                backgroundColor: 'rgba(7, 13, 30, 0.8)',
                padding: '4px 6px',
                borderRadius: '3px',
                border: '1px dashed #1b2f5b',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div>
                <span style={{ color: '#00f5d4', fontWeight: 600 }}>PROVENANCE: </span>
                <span>{activeDevice.provenanceNote}</span>
              </div>
              <button
                type="button"
                onClick={() => handlePingDevice(activeDevice)}
                disabled={pinging}
                style={{
                  background: 'rgba(0, 229, 255, 0.15)',
                  border: '1px solid #00e5ff66',
                  color: '#00e5ff',
                  borderRadius: '3px',
                  padding: '2px 6px',
                  fontSize: '0.60rem',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '3px',
                  whiteSpace: 'nowrap',
                }}
              >
                <RefreshCw size={10} className={pinging ? 'live-pulse-cyan' : ''} />
                {pinging ? 'Pinging...' : 'Ping Diagnostics'}
              </button>
            </div>

            {/* Ping diagnostics output */}
            {pingLog && (
              <div
                style={{
                  marginTop: '4px',
                  padding: '3px 6px',
                  backgroundColor: '#050a18',
                  borderRadius: '3px',
                  fontFamily: 'monospace',
                  fontSize: '0.60rem',
                  color: pingLog.includes('Unreachable') ? '#ef476f' : '#06d6a0',
                  border: `1px solid ${pingLog.includes('Unreachable') ? '#ef476f44' : '#06d6a044'}`,
                }}
              >
                {pingLog}
              </div>
            )}
          </div>
        )}

        {/* Telemetry Metrics Footer */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '6px 10px',
            backgroundColor: '#0a1128',
            borderRadius: '4px',
            border: '1px solid #162547',
            fontSize: '0.70rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            {simMode === 'nominal' ? (
              <CheckCircle size={13} color="#06d6a0" />
            ) : simMode === 'degraded' ? (
              <AlertTriangle size={13} color="#ffd166" />
            ) : (
              <WifiOff size={13} color="#ef476f" />
            )}
            <span style={{ color: '#94a3b8' }}>V2X Link:</span>
            <StatusPill
              label={
                simMode === 'nominal'
                  ? 'Active (Simulated)'
                  : simMode === 'degraded'
                  ? 'Degraded (Jitter)'
                  : 'Offline (Fail-Safe)'
              }
              variant={simMode === 'nominal' ? 'green' : simMode === 'degraded' ? 'amber' : 'red'}
              size="xs"
              pulse={simMode === 'nominal'}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ color: '#94a3b8' }}>Latency: </span>
            <span
              style={{
                color: simMode === 'nominal' ? '#00f5d4' : simMode === 'degraded' ? '#ffd166' : '#ef476f',
                fontWeight: 600,
                fontFamily: 'monospace',
              }}
            >
              {simMode === 'offline' ? 'TIMEOUT' : `${hardwareStatus.latency_ms} ms`}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ color: '#94a3b8' }}>Packet Loss: </span>
            <span
              style={{
                color: simMode === 'nominal' ? '#06d6a0' : simMode === 'degraded' ? '#ffd166' : '#ef476f',
                fontWeight: 600,
                fontFamily: 'monospace',
              }}
            >
              {hardwareStatus.packet_loss_pct}%
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ color: '#64748b', fontSize: '0.64rem' }}>RF: </span>
            <span style={{ color: '#94a3b8', fontSize: '0.66rem', fontFamily: 'monospace' }}>5.9 GHz DSRC / C-V2X</span>
          </div>
        </div>
      </div>
    </PanelFrame>
  );
};

// Reusable individual hardware node card in pipeline
interface PipelineNodeCardProps {
  profile: V2XDeviceInfo;
  isSelected: boolean;
  simMode: SimulationLinkMode;
  onClick: () => void;
}

const PipelineNodeCard: React.FC<PipelineNodeCardProps> = ({ profile, isSelected, simMode, onClick }) => {
  const isSevered = simMode === 'offline';
  const isJitter = simMode === 'degraded';

  const getNodeIcon = () => {
    const color = isSevered ? '#ef476f' : isJitter ? '#ffd166' : '#00e5ff';
    switch (profile.iconType) {
      case 'obu':
        return <Cpu size={15} color={color} />;
      case 'rsu':
        return <Radio size={15} color={isSevered ? '#ef476f' : '#00f5d4'} />;
      case 'edge':
        return <Server size={15} color={color} />;
      case 'signal':
        return <Activity size={15} color={isSevered ? '#ef476f' : '#ffd166'} />;
    }
  };

  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '2px',
        padding: '6px 4px',
        backgroundColor: isSelected ? 'rgba(0, 229, 255, 0.12)' : 'rgba(13, 27, 56, 0.5)',
        border: `1px solid ${isSelected ? '#00e5ff' : isSevered ? '#ef476f44' : '#1b2f5b'}`,
        borderRadius: '5px',
        cursor: 'pointer',
        textAlign: 'center',
        transition: 'all 0.15s ease',
        outline: 'none',
      }}
      title={`Click to inspect ${profile.fullName}`}
    >
      <div style={{ marginBottom: '1px' }}>{getNodeIcon()}</div>
      <div style={{ fontSize: '0.60rem', color: '#94a3b8', fontWeight: 500 }}>{profile.shortName}</div>
      <div
        style={{
          fontSize: '0.74rem',
          fontWeight: 700,
          color: isSevered ? '#ef476f' : isJitter ? '#ffd166' : '#06d6a0',
          fontFamily: 'monospace',
        }}
      >
        {isSevered ? 'Offline' : profile.primaryMetric}
      </div>
      <div style={{ fontSize: '0.58rem', color: '#64748b' }}>
        {isSevered ? '(Severed)' : profile.subMetric}
      </div>
    </button>
  );
};

// Pipeline connector pulse element between nodes
const PipelinePulseConnector: React.FC<{ simMode: SimulationLinkMode }> = ({ simMode }) => {
  return (
    <div
      style={{
        position: 'absolute',
        top: '50%',
        transform: 'translateY(-50%)',
        pointerEvents: 'none',
        display: 'none', // Handled visually by layout spacing
      }}
    />
  );
};

export default V2XHardwarePanel;

