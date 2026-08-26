'use client';

import React from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { KpiCard } from '@/components/dashboard/KpiCard';
import { AisVesselMap } from '@/components/maps/AisVesselMap';
import { Button } from '@/components/ui/Button';
import { getVessels } from '@/services/vessels';
import { getCargoRequirements } from '@/services/cargo';
import { getCharters } from '@/services/charters';
import { formatCurrency, formatDwt } from '@/lib/utils';
import { 
  Ship, 
  Boxes, 
  FileText, 
  DollarSign, 
  Navigation, 
  Plus, 
  ArrowRight,
  TrendingUp,
  CheckCircle2,
  Clock
} from 'lucide-react';

export default function ShipOwnerDashboardPage() {
  const { data: vessels = [] } = useQuery({
    queryKey: ['vessels'],
    queryFn: getVessels,
  });

  const { data: cargoOpportunities = [] } = useQuery({
    queryKey: ['cargoRequirements'],
    queryFn: getCargoRequirements,
  });

  const { data: charters = [] } = useQuery({
    queryKey: ['charters'],
    queryFn: getCharters,
  });

  const availableVessels = vessels.filter((v) => v.isAvailable).length;

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <PageHeader
        title="Ship Owner Fleet Command"
        description="Monitor vessel deployment, browse open cargo procurement tenders, and submit charter bids."
        badge="Carrier Fleet: Oceanic Bulk"
        badgeVariant="info"
      >
        <Link href="/vessels">
          <Button variant="primary" size="md">
            <Plus className="h-4 w-4" />
            <span>Add / Manage Vessel</span>
          </Button>
        </Link>
        <Link href="/cargo/marketplace">
          <Button variant="secondary" size="md">
            <Boxes className="h-4 w-4" />
            <span>Browse Cargo Bids</span>
          </Button>
        </Link>
      </PageHeader>

      {/* KPI Section */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
        <KpiCard
          title="Total Fleet"
          value={vessels.length}
          subtitle="Capesize & Panamax"
          icon={Ship}
        />

        <KpiCard
          title="Available"
          value={availableVessels}
          subtitle="Open for charter"
          icon={CheckCircle2}
          variant="success"
        />

        <KpiCard
          title="Active Voyages"
          value="2"
          subtitle="En route to port"
          icon={Navigation}
        />

        <KpiCard
          title="Tender Offers"
          value={charters.length}
          subtitle="Bids submitted"
          icon={FileText}
          variant="primary"
        />

        <KpiCard
          title="Est. Revenue"
          value="$4.00M"
          subtitle="Contracted voyages"
          icon={DollarSign}
          variant="success"
        />

        <KpiCard
          title="Cargo Needs"
          value={cargoOpportunities.length}
          subtitle="Matching tenders"
          icon={Boxes}
          variant="warning"
        />
      </div>

      {/* CARGO OPPORTUNITY MARKETPLACE BANNER */}
      <section className="bg-gradient-to-r from-sky-950/60 via-slate-900 to-slate-950 border border-sky-500/30 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-sky-500/20 text-sky-300 text-xs font-bold uppercase mb-2">
              <span>New Cargo Opportunity Alert</span>
            </div>
            <h3 className="text-xl font-black text-white">
              75,000 MT Coking Coal • Hay Point (Australia) → Paradip Port (India)
            </h3>
            <p className="text-xs text-slate-300 mt-1">
              Required Laycan: <strong className="text-sky-300">01 Sep – 06 Sep 2026</strong> • Target Freight: <strong className="text-emerald-400">$23.50 – $24.80 / MT</strong>
            </p>
          </div>

          <Link href="/charters">
            <Button variant="primary" size="md" className="font-bold">
              <span>Submit Charter Offer</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </section>

      {/* FLEET STATUS & MAP */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Fleet List */}
        <div className="lg:col-span-1 bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Fleet Status Overview</h3>
            <span className="text-xs text-sky-400 font-mono font-semibold">{vessels.length} vessels</span>
          </div>

          <div className="space-y-3 max-h-[460px] overflow-y-auto pr-1">
            {vessels.map((v) => (
              <div key={v.id} className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 hover:border-slate-700 transition text-xs space-y-1.5">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-white">{v.name}</h4>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                    v.isAvailable ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-slate-800 text-slate-400'
                  }`}>
                    {v.isAvailable ? 'Available' : 'Engaged'}
                  </span>
                </div>
                <div className="text-slate-400 flex items-center justify-between">
                  <span>{v.type} • {formatDwt(v.dwt)}</span>
                  <span className="text-sky-300 font-mono">{formatCurrency(v.dailyCharterRateUsd)}/day</span>
                </div>
                <div className="pt-1.5 border-t border-slate-800/60 text-[11px] flex items-center justify-between text-slate-500">
                  <span>Status: {v.aisPosition.status}</span>
                  <span>Draft: {v.maxDraft}m</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Live AIS Fleet Tracking Map */}
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Ship className="h-4 w-4 text-sky-400" />
              <span>Real-Time Fleet AIS Map</span>
            </h3>
            <span className="text-xs text-emerald-400 flex items-center gap-1 font-mono">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              Live Telemetry Active
            </span>
          </div>
          <AisVesselMap height="500px" />
        </div>
      </div>
    </div>
  );
}
