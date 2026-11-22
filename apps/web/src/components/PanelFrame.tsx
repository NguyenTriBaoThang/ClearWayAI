import React from 'react';
import { LoadingSkeleton } from './LoadingSkeleton';
import { EmptyState } from './EmptyState';
import { DisconnectedBanner } from './DisconnectedBanner';

export interface PanelFrameProps {
  title: string;
  icon?: React.ReactNode;
  subtitle?: string;
  badge?: React.ReactNode;
  headerActions?: React.ReactNode;
  children: React.ReactNode;
  isLoading?: boolean;
  isEmpty?: boolean;
  emptyMessage?: string;
  isDisconnected?: boolean;
  disconnectedMessage?: string;
  onReconnect?: () => void;
  onRefresh?: () => void;
  isSimulated?: boolean;
  className?: string;
  style?: React.CSSProperties;
  bodyStyle?: React.CSSProperties;
}

export const PanelFrame: React.FC<PanelFrameProps> = ({
  title,
  icon,
  subtitle,
  badge,
  headerActions,
  children,
  isLoading = false,
  isEmpty = false,
  emptyMessage,
  isDisconnected = false,
  disconnectedMessage,
  onReconnect,
  onRefresh,
  isSimulated = true,
  className = '',
  style,
  bodyStyle,
}) => {
  return (
    <div
      className={`panel-card cyber-corner ${className}`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: '#0d1b38',
        border: '1px solid #1b2f5b',
        borderRadius: '8px',
        overflow: 'hidden',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.45)',
        ...style,
      }}
    >
      {/* Panel Header */}
      <div
        className="panel-header"
        style={{
          backgroundColor: '#122347',
          borderBottom: '1px solid #162547',
          padding: '8px 12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
          {icon && (
            <div style={{ display: 'flex', alignItems: 'center', color: '#00e5ff', flexShrink: 0 }}>
              {icon}
            </div>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
            <span
              style={{
                fontSize: '0.80rem',
                fontWeight: 600,
                letterSpacing: '0.02em',
                color: '#f8fafc',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {title}
            </span>
            {subtitle && (
              <span style={{ fontSize: '0.65rem', color: '#64748b' }}>
                {subtitle}
              </span>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
          {isSimulated && (
            <span
              title="Synthetic test fixture provenance"
              style={{
                fontSize: '0.62rem',
                color: '#94a3b8',
                fontFamily: 'monospace',
                backgroundColor: 'rgba(15, 23, 42, 0.6)',
                padding: '1px 6px',
                borderRadius: '4px',
                border: '1px solid #1e293b',
              }}
            >
              [SIM]
            </span>
          )}
          {badge}
          {headerActions}
        </div>
      </div>

      {/* Disconnected Warning Alert */}
      {isDisconnected && (
        <DisconnectedBanner
          message={disconnectedMessage}
          onReconnect={onReconnect}
        />
      )}

      {/* Panel Body */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          position: 'relative',
          overflow: 'hidden',
          ...bodyStyle,
        }}
      >
        {isLoading ? (
          <LoadingSkeleton lines={4} />
        ) : isEmpty ? (
          <EmptyState description={emptyMessage} onRetry={onRefresh} />
        ) : (
          children
        )}
      </div>
    </div>
  );
};
