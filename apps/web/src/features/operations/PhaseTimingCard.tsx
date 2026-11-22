import React from 'react';
import { PhaseTimingPanel, PhaseTimingPanelProps } from '../dashboard/PhaseTimingPanel';

export const PhaseTimingCard: React.FC<PhaseTimingPanelProps> = (props) => {
  return <PhaseTimingPanel {...props} />;
};

export { PhaseTimingPanel };
export * from '../dashboard/PhaseTimingPanel';
export default PhaseTimingCard;
