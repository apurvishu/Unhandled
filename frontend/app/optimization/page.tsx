'use client';

import React, { Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { DecisionRecommendation } from '@/components/dashboard/DecisionRecommendation';
import { CostBreakdownChart } from '@/components/charts/CostBreakdownChart';
import { VesselComparisonTable } from '@/components/vessels/VesselComparisonTable';
import { Button } from '@/components/ui/Button';
import { getOptimizationRecommendation } from '@/services/optimization';
import { formatCurrency, formatDwt } from '@/lib/utils';
import { Sparkles, Scale, FileText, ArrowRight, ShieldCheck, DollarSign, Clock, Ship } from 'lucide-react';

function OptimizationContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const cargoId = searchParams.get('cargoId') || 'req-coal-75k';

  const { data: optimizationData, isLoading } = useQuery({
    queryKey: ['optimizationRecommendation', cargoId],
    queryFn: () => getOptimizationRecommendation(cargoId),
  });

  if (!optimizationData) {
    return <div className="p-8 text-slate-400">Loading AI Optimization Recommendation...</div>;
  }

  const { recommendedVessel, alternativeVessels, cargoRequirement, aiRecommendation } = optimizationData;
  const allMatches = [recommendedVessel, ...alternativeVessels];

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <PageHeader
        title="AI Charter Optimization & Decision Engine"
        description="Holistic multi-objective optimization reconciling freight forecasting, vessel ballast positions, discharge port congestion, and bunker fuel consumption."
        badge="Multi-Objective ML Engine"
        badgeVariant="success"
      >
        <Link href="/charters/compare">
          <Button variant="secondary" size="md">
            <Scale className="h-4 w-4" />
            <span>Full Vessel Comparison Matrix</span>
          </Button>
        </Link>
      </PageHeader>

      {/* CORE DECISION RECOMMENDATION COMPONENT */}
      <section>
        <DecisionRecommendation
          data={optimizationData}
          onRequestOffer={(vesselMatch) => {
            router.push(`/charters?createForCargo=${cargoId}&vesselId=${vesselMatch.vessel.id}`);
          }}
        />
      </section>

      {/* COST BREAKDOWN SECTION */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="space-y-3">
          <CostBreakdownChart breakdown={recommendedVessel.costBreakdown} height={280} />
        </section>

        <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2 pb-3 border-b border-slate-800">
              <DollarSign className="h-4 w-4 text-emerald-400" />
              <span>Comprehensive Cost Analysis Summary</span>
            </h3>

            <div className="space-y-3 my-4 text-xs">
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                <span className="text-slate-400">Base Freight (75,000 MT @ ${recommendedVessel.freightRateUsdPerMt}/MT):</span>
                <strong className="text-white font-mono">{formatCurrency(recommendedVessel.costBreakdown.freightCost)}</strong>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                <span className="text-slate-400">Estimated Bunker Fuel (VLSFO Singapore):</span>
                <strong className="text-white font-mono">{formatCurrency(recommendedVessel.costBreakdown.bunkerFuelCost)}</strong>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                <span className="text-slate-400">Port Dues, Pilotage & Berth Charges:</span>
                <strong className="text-white font-mono">{formatCurrency(recommendedVessel.costBreakdown.portCosts)}</strong>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                <span className="text-slate-400">Estimated Demurrage / Anchorage Risk:</span>
                <strong className="text-amber-400 font-mono">{formatCurrency(recommendedVessel.costBreakdown.demurrageWaitingRiskCost)}</strong>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
            <div>
              <span className="text-[10px] text-slate-400 uppercase block font-semibold">Total Estimated Voyage Outlay:</span>
              <span className="text-2xl font-black text-emerald-400 font-mono">
                {formatCurrency(recommendedVessel.estimatedTotalCostUsd)}
              </span>
            </div>

            <Button
              variant="primary"
              size="md"
              className="font-bold"
              onClick={() => {
                router.push(`/charters?createForCargo=${cargoId}&vesselId=${recommendedVessel.vessel.id}`);
              }}
            >
              <span>Execute Charter Request</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </section>
      </div>

      {/* MULTI-VESSEL COMPARISON MATRIX */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Scale className="h-4 w-4 text-sky-400" />
            <span>Alternative Vessel Candidate Comparison</span>
          </h3>
          <span className="text-xs text-slate-400">Evaluated 3 candidates against cargo requirements</span>
        </div>

        <VesselComparisonTable
          matches={allMatches}
          onRequestOffer={(m) => {
            router.push(`/charters?createForCargo=${cargoId}&vesselId=${m.vessel.id}`);
          }}
        />
      </section>
    </div>
  );
}

export default function OptimizationPage() {
  return (
    <Suspense fallback={<div className="p-8 text-slate-400">Loading AI Charter Optimization...</div>}>
      <OptimizationContent />
    </Suspense>
  );
}
