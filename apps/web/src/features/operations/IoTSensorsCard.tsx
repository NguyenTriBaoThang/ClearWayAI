import React from 'react';
import { IoTSensorsPanel, IoTSensorsPanelProps } from '../dashboard/IoTSensorsPanel';

export const IoTSensorsCard: React.FC<IoTSensorsPanelProps> = (props) => {
  return <IoTSensorsPanel {...props} />;
};

export { IoTSensorsPanel };
export * from '../dashboard/IoTSensorsPanel';
export default IoTSensorsCard;
