'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/Button';
import { getCharters, acceptCharterOffer } from '@/services/charters';
import { CharterContract } from '@/types';
import { formatCurrency, formatDwt } from '@/lib/utils';
import { CheckCircle2, Ship, ArrowRight } from 'lucide-react';
import { BackButton } from '@/components/ui/BackButton';

export default function ChartersPage() {
  const { data: charters = [], refetch } = useQuery({
    queryKey: ['charters'],
    queryFn: getCharters,
  });

  const [isContracting, setIsContracting] = useState(false);

  const handleAcceptOffer = async (contractId: string, offerId: string) => {
    setIsContracting(true);
    await acceptCharterOffer(contractId, offerId);
    setIsContracting(false);
    refetch();
  };

  const statusPipeline = [
    'REQUESTED',
    'OFFERED',
    'NEGOTIATING',
    'SELECTED',
    'CONTRACTED',
    'IN_PROGRESS',
    'COMPLETED',
  ];

  return (
    <div className="space-y-6">
      <BackButton href="/" label="Back to Home" />

      <PageHeader
        title="Charter Contracts & Negotiation Pipeline"
        description="End-to-end charter party workflows, carrier bid comparisons, contract execution, and voyage status."
        badge={`${charters.length} Active Charters`}
        badgeVariant="default"
      />

      <div className="space-y-6">
        {charters.map((contract) => {
          const currentStatusIdx = statusPipeline.indexOf(contract.status);

          return (
            <div
              key={contract.id}
              className="bg-white border border-zinc-200 rounded p-6 shadow-sm space-y-6"
            >
              {/* Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-100 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-zinc-950 font-mono">
                      Charter Contract: {contract.id}
                    </h3>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-zinc-900 text-white">
                      {contract.status}
                    </span>
                  </div>
                  <p className="text-xs text-zinc-500 mt-1">
                    Cargo: <strong className="text-zinc-800 font-mono">{formatDwt(contract.cargoSummary.quantityMt)} {contract.cargoSummary.commodity}</strong> • {contract.cargoSummary.origin} → {contract.cargoSummary.destination}
                  </p>
                </div>

                <div className="text-right">
                  <span className="text-[10px] text-zinc-400 uppercase font-mono block">Total Contract Value</span>
                  <span className="text-lg font-bold text-zinc-950 font-mono">
                    {formatCurrency(contract.totalContractValueUsd)}
                  </span>
                  <span className="text-[11px] text-zinc-500 font-mono block">(${contract.freightRateUsdPerMt}/MT)</span>
                </div>
              </div>

              {/* Status Pipeline */}
              <div className="space-y-2">
                <span className="text-[10px] font-bold uppercase text-zinc-400 tracking-wider font-mono">
                  Lifecycle Progress:
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-7 gap-1 text-center text-[10px] font-mono font-medium">
                  {statusPipeline.map((step, idx) => {
                    const isPassed = idx <= currentStatusIdx;
                    const isCurrent = idx === currentStatusIdx;

                    return (
                      <div
                        key={step}
                        className={`p-2 rounded border transition ${
                          isCurrent
                            ? 'bg-zinc-900 border-zinc-900 text-white font-bold'
                            : isPassed
                            ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
                            : 'bg-zinc-50 border-zinc-200 text-zinc-400'
                        }`}
                      >
                        {step}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Vessel & Parties Details */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3.5 rounded bg-zinc-50 border border-zinc-200 text-xs font-mono">
                <div>
                  <span className="text-[10px] text-zinc-400 uppercase block font-sans">Nominated Vessel:</span>
                  <strong className="text-zinc-950">{contract.vesselName}</strong>
                </div>
                <div>
                  <span className="text-[10px] text-zinc-400 uppercase block font-sans">Ship Owner:</span>
                  <span className="text-zinc-800">{contract.shipOwnerName}</span>
                </div>
                <div>
                  <span className="text-[10px] text-zinc-400 uppercase block font-sans">Procurement Officer:</span>
                  <span className="text-zinc-800">{contract.procurementOfficerName}</span>
                </div>
                <div>
                  <span className="text-[10px] text-zinc-400 uppercase block font-sans">Agreed Laycan:</span>
                  <span className="text-zinc-800">{contract.laycanStart} to {contract.laycanEnd}</span>
                </div>
              </div>

              {/* Received Ship Owner Offers */}
              {contract.offers && contract.offers.length > 0 && (
                <div className="space-y-3 pt-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-500 font-mono">
                    Received Carrier Bids ({contract.offers.length})
                  </h4>

                  <div className="space-y-2">
                    {contract.offers.map((offer) => (
                      <div
                        key={offer.id}
                        className="p-4 rounded bg-zinc-50 border border-zinc-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs font-mono"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-zinc-950">{offer.shipOwnerName}</span>
                            <span className="text-zinc-500">({offer.vesselName})</span>
                          </div>
                          <p className="text-zinc-600 text-[11px]">
                            Offered Rate: <strong className="text-zinc-950 font-bold">${offer.offeredFreightRateUsdPerMt}/MT</strong> • Total: <strong className="text-zinc-950">{formatCurrency(offer.totalOfferedCostUsd)}</strong> • Laycan: {offer.laycanStartOffered} to {offer.laycanEndOffered}
                          </p>
                          <p className="text-zinc-400 text-[10px] font-sans">
                            Terms: {offer.terms} • Demurrage: ${offer.demurrageRatePerDayUsd}/day
                          </p>
                        </div>

                        <div className="flex items-center gap-2 shrink-0 font-sans">
                          {contract.status === 'CONTRACTED' ? (
                            <span className="px-3 py-1.5 rounded bg-emerald-50 text-emerald-900 border border-emerald-300 font-semibold flex items-center gap-1.5 text-xs">
                              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-700" /> Contract Signed
                            </span>
                          ) : (
                            <Button
                              variant="primary"
                              size="sm"
                              onClick={() => handleAcceptOffer(contract.id, offer.id)}
                              isLoading={isContracting}
                            >
                              <CheckCircle2 className="h-3.5 w-3.5" />
                              <span>Accept & Execute</span>
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Navigation to Voyage Tracking */}
              {contract.status === 'CONTRACTED' && (
                <div className="pt-2 flex items-center justify-end">
                  <Link href="/voyages">
                    <Button variant="primary" size="sm">
                      <Ship className="h-3.5 w-3.5" />
                      <span>Track Active Voyage</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Button>
                  </Link>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
