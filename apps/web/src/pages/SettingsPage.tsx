import React from 'react';
import { NotImplemented } from '../components/NotImplemented';

export const SettingsPage: React.FC = () => {
  return (
    <NotImplemented
      moduleName="Safety Gateway & System Configuration"
      plannedTask="Task 41 (Signal Safety Gateway) and Task 52 (Threat Modeling, Security & RBAC)"
      description="Administrative settings for safety invariants, watchdog heartbeats, minimum green / yellow / all-red duration constraints, and simulator/pilot mode switches. All operational modes default to SIMULATION_ONLY."
    />
  );
};

