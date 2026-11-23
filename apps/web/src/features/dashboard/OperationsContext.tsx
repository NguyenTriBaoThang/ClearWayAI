/**
 * Operations Center Real-Time Context & State Manager
 *
 * Coordinates live telemetry, backend API integration, WebSocket streaming,
 * simulation execution, emergency mission pre-clearance, and safety audit feeds.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  ConnectionStatus,
  MissionItem,
  MultiNodeETAReport,
  CorridorPlanResult,
  SafetyAuditResult,
  SnapshotSummary,
} from '../../types';
import * as api from '../../services/api';
import { useWebSocketStream } from '../../services/websocket';

interface OperationsContextType {
  // Connection & System
  connectionStatus: ConnectionStatus;
  latencyMs: number;
  fps: number;
  simulationId: string;
  simTimeSec: number;
  isPlaying: boolean;
  playbackSpeed: number;

  // Corridor & Mission Telemetry
  activeMission: MissionItem | null;
  multiNodeETA: MultiNodeETAReport | null;
  corridorPlan: CorridorPlanResult | null;
  safetyAudit: SafetyAuditResult | null;
  snapshots: SnapshotSummary[];
  latestSnapshot: any | null;

  // Operational Actions
  togglePlay: () => void;
  stepSimulation: (dt?: number) => Promise<void>;
  setPlaybackSpeed: (speed: number) => void;
  dispatchMission: (vehicleId?: string) => Promise<void>;
  evaluateNodePreclearance: (nodeId: string) => Promise<void>;
  refreshCorridorState: () => Promise<void>;
}

const OperationsContext = createContext<OperationsContextType | null>(null);

export const OperationsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [simulationId] = useState<string>('sim-corridor-oak');
  const [simTimeSec, setSimTimeSec] = useState<number>(14.2);
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [playbackSpeed, setPlaybackSpeedState] = useState<number>(1.0);

  const [activeMission, setActiveMission] = useState<MissionItem | null>(null);
  const [multiNodeETA, setMultiNodeETA] = useState<MultiNodeETAReport | null>(null);
  const [corridorPlan, setCorridorPlan] = useState<CorridorPlanResult | null>(null);
  const [safetyAudit, setSafetyAudit] = useState<SafetyAuditResult | null>(null);
  const [snapshots, setSnapshots] = useState<SnapshotSummary[]>([]);
  const [latestSnapshot, setLatestSnapshot] = useState<any | null>(null);

  // Real-time WebSocket hook
  const { status, latencyMs, fps, sendCommand } = useWebSocketStream({
    simulationId,
    onSnapshot: (snapData) => {
      setLatestSnapshot(snapData);
      if (typeof snapData.sim_time_sec === 'number') {
        setSimTimeSec(snapData.sim_time_sec);
      }
    },
    onEvent: (event, payload) => {
      console.log(`[WebSocket Event] ${event}:`, payload);
    },
  });

  // Initial data loading from REST API
  const refreshCorridorState = useCallback(async () => {
    try {
      const [plan, audit, missionsList] = await Promise.all([
        api.getCorridorPlan(),
        api.getSafetyAudit(),
        api.listMissions(),
      ]);

      setCorridorPlan(plan);
      setSafetyAudit(audit);

      if (missionsList && missionsList.length > 0) {
        const primary = missionsList[0];
        setActiveMission(primary);
        const eta = await api.getMissionETA(primary.mission_id);
        setMultiNodeETA(eta);
      } else {
        // Fallback default mission for interactive demonstration
        const eta = await api.getMissionETA('mission-amb-339');
        setMultiNodeETA(eta);
        setActiveMission({
          mission_id: 'mission-amb-339',
          vehicle_id: 'AMB-339',
          vehicle_type: 'emergency_ambulance',
          status: 'ACTIVE',
          origin: 'West Feeder Gate',
          destination: 'Metropolitan Trauma Center',
          dispatched_at: new Date().toISOString(),
          current_position_m: -150.0,
          current_speed_kmh: 66.6,
          progress_ratio: 0.18,
          is_active: true,
          route_nodes: ['node_a', 'node_b', 'node_c', 'node_d'],
        });
      }
    } catch (err) {
      console.warn('Could not refresh corridor state from API:', err);
    }
  }, []);

  useEffect(() => {
    refreshCorridorState();
  }, [refreshCorridorState]);

  // Periodic simulation time advancement if isPlaying
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setSimTimeSec((prev) => Math.round((prev + 0.1 * playbackSpeed) * 10) / 10);
    }, 100);
    return () => clearInterval(interval);
  }, [isPlaying, playbackSpeed]);

  const togglePlay = useCallback(() => {
    setIsPlaying((prev) => {
      const next = !prev;
      sendCommand(next ? 'resume' : 'pause');
      return next;
    });
  }, [sendCommand]);

  const stepSimulation = useCallback(
    async (dt = 0.1) => {
      sendCommand('step', { dt });
      try {
        const res = await api.stepSimulation(simulationId, dt, activeMission?.mission_id);
        setSimTimeSec(res.sim_time_sec);
        if ((res as any).snapshot) {
          setLatestSnapshot((res as any).snapshot);
        }
      } catch {
        setSimTimeSec((prev) => Math.round((prev + dt) * 10) / 10);
      }
    },
    [sendCommand, simulationId, activeMission]
  );

  const setPlaybackSpeed = useCallback(
    (speed: number) => {
      setPlaybackSpeedState(speed);
      sendCommand('speed', { multiplier: speed });
    },
    [sendCommand]
  );

  const dispatchMission = useCallback(
    async (vehicleId = 'AMB-339') => {
      try {
        const newMission = await api.createMission(vehicleId, 1);
        setActiveMission(newMission);
        const eta = await api.getMissionETA(newMission.mission_id);
        setMultiNodeETA(eta);
      } catch (err) {
        console.warn('Failed to dispatch mission:', err);
      }
    },
    []
  );

  const evaluateNodePreclearance = useCallback(async (nodeId: string) => {
    try {
      const decision = await api.evaluatePreclearance(nodeId);
      console.log(`Pre-clearance decision for ${nodeId}:`, decision);
    } catch (err) {
      console.warn('Failed to evaluate preclearance:', err);
    }
  }, []);

  return (
    <OperationsContext.Provider
      value={{
        connectionStatus: status,
        latencyMs,
        fps,
        simulationId,
        simTimeSec,
        isPlaying,
        playbackSpeed,
        activeMission,
        multiNodeETA,
        corridorPlan,
        safetyAudit,
        snapshots,
        latestSnapshot,
        togglePlay,
        stepSimulation,
        setPlaybackSpeed,
        dispatchMission,
        evaluateNodePreclearance,
        refreshCorridorState,
      }}
    >
      {children}
    </OperationsContext.Provider>
  );
};

export const useOperations = (): OperationsContextType => {
  const context = useContext(OperationsContext);
  if (!context) {
    throw new Error('useOperations must be used within an OperationsProvider');
  }
  return context;
};

export const useSafeOperations = (): OperationsContextType | null => {
  return useContext(OperationsContext);
};

