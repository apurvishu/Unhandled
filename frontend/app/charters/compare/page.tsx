'use client';

import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { VesselComparisonTable } from '@/components/vessels/VesselComparisonTable';
import { Button } from '@/components/ui/Button';
import { matchVessels } from '@/services/optimization';
import { ArrowLeft, Scale } from 'lucide-react';

export default function CharterComparePage() {
  const router = useRouter();

  const { data: matches = [] } = useQuery({
    queryKey: ['vesselMatches', 'req-coal-75k'],
    queryFn: () => matchVessels('req-coal-75k'),
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Link href="/optimization">
          <Button variant="ghost" size="sm" className="text-zinc-500">
            <ArrowLeft className="h-4 w-4" />
            <span>Back to AI Decision</span>
          </Button>
        </Link>
      </div>

      <PageHeader
        title="Multi-Vessel Charter Comparison Matrix"
        description="Detailed side-by-side evaluation of matched vessels across AI score, freight quotes, ETA, DWT, draft compatibility, and bunker fuel costs."
        badge="3 Candidates Evaluated"
        badgeVariant="default"
      >
        <Link href="/optimization">
          <Button variant="primary" size="md">
            <Scale className="h-4 w-4" />
            <span>Recommend Best Candidate</span>
          </Button>
        </Link>
      </PageHeader>

      <div className="space-y-4">
        <VesselComparisonTable
          matches={matches}
          onRequestOffer={(m) => {
            router.push(`/charters?createForCargo=req-coal-75k&vesselId=${m.vessel.id}`);
          }}
        />
      </div>
    </div>
  );
}
