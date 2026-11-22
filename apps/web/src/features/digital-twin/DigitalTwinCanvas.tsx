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
} from 'lucide-react';
import { StatusPill } from '../../components/StatusPill';
import { SceneEnvironment } from './SceneEnvironment';
import { SceneController, CameraPresetType, ProjectionMode, CameraStateMetrics } from './SceneController';

interface DigitalTwinCanvasProps {
  intersectionId?: string;
  onSelectEntity?: (id: string, type: string) => void;
  style?: React.CSSProperties;
}

export const DigitalTwinCanvas: React.FC<DigitalTwinCanvasProps> = ({
  intersectionId = 'INT-0457',
  style,
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const controllerRef = useRef<SceneController | null>(null);
  const environmentRef = useRef<SceneEnvironment | null>(null);

  const [webglInitialized, setWebglInitialized] = useState<boolean>(false);
  const [fps, setFps] = useState<number>(60);
  const [renderMs, setRenderMs] = useState<number>(2.4);
  const [drawCalls, setDrawCalls] = useState<number>(28);
  const [triangles, setTriangles] = useState<number>(3820);

  const [cameraPreset, setCameraPreset] = useState<CameraPresetType>('iso');
  const [projectionMode, setProjectionMode] = useState<ProjectionMode>('perspective');
  const [autoRotate, setAutoRotate] = useState<boolean>(false);
  const [showLayersMenu, setShowLayersMenu] = useState<boolean>(false);
  const [showMetrics, setShowMetrics] = useState<boolean>(true);

  const [layers, setLayers] = useState({
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

    // 3. Scene Environment (Lighting, Grids, Road Network, City Buildings, Hospital, RSUs)
    const environment = new SceneEnvironment(scene);
    environmentRef.current = environment;

    // 4. Scene Controller (Dual Cameras & OrbitControls)
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

      // Update environment animation (corridor pulsing, hospital beacon, waypoint marker motion)
      const waypointPos = environment.update(now);

      // Update camera controller (interpolation, OrbitControls damping, chase)
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
      controller.dispose();
      environment.dispose();

      if (container && renderer.domElement) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

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

  const handleToggleLayer = (layerKey: keyof typeof layers) => {
    const nextState = !layers[layerKey];
    setLayers((prev) => ({ ...prev, [layerKey]: nextState }));
    if (environmentRef.current) {
      if (layerKey === 'roadMarkings') {
        environmentRef.current.roadNetwork.setMarkingsVisibility(nextState);
      } else if (layerKey === 'crosswalks') {
        environmentRef.current.roadNetwork.setCrosswalksVisibility(nextState);
      } else if (layerKey === 'sidewalks') {
        environmentRef.current.roadNetwork.setSidewalksVisibility(nextState);
      } else if (layerKey === 'buildings') {
        environmentRef.current.cityEnvironment.setBuildingsVisibility(nextState);
      } else if (layerKey === 'streetFurniture') {
        environmentRef.current.cityEnvironment.setStreetFurnitureVisibility(nextState);
      } else if (layerKey === 'trees') {
        environmentRef.current.cityEnvironment.setTreesVisibility(nextState);
      }
    }
  };

  return (
    <div
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
              <StatusPill label="CITY TWIN ACTIVE" variant="cyan" size="xs" pulse />
            </div>

            <div style={{ fontSize: '0.70rem', color: '#94a3b8' }}>
              Intersection:{' '}
              <span style={{ color: '#00e5ff', fontFamily: 'monospace', fontWeight: 600 }}>
                {intersectionId}
              </span>{' '}
              (Oak St. & 5th Ave — Urban Medical & Tech District)
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

            {/* Projection & Controls Secondary Row */}
            <div style={{ display: 'flex', gap: '4px' }}>
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
