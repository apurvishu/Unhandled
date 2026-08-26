import { apiClient, smartFetch } from '@/lib/api';
import { OptimizationResponse, VesselMatch } from '@/types';
import { DEMO_OPTIMIZATION_RESPONSE, DEMO_VESSEL_MATCHES } from '@/lib/demoData';

export async function matchVessels(cargoId: string): Promise<VesselMatch[]> {
  return smartFetch<VesselMatch[]>(
    () => apiClient.post('/optimization/match-vessels', { cargoId }),
    () => DEMO_VESSEL_MATCHES
  );
}

export async function getOptimizationRecommendation(cargoId: string): Promise<OptimizationResponse> {
  return smartFetch<OptimizationResponse>(
    () => apiClient.post('/optimization/recommend', { cargoId }),
    () => DEMO_OPTIMIZATION_RESPONSE
  );
}
