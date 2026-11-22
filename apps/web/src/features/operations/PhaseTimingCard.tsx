import React from 'react';
import { Clock } from 'lucide-react';
import { PanelFrame } from '../../components/PanelFrame';
import { StatusPill } from '../../components/StatusPill';

export const PhaseTimingCard: React.FC = () => {
  const approaches = [
    { name: 'N - Oak St. (NB)', red: 67, yellow: 4, green: 49, cycle: 120, split: 41, status: 'red' },
    { name: 'S - Oak St. (SB)', red: 67, yellow: 4, green: 49, cycle: 120, split: 41, status: 'red' },
    { name: 'E - 5th Ave. (EB)', red: 49, yellow: 4, green: 67, cycle: 120, split: 56, status: 'green' },
    { name: 'W - 5th Ave. (WB)', red: 49, yellow: 4, green: 67, cycle: 120, split: 56, status: 'green' },
  ];

  return (
    <PanelFrame
      title="Oak St. & 5th Ave (INT-0457)"
      icon={<Clock size={15} />}
      badge={<StatusPill label="Split Timing" variant="amber" size="xs" />}
    >
      <div style={{ padding: '6px 10px', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.71rem', textAlign: 'left' }}>
          <thead>
            <tr style={{ color: '#94a3b8', borderBottom: '1px solid #1b2f5b', fontSize: '0.66rem' }}>
              <th style={{ padding: '4px 3px', fontWeight: 500 }}>Approach</th>
              <th style={{ padding: '4px 3px', color: '#ef476f', textAlign: 'center', fontWeight: 600 }}>Red</th>
              <th style={{ padding: '4px 3px', color: '#ffd166', textAlign: 'center', fontWeight: 600 }}>Yellow</th>
              <th style={{ padding: '4px 3px', color: '#06d6a0', textAlign: 'center', fontWeight: 600 }}>Green</th>
              <th style={{ padding: '4px 3px', textAlign: 'center', fontWeight: 500 }}>Cycle</th>
              <th style={{ padding: '4px 3px', textAlign: 'center', fontWeight: 500 }}>Split</th>
            </tr>
          </thead>
          <tbody>
            {approaches.map((app, idx) => (
              <tr
                key={idx}
                style={{
                  borderBottom: '1px solid rgba(27, 47, 91, 0.35)',
                  color: '#e2e8f0',
                }}
              >
                <td style={{ padding: '5px 3px', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span
                    style={{
                      width: '6px',
                      height: '6px',
                      borderRadius: '50%',
                      backgroundColor: app.status === 'green' ? '#06d6a0' : '#ef476f',
                      boxShadow: app.status === 'green' ? '0 0 5px #06d6a0' : 'none',
                    }}
                  />
                  <span>{app.name}</span>
                </td>
                <td style={{ padding: '5px 3px', textAlign: 'center', color: '#ef476f', fontFamily: 'monospace', fontWeight: 700 }}>
                  {app.red}s
                </td>
                <td style={{ padding: '5px 3px', textAlign: 'center', color: '#ffd166', fontFamily: 'monospace', fontWeight: 700 }}>
                  {app.yellow}s
                </td>
                <td style={{ padding: '5px 3px', textAlign: 'center', color: '#06d6a0', fontFamily: 'monospace', fontWeight: 700 }}>
                  {app.green}s
                </td>
                <td style={{ padding: '5px 3px', textAlign: 'center', fontFamily: 'monospace' }}>
                  {app.cycle}s
                </td>
                <td style={{ padding: '5px 3px', textAlign: 'center', color: '#38bdf8', fontFamily: 'monospace', fontWeight: 600 }}>
                  {app.split}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </PanelFrame>
  );
};
