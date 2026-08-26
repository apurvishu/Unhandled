'use client';

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { CommodityType, VesselType } from '@/types';
import { COMMODITIES, MAJOR_PORTS, VESSEL_TYPES } from '@/config/constants';
import { Button } from '@/components/ui/Button';
import { Input, Select } from '@/components/ui/Input';
import { Sparkles, Calendar, Ship, MapPin, Layers } from 'lucide-react';

const cargoSchema = z.object({
  commodity: z.string().min(1, 'Commodity is required'),
  quantityMt: z.number().min(1000, 'Minimum 1,000 MT').max(400000, 'Maximum 400,000 MT'),
  originPortId: z.string().min(1, 'Origin port is required'),
  destinationPortId: z.string().min(1, 'Destination port is required'),
  requiredArrivalDate: z.string().min(1, 'Required arrival date is required'),
  preferredVesselType: z.string().min(1, 'Vessel type is required'),
  minDwt: z.number().min(1000, 'Invalid Min DWT'),
  maxDraft: z.number().min(5, 'Draft must be at least 5m').max(25, 'Max draft is 25m'),
  laycanStart: z.string().min(1, 'Laycan start date is required'),
  laycanEnd: z.string().min(1, 'Laycan end date is required'),
});

export type CargoFormData = z.infer<typeof cargoSchema>;

export interface CargoRequirementFormProps {
  onSubmit: (data: CargoFormData) => Promise<void>;
  isLoading?: boolean;
}

export const CargoRequirementForm: React.FC<CargoRequirementFormProps> = ({
  onSubmit,
  isLoading = false,
}) => {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<CargoFormData>({
    resolver: zodResolver(cargoSchema),
    defaultValues: {
      commodity: 'Coking Coal',
      quantityMt: 75000,
      originPortId: 'port-haypoint',
      destinationPortId: 'port-paradip',
      requiredArrivalDate: '2026-09-18',
      preferredVesselType: 'Panamax',
      minDwt: 75000,
      maxDraft: 14.5,
      laycanStart: '2026-09-01',
      laycanEnd: '2026-09-06',
    },
  });

  const selectedCommodity = watch('commodity');
  const selectedQuantity = watch('quantityMt');

  // Quick preset loader
  const loadPreset = (commodity: CommodityType, qty: number, origin: string, dest: string, vessel: VesselType) => {
    setValue('commodity', commodity);
    setValue('quantityMt', qty);
    setValue('originPortId', origin);
    setValue('destinationPortId', dest);
    setValue('preferredVesselType', vessel);
    setValue('minDwt', qty);
    setValue('maxDraft', vessel === 'Capesize' ? 18.0 : vessel === 'Panamax' ? 14.5 : 12.5);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Quick Presets for Demo */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-3.5 flex items-center justify-between flex-wrap gap-2">
        <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
          <Sparkles className="h-3.5 w-3.5 text-sky-400" />
          Quick Test Presets:
        </span>
        <div className="flex items-center gap-2 flex-wrap">
          <button
            type="button"
            onClick={() => loadPreset('Coking Coal', 75000, 'port-haypoint', 'port-paradip', 'Panamax')}
            className="px-2.5 py-1 text-xs rounded-lg bg-sky-950/40 text-sky-300 border border-sky-500/30 hover:bg-sky-900/40 transition"
          >
            Coal 75k MT (AU → Paradip)
          </button>
          <button
            type="button"
            onClick={() => loadPreset('Iron Ore', 120000, 'port-hedland', 'port-dhamra', 'Capesize')}
            className="px-2.5 py-1 text-xs rounded-lg bg-slate-800 text-slate-300 border border-slate-700 hover:bg-slate-700 transition"
          >
            Iron Ore 120k MT (AU → Dhamra)
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Commodity & Quantity */}
        <Select
          label="Bulk Commodity"
          {...register('commodity')}
          error={errors.commodity?.message}
          options={COMMODITIES.map((c) => ({ value: c, label: c }))}
        />

        <Input
          label="Quantity (Metric Tons - MT)"
          type="number"
          step={1000}
          {...register('quantityMt', { valueAsNumber: true })}
          error={errors.quantityMt?.message}
          helperText="e.g. 75,000 MT for standard Panamax bulk shipment"
        />

        {/* Origin & Destination Ports */}
        <Select
          label="Origin Port / Loading Terminal"
          {...register('originPortId')}
          error={errors.originPortId?.message}
          options={MAJOR_PORTS.map((p) => ({
            value: p.id,
            label: `${p.name} (${p.country}) - Max Depth: ${p.maxDepth}m`,
          }))}
        />

        <Select
          label="Destination Port / Discharge Terminal"
          {...register('destinationPortId')}
          error={errors.destinationPortId?.message}
          options={MAJOR_PORTS.map((p) => ({
            value: p.id,
            label: `${p.name} (${p.country}) - Max Depth: ${p.maxDepth}m`,
          }))}
        />

        {/* Preferred Vessel Type & Min DWT */}
        <Select
          label="Preferred Vessel Class"
          {...register('preferredVesselType')}
          error={errors.preferredVesselType?.message}
          options={VESSEL_TYPES.map((v) => ({ value: v, label: v }))}
        />

        <Input
          label="Minimum Deadweight Tonnage (DWT)"
          type="number"
          {...register('minDwt', { valueAsNumber: true })}
          error={errors.minDwt?.message}
        />

        {/* Max Draft & Required Arrival Date */}
        <Input
          label="Maximum Allowable Draft (Meters)"
          type="number"
          step={0.1}
          {...register('maxDraft', { valueAsNumber: true })}
          error={errors.maxDraft?.message}
          helperText="Discharge channel safety limit"
        />

        <Input
          label="Required Arrival Date"
          type="date"
          {...register('requiredArrivalDate')}
          error={errors.requiredArrivalDate?.message}
        />

        {/* Laycan Window */}
        <Input
          label="Laycan Window: Earliest Start Date"
          type="date"
          {...register('laycanStart')}
          error={errors.laycanStart?.message}
        />

        <Input
          label="Laycan Window: Latest Cancel Date"
          type="date"
          {...register('laycanEnd')}
          error={errors.laycanEnd?.message}
        />
      </div>

      <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-3">
        <Button type="submit" variant="primary" size="lg" isLoading={isLoading}>
          <Sparkles className="h-4 w-4" />
          <span>Save & Find Suitable Vessels</span>
        </Button>
      </div>
    </form>
  );
};
