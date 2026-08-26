import { apiClient, smartFetch } from '@/lib/api';
import { Vessel } from '@/types';
import { DEMO_VESSELS } from '@/lib/demoData';

export async function getVessels(): Promise<Vessel[]> {
  return smartFetch<Vessel[]>(
    () => apiClient.get('/vessels'),
    () => DEMO_VESSELS
  );
}

export async function getVesselById(id: string): Promise<Vessel | undefined> {
  return smartFetch<Vessel | undefined>(
    () => apiClient.get(`/vessels/${id}`),
    () => DEMO_VESSELS.find((v) => v.id === id) || DEMO_VESSELS[0]
  );
}

export async function createVessel(data: Partial<Vessel>): Promise<Vessel> {
  return smartFetch<Vessel>(
    () => apiClient.post('/vessels', data),
    () => {
      const newVessel: Vessel = {
        id: 'vessel-' + Date.now(),
        name: data.name || 'MV NEW CARRIER',
        imo: data.imo || '9999999',
        mmsi: data.mmsi || '538009999',
        type: data.type || 'Panamax',
        dwt: data.dwt || 82000,
        loa: data.loa || 229,
        beam: data.beam || 32.2,
        maxDraft: data.maxDraft || 14.5,
        currentDraft: data.currentDraft || 13.5,
        yearBuilt: data.yearBuilt || 2022,
        flag: data.flag || 'Marshall Islands',
        ownerId: 'usr-ship-01',
        ownerName: 'Oceanic Bulk Carrier Fleet Ltd',
        isAvailable: true,
        availableFrom: new Date().toISOString(),
        dailyCharterRateUsd: data.dailyCharterRateUsd || 19500,
        fuelConsumptionMtPerDay: data.fuelConsumptionMtPerDay || 25,
        aisPosition: {
          latitude: 1.3,
          longitude: 103.8,
          speedKnots: 13.0,
          headingDegrees: 180,
          status: 'Underway',
          destination: 'Paradip Port',
          eta: new Date(Date.now() + 86400000 * 7).toISOString(),
          lastUpdated: new Date().toISOString(),
          isSimulated: true,
        },
      };
      DEMO_VESSELS.push(newVessel);
      return newVessel;
    }
  );
}

export async function updateVessel(id: string, data: Partial<Vessel>): Promise<Vessel> {
  return smartFetch<Vessel>(
    () => apiClient.put(`/vessels/${id}`, data),
    () => {
      const v = DEMO_VESSELS.find((item) => item.id === id) || DEMO_VESSELS[0];
      Object.assign(v, data);
      return v;
    }
  );
}
