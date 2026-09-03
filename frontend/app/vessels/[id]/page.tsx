'use client';

import React from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { AisVesselMap } from '@/components/maps/AisVesselMap';
import { Button } from '@/components/ui/Button';
import { getVesselById } from '@/services/vessels';
import { formatCurrency, formatDwt, formatKnots } from '@/lib/utils';
import { Ship, ArrowLeft, Compass } from 'lucide-react';

export default function VesselDetailPage() {
  const params = useParams();
  const vesselId = (params.id as string) || 'vessel-02';

  const { data: vessel } = useQuery({
    queryKey: ['vessel', vesselId],
    queryFn: () => getVesselById(vesselId),
  });

  if (!vessel) {
    return <div className="p-8 text-xs font-mono text-zinc-500">Loading vessel telemetry...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Link href="/vessels">
          <Button variant="ghost" size="sm" className="text-zinc-500">
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Fleet</span>
          </Button>
        </Link>
      </div>

      <PageHeader
        title={vessel.name}
        description={`IMO: ${vessel.imo} • MMSI: ${vessel.mmsi} • Flag: ${vessel.flag} • Class: ${vessel.type}`}
        badge={vessel.aisPosition.status}
        badgeVariant="default"
      >
        <Link href={`/vessels/match?vesselId=${vessel.id}`}>
          <Button variant="primary" size="md">
            <span>Find Cargo for this Vessel</span>
          </Button>
        </Link>
      </PageHeader>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Specifications */}
        <div className="bg-white border border-zinc-200 rounded p-6 space-y-6 shadow-sm">
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-950 font-mono flex items-center gap-2">
            <Ship className="h-4 w-4 text-zinc-900" />
            <span>Vessel Structural Specifications</span>
          </h3>

          <div className="grid grid-cols-2 gap-3 text-xs font-mono">
            <div className="p-3 bg-zinc-50 rounded border border-zinc-200">
              <span className="text-zinc-400 block font-sans uppercase text-[10px]">DWT Capacity:</span>
              <strong className="text-zinc-950">{formatDwt(vessel.dwt)}</strong>
            </div>

            <div className="p-3 bg-zinc-50 rounded border border-zinc-200">
              <span className="text-zinc-400 block font-sans uppercase text-[10px]">Maximum Draft:</span>
              <strong className="text-zinc-950">{vessel.maxDraft} m</strong>
            </div>

            <div className="p-3 bg-zinc-50 rounded border border-zinc-200">
              <span className="text-zinc-400 block font-sans uppercase text-[10px]">Length Overall (LOA):</span>
              <strong className="text-zinc-950">{vessel.loa} m</strong>
            </div>

            <div className="p-3 bg-zinc-50 rounded border border-zinc-200">
              <span className="text-zinc-400 block font-sans uppercase text-[10px]">Beam Width:</span>
              <strong className="text-zinc-950">{vessel.beam} m</strong>
            </div>

            <div className="p-3 bg-zinc-50 rounded border border-zinc-200">
              <span className="text-zinc-400 block font-sans uppercase text-[10px]">Daily Charter Rate:</span>
              <strong className="text-zinc-950">{formatCurrency(vessel.dailyCharterRateUsd)}</strong>
            </div>

            <div className="p-3 bg-zinc-50 rounded border border-zinc-200">
              <span className="text-zinc-400 block font-sans uppercase text-[10px]">Fuel Burn Rate:</span>
              <strong className="text-zinc-950">{vessel.fuelConsumptionMtPerDay} MT / day</strong>
            </div>
          </div>

          <div className="p-4 bg-zinc-50 rounded border border-zinc-200 text-xs space-y-2">
            <h4 className="font-bold text-zinc-950 font-mono">Owner & Registry Details</h4>
            <p className="text-zinc-600">Registered Owner: <strong className="text-zinc-900">{vessel.ownerName}</strong></p>
            <p className="text-zinc-600">Year Built: <strong className="text-zinc-900">{vessel.yearBuilt}</strong></p>
            <p className="text-zinc-600">Current Base: <strong className="text-zinc-900">{vessel.currentPortName}</strong></p>
          </div>
        </div>

        {/* Live AIS Position Map */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 font-mono flex items-center gap-2">
              <Compass className="h-4 w-4 text-zinc-900" />
              <span>Live Coordinates & Navigation Track</span>
            </h3>
            <span className="text-xs text-zinc-900 font-mono font-bold">
              Speed: {formatKnots(vessel.aisPosition.speedKnots)} • Heading: {vessel.aisPosition.headingDegrees}°
            </span>
          </div>
          <AisVesselMap selectedVesselId={vessel.id} height="460px" />
        </div>
      </div>
    </div>
  );
}
