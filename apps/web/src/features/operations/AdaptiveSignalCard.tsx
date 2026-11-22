import React from 'react';
import { AdaptiveSignalPanel, AdaptiveSignalPanelProps } from '../dashboard/AdaptiveSignalPanel';

export const AdaptiveSignalCard: React.FC<AdaptiveSignalPanelProps> = (props) => {
  return <AdaptiveSignalPanel {...props} />;
};

export { AdaptiveSignalPanel };
export * from '../dashboard/AdaptiveSignalPanel';
export default AdaptiveSignalCard;
