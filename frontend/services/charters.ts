import { apiClient, smartFetch } from '@/lib/api';
import { CharterContract, CharterOffer } from '@/types';
import { DEMO_CHARTERS } from '@/lib/demoData';

export async function getCharters(): Promise<CharterContract[]> {
  return smartFetch<CharterContract[]>(
    () => apiClient.get('/charters'),
    () => DEMO_CHARTERS
  );
}

export async function getCharterById(id: string): Promise<CharterContract | undefined> {
  return smartFetch<CharterContract | undefined>(
    () => apiClient.get(`/charters/${id}`),
    () => DEMO_CHARTERS.find((c) => c.id === id) || DEMO_CHARTERS[0]
  );
}

export async function createCharterRequest(cargoRequirementId: string, vesselId: string): Promise<CharterContract> {
  return smartFetch<CharterContract>(
    () => apiClient.post('/charters', { cargoRequirementId, vesselId }),
    () => {
      const newContract: CharterContract = {
        id: 'ctr-' + Date.now(),
        cargoRequirementId,
        cargoSummary: {
          commodity: 'Coking Coal',
          quantityMt: 75000,
          origin: 'Hay Point (Australia)',
          destination: 'Paradip Port (India)',
        },
        vesselId,
        vesselName: 'MV OCEAN FORTUNE',
        vesselImo: '9842190',
        procurementOfficerName: 'Capt. Rajesh Sharma',
        shipOwnerName: 'Oceanic Bulk Carrier Fleet Ltd',
        freightRateUsdPerMt: 23.75,
        totalContractValueUsd: 1781250,
        status: 'REQUESTED',
        eta: '2026-09-14T08:00:00Z',
        etd: '2026-09-02T16:00:00Z',
        laycanStart: '2026-09-01',
        laycanEnd: '2026-09-05',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        offers: [],
      };
      DEMO_CHARTERS.unshift(newContract);
      return newContract;
    }
  );
}

export async function submitCharterOffer(contractId: string, offer: Partial<CharterOffer>): Promise<CharterOffer> {
  return smartFetch<CharterOffer>(
    () => apiClient.post(`/charters/${contractId}/offers`, offer),
    () => {
      const newOffer: CharterOffer = {
        id: 'ofr-' + Date.now(),
        charterRequestId: contractId,
        shipOwnerId: offer.shipOwnerId || 'usr-ship-01',
        shipOwnerName: offer.shipOwnerName || 'Oceanic Bulk Carrier Fleet Ltd',
        vesselId: offer.vesselId || 'vessel-02',
        vesselName: offer.vesselName || 'MV OCEAN FORTUNE',
        vesselType: offer.vesselType || 'Panamax',
        vesselDwt: offer.vesselDwt || 82000,
        offeredFreightRateUsdPerMt: offer.offeredFreightRateUsdPerMt || 23.75,
        totalOfferedCostUsd: (offer.offeredFreightRateUsdPerMt || 23.75) * 75000,
        laycanStartOffered: offer.laycanStartOffered || '2026-09-02',
        laycanEndOffered: offer.laycanEndOffered || '2026-09-06',
        demurrageRatePerDayUsd: offer.demurrageRatePerDayUsd || 22000,
        despatchRatePerDayUsd: offer.despatchRatePerDayUsd || 11000,
        terms: offer.terms || 'Gencon Charter Party 1994',
        status: 'PENDING',
        submittedAt: new Date().toISOString(),
      };
      const contract = DEMO_CHARTERS.find((c) => c.id === contractId);
      if (contract) {
        contract.offers.push(newOffer);
        contract.status = 'OFFERED';
      }
      return newOffer;
    }
  );
}

export async function acceptCharterOffer(contractId: string, offerId: string): Promise<CharterContract> {
  return smartFetch<CharterContract>(
    () => apiClient.post(`/charters/${contractId}/offers/${offerId}/accept`),
    () => {
      const contract = DEMO_CHARTERS.find((c) => c.id === contractId) || DEMO_CHARTERS[0];
      contract.status = 'CONTRACTED';
      const offer = contract.offers.find((o) => o.id === offerId);
      if (offer) {
        offer.status = 'ACCEPTED';
      }
      return contract;
    }
  );
}
