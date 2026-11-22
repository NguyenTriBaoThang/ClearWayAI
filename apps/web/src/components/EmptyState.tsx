import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  onRetry?: () => void;
  style?: React.CSSProperties;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Data Available',
  description = 'No active telemetry or sensor feed recorded for this scope.',
  icon,
  onRetry,
  style,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px 16px',
        textAlign: 'center',
        gap: '8px',
        color: '#94a3b8',
        ...style,
      }}
    >
      <div style={{ color: '#00e5ff', opacity: 0.8 }}>
        {icon || <AlertCircle size={24} />}
      </div>
      <div style={{ fontSize: '0.78rem', fontWeight: 600, color: '#f1f5f9' }}>
        {title}
      </div>
      <div style={{ fontSize: '0.68rem', color: '#64748b', maxWidth: '240px' }}>
        {description}
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            marginTop: '6px',
            backgroundColor: '#1b2f5b',
            color: '#00e5ff',
            border: '1px solid rgba(0, 229, 255, 0.3)',
            borderRadius: '4px',
            padding: '3px 10px',
            fontSize: '0.68rem',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
            cursor: 'pointer',
          }}
        >
          <RefreshCw size={11} /> Refresh
        </button>
      )}
    </div>
  );
};
