import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface KpiTileProps {
  label: string;
  value: string | number;
  unit?: string;
  delta?: {
    value: string | number;
    direction: 'up' | 'down' | 'neutral';
    isPositiveGood?: boolean;
  };
  subtitle?: string;
  badge?: React.ReactNode;
  style?: React.CSSProperties;
}

export const KpiTile: React.FC<KpiTileProps> = ({
  label,
  value,
  unit,
  delta,
  subtitle,
  badge,
  style,
}) => {
  const getDeltaColor = () => {
    if (!delta) return '#94a3b8';
    if (delta.direction === 'neutral') return '#94a3b8';
    const isGood = delta.isPositiveGood !== false;
    if (delta.direction === 'up') {
      return isGood ? '#06d6a0' : '#ef476f';
    }
    // delta down
    return isGood ? '#ef476f' : '#06d6a0';
  };

  const renderDeltaIcon = () => {
    if (!delta) return null;
    if (delta.direction === 'up') return <TrendingUp size={12} />;
    if (delta.direction === 'down') return <TrendingDown size={12} />;
    return <Minus size={12} />;
  };

  return (
    <div
      style={{
        backgroundColor: '#0a1128',
        border: '1px solid #162547',
        borderRadius: '6px',
        padding: '8px 10px',
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
        ...style,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: '0.65rem', color: '#94a3b8', fontWeight: 500, letterSpacing: '0.02em' }}>
          {label}
        </span>
        {badge}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
        <span
          style={{
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: '1.05rem',
            fontWeight: 700,
            color: '#f8fafc',
          }}
        >
          {value}
        </span>
        {unit && (
          <span style={{ fontSize: '0.68rem', color: '#64748b', fontWeight: 500 }}>
            {unit}
          </span>
        )}
      </div>

      {(delta || subtitle) && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.62rem' }}>
          {delta && (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '2px',
                color: getDeltaColor(),
                fontWeight: 600,
              }}
            >
              {renderDeltaIcon()}
              <span>{delta.value}</span>
            </span>
          )}
          {subtitle && <span style={{ color: '#64748b' }}>{subtitle}</span>}
        </div>
      )}
    </div>
  );
};
