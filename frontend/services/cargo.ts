import { apiClient, smartFetch } from '@/lib/api';
import { CargoRequirement } from '@/types';
import { DEMO_CARGO_REQUIREMENTS } from '@/lib/demoData';

export async function getCargoRequirements(): Promise<CargoRequirement[]> {
  return smartFetch<CargoRequirement[]>(
    () => apiClient.get('/cargo'),
    () => DEMO_CARGO_REQUIREMENTS
  );
}

export async function getCargoRequirementById(id: string): Promise<CargoRequirement | undefined> {
  return smartFetch<CargoRequirement | undefined>(
    () => apiClient.get(`/cargo/${id}`),
    () => DEMO_CARGO_REQUIREMENTS.find((c) => c.id === id) || DEMO_CARGO_REQUIREMENTS[0]
  );
}

export async function createCargoRequirement(
  data: Omit<CargoRequirement, 'id' | 'createdAt' | 'status'>
): Promise<CargoRequirement> {
  return smartFetch<CargoRequirement>(
    () => apiClient.post('/cargo', data),
    () => {
      const newCargo: CargoRequirement = {
        ...data,
        id: 'req-' + Date.now(),
        status: 'MATCHING',
        createdAt: new Date().toISOString(),
      };
      DEMO_CARGO_REQUIREMENTS.unshift(newCargo);
      return newCargo;
    }
  );
}
