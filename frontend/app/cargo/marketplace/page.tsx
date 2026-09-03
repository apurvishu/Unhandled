'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { getCargoRequirements } from '@/services/cargo';
import { CargoRequirement } from '@/types';
import { formatCurrency, formatDwt } from '@/lib/utils';
import { Package, Send, CheckCircle2, ArrowRight } from 'lucide-react';
import { BackButton } from '@/components/ui/BackButton';

export default function CargoMarketplacePage() {
  const { data: requirements = [] } = useQuery({
    queryKey: ['cargoRequirements'],
    queryFn: getCargoRequirements,
  });

  const [selectedCargo, setSelectedCargo] = useState<CargoRequirement | null>(null);
  const [bidRate, setBidRate] = useState<number>(23.8);
  const [vesselName, setVesselName] = useState('MV PACIFIC STAR');
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleOpenBid = (cargo: CargoRequirement) => {
    setSelectedCargo(cargo);
    const rate = cargo.targetFreightRateUsdPerMt || 24.5;
    setBidRate(rate - 0.5);
    setIsSubmitted(false);
  };

  const handleSendBid = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitted(true);
    setTimeout(() => {
      setSelectedCargo(null);
      setIsSubmitted(false);
    }, 1500);
  };

  return (
    <div className="space-y-6">
      <BackButton href="/" label="Back to Home" />

      <PageHeader
        title="Cargo Opportunity Marketplace & Tender Board"
        description="Public and private bulk cargo tenders seeking spot and time-charter carrier bids."
        badge={`${requirements.length} Open Tenders`}
        badgeVariant="default"
      />

      {/* Tenders Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {requirements.map((req) => {
          const targetRate = req.targetFreightRateUsdPerMt || 24.5;

          return (
            <div
              key={req.id}
              className="bg-white border border-zinc-200 rounded p-5 shadow-sm space-y-4 hover:border-zinc-300 transition flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-zinc-950 font-mono">{req.commodity}</h3>
                    <p className="text-xs text-zinc-500 font-mono">Tender ID: {req.id}</p>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-zinc-100 text-zinc-800 border border-zinc-200">
                    {req.status}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 p-3 bg-zinc-50 border border-zinc-200 rounded text-xs font-mono">
                  <div>
                    <span className="text-[10px] text-zinc-400 block uppercase font-sans">Volume:</span>
                    <strong className="text-zinc-900">{formatDwt(req.quantityMt)}</strong>
                  </div>
                  <div>
                    <span className="text-[10px] text-zinc-400 block uppercase font-sans">Target Budget:</span>
                    <strong className="text-zinc-900">${targetRate}/MT</strong>
                  </div>
                  <div>
                    <span className="text-[10px] text-zinc-400 block uppercase font-sans">Load Terminal:</span>
                    <span className="text-zinc-800 font-sans truncate block">{req.originPortName}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-zinc-400 block uppercase font-sans">Discharge Port:</span>
                    <span className="text-zinc-800 font-sans truncate block">{req.destinationPortName}</span>
                  </div>
                </div>

                <div className="text-xs font-mono text-zinc-600">
                  Laycan: <strong>{req.laycanStart}</strong> to <strong>{req.laycanEnd}</strong>
                </div>
              </div>

              <div className="pt-3 border-t border-zinc-100 flex items-center justify-between">
                <span className="text-xs font-mono text-zinc-500">
                  Total Budget: <strong className="text-zinc-950">${(req.quantityMt * targetRate).toLocaleString()}</strong>
                </span>

                <Button variant="primary" size="sm" onClick={() => handleOpenBid(req)}>
                  <span>Submit Carrier Bid</span>
                  <Send className="h-3 w-3" />
                </Button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Bid Submission Modal */}
      {selectedCargo && (
        <Modal
          isOpen={!!selectedCargo}
          onClose={() => setSelectedCargo(null)}
          title={`Submit Carrier Bid • ${selectedCargo.commodity}`}
          description={`Tender ID: ${selectedCargo.id} • ${formatDwt(selectedCargo.quantityMt)}`}
        >
          {isSubmitted ? (
            <div className="py-8 text-center space-y-3">
              <div className="h-10 w-10 bg-emerald-50 border border-emerald-300 text-emerald-800 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle2 className="h-6 w-6" />
              </div>
              <h4 className="text-sm font-bold text-zinc-950">Charter Bid Submitted</h4>
              <p className="text-xs text-zinc-500">
                Your offer of ${bidRate}/MT with {vesselName} has been transmitted to the procurement officer.
              </p>
            </div>
          ) : (
            <form onSubmit={handleSendBid} className="space-y-4">
              <Input
                label="Nominated Vessel"
                value={vesselName}
                onChange={(e) => setVesselName(e.target.value)}
                required
              />

              <Input
                label="Offered Freight Rate (USD / MT)"
                type="number"
                step="0.1"
                value={bidRate}
                onChange={(e) => setBidRate(Number(e.target.value))}
                required
              />

              <div className="p-3 bg-zinc-50 border border-zinc-200 rounded text-xs space-y-1 font-mono">
                <div className="flex justify-between text-zinc-600">
                  <span>Client Target Rate:</span>
                  <span>${selectedCargo.targetFreightRateUsdPerMt || 24.5}/MT</span>
                </div>
                <div className="flex justify-between text-zinc-950 font-bold border-t border-zinc-200 pt-1">
                  <span>Total Bid Contract Value:</span>
                  <span>{formatCurrency(selectedCargo.quantityMt * bidRate)}</span>
                </div>
              </div>

              <div className="pt-3 border-t border-zinc-200 flex items-center justify-end gap-2">
                <Button variant="secondary" size="md" onClick={() => setSelectedCargo(null)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="md">
                  Submit Binding Offer
                </Button>
              </div>
            </form>
          )}
        </Modal>
      )}
    </div>
  );
}
