import { apiClient, smartFetch } from '@/lib/api';
import { MarketData } from '@/types';
import { DEMO_MARKET_DATA } from '@/lib/demoData';

export async function getMarketData(): Promise<MarketData> {
  return smartFetch<MarketData>(
    () => apiClient.get('/market/summary'),
    () => DEMO_MARKET_DATA
  );
}
