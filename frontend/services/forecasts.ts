import { apiClient, smartFetch } from '@/lib/api';
import { FreightForecastResponse, VesselType } from '@/types';
import { DEMO_FREIGHT_FORECAST } from '@/lib/demoData';

export interface ForecastRequestPayload {
  originPort: string;
  destinationPort: string;
  vesselType: VesselType;
  horizonDays: number;
}

export async function getFreightForecast(
  payload?: Partial<ForecastRequestPayload>
): Promise<FreightForecastResponse> {
  return smartFetch<FreightForecastResponse>(
    () => apiClient.post('/forecast/freight', payload || { originPort: 'Hay Point', destinationPort: 'Paradip', vesselType: 'Panamax', horizonDays: 14 }),
    () => {
      // Dynamic adjustments if payload is provided
      if (payload?.vesselType === 'Capesize') {
        return {
          ...DEMO_FREIGHT_FORECAST,
          vesselType: 'Capesize',
          currentRateUsdPerMt: 28.50,
          predictedRateUsdPerMt: 27.20,
          expectedChangePercent: -4.56,
          estimatedPotentialSavingsUsd: 130000,
        };
      }
      return DEMO_FREIGHT_FORECAST;
    }
  );
}
