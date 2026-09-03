'use client';

import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { DecisionRecommendation } from '@/components/dashboard/DecisionRecommendation';
import { CostBreakdownChart } from '@/components/charts/CostBreakdownChart';
import { VesselComparisonTable } from '@/components/vessels/VesselComparisonTable';
import { Button } from '@/components/ui/Button';
import { getOptimizationRecommendation, matchVessels } from '@/services/optimization';
import { formatCurrency, formatDwt } from '@/lib/utils';
import { ArrowRight } from 'lucide-react';
import { BackButton } from '@/components/ui/BackButton';

export default function OptimizationPage() {
  const router = useRouter();
  const cargoId = 'req-coal-75k';

  const { data: recommendation } = useQuery({
    queryKey: ['optimizationRecommendation', cargoId],
    queryFn: () => getOptimizationRecommendation(cargoId),
  });

  const { data: matches = [] } = useQuery({
    queryKey: ['vesselMatches', cargoId],
    queryFn: () => matchVessels(cargoId),
  });

  if (!recommendation) {
    return <div className="p-8 text-xs font-mono text-zinc-500">Evaluating multi-objective optimization engine...</div>;
  }

  const costSummary = (recommendation as any).costSummary || {
    totalOutlayUsd: recommendation.recommendedVessel?.estimatedTotalCostUsd || 1781250,
    baseFreightCostUsd: recommendation.recommendedVessel?.costBreakdown?.freightCost || 1781250,
    bunkerFuelCostUsd: recommendation.recommendedVessel?.costBreakdown?.bunkerFuelCost || 284000,
    portDuesAndHandlingUsd: recommendation.recommendedVessel?.costBreakdown?.portCosts || 62000,
    canalAndTollsUsd: recommendation.recommendedVessel?.costBreakdown?.otherVoyageCost || 18000,
    demurrageRiskCostUsd: recommendation.recommendedVessel?.costBreakdown?.demurrageWaitingRiskCost || 24000,
    freightRateUsdPerMt: recommendation.recommendedVessel?.freightRateUsdPerMt || 23.75,
    cargoQuantityMt: recommendation.cargoRequirement?.quantityMt || 75000,
    potentialSavingsUsd: recommendation.aiRecommendation?.potentialSavingsUsd || 78750,
  };

  return (
    <div className="space-y-8">
      <BackButton href="/" label="Back to Home" />

      <PageHeader
        title="AI Charter Optimization & Decision Engine"
        description="Multi-objective Pareto optimization reconciling AIS ballast locations, draft bathymetry, bunker fuel burn, and ML timing signals."
        badge="Autonomous Decision Engine"
        badgeVariant="default"
      >
        <Link href="/charters">
          <Button variant="outline" size="md">
            <span>View Active Charters</span>
            <ArrowRight className="h-4 w-4" />
          </Button>
        </Link>
      </PageHeader>

      {/* Primary Decision Banner */}
      <section>
        <DecisionRecommendation
          data={recommendation}
          onRequestOffer={(vesselMatch) => {
            router.push(`/charters?createForCargo=${cargoId}&vesselId=${vesselMatch.vessel.id}`);
          }}
        />
      </section>

      {/* Itemized Outlay Cost Breakdown */}
      <section className="bg-white border border-zinc-200 rounded p-6 space-y-4 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-zinc-100">
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-950 font-mono">
              Itemized Voyage Outlay Cost Model
            </h3>
            <p className="text-xs text-zinc-500">
              Total Estimated Voyage Cost: <strong className="text-zinc-950 font-mono">{formatCurrency(costSummary.totalOutlayUsd)}</strong> (${costSummary.freightRateUsdPerMt}/MT on {formatDwt(costSummary.cargoQuantityMt)})
            </p>
          </div>
          <span className="text-xs font-mono text-emerald-800 font-bold bg-emerald-50 border border-emerald-300 px-2 py-1 rounded">
            Projected Savings: {formatCurrency(costSummary.potentialSavingsUsd)}
          </span>
        </div>

        <CostBreakdownChart costSummary={costSummary} />
      </section>

      {/* Candidate Vessel Comparison Table */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 font-mono">
            Candidate Vessels Evaluated by Engine ({matches.length})
          </h3>
          <span className="text-xs font-mono text-zinc-500">Ranked by Multi-Objective Score</span>
        </div>

        <VesselComparisonTable
          matches={matches}
          onRequestOffer={(m) => {
            router.push(`/charters?createForCargo=${cargoId}&vesselId=${m.vessel.id}`);
          }}
        />
      </section>
    </div>
  );
}
