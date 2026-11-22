import React from 'react';
import { V2XHardwarePanel, V2XHardwarePanelProps } from '../dashboard/V2XHardwarePanel';

export const V2XHardwareCard: React.FC<V2XHardwarePanelProps> = (props) => {
  return <V2XHardwarePanel {...props} />;
};

export { V2XHardwarePanel };
export * from '../dashboard/V2XHardwarePanel';
export default V2XHardwareCard;
