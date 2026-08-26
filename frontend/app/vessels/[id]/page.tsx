'use client';

import React from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { AisVesselMap } from '@/components/maps/AisVesselMap';
import { Button } from '@/components/ui/Button';
import { getVesselById } from '@/services/vessels';
import { formatCurrency, formatDwt, formatKnots, formatNauticalMiles, getStatusBadgeColor } from '@/lib/utils';
import { Ship, ArrowLeft, Anchor, Compass, CheckCircle2, ShieldCheck, DollarSign } from 'lucide-react';

export default function VesselDetailPage() {
  const params = useParams();
  const vesselId = (params.id as string) || 'vessel-02';

  const { data: vessel, isLoading } = useQuery({
    queryKey: ['vessel', vesselId],
    queryFn: () => getVesselById(vesselId),
  });

  if (!vessel) {
    return <div className="p-8 text-slate-400">Loading vessel telemetry...</div>;
  }

  const statusStyle = getStatusBadgeColor(vessel.aisPosition.status);

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="flex items-center gap-2">
        <Link href="/vessels">
          <Button variant="ghost" size="sm" className="text-slate-400">
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Fleet</span>
          </Button>
        </Link>
      </div>

      <PageHeader
        title={vessel.name}
        description={`IMO: ${vessel.imo} • MMSI: ${vessel.mmsi} • Flag: ${vessel.flag} • Class: ${vessel.type}`}
        badge={vessel.aisPosition.status}
        badgeVariant="info"
      >
        <Link href={`/vessels/match?vesselId=${vessel.id}`}>
          <Button variant="primary" size="md">
            <span>Find Cargo for this Vessel</span>
          </Button>
        </Link>
      </PageHeader>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Specifications */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 space-y-6">
          <h3 className="text-sm font-bold uppercase tracking-wider text-white flex items-center gap-2">
            <Ship className="h-4 w-4 text-sky-400" />
            <span>Vessel Structural Specifications</span>
          </h3>

          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800">
              <span className="text-slate-400 block">DWT Capacity:</span>
              <strong className="text-slate-100 font-mono text-sm">{formatDwt(vessel.dwt)}</strong>
            </div>

            <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800">
              <span className="text-slate-400 block">Maximum Draft:</span>
              <strong className="text-slate-100 font-mono text-sm">{vessel.maxDraft} m</strong>
            </div>

            <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800">
              <span className="text-slate-400 block">Length Overall (LOA):</span>
              <strong className="text-slate-100 font-mono text-sm">{vessel.loa} m</strong>
            </div>

            <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800">
              <span className="text-slate-400 block">Beam Width:</span>
              <strong className="text-slate-100 font-mono text-sm">{vessel.beam} m</strong>
            </div>

            <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800">
              <span className="text-slate-400 block">Daily Charter Rate:</span>
              <strong className="text-emerald-400 font-mono text-sm">{formatCurrency(vessel.dailyCharterRateUsd)}</strong>
            </div>

            <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800">
              <span className="text-slate-400 block">Fuel Burn Rate:</span>
              <strong className="text-slate-100 font-mono text-sm">{vessel.fuelConsumptionMtPerDay} MT / day</strong>
            </div>
          </div>

          <div className="p-4 bg-slate-950/90 rounded-xl border border-slate-800 text-xs space-y-2">
            <h4 className="font-bold text-slate-200">Owner & Registry Details</h4>
            <p className="text-slate-400">Registered Owner: <strong className="text-slate-200">{vessel.ownerName}</strong></p>
            <p className="text-slate-400">Year Built: <strong className="text-slate-200">{vessel.yearBuilt}</strong></p>
            <p className="text-slate-400">Current Base: <strong className="text-slate-200">{vessel.currentPortName}</strong></p>
          </div>
        </div>

        {/* Live AIS Position Map */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Compass className="h-4 w-4 text-sky-400" />
              <span>Live Coordinates & Navigation Track</span>
            </h3>
            <span className="text-xs text-sky-400 font-mono">
              Speed: {formatKnots(vessel.aisPosition.speedKnots)} • Heading: {vessel.aisPosition.headingDegrees}°
            </span>
          </div>
          <AisVesselMap selectedVesselId={vessel.id} height="460px" />
        </div>
      </div>
    </div>
  );
}
