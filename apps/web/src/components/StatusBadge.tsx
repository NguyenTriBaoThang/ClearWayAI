import React from 'react';

interface StatusBadgeProps {
  status: string;
  variant?: 'green' | 'cyan' | 'yellow' | 'red' | 'gray';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, variant = 'cyan' }) => {
  const getColors = () => {
    switch (variant) {
      case 'green':
        return 'bg-emerald-950/80 text-emerald-400 border-emerald-500/40';
      case 'red':
        return 'bg-rose-950/80 text-rose-400 border-rose-500/40';
      case 'yellow':
        return 'bg-amber-950/80 text-amber-400 border-amber-500/40';
      case 'gray':
        return 'bg-slate-900 text-slate-400 border-slate-700';
      case 'cyan':
      default:
        return 'bg-cyan-950/80 text-cyan-400 border-cyan-500/40';
    }
  };

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 8px',
        borderRadius: '12px',
        fontSize: '0.72rem',
        fontWeight: 600,
        border: '1px solid currentColor',
        letterSpacing: '0.03em',
      }}
      className={getColors()}
    >
      {status}
    </span>
  );
};

