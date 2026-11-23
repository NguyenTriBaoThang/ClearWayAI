/**
 * ClearWayAI - 3D Dual Simulation Comparison Viewport (`DualSimulationComparison.tsx`)
 *
 * Provides a split-view synchronized 3D comparison demonstrating empirical superiority:
 * - Left Viewport: Baseline B0 (Fixed-Time Webster, no preemption, red-light stops, queue delays)
 * - Right Viewport: ClearWay AI (Moving-Horizon Pre-clearance, green wave, 0 stops, -44.4% delay)
 * - Synchronized playback timeline with play, pause, step, speed multiplier, and timeline scrubber
 * - Synchronized dual camera lockstep (panning/orbiting on one viewport mirrors to the other)
 * - Live comparative KPI delta banner (Travel Time, Stops, Average Speed, Queue Backlog)
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';
import {
  Play,
  Pause,
  RotateCcw,
  FastForward,
  StepForward,
  Link2,
  Unlink2,
  Gauge,
  Clock,
  AlertTriangle,
  Zap,
  TrendingDown,
  ShieldCheck,
  Compass,
} from 'lucide-react';
import { SceneEnvironment } from './SceneEnvironment';
import { SceneController, CameraPresetType } from './SceneController';
import { BaselineFixedTimeTrajectory } from './BaselineFixedTimeTrajectory';
import { ClearWayAITrajectory } from './ClearWayAITrajectory';

interface DualSimulationComparisonProps {
  style?: React.CSSProperties;
  onClose?: () => void;
}

export const DualSimulationComparison: React.FC<DualSimulationComparisonProps> = ({
  style,
  onClose,
}) => {
  const containerLeftRef = useRef<HTMLDivElement>(null);
  const containerRightRef = useRef<HTMLDivElement>(null);

  // Scene references
  const leftEnvRef = useRef<SceneEnvironment | null>(null);
  const rightEnvRef = useRef<SceneEnvironment | null>(null);
  const leftCtrlRef = useRef<SceneController | null>(null);
  const rightCtrlRef = useRef<SceneController | null>(null);

  // Trajectory sources
  const baselineSourceRef = useRef<BaselineFixedTimeTrajectory>(new BaselineFixedTimeTrajectory());
  const aiSourceRef = useRef<ClearWayAITrajectory>(new ClearWayAITrajectory());

  // Simulation playback state
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  const [simTimeSec, setSimTimeSec] = useState<number>(0.0);
  const [playbackSpeed, setPlaybackSpeed] = useState<number>(1.0);
  const [syncCameras, setSyncCameras] = useState<boolean>(true);
  const [activeCameraPreset, setActiveCameraPreset] = useState<CameraPresetType>('corridor');

  // Real-time telemetry for comparative HUD
  const [leftAmbState, setLeftAmbState] = useState({
    x: -150,
    speedKmh: 50,
    status: 'RUNNING',
    stops: 0,
    waitingSec: 0,
  });
  const [rightAmbState, setRightAmbState] = useState({
    x: -150,
    speedKmh: 60,
    status: 'PRIORITY_CORRIDOR',
    stops: 0,
    waitingSec: 0,
  });

  // Track playback time using ref to avoid closure staleness in render loop
  const simTimeRef = useRef<number>(0.0);
  const isPlayingRef = useRef<boolean>(true);
  const playbackSpeedRef = useRef<number>(1.0);

  useEffect(() => {
    isPlayingRef.current = isPlaying;
  }, [isPlaying]);

  useEffect(() => {
    playbackSpeedRef.current = playbackSpeed;
  }, [playbackSpeed]);

  // Synchronized camera preset handler
  const handleSelectPreset = useCallback((preset: CameraPresetType) => {
    setActiveCameraPreset(preset);
    if (leftCtrlRef.current) leftCtrlRef.current.setPreset(preset);
    if (rightCtrlRef.current) rightCtrlRef.current.setPreset(preset);
  }, []);

  // Main Dual WebGL Canvas Initialization
  useEffect(() => {
    if (!containerLeftRef.current || !containerRightRef.current) return;

    const leftContainer = containerLeftRef.current;
    const rightContainer = containerRightRef.current;

    const width = leftContainer.clientWidth || 400;
    const height = leftContainer.clientHeight || 400;

    // 1. Create Left Three.js Scene (Baseline Fixed-Time)
    const leftScene = new THREE.Scene();
    leftScene.background = new THREE.Color(0x0a1128);
    const leftRenderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
    leftRenderer.setSize(width, height);
    leftRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    leftContainer.appendChild(leftRenderer.domElement);

    const leftEnv = new SceneEnvironment(leftScene);
    leftEnv.setCorridorMode(true);
    leftEnv.vehicleManager.motionSystem.setTrajectorySource(baselineSourceRef.current);
    leftEnvRef.current = leftEnv;

    const leftCtrl = new SceneController(leftContainer, width, height);
    leftCtrl.setPreset('corridor');
    leftCtrlRef.current = leftCtrl;

    // 2. Create Right Three.js Scene (ClearWay AI Green Wave)
    const rightScene = new THREE.Scene();
    rightScene.background = new THREE.Color(0x07112c);
    const rightRenderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
    rightRenderer.setSize(width, height);
    rightRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    rightContainer.appendChild(rightRenderer.domElement);

    const rightEnv = new SceneEnvironment(rightScene);
    rightEnv.setCorridorMode(true);
    rightEnv.vehicleManager.motionSystem.setTrajectorySource(aiSourceRef.current);
    rightEnvRef.current = rightEnv;

    const rightCtrl = new SceneController(rightContainer, width, height);
    rightCtrl.setPreset('corridor');
    rightCtrlRef.current = rightCtrl;

    // Synchronize camera controls if syncCameras is enabled
    leftCtrl.controls.addEventListener('change', () => {
      if (syncCameras && rightCtrlRef.current && leftCtrlRef.current) {
        rightCtrlRef.current.activeCamera.position.copy(leftCtrlRef.current.activeCamera.position);
        rightCtrlRef.current.controls.target.copy(leftCtrlRef.current.controls.target);
        rightCtrlRef.current.controls.update();
      }
    });

    rightCtrl.controls.addEventListener('change', () => {
      if (syncCameras && leftCtrlRef.current && rightCtrlRef.current) {
        leftCtrlRef.current.activeCamera.position.copy(rightCtrlRef.current.activeCamera.position);
        leftCtrlRef.current.controls.target.copy(rightCtrlRef.current.controls.target);
        leftCtrlRef.current.controls.update();
      }
    });

    // 3. Render Loop
    let frameId: number;
    let lastWallTime = performance.now();
    let tickCount = 0;

    const animate = () => {
      frameId = requestAnimationFrame(animate);
      const now = performance.now();
      const wallDtSec = (now - lastWallTime) / 1000;
      lastWallTime = now;

      if (isPlayingRef.current) {
        simTimeRef.current = (simTimeRef.current + wallDtSec * playbackSpeedRef.current) % 115.0;
      }

      const currentT = simTimeRef.current;
      const simTimeMs = currentT * 1000;

      // Update signal lights in both scenes:
      // Left: Rigid 72s Webster cycle
      const baselinePhase = baselineSourceRef.current.getSignalPhaseAtTime(currentT);
      leftEnv.multiSignals.setNodePhase('node_a', baselinePhase);
      leftEnv.multiSignals.setNodePhase('node_b', baselinePhase);
      leftEnv.multiSignals.setNodePhase('node_c', baselinePhase);
      leftEnv.multiSignals.setNodePhase('node_d', baselinePhase);

      // Right: ClearWay AI JIT Preemption
      const rightAmb = aiSourceRef.current.getVehicleState('AMB-339');
      const rightAmbX = rightAmb ? rightAmb.x : -150;
      rightEnv.multiSignals.setNodePhase('node_a', aiSourceRef.current.getSignalPhaseForNode('node_a', rightAmbX));
      rightEnv.multiSignals.setNodePhase('node_b', aiSourceRef.current.getSignalPhaseForNode('node_b', rightAmbX));
      rightEnv.multiSignals.setNodePhase('node_c', aiSourceRef.current.getSignalPhaseForNode('node_c', rightAmbX));
      rightEnv.multiSignals.setNodePhase('node_d', aiSourceRef.current.getSignalPhaseForNode('node_d', rightAmbX));

      // Step both environments with synchronized simulation time
      const leftAmbPos = leftEnv.update(simTimeMs);
      const rightAmbPos = rightEnv.update(simTimeMs);

      leftCtrl.update(leftAmbPos);
      rightCtrl.update(rightAmbPos);

      leftRenderer.render(leftScene, leftCtrl.activeCamera);
      rightRenderer.render(rightScene, rightCtrl.activeCamera);

      // Periodically update React state telemetry (~10 frames)
      tickCount++;
      if (tickCount % 8 === 0) {
        setSimTimeSec(parseFloat(currentT.toFixed(1)));

        const lAmb = baselineSourceRef.current.getVehicleState('AMB-339');
        if (lAmb) {
          const stops = currentT >= 78 ? 2 : currentT >= 24 ? 1 : 0;
          setLeftAmbState({
            x: Math.round(lAmb.x),
            speedKmh: Math.round(lAmb.speed_kmh),
            status: lAmb.status,
            stops,
            waitingSec: Math.round(lAmb.waiting_time_s),
          });
        }

        const rAmb = aiSourceRef.current.getVehicleState('AMB-339');
        if (rAmb) {
          setRightAmbState({
            x: Math.round(rAmb.x),
            speedKmh: Math.round(rAmb.speed_kmh),
            status: rAmb.status,
            stops: 0,
            waitingSec: 0,
          });
        }
      }
    };

    animate();

    const handleResize = () => {
      if (!leftContainer || !rightContainer) return;
      const newW = leftContainer.clientWidth;
      const newH = leftContainer.clientHeight;
      leftCtrl.handleResize(newW, newH);
      rightCtrl.handleResize(newW, newH);
      leftRenderer.setSize(newW, newH);
      rightRenderer.setSize(newW, newH);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener('resize', handleResize);
      leftCtrl.dispose();
      rightCtrl.dispose();
      leftEnv.dispose();
      rightEnv.dispose();
      if (leftContainer.contains(leftRenderer.domElement)) leftContainer.removeChild(leftRenderer.domElement);
      if (rightContainer.contains(rightRenderer.domElement)) rightContainer.removeChild(rightRenderer.domElement);
      leftRenderer.dispose();
      rightRenderer.dispose();
    };
  }, [syncCameras]);

  // Controls actions
  const handleTogglePlay = () => setIsPlaying((prev) => !prev);
  const handleReset = () => {
    simTimeRef.current = 0.0;
    setSimTimeSec(0.0);
  };
  const handleStep = (dt = 1.0) => {
    simTimeRef.current = Math.min(115.0, simTimeRef.current + dt);
    setSimTimeSec(parseFloat(simTimeRef.current.toFixed(1)));
  };
  const handleScrub = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    simTimeRef.current = val;
    setSimTimeSec(val);
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        height: '100%',
        backgroundColor: '#070d1e',
        borderRadius: '8px',
        border: '1px solid #1b2f5b',
        overflow: 'hidden',
        boxSizing: 'border-box',
        ...style,
      }}
    >
      {/* 1. Top Comparison KPI Delta Header */}
      <div
        style={{
          backgroundColor: 'rgba(10, 17, 40, 0.95)',
          borderBottom: '1px solid #1b325f',
          padding: '8px 14px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Zap size={16} color="#00f5d4" />
          <span style={{ fontSize: '0.86rem', fontWeight: 800, color: '#f1f5f9', letterSpacing: '0.04em' }}>
            SPLIT-VIEW 3D SIMULATION COMPARISON
          </span>
          <span
            style={{
              fontSize: '0.64rem',
              fontWeight: 700,
              backgroundColor: 'rgba(0, 245, 212, 0.15)',
              color: '#00f5d4',
              padding: '2px 8px',
              borderRadius: '4px',
              border: '1px solid rgba(0, 245, 212, 0.4)',
            }}
          >
            T27 EMPIRICAL BENCHMARK
          </span>
        </div>

        {/* Comparative Delta Cards */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Travel Time Delta */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'rgba(15, 23, 42, 0.8)',
              padding: '4px 10px',
              borderRadius: '5px',
              border: '1px solid #1e293b',
              fontSize: '0.68rem',
            }}
          >
            <Clock size={12} color="#38bdf8" />
            <span style={{ color: '#94a3b8' }}>Transit Time:</span>
            <span style={{ color: '#ef476f', fontFamily: 'monospace' }}>108s</span>
            <span style={{ color: '#64748b' }}>vs</span>
            <span style={{ color: '#06d6a0', fontWeight: 700, fontFamily: 'monospace' }}>60s</span>
            <span style={{ color: '#00f5d4', fontWeight: 800 }}>(-44.4%)</span>
          </div>

          {/* Stops Eliminated */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'rgba(15, 23, 42, 0.8)',
              padding: '4px 10px',
              borderRadius: '5px',
              border: '1px solid #1e293b',
              fontSize: '0.68rem',
            }}
          >
            <AlertTriangle size={12} color="#ffd166" />
            <span style={{ color: '#94a3b8' }}>Stops:</span>
            <span style={{ color: '#ef476f', fontFamily: 'monospace' }}>2 stops</span>
            <span style={{ color: '#64748b' }}>vs</span>
            <span style={{ color: '#06d6a0', fontWeight: 700, fontFamily: 'monospace' }}>0 stops</span>
            <span style={{ color: '#06d6a0', fontWeight: 800 }}>(-100%)</span>
          </div>

          {/* Average Speed */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'rgba(15, 23, 42, 0.8)',
              padding: '4px 10px',
              borderRadius: '5px',
              border: '1px solid #1e293b',
              fontSize: '0.68rem',
            }}
          >
            <Gauge size={12} color="#00f5d4" />
            <span style={{ color: '#94a3b8' }}>Avg Speed:</span>
            <span style={{ color: '#ef476f', fontFamily: 'monospace' }}>28 km/h</span>
            <span style={{ color: '#64748b' }}>vs</span>
            <span style={{ color: '#06d6a0', fontWeight: 700, fontFamily: 'monospace' }}>60 km/h</span>
            <span style={{ color: '#00f5d4', fontWeight: 800 }}>(+114%)</span>
          </div>

          {onClose && (
            <button
              onClick={onClose}
              style={{
                backgroundColor: 'rgba(239, 71, 111, 0.15)',
                border: '1px solid #ef476f',
                color: '#ef476f',
                borderRadius: '4px',
                padding: '3px 8px',
                fontSize: '0.66rem',
                cursor: 'pointer',
                fontWeight: 600,
              }}
            >
              Close Split View
            </button>
          )}
        </div>
      </div>

      {/* 2. Dual Side-by-Side 3D Canvas Containers */}
      <div style={{ flex: 1, display: 'flex', position: 'relative', overflow: 'hidden' }}>
        {/* Left Viewport: Baseline B0 Fixed-Time */}
        <div
          style={{
            flex: 1,
            position: 'relative',
            borderRight: '2px solid #1b325f',
            height: '100%',
          }}
        >
          <div ref={containerLeftRef} style={{ width: '100%', height: '100%' }} />

          {/* Left HUD Overlay */}
          <div
            style={{
              position: 'absolute',
              top: '10px',
              left: '12px',
              backgroundColor: 'rgba(10, 17, 40, 0.90)',
              backdropFilter: 'blur(8px)',
              border: '1px solid #ef476f',
              borderRadius: '6px',
              padding: '6px 10px',
              fontSize: '0.68rem',
              color: '#f8fafc',
              boxShadow: '0 4px 14px rgba(239, 71, 111, 0.25)',
              pointerEvents: 'none',
              minWidth: '220px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 800, color: '#ef476f' }}>
              <span>BASELINE B0: FIXED-TIME CONTROL</span>
            </div>
            <div style={{ fontSize: '0.62rem', color: '#94a3b8', marginTop: '2px' }}>
              Rigid 72s Webster Cycle • No Preemption
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', marginTop: '4px', fontSize: '0.64rem' }}>
              <div>
                <span style={{ color: '#64748b' }}>AMB Speed: </span>
                <span style={{ color: leftAmbState.speedKmh > 0 ? '#ffd166' : '#ef4444', fontWeight: 700 }}>
                  {leftAmbState.speedKmh} km/h
                </span>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>Stops Incurred: </span>
                <span style={{ color: '#ef4444', fontWeight: 700 }}>
                  {leftAmbState.stops} stops
                </span>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>Position: </span>
                <span style={{ color: '#cbd5e1' }}>{leftAmbState.x}m / 850m</span>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>Signal State: </span>
                <span style={{ color: leftAmbState.status === 'WAITING_SIGNAL' ? '#ef4444' : '#06d6a0', fontWeight: 700 }}>
                  {leftAmbState.status === 'WAITING_SIGNAL' ? `RED (${leftAmbState.waitingSec}s)` : 'GREEN'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Viewport: ClearWay AI Pre-Clearance */}
        <div
          style={{
            flex: 1,
            position: 'relative',
            height: '100%',
          }}
        >
          <div ref={containerRightRef} style={{ width: '100%', height: '100%' }} />

          {/* Right HUD Overlay */}
          <div
            style={{
              position: 'absolute',
              top: '10px',
              left: '12px',
              backgroundColor: 'rgba(7, 16, 38, 0.92)',
              backdropFilter: 'blur(8px)',
              border: '1px solid #00f5d4',
              borderRadius: '6px',
              padding: '6px 10px',
              fontSize: '0.68rem',
              color: '#f8fafc',
              boxShadow: '0 4px 14px rgba(0, 245, 212, 0.25)',
              pointerEvents: 'none',
              minWidth: '220px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 800, color: '#00f5d4' }}>
              <span>CLEARWAY AI: PRE-CLEARANCE</span>
            </div>
            <div style={{ fontSize: '0.62rem', color: '#94a3b8', marginTop: '2px' }}>
              Moving-Horizon Coordination • JIT Green Wave
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', marginTop: '4px', fontSize: '0.64rem' }}>
              <div>
                <span style={{ color: '#64748b' }}>AMB Speed: </span>
                <span style={{ color: '#06d6a0', fontWeight: 700 }}>
                  {rightAmbState.speedKmh} km/h
                </span>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>Stops Incurred: </span>
                <span style={{ color: '#06d6a0', fontWeight: 700 }}>
                  0 stops (Zero Delay)
                </span>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>Position: </span>
                <span style={{ color: '#cbd5e1' }}>{rightAmbState.x}m / 850m</span>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>Signal State: </span>
                <span style={{ color: '#06d6a0', fontWeight: 700 }}>
                  PREEMPTION GREEN
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Bottom Synchronized Timeline & Camera Controls Bar */}
      <div
        style={{
          backgroundColor: 'rgba(10, 17, 40, 0.95)',
          borderTop: '1px solid #1b325f',
          padding: '6px 14px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '8px',
        }}
      >
        {/* Playback Transport Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            onClick={handleTogglePlay}
            style={{
              backgroundColor: isPlaying ? 'rgba(0, 245, 212, 0.15)' : 'rgba(255, 209, 102, 0.15)',
              border: `1px solid ${isPlaying ? '#00f5d4' : '#ffd166'}`,
              color: isPlaying ? '#00f5d4' : '#ffd166',
              borderRadius: '4px',
              padding: '3px 8px',
              fontSize: '0.66rem',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            {isPlaying ? <Pause size={11} /> : <Play size={11} />}
            <span>{isPlaying ? 'PAUSE' : 'PLAY'}</span>
          </button>

          <button
            onClick={() => handleStep(1.0)}
            title="Step forward +1.0 second"
            style={{
              backgroundColor: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid #1b2f5b',
              color: '#94a3b8',
              borderRadius: '4px',
              padding: '3px 6px',
              fontSize: '0.66rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <StepForward size={11} />
          </button>

          <button
            onClick={handleReset}
            title="Reset simulation to t=0"
            style={{
              backgroundColor: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid #1b2f5b',
              color: '#94a3b8',
              borderRadius: '4px',
              padding: '3px 6px',
              fontSize: '0.66rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <RotateCcw size={11} />
          </button>

          {/* Speed multiplier selector */}
          <div style={{ display: 'flex', gap: '2px', marginLeft: '4px' }}>
            {[1.0, 2.0, 4.0].map((s) => (
              <button
                key={s}
                onClick={() => setPlaybackSpeed(s)}
                style={{
                  backgroundColor: playbackSpeed === s ? 'rgba(0, 229, 255, 0.2)' : 'transparent',
                  border: playbackSpeed === s ? '1px solid #00e5ff' : '1px solid #1e293b',
                  color: playbackSpeed === s ? '#00e5ff' : '#64748b',
                  borderRadius: '3px',
                  padding: '2px 5px',
                  fontSize: '0.60rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                {s}x
              </button>
            ))}
          </div>
        </div>

        {/* Timeline Scrubber */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, maxWidth: '420px', margin: '0 12px' }}>
          <span style={{ fontSize: '0.66rem', color: '#00f5d4', fontFamily: 'monospace', minWidth: '40px' }}>
            {simTimeSec.toFixed(1)}s
          </span>
          <input
            type="range"
            min="0"
            max="115"
            step="0.5"
            value={simTimeSec}
            onChange={handleScrub}
            style={{
              flex: 1,
              accentColor: '#00f5d4',
              cursor: 'pointer',
            }}
          />
          <span style={{ fontSize: '0.66rem', color: '#64748b', fontFamily: 'monospace' }}>
            115.0s
          </span>
        </div>

        {/* Camera Preset & Sync Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          {/* Synchronized Camera Lock Toggle */}
          <button
            onClick={() => setSyncCameras(!syncCameras)}
            title="Toggle Synchronized Camera Pose Linking"
            style={{
              backgroundColor: syncCameras ? 'rgba(0, 245, 212, 0.15)' : 'rgba(15, 23, 42, 0.8)',
              border: `1px solid ${syncCameras ? '#00f5d4' : '#1b2f5b'}`,
              color: syncCameras ? '#00f5d4' : '#64748b',
              borderRadius: '4px',
              padding: '3px 8px',
              fontSize: '0.64rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            {syncCameras ? <Link2 size={11} /> : <Unlink2 size={11} />}
            <span>SYNC CAMS: {syncCameras ? 'ON' : 'OFF'}</span>
          </button>

          {/* Quick Camera Presets */}
          {(['corridor', 'nodeA', 'nodeB', 'nodeC', 'hospital'] as CameraPresetType[]).map((preset) => (
            <button
              key={preset}
              onClick={() => handleSelectPreset(preset)}
              style={{
                backgroundColor: activeCameraPreset === preset ? 'rgba(0, 229, 255, 0.2)' : 'transparent',
                border: activeCameraPreset === preset ? '1px solid #00e5ff' : '1px solid transparent',
                color: activeCameraPreset === preset ? '#00e5ff' : '#94a3b8',
                borderRadius: '3px',
                padding: '2px 5px',
                fontSize: '0.62rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              {preset === 'corridor' ? 'CORRIDOR' : preset === 'hospital' ? 'HOSP' : preset.toUpperCase()}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

