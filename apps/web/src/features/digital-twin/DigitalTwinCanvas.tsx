import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import {
  Box,
  Layers,
  RotateCcw,
  Compass,
  Radio,
  Flame,
  ShieldCheck,
  Video,
  Eye,
  Check,
  Car,
  Crosshair,
  Activity,
  X,
} from 'lucide-react';
import { StatusPill } from '../../components/StatusPill';
import { SceneEnvironment } from './SceneEnvironment';
import { SceneController, CameraPresetType, ProjectionMode, CameraStateMetrics } from './SceneController';
import { VehicleSnapshot } from './VehicleTrajectorySource';
import { InspectedSignalPole } from './TrafficSignal3D';
import { CorridorPlanTelemetry } from './CorridorOverlay3D';
import { CorridorSyncBridge, SyncTelemetry } from './CorridorSyncBridge';
import { useSafeOperations } from '../dashboard/OperationsContext';

interface DigitalTwinCanvasProps {
  intersectionId?: string;
  onSelectEntity?: (id: string, type: string) => void;
  liveSnapshot?: any;
  style?: React.CSSProperties;
}

export const DigitalTwinCanvas: React.FC<DigitalTwinCanvasProps> = ({
  intersectionId = 'INT-0457',
  onSelectEntity,
  liveSnapshot,
  style,
}) => {
  const operations = useSafeOperations();
  const mountRef = useRef<HTMLDivElement>(null);
  const controllerRef = useRef<SceneController | null>(null);
  const environmentRef = useRef<SceneEnvironment | null>(null);
  const bridgeRef = useRef<CorridorSyncBridge | null>(null);

  const [syncTelemetry, setSyncTelemetry] = useState<SyncTelemetry>({
    mode: 'LIVE_SUMO',
    status: 'SYNCED',
    activeVehiclesCount: 0,
    simTimeSec: 0,
    lastPacketAgeMs: 0,
    preemptionActive: false,
    activeNodePhases: { node_a: 0, node_b: 0, node_c: 0, node_d: 0 },
  });

  const [webglInitialized, setWebglInitialized] = useState<boolean>(false);
  const [fps, setFps] = useState<number>(60);
  const [renderMs, setRenderMs] = useState<number>(2.4);
  const [drawCalls, setDrawCalls] = useState<number>(32);
  const [triangles, setTriangles] = useState<number>(5480);

  const [cameraPreset, setCameraPreset] = useState<CameraPresetType>('iso');
  const [corridorMode, setCorridorMode] = useState<boolean>(true);
  const [projectionMode, setProjectionMode] = useState<ProjectionMode>('perspective');
  const [autoRotate, setAutoRotate] = useState<boolean>(false);
  const [showLayersMenu, setShowLayersMenu] = useState<boolean>(false);
  const [showMetrics, setShowMetrics] = useState<boolean>(true);
  const [selectedVehicle, setSelectedVehicle] = useState<VehicleSnapshot | null>(null);
  const [selectedPole, setSelectedPole] = useState<InspectedSignalPole | null>(null);
  const [selectedCorridor, setSelectedCorridor] = useState<CorridorPlanTelemetry | null>(null);
  const [phaseSnapshot, setPhaseSnapshot] = useState<{ ew: string; ns: string; ewSec: number; nsSec: number }>({
    ew: 'green',
    ns: 'red',
    ewSec: 25,
    nsSec: 30,
  });

  const [layers, setLayers] = useState({
    vehicles: true,
    vehicleBadges: true,
    trafficSignals: true,
    pedestrians: true,
    corridor: true,
    flowArrows: true,
    conflictZone: true,
    sensorFootprints: true,
    queueHotspots: true,
    vehicleCallouts: true,
    roadMarkings: true,
    crosswalks: true,
    sidewalks: true,
    buildings: true,
    streetFurniture: true,
    trees: true,
  });

  const [camMetrics, setCamMetrics] = useState<CameraStateMetrics>({
    position: { x: 46, y: 50, z: 46 },
    target: { x: 0, y: 0, z: 0 },
    distance: 81,
    pitchDeg: 38,
    yawDeg: 45,
    projection: 'perspective',
    preset: 'iso',
    autoRotate: false,
  });

  useEffect(() => {
    if (!mountRef.current) return;

    const container = mountRef.current;
    const width = container.clientWidth || 800;
    const height = container.clientHeight || 500;

    // 1. Three.js Scene Setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a1128);

    // 2. WebGL Renderer
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: false,
        powerPreference: 'high-performance',
      });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      container.appendChild(renderer.domElement);
      setWebglInitialized(true);
    } catch (e) {
      console.error('WebGL initialization failed:', e);
      return;
    }

    // 3. Scene Environment (Lighting, Grids, Road Network, City Buildings, Mixed Traffic Fleet)
    const environment = new SceneEnvironment(scene);
    environmentRef.current = environment;

    // 4. Corridor Synchronization Bridge (SUMO to 3D sync & failover)
    const bridge = new CorridorSyncBridge(environment);
    bridgeRef.current = bridge;

    // 5. Scene Controller (Dual Cameras & OrbitControls)
    const controller = new SceneController(container, width, height);
    controllerRef.current = controller;

    // 5. Render Loop with Diagnostics
    let frameId: number;
    let lastTime = performance.now();
    let frameCount = 0;
    let metricsTicker = 0;

    const animate = () => {
      const startTime = performance.now();
      frameId = requestAnimationFrame(animate);

      // Measure FPS & Frame Count
      frameCount++;
      const now = performance.now();
      if (now - lastTime >= 1000) {
        setFps(Math.round((frameCount * 1000) / (now - lastTime)));
        frameCount = 0;
        lastTime = now;
      }

      // Update environment animation (vehicles, strobe lightbars, ambulance corridor motion)
      const waypointPos = environment.update(now);

      // Update corridor synchronization bridge (dead reckoning, watchdog fallback)
      bridge.update(now);

      // Update camera controller (interpolation, OrbitControls damping, chase cam)
      controller.update(waypointPos);

      // Render Active Camera View
      renderer.render(scene, controller.activeCamera);

      // Periodically sample telemetry diagnostics (every ~10 frames)
      metricsTicker++;
      if (metricsTicker % 10 === 0) {
        setRenderMs(parseFloat((performance.now() - startTime).toFixed(1)));
        setDrawCalls(renderer.info.render.calls);
        setTriangles(renderer.info.render.triangles);
        setCamMetrics(controller.getMetrics());
        setSyncTelemetry(bridge.getTelemetry());

        const sigSnap = environment.trafficSignals.controller.getSnapshotAtTime(now);
        setPhaseSnapshot({
          ew: sigSnap.eastWest.vehicularPhase,
          ns: sigSnap.northSouth.vehicularPhase,
          ewSec: sigSnap.eastWest.countdownSec,
          nsSec: sigSnap.northSouth.countdownSec,
        });
      }
    };

    animate();

    // 6. Window Resize Listener
    const handleResize = () => {
      if (!container) return;
      const newWidth = container.clientWidth;
      const newHeight = container.clientHeight;
      controller.handleResize(newWidth, newHeight);
      renderer.setSize(newWidth, newHeight);
    };

    window.addEventListener('resize', handleResize);

    // 7. Cleanup & Disposals
    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener('resize', handleResize);
      bridge.dispose();
      controller.dispose();
      environment.dispose();

      if (container && renderer.domElement) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  // Ingest live telemetry snapshots from WebSocket stream or props
  useEffect(() => {
    const snap = liveSnapshot || operations?.latestSnapshot;
    if (snap && bridgeRef.current) {
      bridgeRef.current.ingestSnapshot(snap);
      setSyncTelemetry(bridgeRef.current.getTelemetry());
    }
  }, [liveSnapshot, operations?.latestSnapshot]);

  // Click Raycaster for Vehicle & Signal Pole Inspection
  const handleCanvasClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!mountRef.current || !controllerRef.current || !environmentRef.current) return;

    const rect = mountRef.current.getBoundingClientRect();
    const mouse = new THREE.Vector2(
      ((e.clientX - rect.left) / rect.width) * 2 - 1,
      -((e.clientY - rect.top) / rect.height) * 2 + 1
    );

    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(mouse, controllerRef.current.activeCamera);

    // 1. Raycast Vehicles
    const vehicleIntersects = raycaster.intersectObjects(
      environmentRef.current.vehicleManager.group.children,
      true
    );
    const vehicleHit = environmentRef.current.vehicleManager.findVehicleByIntersection(vehicleIntersects);
    if (vehicleHit) {
      setSelectedVehicle(vehicleHit);
      setSelectedPole(null);
      if (onSelectEntity) {
        onSelectEntity(vehicleHit.id, vehicleHit.vehicle_class);
      }
      return;
    }

    // 2. Raycast Signal Poles
    const poleIntersects = raycaster.intersectObjects(
      environmentRef.current.trafficSignals.signalsGroup.children,
      true
    );
    const poleHit = environmentRef.current.trafficSignals.findSignalPoleByIntersection(poleIntersects, performance.now());
    if (poleHit) {
      setSelectedPole(poleHit);
      setSelectedVehicle(null);
      setSelectedCorridor(null);
      if (onSelectEntity) {
        onSelectEntity(poleHit.poleId, 'TRAFFIC_SIGNAL_POLE');
      }
      return;
    }

    // 3. Raycast Emergency Corridor Ribbon
    const corridorIntersects = raycaster.intersectObjects(
      environmentRef.current.corridorOverlay.group.children,
      true
    );
    const corridorHit = corridorIntersects.find((h) => h.object.userData?.isCorridor);
    if (corridorHit) {
      const plan = environmentRef.current.corridorOverlay.getCorridorTelemetry(performance.now());
      setSelectedCorridor(plan);
      setSelectedVehicle(null);
      setSelectedPole(null);
      if (onSelectEntity) {
        onSelectEntity(plan.corridorId, 'EMERGENCY_CORRIDOR');
      }
      return;
    }

    setSelectedVehicle(null);
    setSelectedPole(null);
    setSelectedCorridor(null);
  };

  // UI Handlers for Preset and Projection switching
  const handleSelectPreset = (preset: CameraPresetType) => {
    setCameraPreset(preset);
    if (controllerRef.current) {
      controllerRef.current.setPreset(preset);
    }
  };

  const handleToggleProjection = () => {
    const nextMode: ProjectionMode = projectionMode === 'perspective' ? 'orthographic' : 'perspective';
    setProjectionMode(nextMode);
    if (controllerRef.current && mountRef.current) {
      controllerRef.current.setProjectionMode(
        nextMode,
        mountRef.current.clientWidth,
        mountRef.current.clientHeight
      );
    }
  };

  const handleToggleAutoRotate = () => {
    const nextState = !autoRotate;
    setAutoRotate(nextState);
    if (controllerRef.current) {
      controllerRef.current.autoRotate = nextState;
    }
  };

  const handleResetCamera = () => {
    handleSelectPreset('iso');
  };

  const handleToggleCorridorMode = () => {
    const nextState = !corridorMode;
    setCorridorMode(nextState);
    if (environmentRef.current) {
      environmentRef.current.setCorridorMode(nextState);
    }
  };

  const handleToggleLayer = (layerKey: keyof typeof layers) => {
    const nextState = !layers[layerKey];
    setLayers((prev) => ({ ...prev, [layerKey]: nextState }));
    if (environmentRef.current) {
      if (layerKey === 'vehicles') {
        environmentRef.current.vehicleManager.setVehiclesVisibility(nextState);
      } else if (layerKey === 'vehicleBadges') {
        environmentRef.current.vehicleManager.setShowBadges(nextState);
      } else if (layerKey === 'trafficSignals') {
        environmentRef.current.trafficSignals.setSignalsVisibility(nextState);
        environmentRef.current.multiSignals.setSignalsVisibility(nextState);
      } else if (layerKey === 'pedestrians') {
        environmentRef.current.trafficSignals.setPedestriansVisibility(nextState);
      } else if (layerKey === 'corridor') {
        environmentRef.current.corridorOverlay.setVisibility(nextState);
      } else if (layerKey === 'flowArrows') {
        environmentRef.current.flowArrows.setFlowArrowsVisibility(nextState);
      } else if (layerKey === 'conflictZone') {
        environmentRef.current.flowArrows.setConflictZoneVisibility(nextState);
      } else if (layerKey === 'sensorFootprints') {
        environmentRef.current.flowArrows.setSensorFootprintsVisibility(nextState);
      } else if (layerKey === 'queueHotspots') {
        environmentRef.current.flowArrows.setQueueHotspotsVisibility(nextState);
      } else if (layerKey === 'vehicleCallouts') {
        environmentRef.current.corridorOverlay.setShowCallouts(nextState);
      } else if (layerKey === 'roadMarkings') {
        environmentRef.current.roadNetwork.setMarkingsVisibility(nextState);
        environmentRef.current.corridorRoadNetwork.setMarkingsVisibility(nextState);
      } else if (layerKey === 'crosswalks') {
        environmentRef.current.roadNetwork.setCrosswalksVisibility(nextState);
        environmentRef.current.corridorRoadNetwork.setCrosswalksVisibility(nextState);
      } else if (layerKey === 'sidewalks') {
        environmentRef.current.roadNetwork.setSidewalksVisibility(nextState);
        environmentRef.current.corridorRoadNetwork.setSidewalksVisibility(nextState);
      } else if (layerKey === 'buildings') {
        environmentRef.current.cityEnvironment.setBuildingsVisibility(nextState);
        environmentRef.current.corridorCity.setBuildingsVisibility(nextState);
      } else if (layerKey === 'streetFurniture') {
        environmentRef.current.cityEnvironment.setStreetFurnitureVisibility(nextState);
        environmentRef.current.corridorCity.setStreetFurnitureVisibility(nextState);
      } else if (layerKey === 'trees') {
        environmentRef.current.cityEnvironment.setTreesVisibility(nextState);
        environmentRef.current.corridorCity.setTreesVisibility(nextState);
      }
    }
  };

  return (
    <div
      onClick={handleCanvasClick}
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        minHeight: '440px',
        backgroundColor: '#0a1128',
        overflow: 'hidden',
        borderRadius: '8px',
        border: '1px solid #1b2f5b',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.45)',
        cursor: 'default',
        ...style,
      }}
    >
      {/* Three.js Canvas DOM Container */}
      <div ref={mountRef} style={{ width: '100%', height: '100%' }} />

      {/* Floating HUD Layer - pointer-events: none so user can orbit/pan canvas smoothly */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: '10px 12px',
        }}
      >
        {/* Top Floating HUD Bar: Info on Left, Interactive Controls on Right */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          {/* Top-Left: Viewport Title & Diagnostics */}
          <div
            style={{
              backgroundColor: 'rgba(10, 17, 40, 0.88)',
              backdropFilter: 'blur(8px)',
              border: '1px solid #1b325f',
              padding: '8px 12px',
              borderRadius: '6px',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
              pointerEvents: 'auto',
              boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Box size={14} color="#00e5ff" />
              <span style={{ fontSize: '0.78rem', fontWeight: 800, color: '#f1f5f9', letterSpacing: '0.04em' }}>
                3D DIGITAL TWIN VIEWPORT
              </span>
              <StatusPill label="CORRIDOR & HUD ACTIVE" variant="cyan" size="xs" pulse />
              <button
                onClick={() => {
                  if (bridgeRef.current) {
                    bridgeRef.current.toggleSyncMode();
                    setSyncTelemetry(bridgeRef.current.getTelemetry());
                  }
                }}
                title="Toggle Real-Time SUMO Telemetry Sync vs Deterministic Fixture"
                style={{
                  backgroundColor: syncTelemetry.mode === 'LIVE_SUMO' ? 'rgba(0, 245, 212, 0.15)' : 'rgba(255, 209, 102, 0.15)',
                  border: `1px solid ${syncTelemetry.mode === 'LIVE_SUMO' ? '#00f5d4' : '#ffd166'}`,
                  color: syncTelemetry.mode === 'LIVE_SUMO' ? '#00f5d4' : '#ffd166',
                  borderRadius: '12px',
                  padding: '2px 8px',
                  fontSize: '0.62rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                <Radio size={10} color={syncTelemetry.mode === 'LIVE_SUMO' ? '#00f5d4' : '#ffd166'} />
                <span>
                  {syncTelemetry.mode === 'LIVE_SUMO' ? `SUMO LIVE (${syncTelemetry.activeVehiclesCount} veh)` : 'FIXTURE'}
                </span>
                <span style={{ fontSize: '0.58rem', opacity: 0.8 }}>
                  [{syncTelemetry.status}]
                </span>
              </button>
              {syncTelemetry.preemptionActive && (
                <StatusPill label="PREEMPTION ACTIVE" variant="amber" size="xs" pulse />
              )}
            </div>

            <div style={{ fontSize: '0.70rem', color: '#94a3b8' }}>
              Intersection:{' '}
              <span style={{ color: '#00e5ff', fontFamily: 'monospace', fontWeight: 600 }}>
                {intersectionId}
              </span>{' '}
              (Oak St. & 5th Ave — Mixed Traffic & Priority EV)
            </div>

            <div style={{ fontSize: '0.66rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ color: '#06d6a0' }}>● Three.js WebGL</span>
              <span>|</span>
              <span style={{ color: '#06d6a0', fontFamily: 'monospace', fontWeight: 600 }}>{fps} FPS</span>
              <span>|</span>
              <span>{renderMs}ms</span>
              <span>|</span>
              <span>{drawCalls} calls</span>
              <span>|</span>
              <span>{triangles} tris</span>
            </div>

            {/* Realtime Signal Phase Mini Badge */}
            <div
              style={{
                marginTop: '2px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '0.64rem',
                backgroundColor: 'rgba(15, 23, 42, 0.7)',
                padding: '2px 8px',
                borderRadius: '4px',
                border: '1px solid #1b2f5b',
              }}
            >
              <span style={{ color: '#94a3b8' }}>Signal Phase:</span>
              <span style={{ color: phaseSnapshot.ew === 'green' ? '#06d6a0' : phaseSnapshot.ew === 'yellow' ? '#ffd166' : '#ef4444', fontWeight: 600 }}>
                5th Ave (EW): {phaseSnapshot.ew.toUpperCase()} {phaseSnapshot.ewSec}s
              </span>
              <span style={{ color: '#334155' }}>|</span>
              <span style={{ color: phaseSnapshot.ns === 'green' ? '#06d6a0' : phaseSnapshot.ns === 'yellow' ? '#ffd166' : '#ef4444', fontWeight: 600 }}>
                Oak St (NS): {phaseSnapshot.ns.toUpperCase()} {phaseSnapshot.nsSec}s
              </span>
            </div>

            {/* Selected Vehicle Inspector Card */}
            {selectedVehicle && (
              <div
                style={{
                  marginTop: '6px',
                  backgroundColor: 'rgba(10, 25, 47, 0.95)',
                  border: '1px solid #00e5ff',
                  borderRadius: '6px',
                  padding: '6px 10px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                  fontSize: '0.68rem',
                  color: '#e2e8f0',
                  boxShadow: '0 4px 16px rgba(0, 229, 255, 0.25)',
                  minWidth: '220px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Car size={13} color="#00e5ff" />
                    <span style={{ color: '#94a3b8', fontSize: '0.62rem' }}>Inspector:</span>
                    <span style={{ fontWeight: 800, color: '#00e5ff', fontFamily: 'monospace' }}>
                      {selectedVehicle.id}
                    </span>
                    <span style={{ fontSize: '0.62rem', color: '#94a3b8' }}>
                      [{selectedVehicle.vehicle_class}]
                    </span>
                  </div>
                  <button
                    onClick={() => setSelectedVehicle(null)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#64748b',
                      cursor: 'pointer',
                      padding: 0,
                    }}
                  >
                    <X size={12} />
                  </button>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '0.64rem' }}>
                  <div>
                    <span style={{ color: '#64748b' }}>Speed: </span>
                    <span style={{ color: '#06d6a0', fontWeight: 700, fontFamily: 'monospace' }}>
                      {selectedVehicle.speed_kmh} km/h
                    </span>
                    <span style={{ color: '#64748b', fontSize: '0.60rem' }}>
                      {' '}({selectedVehicle.speed_ms.toFixed(1)} m/s)
                    </span>
                  </div>
                  <div>
                    <span style={{ color: '#64748b' }}>Lane: </span>
                    <span style={{ color: '#f1f5f9', fontFamily: 'monospace' }}>
                      {selectedVehicle.current_lane_id}
                    </span>
                  </div>
                  <div>
                    <span style={{ color: '#64748b' }}>Heading: </span>
                    <span style={{ color: '#f1f5f9', fontFamily: 'monospace' }}>
                      {Math.round(selectedVehicle.heading)}°
                    </span>
                  </div>
                  <div>
                    <span style={{ color: '#64748b' }}>Status: </span>
                    <span
                      style={{
                        color:
                          selectedVehicle.status === 'STALE'
                            ? '#ef4444'
                            : selectedVehicle.status === 'PRIORITY_CORRIDOR'
                            ? '#00e5ff'
                            : selectedVehicle.status === 'WAITING_SIGNAL'
                            ? '#ffd166'
                            : '#06d6a0',
                        fontWeight: 600,
                      }}
                    >
                      {selectedVehicle.status}
                    </span>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px', borderTop: '1px solid #1e293b', paddingTop: '4px' }}>
                  <span style={{ fontSize: '0.60rem', color: '#64748b' }}>
                    Src: <span style={{ color: '#38bdf8' }}>{selectedVehicle.provenance}</span>
                  </span>
                  <button
                    onClick={() => {
                      handleSelectPreset('chase');
                    }}
                    style={{
                      backgroundColor: 'rgba(0, 229, 255, 0.15)',
                      border: '1px solid rgba(0, 229, 255, 0.4)',
                      borderRadius: '3px',
                      color: '#00e5ff',
                      fontSize: '0.62rem',
                      fontWeight: 600,
                      padding: '2px 6px',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                    }}
                  >
                    <Crosshair size={10} />
                    <span>Follow Cam</span>
                  </button>
                </div>
              </div>
            )}

            {/* Selected Signal Pole Inspector Card */}
            {selectedPole && (
              <div
                style={{
                  marginTop: '6px',
                  backgroundColor: 'rgba(10, 25, 47, 0.95)',
                  border: '1px solid #ffd166',
                  borderRadius: '6px',
                  padding: '6px 10px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '4px',
                  fontSize: '0.68rem',
                  color: '#e2e8f0',
                  boxShadow: '0 4px 16px rgba(255, 209, 102, 0.25)',
                  minWidth: '220px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <ShieldCheck size={13} color="#ffd166" />
                    <span style={{ color: '#94a3b8', fontSize: '0.62rem' }}>Signal Pole:</span>
                    <span style={{ fontWeight: 800, color: '#ffd166', fontFamily: 'monospace' }}>
                      {selectedPole.poleId}
                    </span>
                  </div>
                  <button
                    onClick={() => setSelectedPole(null)}
                    style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', padding: 0 }}
                  >
                    <X size={12} />
                  </button>
                </div>

                <div style={{ fontSize: '0.64rem', color: '#94a3b8' }}>
                  Approach: <span style={{ color: '#00e5ff' }}>{selectedPole.approachName}</span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '0.64rem' }}>
                  <div>
                    <span style={{ color: '#64748b' }}>Vehicular: </span>
                    <span
                      style={{
                        color:
                          selectedPole.vehicularPhase === 'green'
                            ? '#06d6a0'
                            : selectedPole.vehicularPhase === 'yellow'
                            ? '#ffd166'
                            : '#ef4444',
                        fontWeight: 700,
                        textTransform: 'uppercase',
                      }}
                    >
                      ● {selectedPole.vehicularPhase} ({selectedPole.countdownSec}s)
                    </span>
                  </div>
                  <div>
                    <span style={{ color: '#64748b' }}>Crosswalk: </span>
                    <span
                      style={{
                        color: selectedPole.pedestrianPhase === 'WALK' ? '#06d6a0' : '#ef4444',
                        fontWeight: 600,
                      }}
                    >
                      {selectedPole.pedestrianPhase}
                    </span>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px', borderTop: '1px solid #1e293b', paddingTop: '4px' }}>
                  <span style={{ fontSize: '0.60rem', color: '#06d6a0' }}>
                    ✓ {selectedPole.conflictFreeStatus}
                  </span>
                  <span style={{ fontSize: '0.60rem', color: '#64748b' }}>
                    Src: <span style={{ color: '#38bdf8' }}>{selectedPole.provenance}</span>
                  </span>
                </div>
              </div>
            )}

            {/* Selected Emergency Corridor Inspector Card */}
            {selectedCorridor && (
              <div
                style={{
                  marginTop: '6px',
                  backgroundColor: 'rgba(7, 16, 38, 0.96)',
                  border: '1px solid #00f5d4',
                  borderRadius: '6px',
                  padding: '8px 10px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '5px',
                  fontSize: '0.68rem',
                  color: '#e2e8f0',
                  boxShadow: '0 4px 18px rgba(0, 245, 212, 0.3)',
                  minWidth: '260px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Flame size={13} color="#00f5d4" />
                    <span style={{ color: '#94a3b8', fontSize: '0.62rem' }}>Corridor:</span>
                    <span style={{ fontWeight: 800, color: '#00f5d4', fontFamily: 'monospace' }}>
                      {selectedCorridor.corridorId}
                    </span>
                    <span
                      style={{
                        fontSize: '0.60rem',
                        fontWeight: 700,
                        padding: '1px 4px',
                        borderRadius: '3px',
                        backgroundColor:
                          selectedCorridor.mode === 'BLOCKED'
                            ? 'rgba(239, 68, 68, 0.2)'
                            : 'rgba(0, 245, 212, 0.2)',
                        color: selectedCorridor.mode === 'BLOCKED' ? '#ef4444' : '#00f5d4',
                      }}
                    >
                      {selectedCorridor.mode}
                    </span>
                  </div>
                  <button
                    onClick={() => setSelectedCorridor(null)}
                    style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', padding: 0 }}
                  >
                    <X size={12} />
                  </button>
                </div>

                <div style={{ fontSize: '0.62rem', color: '#94a3b8' }}>
                  Target: <strong style={{ color: '#f1f5f9' }}>{selectedCorridor.targetVehicleId}</strong> ({selectedCorridor.missionId})
                </div>

                <div style={{ fontSize: '0.60rem', color: '#cbd5e1', lineHeight: '1.2' }}>
                  {selectedCorridor.reason}
                </div>

                {/* Node Progression Chain A–D */}
                <div style={{ borderTop: '1px solid #1e293b', paddingTop: '4px', marginTop: '2px' }}>
                  <div style={{ fontSize: '0.62rem', color: '#64748b', fontWeight: 600, marginBottom: '2px' }}>
                    Corridor Intersections (A–D Chain):
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    {selectedCorridor.nodes.map((node) => (
                      <div
                        key={node.id}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          fontSize: '0.60rem',
                          padding: '1px 4px',
                          borderRadius: '2px',
                          backgroundColor:
                            node.status === 'ACTIVE'
                              ? 'rgba(0, 245, 212, 0.15)'
                              : node.status === 'COMPLETED'
                              ? 'rgba(16, 185, 129, 0.1)'
                              : 'rgba(30, 41, 59, 0.4)',
                        }}
                      >
                        <span style={{ color: node.status === 'ACTIVE' ? '#00f5d4' : '#94a3b8' }}>
                          {node.name}
                        </span>
                        <span style={{ color: node.status === 'ACTIVE' ? '#06d6a0' : '#64748b', fontWeight: 600 }}>
                          {node.phaseWindow}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px', borderTop: '1px solid #1e293b', paddingTop: '4px' }}>
                  <span style={{ fontSize: '0.60rem', color: '#64748b' }}>
                    Lead: <strong style={{ color: '#f1f5f9' }}>{selectedCorridor.clearanceDistanceM}m</strong> ({selectedCorridor.preemptionLeadSec}s)
                  </span>
                  <span style={{ fontSize: '0.60rem', color: '#38bdf8' }}>
                    {selectedCorridor.provenance}
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Top-Right: Camera Presets & Interaction Controls */}
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'flex-end',
              gap: '6px',
              pointerEvents: 'auto',
            }}
          >
            {/* Camera Presets Bar */}
            <div
              style={{
                backgroundColor: 'rgba(10, 17, 40, 0.88)',
                backdropFilter: 'blur(8px)',
                border: '1px solid #1b2f5b',
                borderRadius: '6px',
                padding: '3px',
                display: 'flex',
                gap: '3px',
              }}
            >
              <button
                onClick={() => handleSelectPreset('iso')}
                title="Isometric Perspective View (45° Yaw, 38° Pitch)"
                style={{
                  backgroundColor: cameraPreset === 'iso' ? 'rgba(0, 229, 255, 0.2)' : 'transparent',
                  border: cameraPreset === 'iso' ? '1px solid #00e5ff' : '1px solid transparent',
                  color: cameraPreset === 'iso' ? '#00e5ff' : '#94a3b8',
                  borderRadius: '4px',
                  padding: '3px 8px',
                  fontSize: '0.68rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                ISO
              </button>

              <button
                onClick={() => handleSelectPreset('top')}
                title="Top-Down Ortho View (90° Zenith)"
                style={{
                  backgroundColor: cameraPreset === 'top' ? 'rgba(0, 229, 255, 0.2)' : 'transparent',
                  border: cameraPreset === 'top' ? '1px solid #00e5ff' : '1px solid transparent',
                  color: cameraPreset === 'top' ? '#00e5ff' : '#94a3b8',
                  borderRadius: '4px',
                  padding: '3px 8px',
                  fontSize: '0.68rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                TOP
              </button>

              <button
                onClick={() => handleSelectPreset('close')}
                title="Intersection Conflict Close-up View"
                style={{
                  backgroundColor: cameraPreset === 'close' ? 'rgba(0, 229, 255, 0.2)' : 'transparent',
                  border: cameraPreset === 'close' ? '1px solid #00e5ff' : '1px solid transparent',
                  color: cameraPreset === 'close' ? '#00e5ff' : '#94a3b8',
                  borderRadius: '4px',
                  padding: '3px 8px',
                  fontSize: '0.68rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                CLOSE
              </button>

              <button
                onClick={() => handleSelectPreset('chase')}
                title="Emergency Ambulance Follow Cam (AMB-339)"
                style={{
                  backgroundColor: cameraPreset === 'chase' ? 'rgba(239, 71, 111, 0.2)' : 'transparent',
                  border: cameraPreset === 'chase' ? '1px solid #ef476f' : '1px solid transparent',
                  color: cameraPreset === 'chase' ? '#ef476f' : '#94a3b8',
                  borderRadius: '4px',
                  padding: '3px 8px',
                  fontSize: '0.68rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '3px',
                }}
              >
                <Video size={10} /> CHASE
              </button>
            </div>

            {/* Corridor Node Jump Presets Bar */}
            <div
              style={{
                backgroundColor: 'rgba(10, 17, 40, 0.88)',
                backdropFilter: 'blur(8px)',
                border: '1px solid #1b2f5b',
                borderRadius: '6px',
                padding: '3px',
                display: 'flex',
                gap: '3px',
              }}
            >
              <button
                onClick={() => handleSelectPreset('corridor')}
                title="Corridor 1,000m Overview (5th Ave)"
                style={{
                  backgroundColor: cameraPreset === 'corridor' ? 'rgba(0, 245, 212, 0.2)' : 'transparent',
                  border: cameraPreset === 'corridor' ? '1px solid #00f5d4' : '1px solid transparent',
                  color: cameraPreset === 'corridor' ? '#00f5d4' : '#94a3b8',
                  borderRadius: '4px',
                  padding: '3px 7px',
                  fontSize: '0.66rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                }}
              >
                CORRIDOR
              </button>
              <button
                onClick={() => handleSelectPreset('nodeA')}
                title="Node A (Maple St, 0m)"
                style={{
                  backgroundColor: cameraPreset === 'nodeA' ? 'rgba(0, 229, 255, 0.2)' : 'transparent',
                  border: cameraPreset === 'nodeA' ? '1px solid #00e5ff' : '1px solid transparent',
                  color: cameraPreset === 'nodeA' ? '#00e5ff' : '#94a3b8',
                  borderRadius: '4px',
                  padding: '3px 6px',
                  fontSize: '0.64rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                NODE A
              </button>
              <button
                onClick={() => handleSelectPreset('nodeB')}
                title="Node B (Oak St / INT-0457, 250m)"
                style={{
                  backgroundColor: cameraPreset === 'nodeB' ? 'rgba(0, 229, 255, 0.2)' : 'transparent',
                  border: cameraPreset === 'nodeB' ? '1px solid #00e5ff' : '1px solid transparent',
                  color: cameraPreset === 'nodeB' ? '#00e5ff' : '#94a3b8',
                  borderRadius: '4px',
                  padding: '3px 6px',
                  fontSize: '0.64rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                NODE B
              </button>
              <button
                onClick={() => handleSelectPreset('nodeC')}
                title="Node C (Pine St, 500m)"
                style={{
                  backgroundColor: cameraPreset === 'nodeC' ? 'rgba(0, 229, 255, 0.2)' : 'transparent',
                  border: cameraPreset === 'nodeC' ? '1px solid #00e5ff' : '1px solid transparent',
                  color: cameraPreset === 'nodeC' ? '#00e5ff' : '#94a3b8',
                  borderRadius: '4px',
                  padding: '3px 6px',
                  fontSize: '0.64rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                NODE C
              </button>
              <button
                onClick={() => handleSelectPreset('nodeD')}
                title="Node D (Elm St, 750m)"
                style={{
                  backgroundColor: cameraPreset === 'nodeD' ? 'rgba(0, 229, 255, 0.2)' : 'transparent',
                  border: cameraPreset === 'nodeD' ? '1px solid #00e5ff' : '1px solid transparent',
                  color: cameraPreset === 'nodeD' ? '#00e5ff' : '#94a3b8',
                  borderRadius: '4px',
                  padding: '3px 6px',
                  fontSize: '0.64rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                NODE D
              </button>
              <button
                onClick={() => handleSelectPreset('hospital')}
                title="Trauma Center Hospital (850m)"
                style={{
                  backgroundColor: cameraPreset === 'hospital' ? 'rgba(239, 71, 111, 0.2)' : 'transparent',
                  border: cameraPreset === 'hospital' ? '1px solid #ef476f' : '1px solid transparent',
                  color: cameraPreset === 'hospital' ? '#ef476f' : '#94a3b8',
                  borderRadius: '4px',
                  padding: '3px 6px',
                  fontSize: '0.64rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                TRAUMA CTR
              </button>
            </div>

            {/* Projection & Controls Secondary Row */}
            <div style={{ display: 'flex', gap: '4px' }}>
              {/* SUMO Live Sync Switcher */}
              <button
                onClick={() => {
                  if (bridgeRef.current) {
                    bridgeRef.current.toggleSyncMode();
                    setSyncTelemetry(bridgeRef.current.getTelemetry());
                  }
                }}
                title="Toggle Real-Time SUMO Telemetry Sync vs Local Fixture"
                style={{
                  backgroundColor: syncTelemetry.mode === 'LIVE_SUMO' ? 'rgba(0, 245, 212, 0.15)' : 'rgba(10, 17, 40, 0.88)',
                  backdropFilter: 'blur(8px)',
                  border: `1px solid ${syncTelemetry.mode === 'LIVE_SUMO' ? '#00f5d4' : '#1b2f5b'}`,
                  color: syncTelemetry.mode === 'LIVE_SUMO' ? '#00f5d4' : '#94a3b8',
                  borderRadius: '5px',
                  padding: '3px 8px',
                  fontSize: '0.65rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                <Radio size={10} />
                <span>SYNC: {syncTelemetry.mode === 'LIVE_SUMO' ? 'SUMO' : 'FIXTURE'}</span>
              </button>

              {/* Corridor Mode Switcher */}
              <button
                onClick={handleToggleCorridorMode}
                title="Toggle 1,000m Arterial Corridor World vs Single Intersection"
                style={{
                  backgroundColor: corridorMode ? 'rgba(0, 245, 212, 0.15)' : 'rgba(10, 17, 40, 0.88)',
                  backdropFilter: 'blur(8px)',
                  border: `1px solid ${corridorMode ? '#00f5d4' : '#1b2f5b'}`,
                  color: corridorMode ? '#00f5d4' : '#94a3b8',
                  borderRadius: '5px',
                  padding: '3px 8px',
                  fontSize: '0.65rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                CORRIDOR: {corridorMode ? '4-NODE' : 'SINGLE'}
              </button>

              {/* Projection Mode Switcher */}
              <button
                onClick={handleToggleProjection}
                title="Toggle Perspective vs Orthographic Projection"
                style={{
                  backgroundColor: 'rgba(10, 17, 40, 0.88)',
                  backdropFilter: 'blur(8px)',
                  border: '1px solid #1b2f5b',
                  color: projectionMode === 'orthographic' ? '#00f5d4' : '#94a3b8',
                  borderRadius: '5px',
                  padding: '3px 8px',
                  fontSize: '0.65rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                <Eye size={11} />
                <span>{projectionMode === 'perspective' ? 'PERSP' : 'ORTHO'}</span>
              </button>

              {/* Turntable Auto-Rotate Button */}
              <button
                onClick={handleToggleAutoRotate}
                title="Toggle Turntable Auto-Rotation"
                style={{
                  backgroundColor: autoRotate ? 'rgba(6, 214, 160, 0.15)' : 'rgba(10, 17, 40, 0.88)',
                  backdropFilter: 'blur(8px)',
                  border: `1px solid ${autoRotate ? 'rgba(6, 214, 160, 0.4)' : '#1b2f5b'}`,
                  color: autoRotate ? '#06d6a0' : '#94a3b8',
                  borderRadius: '5px',
                  padding: '3px 8px',
                  fontSize: '0.65rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                AUTO-ROT: {autoRotate ? 'ON' : 'OFF'}
              </button>

              {/* Layers Dropdown Toggle */}
              <button
                onClick={() => setShowLayersMenu(!showLayersMenu)}
                title="Toggle 3D Scene Layer Visibility"
                style={{
                  backgroundColor: showLayersMenu ? 'rgba(0, 229, 255, 0.2)' : 'rgba(10, 17, 40, 0.88)',
                  backdropFilter: 'blur(8px)',
                  border: '1px solid #1b2f5b',
                  color: showLayersMenu ? '#00e5ff' : '#94a3b8',
                  borderRadius: '5px',
                  padding: '3px 8px',
                  fontSize: '0.65rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '3px',
                }}
              >
                <Layers size={11} /> LAYERS
              </button>

              {/* Reset Camera Button */}
              <button
                onClick={handleResetCamera}
                title="Reset Camera to Default Isometric View"
                style={{
                  backgroundColor: 'rgba(10, 17, 40, 0.88)',
                  backdropFilter: 'blur(8px)',
                  border: '1px solid #1b2f5b',
                  color: '#94a3b8',
                  borderRadius: '5px',
                  padding: '3px 6px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                <RotateCcw size={12} />
              </button>
            </div>

            {/* Layer Visibility Menu Drawer */}
            {showLayersMenu && (
              <div
                style={{
                  backgroundColor: 'rgba(11, 21, 45, 0.95)',
                  backdropFilter: 'blur(10px)',
                  border: '1px solid #1b325f',
                  borderRadius: '6px',
                  padding: '8px 10px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                  fontSize: '0.66rem',
                  boxShadow: '0 4px 16px rgba(0,0,0,0.5)',
                  minWidth: '160px',
                }}
              >
                <div style={{ color: '#94a3b8', fontWeight: 600, borderBottom: '1px solid #1b2f5b', paddingBottom: '3px' }}>
                  Scene Layers
                </div>

                <label
                  onClick={() => handleToggleLayer('vehicles')}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: layers.vehicles ? '#00e5ff' : '#64748b' }}
                >
                  <div style={{ width: '12px', height: '12px', border: '1px solid #1b2f5b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {layers.vehicles && <Check size={10} color="#00e5ff" />}
                  </div>
                  <span>3D Vehicle Fleet</span>
                </label>

                <label
                  onClick={() => handleToggleLayer('vehicleBadges')}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: layers.vehicleBadges ? '#00e5ff' : '#64748b' }}
                >
                  <div style={{ width: '12px', height: '12px', border: '1px solid #1b2f5b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {layers.vehicleBadges && <Check size={10} color="#00e5ff" />}
                  </div>
                  <span>Vehicle Badges / Speeds</span>
                </label>

                <label
                  onClick={() => handleToggleLayer('trafficSignals')}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: layers.trafficSignals ? '#00e5ff' : '#64748b' }}
                >
                  <div style={{ width: '12px', height: '12px', border: '1px solid #1b2f5b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {layers.trafficSignals && <Check size={10} color="#00e5ff" />}
                  </div>
                  <span>Traffic Signal Poles</span>
                </label>

                <label
                  onClick={() => handleToggleLayer('pedestrians')}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: layers.pedestrians ? '#00e5ff' : '#64748b' }}
                >
                  <div style={{ width: '12px', height: '12px', border: '1px solid #1b2f5b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {layers.pedestrians && <Check size={10} color="#00e5ff" />}
                  </div>
                  <span>Pedestrians Crossing</span>
                </label>

                <label
                  onClick={() => handleToggleLayer('corridor')}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: layers.corridor ? '#00e5ff' : '#64748b' }}
                >
                  <div style={{ width: '12px', height: '12px', border: '1px solid #1b2f5b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {layers.corridor && <Check size={10} color="#00e5ff" />}
                  </div>
                  <span>Emergency Corridor Ribbon</span>
                </label>

                <label
                  onClick={() => handleToggleLayer('flowArrows')}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: layers.flowArrows ? '#00e5ff' : '#64748b' }}
                >
                  <div style={{ width: '12px', height: '12px', border: '1px solid #1b2f5b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {layers.flowArrows && <Check size={10} color="#00e5ff" />}
                  </div>
                  <span>Traffic Flow Arrows</span>
                </label>

                <label
                  onClick={() => handleToggleLayer('conflictZone')}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: layers.conflictZone ? '#00e5ff' : '#64748b' }}
                >
                  <div style={{ width: '12px', height: '12px', border: '1px solid #1b2f5b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {layers.conflictZone && <Check size={10} color="#00e5ff" />}
                  </div>
                  <span>Conflict Zone Box</span>
                </label>

                <label
                  onClick={() => handleToggleLayer('sensorFootprints')}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: layers.sensorFootprints ? '#00e5ff' : '#64748b' }}
                >
                  <div style={{ width: '12px', height: '12px', border: '1px solid #1b2f5b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {layers.sensorFootprints && <Check size={10} color="#00e5ff" />}
                  </div>
                  <span>Sensor Footprints (RSU)</span>
                </label>

                <label
                  onClick={() => handleToggleLayer('queueHotspots')}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: layers.queueHotspots ? '#00e5ff' : '#64748b' }}
                >
                  <div style={{ width: '12px', height: '12px', border: '1px solid #1b2f5b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {layers.queueHotspots && <Check size={10} color="#00e5ff" />}
                  </div>
                  <span>Queue Hotspots</span>
                </label>

                <label
                  onClick={() => handleToggleLayer('vehicleCallouts')}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: layers.vehicleCallouts ? '#00e5ff' : '#64748b' }}
                >
                  <div style={{ width: '12px', height: '12px', border: '1px solid #1b2f5b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {layers.vehicleCallouts && <Check size={10} color="#00e5ff" />}
                  </div>
                  <span>Vehicle 3D Callouts</span>
                </label>

                <label
                  onClick={() => handleToggleLayer('buildings')}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: layers.buildings ? '#00e5ff' : '#64748b' }}
                >
                  <div style={{ width: '12px', height: '12px', border: '1px solid #1b2f5b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {layers.buildings && <Check size={10} color="#00e5ff" />}
                  </div>
                  <span>Buildings & Hospital</span>
                </label>

                <label
                  onClick={() => handleToggleLayer('streetFurniture')}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: layers.streetFurniture ? '#00e5ff' : '#64748b' }}
                >
                  <div style={{ width: '12px', height: '12px', border: '1px solid #1b2f5b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {layers.streetFurniture && <Check size={10} color="#00e5ff" />}
                  </div>
                  <span>Streetlights & RSUs</span>
                </label>

                <label
                  onClick={() => handleToggleLayer('trees')}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: layers.trees ? '#00e5ff' : '#64748b' }}
                >
                  <div style={{ width: '12px', height: '12px', border: '1px solid #1b2f5b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {layers.trees && <Check size={10} color="#00e5ff" />}
                  </div>
                  <span>Urban Trees</span>
                </label>

                <div style={{ height: '1px', backgroundColor: '#1b2f5b', margin: '2px 0' }} />

                <label
                  onClick={() => handleToggleLayer('roadMarkings')}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: layers.roadMarkings ? '#00e5ff' : '#64748b' }}
                >
                  <div style={{ width: '12px', height: '12px', border: '1px solid #1b2f5b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {layers.roadMarkings && <Check size={10} color="#00e5ff" />}
                  </div>
                  <span>Lanes & Markings</span>
                </label>

                <label
                  onClick={() => handleToggleLayer('crosswalks')}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: layers.crosswalks ? '#00e5ff' : '#64748b' }}
                >
                  <div style={{ width: '12px', height: '12px', border: '1px solid #1b2f5b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {layers.crosswalks && <Check size={10} color="#00e5ff" />}
                  </div>
                  <span>Zebra Crosswalks</span>
                </label>

                <label
                  onClick={() => handleToggleLayer('sidewalks')}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer', color: layers.sidewalks ? '#00e5ff' : '#64748b' }}
                >
                  <div style={{ width: '12px', height: '12px', border: '1px solid #1b2f5b', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {layers.sidewalks && <Check size={10} color="#00e5ff" />}
                  </div>
                  <span>Corner Sidewalks</span>
                </label>
              </div>
            )}

            {/* Camera Coordinates Overlay */}
            {showMetrics && (
              <div
                style={{
                  backgroundColor: 'rgba(10, 17, 40, 0.85)',
                  border: '1px solid #162547',
                  borderRadius: '4px',
                  padding: '2px 8px',
                  fontSize: '0.62rem',
                  color: '#64748b',
                  fontFamily: 'monospace',
                }}
              >
                Pos: ({camMetrics.position.x}, {camMetrics.position.y}, {camMetrics.position.z}) | Pitch: {camMetrics.pitchDeg}° | Yaw: {camMetrics.yawDeg}° | Dist: {camMetrics.distance}m
              </div>
            )}
          </div>
        </div>

        {/* Center Floating Callout: Priority Vehicle Dynamic Tracking */}
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <div
            style={{
              backgroundColor: 'rgba(11, 21, 45, 0.92)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(0, 229, 255, 0.4)',
              borderRadius: '24px',
              padding: '6px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              pointerEvents: 'auto',
              boxShadow: '0 4px 20px rgba(0, 229, 255, 0.25)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span className="live-pulse-red" style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#ef476f' }} />
              <Flame size={14} color="#ef476f" />
              <span style={{ fontSize: '0.75rem', fontWeight: 800, color: '#f8fafc' }}>
                AMB-339
              </span>
              <span style={{ fontSize: '0.68rem', color: '#94a3b8' }}>(Ambulance)</span>
            </div>
            <div style={{ width: '1px', height: '14px', backgroundColor: '#1b2f5b' }} />
            <div style={{ fontSize: '0.72rem', color: '#cbd5e1' }}>
              Speed: <strong style={{ color: '#00e5ff', fontFamily: 'monospace' }}>62 km/h</strong>
            </div>
            <div style={{ width: '1px', height: '14px', backgroundColor: '#1b2f5b' }} />
            <div style={{ fontSize: '0.72rem', color: '#cbd5e1' }}>
              Corridor Clearance: <strong style={{ color: '#06d6a0', fontFamily: 'monospace' }}>84%</strong>
            </div>
            <div style={{ width: '1px', height: '14px', backgroundColor: '#1b2f5b' }} />
            <div style={{ fontSize: '0.70rem', color: '#ffd166', fontWeight: 600 }}>
              Phase P3 GREEN HELD
            </div>
          </div>
        </div>

        {/* Bottom Floating Telemetry Strip */}
        <div
          style={{
            backgroundColor: 'rgba(11, 21, 45, 0.90)',
            backdropFilter: 'blur(10px)',
            border: '1px solid #1b2f5b',
            borderRadius: '6px',
            padding: '6px 14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            pointerEvents: 'auto',
            fontSize: '0.72rem',
            color: '#cbd5e1',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.5)',
          }}
        >
          {/* Telemetry metrics */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Radio size={13} color="#00e5ff" />
              <span style={{ color: '#94a3b8' }}>Connected Vehicles:</span>
              <strong style={{ color: '#00e5ff', fontFamily: 'monospace' }}>48 veh</strong>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ color: '#94a3b8' }}>Avg Speed:</span>
              <strong style={{ color: '#06d6a0', fontFamily: 'monospace' }}>38.4 km/h</strong>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ color: '#94a3b8' }}>Corridor Progress:</span>
              <strong style={{ color: '#ffd166', fontFamily: 'monospace' }}>88%</strong>
            </div>
          </div>

          {/* Safety Notice & Interlock */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <ShieldCheck size={14} color="#06d6a0" />
              <span style={{ color: '#06d6a0', fontWeight: 600 }}>Safety Interlock ACTIVE</span>
            </div>
            <span style={{ color: '#64748b' }}>|</span>
            <span style={{ color: '#94a3b8', fontSize: '0.68rem' }}>
              SIMULATION ONLY (No live physical actuator)
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
