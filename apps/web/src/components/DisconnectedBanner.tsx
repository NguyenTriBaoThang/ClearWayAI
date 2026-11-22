import React from 'react';
import { WifiOff, RefreshCw } from 'lucide-react';

interface DisconnectedBannerProps {
  message?: string;
  onReconnect?: () => void;
}

export const DisconnectedBanner: React.FC<DisconnectedBannerProps> = ({
  message = 'Telemetry bridge disconnected. Attempting automatic reconnection...',
  onReconnect,
}) => {
  return (
    <div
      style={{
        backgroundColor: 'rgba(239, 71, 111, 0.15)',
        border: '1px solid rgba(239, 71, 111, 0.4)',
        borderRadius: '6px',
        padding: '8px 12px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '8px',
        color: '#ef476f',
        fontSize: '0.72rem',
        margin: '8px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <WifiOff size={15} />
        <span style={{ fontWeight: 500 }}>{message}</span>
      </div>
      {onReconnect && (
        <button
          onClick={onReconnect}
          style={{
            backgroundColor: '#ef476f',
            color: '#ffffff',
            border: 'none',
            borderRadius: '4px',
            padding: '3px 8px',
            fontSize: '0.65rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
          }}
        >
          <RefreshCw size={10} /> Reconnect
        </button>
      )}
    </div>
  );
};
