import React from 'react';

interface MermaidChartProps {
  chart: string;
}

export const MermaidChart: React.FC<MermaidChartProps> = ({ chart }) => {
  return (
    <div
      style={{
        margin: '20px 0',
        padding: '16px',
        backgroundColor: 'var(--code-bg)',
        border: '1px solid var(--border-color)',
        borderRadius: '8px',
        overflowX: 'auto',
      }}
    >
      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 600 }}>
        Architecture Flow Diagram
      </div>
      <pre style={{ margin: 0, background: 'none', border: 'none', padding: 0 }}>
        <code style={{ fontSize: '0.82rem', color: 'var(--accent-cyan)' }}>
          {chart.trim()}
        </code>
      </pre>
    </div>
  );
};

