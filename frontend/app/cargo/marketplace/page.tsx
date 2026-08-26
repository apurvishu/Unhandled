'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { getCargoRequirements } from '@/services/cargo';
import { submitCharterOffer } from '@/services/charters';
import { CargoRequirement } from '@/types';
import { formatCurrency, formatDwt } from '@/lib/utils';
import { Boxes, Sparkles, Send, CheckCircle2, Calendar, MapPin, DollarSign } from 'lucide-react';

export default function CargoMarketplacePage() {
  const { data: cargoList = [] } = useQuery({
    queryKey: ['cargoRequirements'],
    queryFn: getCargoRequirements,
  });

  const [selectedCargo, setSelectedCargo] = useState<CargoRequirement | null>(null);
  const [freightQuote, setFreightQuote] = useState('23.75');
  const [laycanStart, setLaycanStart] = useState('2026-09-02');
  const [laycanEnd, setLaycanEnd] = useState('2026-09-06');
  const [isSuccess, setIsSuccess] = useState(false);

  const handleSubmitOffer = async () => {
    if (!selectedCargo) return;
    await submitCharterOffer('ctr-2026-089', {
      offeredFreightRateUsdPerMt: parseFloat(freightQuote),
      laycanStartOffered: laycanStart,
      laycanEndOffered: laycanEnd,
    });
    setIsSuccess(true);
    setTimeout(() => {
      setIsSuccess(false);
      setSelectedCargo(null);
    }, 2000);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <PageHeader
        title="Cargo Opportunity Marketplace"
        description="Browse open bulk procurement tenders matching your fleet capacity and submit charter bids directly."
        badge="Carrier Marketplace"
        badgeVariant="success"
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {cargoList.map((cargo) => (
          <div
            key={cargo.id}
            className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4 hover:border-slate-700 transition"
          >
            <div className="flex items-start justify-between">
              <div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-sky-500/20 text-sky-300 border border-sky-500/30">
                  {cargo.preferredVesselType} Preferred
                </span>
                <h3 className="text-xl font-extrabold text-white mt-2">
                  {formatDwt(cargo.quantityMt)} {cargo.commodity}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">Tender ID: {cargo.id}</p>
              </div>

              <div className="text-right">
                <span className="text-[10px] text-slate-400 uppercase font-semibold block">Est. Market Freight</span>
                <span className="text-lg font-black text-emerald-400 font-mono">$23.50 – $24.80</span>
                <span className="text-[10px] text-slate-400 block">/ MT</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 text-xs">
              <div>
                <span className="text-slate-400 block text-[10px] uppercase">Route:</span>
                <strong className="text-slate-200">
                  {cargo.originPortName.split(' ')[0]} → {cargo.destinationPortName.split(' ')[0]}
                </strong>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase">Required Laycan:</span>
                <strong className="text-slate-200">{cargo.laycanStart} to {cargo.laycanEnd}</strong>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase">Max Discharge Draft:</span>
                <span className="text-slate-200 font-semibold">{cargo.maxDraft}m</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px] uppercase">Procurement Officer:</span>
                <span className="text-slate-200">{cargo.procurementOfficerName}</span>
              </div>
            </div>

            <div className="pt-2 flex items-center justify-between">
              <span className="text-xs text-emerald-400 font-medium flex items-center gap-1">
                <CheckCircle2 className="h-3.5 w-3.5" /> MV OCEAN FORTUNE is compatible
              </span>

              <Button
                variant="primary"
                size="sm"
                className="font-bold"
                onClick={() => setSelectedCargo(cargo)}
              >
                <Send className="h-3.5 w-3.5" />
                <span>Submit Charter Bid</span>
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* Submit Offer Modal */}
      {selectedCargo && (
        <Modal
          isOpen={!!selectedCargo}
          onClose={() => setSelectedCargo(null)}
          title="Submit Charter Offer"
          description={`Tender: ${selectedCargo.quantityMt.toLocaleString()} MT ${selectedCargo.commodity} (${selectedCargo.originPortName.split(' ')[0]} → ${selectedCargo.destinationPortName.split(' ')[0]})`}
        >
          {isSuccess ? (
            <div className="py-8 text-center space-y-3">
              <div className="h-12 w-12 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
                <CheckCircle2 className="h-6 w-6" />
              </div>
              <h4 className="text-lg font-bold text-white">Charter Offer Submitted!</h4>
              <p className="text-xs text-slate-400">
                Your quote of ${freightQuote}/MT has been delivered to the procurement officer.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs flex items-center justify-between">
                <div>
                  <span className="text-slate-400 block">Deploying Vessel:</span>
                  <strong className="text-sky-300 text-sm">MV OCEAN FORTUNE (Panamax, 82,000 DWT)</strong>
                </div>
                <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  Ready & Available
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input
                  label="Freight Rate Quote ($/MT)"
                  type="number"
                  step="0.05"
                  value={freightQuote}
                  onChange={(e) => setFreightQuote(e.target.value)}
                  leftIcon={<DollarSign className="h-4 w-4" />}
                  helperText={`Est. Total Value: ${formatCurrency(parseFloat(freightQuote || '0') * selectedCargo.quantityMt)}`}
                  required
                />

                <Input
                  label="Offered Laycan Start"
                  type="date"
                  value={laycanStart}
                  onChange={(e) => setLaycanStart(e.target.value)}
                  required
                />
              </div>

              <Input
                label="Offered Laycan Cancel Date"
                type="date"
                value={laycanEnd}
                onChange={(e) => setLaycanEnd(e.target.value)}
                required
              />

              <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-3">
                <Button variant="secondary" size="md" onClick={() => setSelectedCargo(null)}>
                  Cancel
                </Button>
                <Button variant="primary" size="md" onClick={handleSubmitOffer} className="font-bold">
                  <Send className="h-4 w-4" />
                  <span>Transmit Official Offer</span>
                </Button>
              </div>
            </div>
          )}
        </Modal>
      )}
    </div>
  );
}
