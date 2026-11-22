import React, { useState, useEffect } from 'react';
import {
  Flame,
  X,
  CheckCircle,
  AlertTriangle,
  Clock,
  Navigation,
  ShieldAlert,
  Radio,
  Hospital,
  ChevronRight,
  Activity,
  RotateCcw,
} from 'lucide-react';
import { StatusPill } from '../../components/StatusPill';
import { EmergencyMission, DataProvenance } from '@clearway/shared';

export interface MissionDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  onTogglePreemption?: (active: boolean) => void;
}

export const MissionDrawer: React.FC<MissionDrawerProps> = ({
  isOpen,
  onClose,
  onTogglePreemption,
}) => {
  const [missionStatus, setMissionStatus] = useState<'ACTIVE' | 'STANDBY' | 'COMPLETED'>('ACTIVE');
  const [etaSeconds, setEtaSeconds] = useState<number>(42);
  const [speedKmh, setSpeedKmh] = useState<number>(58);
  const [simulatedObstacle, setSimulatedObstacle] = useState<boolean>(false);

  // Live ETA countdown
  useEffect(() => {
    if (!isOpen || missionStatus !== 'ACTIVE') return;
    const interval = setInterval(() => {
      setEtaSeconds((prev) => (prev > 1 ? prev - 1 : 45));
      setSpeedKmh((prev) => Number((55 + (Math.random() - 0.5) * 6).toFixed(0)));
    }, 1000);
    return () => clearInterval(interval);
  }, [isOpen, missionStatus]);

  if (!isOpen) return null;

  const missionData: EmergencyMission = {
    mission_id: 'EM-2026-088',
    vehicle_id: 'AMB-339',
    vehicle_type: 'ambulance',
    target_facility: 'Metropolitan General Hospital (Trauma Center)',
    eta_hospital_min: Number((etaSeconds / 60).toFixed(1)),
    status: missionStatus,
    corridor_intersections: ['INT-0455', 'INT-0456', 'INT-0457', 'INT-0458'],
    provenance: 'DEMO_FIXTURE' as DataProvenance,
  };

  const handleToggleActive = () => {
    const nextStatus = missionStatus === 'ACTIVE' ? 'STANDBY' : 'ACTIVE';
    setMissionStatus(nextStatus);
    if (onTogglePreemption) {
      onTogglePreemption(nextStatus === 'ACTIVE');
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: '48px',
        right: '0',
        width: '380px',
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
      {/* Drawer Header */}
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
              backgroundColor: 'rgba(239, 71, 111, 0.2)',
              border: '1px solid #ef476f',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Flame size={16} color="#ef476f" className="live-pulse-red" />
          </div>
          <div>
            <div style={{ fontSize: '0.85rem', fontWeight: 800, color: '#f1f5f9' }}>
              Mission Control: {missionData.mission_id}
            </div>
            <div style={{ fontSize: '0.62rem', color: '#94a3b8' }}>
              Priority Vehicle Emergency Corridor
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            color: '#94a3b8',
            cursor: 'pointer',
            padding: '4px',
            borderRadius: '4px',
          }}
          title="Close Mission Drawer [ESC]"
        >
          <X size={18} />
        </button>
      </div>

      {/* Body Content */}
      <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {/* Mission Status Card */}
        <div
          style={{
            backgroundColor: '#0d1b38',
            border: '1px solid #1b2f5b',
            borderRadius: '6px',
            padding: '10px 12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '0.68rem', color: '#94a3b8' }}>Corridor Pre-emption Status</span>
            <StatusPill
              label={missionStatus === 'ACTIVE' ? 'CORRIDOR ACTIVE' : 'STANDBY'}
              variant={missionStatus === 'ACTIVE' ? 'red' : 'neutral'}
              size="xs"
              pulse={missionStatus === 'ACTIVE'}
            />
          </div>

          {/* Large ETA and Speed Readout */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', textAlign: 'center' }}>
            <div style={{ backgroundColor: '#070d1e', padding: '8px', borderRadius: '4px', border: '1px solid #162547' }}>
              <div style={{ fontSize: '0.62rem', color: '#64748b' }}>Time to Hospital</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#00f5d4', fontFamily: 'monospace' }}>
                {etaSeconds}s
              </div>
              <div style={{ fontSize: '0.58rem', color: '#06d6a0' }}>1.8 km Remaining</div>
            </div>

            <div style={{ backgroundColor: '#070d1e', padding: '8px', borderRadius: '4px', border: '1px solid #162547' }}>
              <div style={{ fontSize: '0.62rem', color: '#64748b' }}>Vehicle Speed</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#ef476f', fontFamily: 'monospace' }}>
                {speedKmh} <span style={{ fontSize: '0.65rem' }}>km/h</span>
              </div>
              <div style={{ fontSize: '0.58rem', color: '#94a3b8' }}>Unit: {missionData.vehicle_id}</div>
            </div>
          </div>
        </div>

        {/* Target Facility & Vehicle Profile */}
        <div
          style={{
            backgroundColor: '#0d1b38',
            border: '1px solid #1b2f5b',
            borderRadius: '6px',
            padding: '10px 12px',
            fontSize: '0.68rem',
            color: '#cbd5e1',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
            <Hospital size={14} color="#00e5ff" />
            <strong style={{ color: '#f1f5f9' }}>Destination Facility</strong>
          </div>
          <div style={{ color: '#00f5d4', fontWeight: 600, marginBottom: '6px' }}>
            {missionData.target_facility}
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '0.62rem', color: '#94a3b8' }}>
            <div>Unit Type: <strong style={{ color: '#f1f5f9' }}>ALS Ambulance</strong></div>
            <div>Call Sign: <strong style={{ color: '#f1f5f9' }}>AMB-339</strong></div>
            <div>Corridor: <strong style={{ color: '#00e5ff' }}>5th Avenue E-W</strong></div>
            <div>Dispatched: <strong style={{ color: '#f1f5f9' }}>Station 04 (02m 14s)</strong></div>
          </div>
        </div>

        {/* 4-Intersection Node Chain State Machine */}
        <div
          style={{
            backgroundColor: '#0d1b38',
            border: '1px solid #1b2f5b',
            borderRadius: '6px',
            padding: '10px 12px',
          }}
        >
          <div style={{ fontSize: '0.68rem', fontWeight: 700, color: '#94a3b8', marginBottom: '8px' }}>
            Corridor Nodes Green Wave Chain
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {/* Node 1: INT-0455 */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.65rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <CheckCircle size={12} color="#06d6a0" />
                <span style={{ color: '#f1f5f9' }}>INT-0455 (Maple & 5th)</span>
              </div>
              <span style={{ color: '#06d6a0', fontFamily: 'monospace', fontWeight: 700 }}>CLEARED</span>
            </div>

            {/* Node 2: INT-0456 */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.65rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Activity size={12} color="#00e5ff" />
                <span style={{ color: '#f1f5f9' }}>INT-0456 (Cedar & 5th)</span>
              </div>
              <span style={{ color: '#00e5ff', fontFamily: 'monospace', fontWeight: 700 }}>ACTIVE WAVE</span>
            </div>

            {/* Node 3: INT-0457 (Target) */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontSize: '0.65rem',
                backgroundColor: 'rgba(0, 229, 255, 0.08)',
                padding: '4px 6px',
                borderRadius: '4px',
                border: '1px solid #00e5ff44',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Flame size={12} color="#ef476f" />
                <span style={{ color: '#00f5d4', fontWeight: 700 }}>INT-0457 (Oak & 5th - Digital Twin)</span>
              </div>
              <span style={{ color: '#ef476f', fontFamily: 'monospace', fontWeight: 700 }}>PREEMPTED (HOLD)</span>
            </div>

            {/* Node 4: INT-0458 */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.65rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Clock size={12} color="#ffd166" />
                <span style={{ color: '#94a3b8' }}>INT-0458 (Pine & 5th)</span>
              </div>
              <span style={{ color: '#ffd166', fontFamily: 'monospace', fontWeight: 700 }}>STAGED</span>
            </div>
          </div>
        </div>

        {/* Operational Actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <button
            type="button"
            onClick={handleToggleActive}
            style={{
              padding: '8px',
              backgroundColor: missionStatus === 'ACTIVE' ? 'rgba(239, 71, 111, 0.25)' : 'rgba(6, 214, 160, 0.25)',
              border: `1px solid ${missionStatus === 'ACTIVE' ? '#ef476f' : '#06d6a0'}`,
              color: missionStatus === 'ACTIVE' ? '#ef476f' : '#06d6a0',
              borderRadius: '5px',
              fontSize: '0.72rem',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            {missionStatus === 'ACTIVE' ? 'DISENGAGE CORRIDOR PRE-EMPTION' : 'ENGAGE CORRIDOR PRE-EMPTION'}
          </button>

          <button
            type="button"
            onClick={() => setSimulatedObstacle(!simulatedObstacle)}
            style={{
              padding: '6px',
              backgroundColor: simulatedObstacle ? 'rgba(255, 209, 102, 0.2)' : 'rgba(30, 41, 59, 0.6)',
              border: `1px solid ${simulatedObstacle ? '#ffd166' : '#1e293b'}`,
              color: simulatedObstacle ? '#ffd166' : '#94a3b8',
              borderRadius: '5px',
              fontSize: '0.68rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '4px',
            }}
          >
            <AlertTriangle size={12} />
            <span>{simulatedObstacle ? 'Remove Spillback Obstacle' : 'Inject Simulated Spillback (INC-092)'}</span>
          </button>
        </div>

        {/* Simulated Obstacle Notice */}
        {simulatedObstacle && (
          <div
            style={{
              padding: '6px 8px',
              backgroundColor: 'rgba(255, 209, 102, 0.12)',
              border: '1px solid rgba(255, 209, 102, 0.35)',
              borderRadius: '4px',
              fontSize: '0.62rem',
              color: '#ffd166',
            }}
          >
            <strong>Incident Active:</strong> Stalled delivery truck on 5th Ave EB lane 2. AI route advisor recommendation: dynamic green wave extension on Oak St.
          </div>
        )}

        {/* Safety Gate & Provenance Disclaimer */}
        <div
          style={{
            marginTop: 'auto',
            padding: '8px',
            backgroundColor: '#070d1e',
            borderRadius: '4px',
            border: '1px dashed #1b2f5b',
            fontSize: '0.60rem',
            color: '#64748b',
          }}
        >
          <div style={{ color: '#00f5d4', fontWeight: 600, marginBottom: '2px' }}>
            SAFETY INTERLOCK ACTIVE — DEMO_FIXTURE
          </div>
          <div>
            All corridor signal timing adjustments are computed in software simulation mode. No direct physical actuator commands are permitted on live public roadways.
          </div>
        </div>
      </div>
    </div>
  );
};

export default MissionDrawer;

