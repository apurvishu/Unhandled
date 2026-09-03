import { apiClient, smartFetch } from '@/lib/api';
import { Port } from '@/types';
import { DEMO_PORTS } from '@/lib/demoData';

export async function getPorts(): Promise<Port[]> {
  return smartFetch<Port[]>(
    () => apiClient.get('/ports'),
    () => DEMO_PORTS
  );
}

export async function getPortById(id: string): Promise<Port | undefined> {
  return smartFetch<Port | undefined>(
    () => apiClient.get(`/ports/${id}`),
    () => DEMO_PORTS.find((p) => p.id === id || p.code.toLowerCase().includes(id.toLowerCase())) || DEMO_PORTS[0]
  );
}

export async function checkPortBathymetryCompatibility(
  portId: string,
  vesselDraft: number
): Promise<{ isCompatible: boolean; maxDepth: number; draft: number; marginMeters: number; reason: string }> {
  return smartFetch(
    () => apiClient.post(`/ports/${portId}/check-compatibility`, { vesselDraft }),
    () => {
      const port = DEMO_PORTS.find((p) => p.id === portId) || DEMO_PORTS[0];
      const maxDepth = port.channelMaxDepth;
      const marginMeters = Number((maxDepth - vesselDraft).toFixed(2));
      const isCompatible = marginMeters >= 1.5; // Requires 1.5m under keel clearance (UKC)
      return {
        isCompatible,
        maxDepth,
        draft: vesselDraft,
        marginMeters,
        reason: isCompatible
          ? `Adequate Under Keel Clearance (${marginMeters}m clearance available with Channel Depth ${maxDepth}m).`
          : `Insufficient UKC! Channel depth ${maxDepth}m does not provide required safety clearance for ${vesselDraft}m draft.`,
      };
    }
  );
}

export async function getBerthsByPort(portId: string): Promise<any[]> {
  return smartFetch<any[]>(
    () => apiClient.get(`/ports/${portId}/berths`),
    () => {
      const port = DEMO_PORTS.find((p) => p.id === portId) || DEMO_PORTS[0];
      return port.berths || [];
    }
  );
}
