import { apiClient, smartFetch } from '@/lib/api';
import { ProcurementKpis } from '@/types';
import { DEMO_KPIS } from '@/lib/demoData';

export async function getProcurementKpis(): Promise<ProcurementKpis> {
  return smartFetch<ProcurementKpis>(
    () => apiClient.get('/freight/kpis'),
    () => DEMO_KPIS
  );
}
