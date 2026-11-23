/**
 * ClearWayAI Variable Message Sign (VMS) Advisory Monitor Card
 * (`apps/web/src/features/operations/VMSAdvisoryCard.tsx`)
 *
 * Real-time operator dashboard monitoring the 4 overhead arterial VMS gantries:
 * - VMS-A (-80m): Maple St approach
 * - VMS-B (170m): Oak St approach
 * - VMS-C (420m): Pine St approach
 * - VMS-D (670m): Elm St approach
 *
 * Features:
 * - Cyber LED matrix visual styling with dynamic color palettes (Amber / Red / Cyan)
 * - Real-time bilingual driver advisory messages (VI & EN)
 * - Flashing strobe alert badges and chevron indicators
 * - Dynamic speed recommendations (30 / 40 / 50 km/h)
 */

import React, { useEffect, useState } from 'react';
import { PanelFrame } from '../../components/ui/PanelFrame';
import { StatusPill } from '../../components/ui/StatusPill';

export interface VMSBoardItem {
  board_id: string;
  node_id: string;
  gantry_x_m: number;
  target_stopline_x: number;
  mode: 'NOMINAL' | 'PRE_CLEARANCE' | 'EMERGENCY_CORRIDOR' | 'CAUTION_RECOVERY' | string;
  message_line_1_vi: string;
  message_line_2_en: string;
  recommended_speed_kmh: number;
  flashing_strobe: boolean;
  chevron_direction: 'RIGHT' | 'NONE' | 'BOTH' | string;
  ev_distance_m?: number | null;
  ev_eta_sec?: number | null;
}

export interface VMSAdvisoryCardProps {
  activeMissionId?: string | null;
  corridorPreempted?: boolean;
}

const DEFAULT_BOARDS: Record<string, VMSBoardItem> = {
  node_a: {
    board_id: 'VMS-A',
    node_id: 'node_a',
    gantry_x_m: -80.0,
    target_stopline_x: 0.0,
    mode: 'NOMINAL',
    message_line_1_vi: 'CHÚC QUÝ KHÁCH BÌNH AN',
    message_line_2_en: 'SPEED LIMIT 50 KM/H',
    recommended_speed_kmh: 50,
    flashing_strobe: false,
    chevron_direction: 'NONE',
  },
  node_b: {
    board_id: 'VMS-B',
    node_id: 'node_b',
    gantry_x_m: 170.0,
    target_stopline_x: 250.0,
    mode: 'NOMINAL',
    message_line_1_vi: 'CHÚC QUÝ KHÁCH BÌNH AN',
    message_line_2_en: 'SPEED LIMIT 50 KM/H',
    recommended_speed_kmh: 50,
    flashing_strobe: false,
    chevron_direction: 'NONE',
  },
  node_c: {
    board_id: 'VMS-C',
    node_id: 'node_c',
    gantry_x_m: 420.0,
    target_stopline_x: 500.0,
    mode: 'NOMINAL',
    message_line_1_vi: 'CHÚC QUÝ KHÁCH BÌNH AN',
    message_line_2_en: 'SPEED LIMIT 50 KM/H',
    recommended_speed_kmh: 50,
    flashing_strobe: false,
    chevron_direction: 'NONE',
  },
  node_d: {
    board_id: 'VMS-D',
    node_id: 'node_d',
    gantry_x_m: 670.0,
    target_stopline_x: 750.0,
    mode: 'NOMINAL',
    message_line_1_vi: 'CHÚC QUÝ KHÁCH BÌNH AN',
    message_line_2_en: 'SPEED LIMIT 50 KM/H',
    recommended_speed_kmh: 50,
    flashing_strobe: false,
    chevron_direction: 'NONE',
  },
};

export const VMSAdvisoryCard: React.FC<VMSAdvisoryCardProps> = ({
  activeMissionId,
  corridorPreempted = false,
}) => {
  const [boards, setBoards] = useState<Record<string, VMSBoardItem>>(DEFAULT_BOARDS);

  useEffect(() => {
    // If priority mission active, synthesize realistic corridor pre-clearance advisory
    if (activeMissionId || corridorPreempted) {
      setBoards({
        node_a: {
          board_id: 'VMS-A',
          node_id: 'node_a',
          gantry_x_m: -80.0,
          target_stopline_x: 0.0,
          mode: 'EMERGENCY_CORRIDOR',
          message_line_1_vi: 'NHƯỜNG ĐƯỜNG XE CẤP CỨU',
          message_line_2_en: 'MERGE RIGHT >>> AMB-339',
          recommended_speed_kmh: 30,
          flashing_strobe: true,
          chevron_direction: 'RIGHT',
          ev_distance_m: 60.0,
          ev_eta_sec: 3.2,
        },
        node_b: {
          board_id: 'VMS-B',
          node_id: 'node_b',
          gantry_x_m: 170.0,
          target_stopline_x: 250.0,
          mode: 'PRE_CLEARANCE',
          message_line_1_vi: 'ĐANG GIẢI TỎA DÒNG XE',
          message_line_2_en: 'PRIORITY CORRIDOR AHEAD',
          recommended_speed_kmh: 40,
          flashing_strobe: true,
          chevron_direction: 'RIGHT',
          ev_distance_m: 310.0,
          ev_eta_sec: 16.8,
        },
        node_c: {
          board_id: 'VMS-C',
          node_id: 'node_c',
          gantry_x_m: 420.0,
          target_stopline_x: 500.0,
          mode: 'NOMINAL',
          message_line_1_vi: 'CHÚC QUÝ KHÁCH BÌNH AN',
          message_line_2_en: 'SPEED LIMIT 50 KM/H',
          recommended_speed_kmh: 50,
          flashing_strobe: false,
          chevron_direction: 'NONE',
        },
        node_d: {
          board_id: 'VMS-D',
          node_id: 'node_d',
          gantry_x_m: 670.0,
          target_stopline_x: 750.0,
          mode: 'NOMINAL',
          message_line_1_vi: 'CHÚC QUÝ KHÁCH BÌNH AN',
          message_line_2_en: 'SPEED LIMIT 50 KM/H',
          recommended_speed_kmh: 50,
          flashing_strobe: false,
          chevron_direction: 'NONE',
        },
      });
    } else {
      setBoards(DEFAULT_BOARDS);
    }
  }, [activeMissionId, corridorPreempted]);

  return (
    <PanelFrame
      title="Variable Message Signs (VMS) Advisory"
      badge="Overhead Gantries"
      variant="cyan"
    >
      <div className="space-y-2.5">
        <div className="flex items-center justify-between text-xs text-slate-400 pb-1 border-b border-slate-800">
          <span>Corridor Gantries (4 Active)</span>
          <span className="flex items-center gap-1.5 font-mono text-[11px] text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            V2X Dynamic Guidance
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {Object.values(boards).map((b) => {
            const isEmergency = b.mode === 'EMERGENCY_CORRIDOR';
            const isPreClearance = b.mode === 'PRE_CLEARANCE';
            const isRecovery = b.mode === 'CAUTION_RECOVERY';

            let borderStyle = 'border-amber-500/30 bg-amber-950/10';
            let pillVariant: 'green' | 'amber' | 'red' | 'cyan' | 'neutral' = 'neutral';
            let dotColor = 'bg-amber-400';

            if (isEmergency) {
              borderStyle = 'border-rose-500/50 bg-rose-950/20 shadow-lg shadow-rose-950/30';
              pillVariant = 'red';
              dotColor = 'bg-rose-500';
            } else if (isPreClearance) {
              borderStyle = 'border-amber-500/50 bg-amber-950/20';
              pillVariant = 'amber';
              dotColor = 'bg-amber-400';
            } else if (isRecovery) {
              borderStyle = 'border-cyan-500/40 bg-cyan-950/20';
              pillVariant = 'cyan';
              dotColor = 'bg-cyan-400';
            }

            return (
              <div
                key={b.board_id}
                className={`p-2.5 rounded-lg border ${borderStyle} transition-all duration-300`}
              >
                {/* Header row */}
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-1.5">
                    <span className={`w-2 h-2 rounded-full ${dotColor} ${b.flashing_strobe ? 'animate-ping' : ''}`} />
                    <span className="font-mono text-xs font-bold text-slate-200">
                      {b.board_id}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      x={b.gantry_x_m > 0 ? `+${b.gantry_x_m}m` : `${b.gantry_x_m}m`}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                      {b.recommended_speed_kmh} km/h
                    </span>
                    <StatusPill variant={pillVariant} size="sm">
                      {b.mode}
                    </StatusPill>
                  </div>
                </div>

                {/* LED Matrix Screen Representation */}
                <div className="p-2 rounded bg-slate-950 border border-slate-800 font-mono text-center">
                  <div
                    className={`text-xs font-bold tracking-wide truncate ${
                      isEmergency ? 'text-rose-400' : isPreClearance ? 'text-amber-400' : 'text-amber-300'
                    }`}
                  >
                    {b.message_line_1_vi}
                  </div>
                  <div className="text-[11px] font-medium text-slate-200 tracking-wider truncate flex items-center justify-center gap-1 mt-0.5">
                    {b.chevron_direction === 'RIGHT' && (
                      <span className="text-amber-400 font-bold animate-pulse">&gt;&gt;</span>
                    )}
                    <span>{b.message_line_2_en}</span>
                    {b.chevron_direction === 'RIGHT' && (
                      <span className="text-amber-400 font-bold animate-pulse">&gt;&gt;</span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </PanelFrame>
  );
};

