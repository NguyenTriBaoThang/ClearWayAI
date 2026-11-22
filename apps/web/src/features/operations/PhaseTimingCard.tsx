import React from 'react';
import { Clock } from 'lucide-react';

export const PhaseTimingCard: React.FC = () => {
  const approaches = [
    { name: 'N - Oak St. (NB)', red: 67, yellow: 4, green: 49, cycle: 120, split: 41 },
    { name: 'S - Oak St. (SB)', red: 67, yellow: 4, green: 49, cycle: 120, split: 41 },
    { name: 'E - 5th Ave. (EB)', red: 49, yellow: 4, green: 67, cycle: 120, split: 56 },
    { name: 'W - 5th Ave. (WB)', red: 49, yellow: 4, green: 67, cycle: 120, split: 56 },
  ];

  return (
    <div className="panel-card" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Clock size={14} color="#ffd166" />
          <span>Oak St. & 5th Ave (INT-0457)</span>
        </div>
        <span style={{ fontSize: '0.68rem', color: '#64748b' }}>Approach Split Timing</span>
      </div>

      <div style={{ padding: '8px 12px', flex: 1, overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.73rem', textAlign: 'left' }}>
          <thead>
            <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1b2f5b', fontSize: '0.68rem' }}>
              <th style={{ padding: '6px 4px', fontWeight: 500 }}>Approach</th>
              <th style={{ padding: '6px 4px', color: '#ef476f', textAlign: 'center', fontWeight: 600 }}>Red</th>
              <th style={{ padding: '6px 4px', color: '#ffd166', textAlign: 'center', fontWeight: 600 }}>Yellow</th>
              <th style={{ padding: '6px 4px', color: '#06d6a0', textAlign: 'center', fontWeight: 600 }}>Green</th>
              <th style={{ padding: '6px 4px', textAlign: 'center', fontWeight: 500 }}>Cycle</th>
              <th style={{ padding: '6px 4px', textAlign: 'center', fontWeight: 500 }}>Split</th>
            </tr>
          </thead>
          <tbody>
            {approaches.map((app, idx) => (
              <tr
                key={idx}
                style={{
                  borderBottom: '1px solid rgba(27, 47, 91, 0.4)',
                  color: '#e2e8f0',
                }}
              >
                <td style={{ padding: '6px 4px', fontWeight: 500 }}>{app.name}</td>
                <td style={{ padding: '6px 4px', textAlign: 'center', color: '#ef476f', fontFamily: 'monospace', fontWeight: 700 }}>
                  {app.red}s
                </td>
                <td style={{ padding: '6px 4px', textAlign: 'center', color: '#ffd166', fontFamily: 'monospace', fontWeight: 700 }}>
                  {app.yellow}s
                </td>
                <td style={{ padding: '6px 4px', textAlign: 'center', color: '#06d6a0', fontFamily: 'monospace', fontWeight: 700 }}>
                  {app.green}s
                </td>
                <td style={{ padding: '6px 4px', textAlign: 'center', fontFamily: 'monospace' }}>
                  {app.cycle}s
                </td>
                <td style={{ padding: '6px 4px', textAlign: 'center', color: '#38bdf8', fontFamily: 'monospace', fontWeight: 600 }}>
                  {app.split}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

