'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Input, Select } from '@/components/ui/Input';
import { COMMODITY_TYPES, VESSEL_TYPES } from '@/config/constants';
import { CommodityType, VesselType } from '@/types';
import { ArrowRight, Sparkles } from 'lucide-react';

interface CargoRequirementFormProps {
  onSubmit: (data: any) => void;
  isLoading?: boolean;
}

export const CargoRequirementForm: React.FC<CargoRequirementFormProps> = ({
  onSubmit,
  isLoading = false,
}) => {
  const [commodity, setCommodity] = useState<CommodityType>('Coking Coal');
  const [quantityMt, setQuantityMt] = useState<number>(75000);
  const [originPort, setOriginPort] = useState('Hay Point, Australia');
  const [destinationPort, setDestinationPort] = useState('Paradip Port, India');
  const [laycanStart, setLaycanStart] = useState('2026-09-15');
  const [laycanEnd, setLaycanEnd] = useState('2026-09-22');
  const [targetRate, setTargetRate] = useState<number>(24.5);
  const [preferredVesselType, setPreferredVesselType] = useState<VesselType>('Panamax');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      commodity,
      quantityMt,
      originPortName: originPort,
      destinationPortName: destinationPort,
      laycanStart,
      laycanEnd,
      targetFreightRateUsdPerMt: targetRate,
      preferredVesselType,
    });
  };

  const handleQuickPreset = (presetType: 'coal' | 'iron_ore' | 'grain') => {
    if (presetType === 'coal') {
      setCommodity('Coking Coal');
      setQuantityMt(75000);
      setOriginPort('Hay Point, Australia');
      setDestinationPort('Paradip Port, India');
      setTargetRate(24.5);
      setPreferredVesselType('Panamax');
    } else if (presetType === 'iron_ore') {
      setCommodity('Iron Ore');
      setQuantityMt(160000);
      setOriginPort('Port Hedland, Australia');
      setDestinationPort('Visakhapatnam, India');
      setTargetRate(18.2);
      setPreferredVesselType('Capesize');
    } else if (presetType === 'grain') {
      setCommodity('Grain / Wheat');
      setQuantityMt(55000);
      setOriginPort('Santos, Brazil');
      setDestinationPort('Haldia, India');

      setTargetRate(38.0);
      setPreferredVesselType('Supramax');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white border border-zinc-200 rounded p-6 shadow-sm space-y-6">
      {/* Quick Presets */}
      <div className="flex items-center justify-between pb-4 border-b border-zinc-100 flex-wrap gap-2">
        <div className="text-xs font-bold uppercase tracking-wider text-zinc-500 font-mono">
          Quick Cargo Presets
        </div>
        <div className="flex items-center gap-1.5">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => handleQuickPreset('coal')}
          >
            75k MT Coal (Australia → Paradip)
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => handleQuickPreset('iron_ore')}
          >
            160k MT Ore (Hedland → Vizag)
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Select
          label="Bulk Commodity"
          value={commodity}
          onChange={(e) => setCommodity(e.target.value as CommodityType)}
          options={COMMODITY_TYPES.map((c) => ({ value: c, label: c }))}
        />

        <Input
          label="Quantity (Metric Tons)"
          type="number"
          step="1000"
          value={quantityMt}
          onChange={(e) => setQuantityMt(Number(e.target.value))}
          required
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Origin / Loading Terminal"
          value={originPort}
          onChange={(e) => setOriginPort(e.target.value)}
          required
        />

        <Input
          label="Discharge Port"
          value={destinationPort}
          onChange={(e) => setDestinationPort(e.target.value)}
          required
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Laycan Window Start"
          type="date"
          value={laycanStart}
          onChange={(e) => setLaycanStart(e.target.value)}
          required
        />

        <Input
          label="Laycan Window End"
          type="date"
          value={laycanEnd}
          onChange={(e) => setLaycanEnd(e.target.value)}
          required
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Input
          label="Target Freight Budget ($/MT)"
          type="number"
          step="0.1"
          value={targetRate}
          onChange={(e) => setTargetRate(Number(e.target.value))}
          required
        />

        <Select
          label="Preferred Vessel Class"
          value={preferredVesselType}
          onChange={(e) => setPreferredVesselType(e.target.value as VesselType)}
          options={VESSEL_TYPES.map((t) => ({ value: t, label: t }))}
        />
      </div>

      <div className="pt-4 border-t border-zinc-200 flex items-center justify-between">
        <span className="text-xs text-zinc-500 font-mono">
          Est. Total Cargo Outlay: <strong className="text-zinc-950">${(quantityMt * targetRate).toLocaleString()}</strong>
        </span>

        <Button type="submit" variant="primary" size="md" isLoading={isLoading}>
          <span>Run AI Optimization Match</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </Button>
      </div>
    </form>
  );
};
