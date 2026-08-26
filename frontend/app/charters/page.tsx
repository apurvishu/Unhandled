'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Card';
import { getCharters, acceptCharterOffer } from '@/services/charters';
import { CharterContract, CharterOffer } from '@/types';
import { formatCurrency, formatDwt, getStatusBadgeColor } from '@/lib/utils';
import { FileText, CheckCircle2, Clock, Ship, ArrowRight, DollarSign, Send } from 'lucide-react';

export default function ChartersPage() {
  const { data: charters = [], refetch } = useQuery({
    queryKey: ['charters'],
    queryFn: getCharters,
  });

  const [selectedContract, setSelectedContract] = useState<CharterContract | null>(null);
  const [isContracting, setIsContracting] = useState(false);

  const handleAcceptOffer = async (contractId: string, offerId: string) => {
    setIsContracting(true);
    await acceptCharterOffer(contractId, offerId);
    setIsContracting(false);
    setSelectedContract(null);
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
    <div className="space-y-6 animate-in fade-in duration-300">
      <PageHeader
        title="Charter Contracts & Negotiation Pipeline"
        description="End-to-end charter party workflows, ship owner bid comparisons, contract execution, and voyage status."
        badge={`${charters.length} Active Charters`}
        badgeVariant="info"
      />

      {/* PIPELINE CARDS */}
      <div className="space-y-6">
        {charters.map((contract) => {
          const currentStatusIdx = statusPipeline.indexOf(contract.status);

          return (
            <div
              key={contract.id}
              className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6 hover:border-slate-700 transition"
            >
              {/* Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-bold text-white">
                      Charter Contract: {contract.id}
                    </h3>
                    <span className="px-2.5 py-0.5 rounded text-[10px] font-bold uppercase bg-sky-500/20 text-sky-300 border border-sky-500/30">
                      {contract.status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    Cargo: <strong className="text-slate-200">{formatDwt(contract.cargoSummary.quantityMt)} {contract.cargoSummary.commodity}</strong> • {contract.cargoSummary.origin} → {contract.cargoSummary.destination}
                  </p>
                </div>

                <div className="text-right">
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block">Total Contract Value</span>
                  <span className="text-xl font-black text-emerald-400 font-mono">
                    {formatCurrency(contract.totalContractValueUsd)}
                  </span>
                  <span className="text-[11px] text-slate-400 font-mono block">(${contract.freightRateUsdPerMt}/MT)</span>
                </div>
              </div>

              {/* Status Timeline Progress Bar */}
              <div className="space-y-2">
                <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider">
                  Charter Lifecycle Status:
                </span>
                <div className="grid grid-cols-2 sm:grid-cols-7 gap-1 text-center text-[10px] font-bold">
                  {statusPipeline.map((step, idx) => {
                    const isPassed = idx <= currentStatusIdx;
                    const isCurrent = idx === currentStatusIdx;

                    return (
                      <div
                        key={step}
                        className={`p-2 rounded-lg border transition ${
                          isCurrent
                            ? 'bg-sky-500/20 border-sky-400 text-sky-300 font-extrabold'
                            : isPassed
                            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                            : 'bg-slate-950/40 border-slate-800 text-slate-500'
                        }`}
                      >
                        {step}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Vessel & Parties Details */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 text-xs text-slate-300">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase block">Nominated Vessel:</span>
                  <strong className="text-white text-sm">{contract.vesselName}</strong>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase block">Ship Owner:</span>
                  <span className="text-slate-200">{contract.shipOwnerName}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase block">Procurement Officer:</span>
                  <span className="text-slate-200">{contract.procurementOfficerName}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase block">Agreed Laycan:</span>
                  <span className="text-slate-200">{contract.laycanStart} to {contract.laycanEnd}</span>
                </div>
              </div>

              {/* Received Ship Owner Offers & Actions */}
              {contract.offers && contract.offers.length > 0 && (
                <div className="space-y-3 pt-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                    Received Charter Bids ({contract.offers.length})
                  </h4>

                  <div className="space-y-2">
                    {contract.offers.map((offer) => (
                      <div
                        key={offer.id}
                        className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-white text-sm">{offer.shipOwnerName}</span>
                            <span className="text-sky-300 font-mono font-semibold">({offer.vesselName})</span>
                          </div>
                          <p className="text-slate-400 text-[11px]">
                            Offered Rate: <strong className="text-emerald-400 font-mono text-xs">${offer.offeredFreightRateUsdPerMt}/MT</strong> • Total: <strong className="text-slate-200 font-mono">{formatCurrency(offer.totalOfferedCostUsd)}</strong> • Laycan: {offer.laycanStartOffered} to {offer.laycanEndOffered}
                          </p>
                          <p className="text-slate-500 text-[10px]">
                            Terms: {offer.terms} • Demurrage: ${offer.demurrageRatePerDayUsd}/day
                          </p>
                        </div>

                        <div className="flex items-center gap-2 shrink-0">
                          {contract.status === 'CONTRACTED' ? (
                            <span className="px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-bold flex items-center gap-1.5">
                              <CheckCircle2 className="h-4 w-4" /> Contract Signed
                            </span>
                          ) : (
                            <Button
                              variant="success"
                              size="sm"
                              className="font-bold"
                              onClick={() => handleAcceptOffer(contract.id, offer.id)}
                              isLoading={isContracting}
                            >
                              <CheckCircle2 className="h-3.5 w-3.5" />
                              <span>Accept & Execute Contract</span>
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Navigation to Voyage Tracking once contracted */}
              {contract.status === 'CONTRACTED' && (
                <div className="pt-2 flex items-center justify-end">
                  <Link href="/voyages">
                    <Button variant="primary" size="sm">
                      <Ship className="h-3.5 w-3.5" />
                      <span>Track Active Voyage in Real-Time</span>
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
