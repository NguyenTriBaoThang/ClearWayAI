import React from 'react';

export const App: React.FC = () => {
  return (
    <div style={{ maxWidth: '900px', margin: '40px auto', padding: '0 24px', lineHeight: 1.6 }}>
      <div style={{ borderBottom: '1px solid #334155', paddingBottom: '16px', marginBottom: '24px' }}>
        <h1 style={{ color: '#38bdf8', fontSize: '2rem', margin: '0 0 8px 0' }}>
          ClearWay AI — Technical Documentation
        </h1>
        <p style={{ color: '#94a3b8', margin: 0 }}>
          Comprehensive architecture, simulation pipelines, ML clearance time prediction, and 3D digital twin specifications.
        </p>
      </div>

      <div style={{ background: '#1e293b', border: '1px solid #3b82f6', borderRadius: '8px', padding: '16px', marginBottom: '24px' }}>
        <strong style={{ color: '#60a5fa' }}>Status: Scaffold Ready (Task 01)</strong>
        <p style={{ margin: '8px 0 0 0', color: '#cbd5e1', fontSize: '0.9rem' }}>
          Full documentation website structure with interactive sidebar, search, and Markdown sources will be populated in <strong>Task 03</strong>.
        </p>
      </div>

      <h2 style={{ color: '#f1f5f9' }}>Core Modules Overview</h2>
      <ul>
        <li><strong>Architecture & System Bounds:</strong> Strict separation of simulated telemetry and real-world hardware.</li>
        <li><strong>SUMO Microscopic Simulation:</strong> Multi-intersection synthetic networks (A–D corridor).</li>
        <li><strong>AI Pre-clearance Prediction:</strong> Tabular baselines (XGBoost) and sequential LSTM models.</li>
        <li><strong>Three.js / WebGL 3D Twin:</strong> Real-time vehicle instancing, lane topology, and signal phase HUD.</li>
      </ul>
    </div>
  );
};

export default App;
