/**
 * Unified Corridor Operations View (`apps/web/src/features/corridor/CorridorOperationsView.tsx`)
 *
 * Integrates the 2D Arterial Corridor Route Map with the Moving-Horizon
 * Coordination Timeline into a single interactive operations panel.
 */

import React, { useState } from 'react';
import { Route, Clock, Maximize2, Minimize2, MapPin } from 'lucide-react';
import { CorridorRouteMap2D } from './CorridorRouteMap2D';
import { CorridorTimeline } from './CorridorTimeline';

export type CorridorViewTab = 'all' | 'map' | 'timeline';

export interface CorridorOperationsViewProps {
  onClose?: () => void;
  className?: string;
  style?: React.CSSProperties;
}

export const CorridorOperationsView: React.FC<CorridorOperationsViewProps> = ({
  onClose,
  className = '',
  style,
}) => {
  const [activeTab, setActiveTab] = useState<CorridorViewTab>('all');
  const [isExpanded, setIsExpanded] = useState<boolean>(false);

  return (
    <div
      className={`corridor-operations-view ${className}`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        backgroundColor: '#070d1e',
        borderRadius: '8px',
        width: '100%',
        boxSizing: 'border-box',
        ...style,
      }}
    >
      {/* View Switcher Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '6px 10px',
          backgroundColor: '#0a1428',
          border: '1px solid #1b2f5b',
          borderRadius: '6px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Route size={14} color="#00e5ff" />
          <span style={{ fontSize: '0.76rem', fontWeight: 700, color: '#f8fafc', letterSpacing: '0.02em' }}>
            CORRIDOR SURVEILLANCE & TIMELINE DECK
          </span>
        </div>

        {/* Tab Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <button
            onClick={() => setActiveTab('all')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '3px 8px',
              borderRadius: '4px',
              fontSize: '0.68rem',
              fontWeight: 600,
              cursor: 'pointer',
              backgroundColor: activeTab === 'all' ? '#1b2f5b' : 'transparent',
              color: activeTab === 'all' ? '#00e5ff' : '#94a3b8',
              border: activeTab === 'all' ? '1px solid #00e5ff' : '1px solid transparent',
            }}
          >
            <span>Dual Deck</span>
          </button>

          <button
            onClick={() => setActiveTab('map')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '3px 8px',
              borderRadius: '4px',
              fontSize: '0.68rem',
              fontWeight: 600,
              cursor: 'pointer',
              backgroundColor: activeTab === 'map' ? '#1b2f5b' : 'transparent',
              color: activeTab === 'map' ? '#00e5ff' : '#94a3b8',
              border: activeTab === 'map' ? '1px solid #00e5ff' : '1px solid transparent',
            }}
          >
            <MapPin size={11} />
            <span>2D Map</span>
          </button>

          <button
            onClick={() => setActiveTab('timeline')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              padding: '3px 8px',
              borderRadius: '4px',
              fontSize: '0.68rem',
              fontWeight: 600,
              cursor: 'pointer',
              backgroundColor: activeTab === 'timeline' ? '#1b2f5b' : 'transparent',
              color: activeTab === 'timeline' ? '#00e5ff' : '#94a3b8',
              border: activeTab === 'timeline' ? '1px solid #00e5ff' : '1px solid transparent',
            }}
          >
            <Clock size={11} />
            <span>Timeline</span>
          </button>

          {onClose && (
            <button
              onClick={onClose}
              style={{
                background: 'none',
                border: 'none',
                color: '#64748b',
                cursor: 'pointer',
                padding: '2px 4px',
                marginLeft: '6px',
              }}
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Conditional Rendering of Map and Timeline */}
      {(activeTab === 'all' || activeTab === 'map') && <CorridorRouteMap2D />}
      {(activeTab === 'all' || activeTab === 'timeline') && <CorridorTimeline />}
    </div>
  );
};

export default CorridorOperationsView;

