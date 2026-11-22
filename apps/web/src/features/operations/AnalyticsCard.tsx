import React from 'react';
import { OperationsAnalyticsPanel, OperationsAnalyticsPanelProps } from '../dashboard/OperationsAnalyticsPanel';

export const AnalyticsCard: React.FC<OperationsAnalyticsPanelProps> = (props) => {
  return <OperationsAnalyticsPanel {...props} />;
};

export { OperationsAnalyticsPanel };
export * from '../dashboard/OperationsAnalyticsPanel';
export default AnalyticsCard;
