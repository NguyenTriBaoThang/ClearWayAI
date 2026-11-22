import React from 'react';

export type StatusPillVariant = 'cyan' | 'green' | 'amber' | 'red' | 'purple' | 'neutral';
export type StatusPillSize = 'xs' | 'sm' | 'md';

interface StatusPillProps {
  label: string;
  variant?: StatusPillVariant;
  size?: StatusPillSize;
  pulse?: boolean;
  prefix?: React.ReactNode;
  title?: string;
  className?: string;
  style?: React.CSSProperties;
}

export const StatusPill: React.FC<StatusPillProps> = ({
  label,
  variant = 'cyan',
  size = 'sm',
  pulse = false,
  prefix,
  title,
  className = '',
  style,
}) => {
  const getVariantStyles = () => {
    switch (variant) {
      case 'green':
        return {
          bg: 'rgba(6, 214, 160, 0.12)',
          color: '#06d6a0',
          border: '1px solid rgba(6, 214, 160, 0.35)',
          dotBg: '#06d6a0',
          pulseClass: 'live-pulse-green',
        };
      case 'amber':
        return {
          bg: 'rgba(255, 209, 102, 0.12)',
          color: '#ffd166',
          border: '1px solid rgba(255, 209, 102, 0.35)',
          dotBg: '#ffd166',
          pulseClass: '',
        };
      case 'red':
        return {
          bg: 'rgba(239, 71, 111, 0.12)',
          color: '#ef476f',
          border: '1px solid rgba(239, 71, 111, 0.35)',
          dotBg: '#ef476f',
          pulseClass: 'live-pulse-red',
        };
      case 'purple':
        return {
          bg: 'rgba(168, 85, 247, 0.12)',
          color: '#a855f7',
          border: '1px solid rgba(168, 85, 247, 0.35)',
          dotBg: '#a855f7',
          pulseClass: '',
        };
      case 'neutral':
        return {
          bg: 'rgba(148, 163, 184, 0.1)',
          color: '#94a3b8',
          border: '1px solid rgba(148, 163, 184, 0.25)',
          dotBg: '#94a3b8',
          pulseClass: '',
        };
      case 'cyan':
      default:
        return {
          bg: 'rgba(0, 229, 255, 0.12)',
          color: '#00e5ff',
          border: '1px solid rgba(0, 229, 255, 0.35)',
          dotBg: '#00e5ff',
          pulseClass: 'live-pulse-cyan',
        };
    }
  };

  const getSizeStyles = () => {
    switch (size) {
      case 'xs':
        return { padding: '1px 6px', fontSize: '0.62rem', dotSize: '5px' };
      case 'md':
        return { padding: '4px 12px', fontSize: '0.78rem', dotSize: '8px' };
      case 'sm':
      default:
        return { padding: '2px 8px', fontSize: '0.70rem', dotSize: '6px' };
    }
  };

  const v = getVariantStyles();
  const s = getSizeStyles();

  return (
    <span
      title={title}
      className={className}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        backgroundColor: v.bg,
        color: v.color,
        border: v.border,
        borderRadius: '12px',
        fontWeight: 600,
        letterSpacing: '0.02em',
        lineHeight: 1.2,
        padding: s.padding,
        fontSize: s.fontSize,
        whiteSpace: 'nowrap',
        ...style,
      }}
    >
      {pulse && (
        <span
          className={v.pulseClass}
          style={{
            width: s.dotSize,
            height: s.dotSize,
            borderRadius: '50%',
            backgroundColor: v.dotBg,
            display: 'inline-block',
            flexShrink: 0,
          }}
        />
      )}
      {prefix}
      <span>{label}</span>
    </span>
  );
};

