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
  arg1?: Partial<ForecastRequestPayload> | string,
  arg2?: VesselType,
  arg3?: number
): Promise<FreightForecastResponse> {
  let payload: Partial<ForecastRequestPayload>;

  if (typeof arg1 === 'string') {
    payload = {
      originPort: arg1.includes('aus') ? 'Hay Point' : 'Australia',
      destinationPort: 'Paradip',
      vesselType: arg2 || 'Panamax',
      horizonDays: arg3 || 14,
    };
  } else {
    payload = arg1 || { originPort: 'Hay Point', destinationPort: 'Paradip', vesselType: 'Panamax', horizonDays: 14 };
  }

  return smartFetch<FreightForecastResponse>(
    () => apiClient.post('/forecast/freight', payload),
    () => {
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
