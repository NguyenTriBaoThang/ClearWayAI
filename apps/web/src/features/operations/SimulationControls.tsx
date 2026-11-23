import React, { useState, useEffect } from 'react';
import {
  Play,
  Pause,
  SkipForward,
  RotateCcw,
  Sliders,
  Flame,
  Search,
  Clock,
  Gauge,
  CheckCircle,
  Zap,
} from 'lucide-react';
import { StatusPill } from '../../components/StatusPill';

export type SimulationScenarioId =
  | 'normal_mixed'
  | 'amb_emergency'
  | 'peak_congestion'
  | 'adverse_weather';

export interface SimulationControlsProps {
  onTogglePlay?: (isRunning: boolean) => void;
  onStep?: () => void;
  onReset?: () => void;
  onChangeSpeed?: (speed: number) => void;
  onChangeScenario?: (scenario: SimulationScenarioId) => void;
  onOpenMissionDrawer?: () => void;
  onOpenInspector?: () => void;
  onOpenAuditDrawer?: () => void;
  className?: string;
  style?: React.CSSProperties;
}

export const SimulationControls: React.FC<SimulationControlsProps> = ({
  onTogglePlay,
  onStep,
  onReset,
  onChangeSpeed,
  onChangeScenario,
  onOpenMissionDrawer,
  onOpenInspector,
  onOpenAuditDrawer,
  className = '',
  style,
}) => {
  const [isRunning, setIsRunning] = useState<boolean>(true);
  const [speedMultiplier, setSpeedMultiplier] = useState<number>(1);
  const [scenario, setScenario] = useState<SimulationScenarioId>('amb_emergency');
  const [simSeconds, setSimSeconds] = useState<number>(142); // 02:22 elapsed

  // Simulation timer tick
  useEffect(() => {
    if (!isRunning) return;
    const interval = setInterval(() => {
      setSimSeconds((prev) => (prev + 1) % 1800);
    }, 1000 / speedMultiplier);
    return () => clearInterval(interval);
  }, [isRunning, speedMultiplier]);

  const handlePlayToggle = () => {
    const nextState = !isRunning;
    setIsRunning(nextState);
    if (onTogglePlay) onTogglePlay(nextState);
  };

  const handleStep = () => {
    setSimSeconds((prev) => prev + 1);
    if (onStep) onStep();
  };

  const handleReset = () => {
    setSimSeconds(0);
    if (onReset) onReset();
  };

  const handleSpeedChange = (speed: number) => {
    setSpeedMultiplier(speed);
    if (onChangeSpeed) onChangeSpeed(speed);
  };

  const handleScenarioChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newScen = e.target.value as SimulationScenarioId;
    setScenario(newScen);
    if (onChangeScenario) onChangeScenario(newScen);
  };

  // Format MM:SS
  const mins = Math.floor(simSeconds / 60);
  const secs = simSeconds % 60;
  const timeFormatted = `${mins < 10 ? '0' + mins : mins}:${secs < 10 ? '0' + secs : secs}`;

  return (
    <div
      className={`cyber-corner ${className}`}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '6px 12px',
        backgroundColor: 'rgba(10, 17, 40, 0.92)',
        border: '1px solid #1b2f5b',
        borderRadius: '8px',
        backdropFilter: 'blur(8px)',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.5)',
        color: '#f1f5f9',
        fontSize: '0.72rem',
        gap: '10px',
        flexWrap: 'wrap',
        ...style,
      }}
    >
      {/* Left: Playback Controls (Play/Pause, Step, Reset) */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <button
          type="button"
          onClick={handlePlayToggle}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            backgroundColor: isRunning ? 'rgba(239, 71, 111, 0.2)' : 'rgba(6, 214, 160, 0.2)',
            border: `1px solid ${isRunning ? '#ef476f' : '#06d6a0'}`,
            color: isRunning ? '#ef476f' : '#06d6a0',
            borderRadius: '4px',
            padding: '4px 8px',
            cursor: 'pointer',
            fontWeight: 700,
            fontSize: '0.70rem',
            transition: 'all 0.15s ease',
          }}
          title={isRunning ? 'Pause Simulation [Space]' : 'Resume Simulation [Space]'}
        >
          {isRunning ? <Pause size={13} /> : <Play size={13} />}
          <span>{isRunning ? 'PAUSE' : 'PLAY'}</span>
        </button>

        <button
          type="button"
          onClick={handleStep}
          disabled={isRunning}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '3px',
            backgroundColor: isRunning ? 'rgba(30, 41, 59, 0.4)' : 'rgba(0, 229, 255, 0.15)',
            border: `1px solid ${isRunning ? '#334155' : '#00e5ff'}`,
            color: isRunning ? '#64748b' : '#00e5ff',
            borderRadius: '4px',
            padding: '4px 7px',
            cursor: isRunning ? 'not-allowed' : 'pointer',
            fontSize: '0.68rem',
          }}
          title="Step +1 second (Pause simulation first)"
        >
          <SkipForward size={12} />
          <span>Step</span>
        </button>

        <button
          type="button"
          onClick={handleReset}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '3px',
            backgroundColor: 'rgba(30, 41, 59, 0.6)',
            border: '1px solid #1e293b',
            color: '#94a3b8',
            borderRadius: '4px',
            padding: '4px 7px',
            cursor: 'pointer',
            fontSize: '0.68rem',
          }}
          title="Reset Simulation Clock to 00:00"
        >
          <RotateCcw size={12} />
          <span>Reset</span>
        </button>

        {/* Speed multiplier selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '2px', marginLeft: '4px' }}>
          {[0.5, 1, 2, 5].map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => handleSpeedChange(s)}
              style={{
                backgroundColor: speedMultiplier === s ? '#00e5ff' : 'rgba(15, 23, 42, 0.6)',
                color: speedMultiplier === s ? '#070d1e' : '#94a3b8',
                border: `1px solid ${speedMultiplier === s ? '#00e5ff' : '#1e293b'}`,
                borderRadius: '3px',
                padding: '2px 5px',
                fontSize: '0.62rem',
                cursor: 'pointer',
                fontWeight: speedMultiplier === s ? 700 : 500,
              }}
            >
              {s}x
            </button>
          ))}
        </div>
      </div>

      {/* Center: Simulation Clock & Scenario Selector */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {/* Sim Clock */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '5px',
            backgroundColor: '#070d1e',
            border: '1px solid #1b2f5b',
            padding: '3px 8px',
            borderRadius: '4px',
            fontFamily: 'monospace',
          }}
        >
          <Clock size={12} color="#00e5ff" />
          <span style={{ color: '#64748b', fontSize: '0.62rem' }}>SIM:</span>
          <span style={{ color: '#00f5d4', fontWeight: 700, fontSize: '0.78rem' }}>{timeFormatted}</span>
          <span style={{ color: '#64748b', fontSize: '0.58rem' }}>/ 30:00</span>
        </div>

        {/* Scenario Selector Dropdown */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ fontSize: '0.64rem', color: '#64748b' }}>Scenario:</span>
          <select
            value={scenario}
            onChange={handleScenarioChange}
            style={{
              backgroundColor: '#070d1e',
              border: '1px solid #1b2f5b',
              color: '#00f5d4',
              borderRadius: '4px',
              padding: '3px 6px',
              fontSize: '0.66rem',
              outline: 'none',
              cursor: 'pointer',
              fontFamily: 'inherit',
            }}
          >
            <option value="amb_emergency">🚨 AMB-339 Priority Corridor (Active)</option>
            <option value="normal_mixed">🚗 Normal Mixed Demand (SUMO A)</option>
            <option value="peak_congestion">⚠️ Evening Peak Spillback Stress</option>
            <option value="adverse_weather">🌧️ Heavy Rain Wet Road Surface</option>
          </select>
        </div>
      </div>

      {/* Right: Operational Modals / Drawers (Mission Control & Unified Inspector & AI Audit) */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <button
          type="button"
          onClick={onOpenAuditDrawer}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            backgroundColor: 'rgba(255, 209, 102, 0.15)',
            border: '1px solid #ffd166',
            color: '#ffd166',
            borderRadius: '4px',
            padding: '4px 8px',
            cursor: 'pointer',
            fontSize: '0.68rem',
            fontWeight: 700,
          }}
          title="Open AI Decision Audit & Explainability Logs"
        >
          <Zap size={12} />
          <span>AI Audit</span>
        </button>

        <button
          type="button"
          onClick={onOpenMissionDrawer}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            backgroundColor: 'rgba(239, 71, 111, 0.18)',
            border: '1px solid #ef476f',
            color: '#ef476f',
            borderRadius: '4px',
            padding: '4px 8px',
            cursor: 'pointer',
            fontSize: '0.68rem',
            fontWeight: 700,
          }}
          title="Open Emergency Vehicle Mission Drawer (AMB-339)"
        >
          <Flame size={12} className="live-pulse-red" />
          <span>Mission Control</span>
        </button>

        <button
          type="button"
          onClick={onOpenInspector}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            backgroundColor: 'rgba(0, 229, 255, 0.15)',
            border: '1px solid #00e5ff',
            color: '#00e5ff',
            borderRadius: '4px',
            padding: '4px 8px',
            cursor: 'pointer',
            fontSize: '0.68rem',
            fontWeight: 600,
          }}
          title="Open Unified Object Inspector"
        >
          <Search size={12} />
          <span>Inspector</span>
        </button>
      </div>
    </div>
  );
};

export default SimulationControls;

