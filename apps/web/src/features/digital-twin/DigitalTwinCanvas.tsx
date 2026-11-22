import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { Box, Layers, RotateCw, ZoomIn, ZoomOut, AlertTriangle } from 'lucide-react';

interface DigitalTwinCanvasProps {
  intersectionId?: string;
  onSelectEntity?: (id: string, type: string) => void;
}

export const DigitalTwinCanvas: React.FC<DigitalTwinCanvasProps> = ({
  intersectionId = 'INT-0457',
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const [webglInitialized, setWebglInitialized] = useState<boolean>(false);
  const [fps, setFps] = useState<number>(60);

  useEffect(() => {
    if (!mountRef.current) return;

    const width = mountRef.current.clientWidth || 800;
    const height = mountRef.current.clientHeight || 500;

    // 1. Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a1128);

    // 2. Camera setup (Isometric perspective)
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

    // 5. Ground grid and intersection platform placeholder
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

    // Compass/Axis Helper
    const axesHelper = new THREE.AxesHelper(5);
    scene.add(axesHelper);

    // Subtle gentle camera rotation for pending preview
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

      // Gentle pivot around center
      const time = now * 0.0003;
      camera.position.x = 42 * Math.cos(time);
      camera.position.z = 42 * Math.sin(time);
      camera.lookAt(0, 0, 0);

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
    };
  }, []);

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
      }}
    >
      {/* Three.js Canvas Container */}
      <div ref={mountRef} style={{ width: '100%', height: '100%' }} />

      {/* Floating HUD: Scene Status and Lifecycle Notice */}
      <div
        style={{
          position: 'absolute',
          top: '12px',
          left: '12px',
          backgroundColor: 'rgba(10, 17, 40, 0.85)',
          backdropFilter: 'blur(8px)',
          border: '1px solid #1b325f',
          padding: '8px 14px',
          borderRadius: '6px',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
          zIndex: 10,
          pointerEvents: 'none',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Box size={14} color="#00e5ff" />
          <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#f1f5f9' }}>
            3D DIGITAL TWIN CANVAS
          </span>
          <span
            style={{
              backgroundColor: 'rgba(255, 209, 102, 0.2)',
              color: '#ffd166',
              fontSize: '0.65rem',
              fontWeight: 700,
              padding: '1px 6px',
              borderRadius: '4px',
              border: '1px solid rgba(255, 209, 102, 0.4)',
            }}
          >
            STATUS: PENDING
          </span>
        </div>
        <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>
          Active Target: <span style={{ color: '#00e5ff', fontFamily: 'monospace' }}>{intersectionId}</span> (Oak St. & 5th Ave)
        </div>
        <div style={{ fontSize: '0.68rem', color: '#64748b' }}>
          Engine: Three.js WebGL {webglInitialized ? '● Online' : '○ Initializing'} | {fps} FPS
        </div>
      </div>

      {/* Floating Badge Explaining Development State */}
      <div
        style={{
          position: 'absolute',
          bottom: '16px',
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: 'rgba(11, 21, 45, 0.92)',
          backdropFilter: 'blur(10px)',
          border: '1px solid #1e3a8a',
          padding: '8px 18px',
          borderRadius: '24px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          zIndex: 10,
          boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
        }}
      >
        <AlertTriangle size={15} color="#ffd166" />
        <span style={{ fontSize: '0.75rem', color: '#cbd5e1' }}>
          WebGL Engine active. Full road geometry & vehicle instancing builds in{' '}
          <strong style={{ color: '#00e5ff' }}>Task 07–13</strong>.
        </span>
      </div>

      {/* Camera View Controls */}
      <div
        style={{
          position: 'absolute',
          top: '12px',
          right: '12px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          zIndex: 10,
        }}
      >
        <button
          title="Isometric View"
          style={{
            width: '32px',
            height: '32px',
            borderRadius: '6px',
            backgroundColor: '#0d1b38',
            border: '1px solid #1b2f5b',
            color: '#00e5ff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
          }}
        >
          <RotateCw size={14} />
        </button>
        <button
          title="Zoom In"
          style={{
            width: '32px',
            height: '32px',
            borderRadius: '6px',
            backgroundColor: '#0d1b38',
            border: '1px solid #1b2f5b',
            color: '#94a3b8',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
          }}
        >
          <ZoomIn size={14} />
        </button>
        <button
          title="Zoom Out"
          style={{
            width: '32px',
            height: '32px',
            borderRadius: '6px',
            backgroundColor: '#0d1b38',
            border: '1px solid #1b2f5b',
            color: '#94a3b8',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
          }}
        >
          <ZoomOut size={14} />
        </button>
        <button
          title="Layers Toggle"
          style={{
            width: '32px',
            height: '32px',
            borderRadius: '6px',
            backgroundColor: '#0d1b38',
            border: '1px solid #1b2f5b',
            color: '#94a3b8',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
          }}
        >
          <Layers size={14} />
        </button>
      </div>
    </div>
  );
};
