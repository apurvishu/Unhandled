import { apiClient, smartFetch } from '@/lib/api';
import { PortCongestionResponse } from '@/types';
import { DEMO_PORT_CONGESTION } from '@/lib/demoData';

export async function getPortCongestion(portId: string): Promise<PortCongestionResponse> {
  return smartFetch<PortCongestionResponse>(
    () => apiClient.get(`/congestion/${portId}`),
    () => DEMO_PORT_CONGESTION[portId] || DEMO_PORT_CONGESTION['port-paradip']
  );
}

export async function predictCongestion(portId: string, daysAhead: number = 7): Promise<PortCongestionResponse> {
  return smartFetch<PortCongestionResponse>(
    () => apiClient.post('/congestion/predict', { portId, daysAhead }),
    () => DEMO_PORT_CONGESTION[portId] || DEMO_PORT_CONGESTION['port-paradip']
  );
}
