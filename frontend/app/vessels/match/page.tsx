'use client';

import React, { Suspense, useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { VesselCard } from '@/components/vessels/VesselCard';
import { DecisionRecommendation } from '@/components/dashboard/DecisionRecommendation';
import { AisVesselMap } from '@/components/maps/AisVesselMap';
import { Button } from '@/components/ui/Button';
import { matchVessels, getOptimizationRecommendation } from '@/services/optimization';
import { ArrowLeft, Scale, SlidersHorizontal, Ship } from 'lucide-react';

function VesselMatchContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const cargoId = searchParams.get('cargoId') || 'req-coal-75k';

  const [sortBy, setSortBy] = useState<'score' | 'freight' | 'eta' | 'distance'>('score');

  const { data: matches = [] } = useQuery({
    queryKey: ['vesselMatches', cargoId],
    queryFn: () => matchVessels(cargoId),
  });

  const { data: optimizationData } = useQuery({
    queryKey: ['optimizationRecommendation', cargoId],
    queryFn: () => getOptimizationRecommendation(cargoId),
  });

  const sortedMatches = [...matches].sort((a, b) => {
    if (sortBy === 'score') return b.matchScorePercent - a.matchScorePercent;
    if (sortBy === 'freight') return a.freightRateUsdPerMt - b.freightRateUsdPerMt;
    if (sortBy === 'distance') return a.distanceNauticalMiles - b.distanceNauticalMiles;
    return 0;
  });

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-2">
        <Link href="/cargo">
          <Button variant="ghost" size="sm" className="text-zinc-500">
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Cargo Requirements</span>
          </Button>
        </Link>
      </div>

      <PageHeader
        title="AI Vessel Matching & Fleet Optimization"
        description="Ranked vessel candidates evaluated against AIS ballast location, draft constraints, laycan window, and port bathymetry."
        badge="Multi-Objective Optimization"
        badgeVariant="default"
      >
        <Link href="/charters/compare">
          <Button variant="secondary" size="md">
            <Scale className="h-4 w-4" />
            <span>Compare Candidates</span>
          </Button>
        </Link>
      </PageHeader>

      {/* AI CHARTER DECISION CENTERPIECE */}
      {optimizationData && (
        <section>
          <DecisionRecommendation
            data={optimizationData}
            onRequestOffer={(vesselMatch) => {
              router.push(`/charters?createForCargo=${cargoId}&vesselId=${vesselMatch.vessel.id}`);
            }}
          />
        </section>
      )}

      {/* SORTING & FILTER BAR */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white border border-zinc-200 p-4 rounded shadow-sm">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-zinc-600 font-mono">
          <SlidersHorizontal className="h-4 w-4 text-zinc-800" />
          <span>Sort Candidates:</span>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <Button
            variant={sortBy === 'score' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setSortBy('score')}
          >
            Match Score (Highest)
          </Button>

          <Button
            variant={sortBy === 'freight' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setSortBy('freight')}
          >
            Freight Quote ($/MT)
          </Button>

          <Button
            variant={sortBy === 'distance' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setSortBy('distance')}
          >
            Ballast Distance (NM)
          </Button>
        </div>
      </div>

      {/* RANKED VESSEL CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {sortedMatches.map((match, index) => (
          <VesselCard
            key={match.vessel.id}
            match={match}
            isBestMatch={index === 0 && sortBy === 'score'}
            onRequestOffer={(m) => {
              router.push(`/charters?createForCargo=${cargoId}&vesselId=${m.vessel.id}`);
            }}
            onViewDetails={(m) => {
              router.push(`/vessels/${m.vessel.id}`);
            }}
          />
        ))}
      </div>

      {/* LIVE AIS TRACKING MAP */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 font-mono flex items-center gap-2">
            <Ship className="h-4 w-4 text-zinc-800" />
            <span>Real-Time Ballast Locations & Navigational Corridor</span>
          </h3>
          <span className="text-xs text-zinc-500">Track vessel movements approaching loading terminal</span>
        </div>
        <AisVesselMap height="440px" />
      </section>
    </div>
  );
}

export default function VesselMatchingPage() {
  return (
    <Suspense fallback={<div className="p-8 text-xs font-mono text-zinc-500">Loading AI vessel matches...</div>}>
      <VesselMatchContent />
    </Suspense>
  );
}
