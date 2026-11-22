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
  Maximize2,
  Video,
} from 'lucide-react';
import { StatusPill } from '../../components/StatusPill';

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
  const [webglInitialized, setWebglInitialized] = useState<boolean>(false);
  const [fps, setFps] = useState<number>(60);
  const [cameraPreset, setCameraPreset] = useState<'iso' | 'top' | 'close' | 'chase'>('iso');
  const [showLayersMenu, setShowLayersMenu] = useState<boolean>(false);

  useEffect(() => {
    if (!mountRef.current) return;

    const width = mountRef.current.clientWidth || 800;
    const height = mountRef.current.clientHeight || 500;

    // 1. Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a1128);

    // 2. Camera setup
    const aspect = width / height;
    const camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 1000);
    camera.position.set(40, 45, 40);
    camera.lookAt(0, 0, 0);

    // 3. WebGL Renderer
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      mountRef.current.appendChild(renderer.domElement);
      setWebglInitialized(true);
    } catch (e) {
      console.error('WebGL initialization failed:', e);
      return;
    }

    // 4. Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x00f5d4, 1.2);
    dirLight.position.set(30, 50, 20);
    scene.add(dirLight);

    const secondaryLight = new THREE.DirectionalLight(0xffd166, 0.5);
    secondaryLight.position.set(-30, 20, -20);
    scene.add(secondaryLight);

    // 5. Ground grid and intersection platform
    const gridHelper = new THREE.GridHelper(80, 40, 0x00e5ff, 0x1b2f5b);
    gridHelper.position.y = 0;
    scene.add(gridHelper);

    // Center junction boundary indicator
    const junctionGeometry = new THREE.BoxGeometry(20, 0.2, 20);
    const junctionMaterial = new THREE.MeshStandardMaterial({
      color: 0x0f1c3f,
      roughness: 0.8,
      metalness: 0.2,
      wireframe: false,
    });
    const junctionMesh = new THREE.Mesh(junctionGeometry, junctionMaterial);
    junctionMesh.position.y = -0.1;
    scene.add(junctionMesh);

    // Simulated Emergency Corridor Path (visual indicator in 3D scene)
    const corridorGeometry = new THREE.BoxGeometry(38, 0.22, 5);
    const corridorMaterial = new THREE.MeshBasicMaterial({
      color: 0x00e5ff,
      transparent: true,
      opacity: 0.25,
      wireframe: true,
    });
    const corridorMesh = new THREE.Mesh(corridorGeometry, corridorMaterial);
    corridorMesh.position.set(0, -0.05, 0);
    scene.add(corridorMesh);

    // Compass / Axis Helper
    const axesHelper = new THREE.AxesHelper(6);
    scene.add(axesHelper);

    // Camera animation
    let frameId: number;
    let lastTime = performance.now();
    let frameCount = 0;

    const animate = () => {
      frameId = requestAnimationFrame(animate);

      // Measure FPS
      frameCount++;
      const now = performance.now();
      if (now - lastTime >= 1000) {
        setFps(Math.round((frameCount * 1000) / (now - lastTime)));
        frameCount = 0;
        lastTime = now;
      }

      // Gentle pivot around center (subtle live animation)
      if (cameraPreset === 'iso') {
        const time = now * 0.0003;
        camera.position.x = 44 * Math.cos(time);
        camera.position.z = 44 * Math.sin(time);
        camera.position.y = 45;
        camera.lookAt(0, 0, 0);
      } else if (cameraPreset === 'top') {
        camera.position.set(0, 65, 0.01);
        camera.lookAt(0, 0, 0);
      } else if (cameraPreset === 'close') {
        camera.position.set(18, 16, 18);
        camera.lookAt(0, 1, 0);
      } else if (cameraPreset === 'chase') {
        const time = now * 0.0008;
        const xPos = 16 * Math.sin(time);
        camera.position.set(xPos - 8, 8, 4);
        camera.lookAt(xPos, 0, 0);
      }

      renderer.render(scene, camera);
    };

    animate();

    // Handle Resize
    const handleResize = () => {
      if (!mountRef.current) return;
      const newWidth = mountRef.current.clientWidth;
      const newHeight = mountRef.current.clientHeight;
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener('resize', handleResize);
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
      junctionGeometry.dispose();
      junctionMaterial.dispose();
      corridorGeometry.dispose();
      corridorMaterial.dispose();
    };
  }, [cameraPreset]);

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
      {/* Three.js Canvas Container */}
      <div ref={mountRef} style={{ width: '100%', height: '100%' }} />

      {/* Floating HUD Layer - pointer-events: none so mouse can orbit canvas */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: '12px',
        }}
      >
        {/* Top Floating HUD Bar: Info on Left, Controls on Right */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          {/* Top-Left: Scene Title & Engine Status */}
          <div
            style={{
              backgroundColor: 'rgba(10, 17, 40, 0.88)',
              backdropFilter: 'blur(8px)',
              border: '1px solid #1b325f',
              padding: '8px 14px',
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
              <StatusPill label="STATUS: PENDING" variant="amber" size="xs" />
            </div>
            <div style={{ fontSize: '0.70rem', color: '#94a3b8' }}>
              Active Intersection:{' '}
              <span style={{ color: '#00e5ff', fontFamily: 'monospace', fontWeight: 600 }}>
                {intersectionId}
              </span>{' '}
              (Oak St. & 5th Ave)
            </div>
            <div style={{ fontSize: '0.66rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span>Engine: Three.js WebGL {webglInitialized ? '● Online' : '○ Booting'}</span>
              <span>|</span>
              <span style={{ color: '#06d6a0', fontFamily: 'monospace', fontWeight: 600 }}>{fps} FPS</span>
              <span>|</span>
              <span style={{ color: '#ffd166' }}>Road Meshes: Task 07–13</span>
            </div>
          </div>

          {/* Top-Right: Camera Presets & Layer Controls */}
          <div
            style={{
              display: 'flex',
              gap: '6px',
              pointerEvents: 'auto',
            }}
          >
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
                onClick={() => setCameraPreset('iso')}
                title="Isometric 3D Perspective Orbit"
                style={{
                  backgroundColor: cameraPreset === 'iso' ? 'rgba(0, 229, 255, 0.2)' : 'transparent',
                  border: cameraPreset === 'iso' ? '1px solid #00e5ff' : '1px solid transparent',
                  color: cameraPreset === 'iso' ? '#00e5ff' : '#94a3b8',
                  borderRadius: '4px',
                  padding: '3px 8px',
                  fontSize: '0.68rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                }}
              >
                ISO
              </button>
              <button
                onClick={() => setCameraPreset('top')}
                title="Top-Down 2D Orthographic View"
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
                onClick={() => setCameraPreset('close')}
                title="Junction Close-up View"
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
                onClick={() => setCameraPreset('chase')}
                title="Emergency Vehicle Follow / Chase Cam"
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
                  gap: '4px',
                }}
              >
                <Video size={11} /> CHASE
              </button>
            </div>

            {/* Layer Menu Toggle */}
            <button
              onClick={() => setShowLayersMenu(!showLayersMenu)}
              title="Toggle Digital Twin Scene Layers"
              style={{
                backgroundColor: showLayersMenu ? 'rgba(0, 229, 255, 0.2)' : 'rgba(10, 17, 40, 0.88)',
                backdropFilter: 'blur(8px)',
                border: '1px solid #1b2f5b',
                color: showLayersMenu ? '#00e5ff' : '#94a3b8',
                borderRadius: '6px',
                padding: '6px 10px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                fontSize: '0.70rem',
              }}
            >
              <Layers size={13} />
              <span>Layers</span>
            </button>
          </div>
        </div>

        {/* Center Floating Callout: Emergency Vehicle Priority Tracking */}
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
