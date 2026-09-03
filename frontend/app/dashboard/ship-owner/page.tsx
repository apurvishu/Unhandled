'use client';

import React from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { KpiCard } from '@/components/dashboard/KpiCard';
import { Button } from '@/components/ui/Button';
import { BackButton } from '@/components/ui/BackButton';
import { getVessels } from '@/services/vessels';
import { getCargoRequirements } from '@/services/cargo';
import { getCharters } from '@/services/charters';
import { formatCurrency, formatDwt, formatKnots, getStatusBadgeColor } from '@/lib/utils';
import { 
  Ship, 
  Package, 
  DollarSign, 
  Navigation, 
  ArrowRight, 
  Compass,
  FileText
} from 'lucide-react';

export default function ShipOwnerDashboard() {
  const { data: vessels = [] } = useQuery({
    queryKey: ['vessels'],
    queryFn: getVessels,
  });

  const { data: opportunities = [] } = useQuery({
    queryKey: ['cargoRequirements'],
    queryFn: getCargoRequirements,
  });

  const { data: charters = [] } = useQuery({
    queryKey: ['charters'],
    queryFn: getCharters,
  });

  return (
    <div className="space-y-8">
      <BackButton href="/" label="Back to Home" />

      <PageHeader
        title="Ship Owner Fleet Management & Bidding Desk"
        description="Monitor carrier deployment, evaluate open bulk cargo tenders, and execute charter party agreements."
        badge={`${vessels.length} Managed Vessels`}
        badgeVariant="default"
      >
        <Link href="/cargo/marketplace">
          <Button variant="primary" size="md">
            <Package className="h-4 w-4" />
            <span>Browse Open Cargo Tenders</span>
          </Button>
        </Link>
      </PageHeader>

      {/* 4 Essential Fleet KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Total Fleet Size"
          value={vessels.length}
          subtitle="Capesize, Panamax & Supramax"
          icon={Ship}
        />

        <KpiCard
          title="Vessels Underway"
          value={vessels.filter((v) => v.aisPosition.status === 'Underway').length}
          subtitle="Operating in East India corridors"
          icon={Navigation}
        />

        <KpiCard
          title="Open Cargo Tenders"
          value={opportunities.length}
          subtitle="Compatible with fleet dimensions"
          icon={Package}
        />

        <KpiCard
          title="Average Daily Hire"
          value={formatCurrency(19850)}
          subtitle="USD / day benchmark"
          icon={DollarSign}
        />
      </div>

      {/* Managed Fleet Table */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 font-mono">
            Active Fleet Telemetry & Deployment
          </h3>
          <Link href="/vessels" className="text-xs font-semibold text-black hover:underline">
            Manage All ({vessels.length})
          </Link>
        </div>

        <div className="w-full overflow-x-auto border border-zinc-200 rounded bg-white shadow-sm">
          <table className="w-full text-left text-xs text-zinc-800 font-mono">
            <thead className="bg-zinc-50 text-[10px] uppercase font-bold text-zinc-500 border-b border-zinc-200 font-sans tracking-wider">
              <tr>
                <th className="py-3 px-4">Vessel Name / IMO</th>
                <th className="py-3 px-4">Class</th>
                <th className="py-3 px-4">DWT</th>
                <th className="py-3 px-4">Max Draft</th>
                <th className="py-3 px-4">Current Speed</th>
                <th className="py-3 px-4">Destination / ETA</th>
                <th className="py-3 px-4">Daily Rate</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right font-sans">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100 font-medium">
              {vessels.map((v) => {
                const statusStyle = getStatusBadgeColor(v.aisPosition.status);

                return (
                  <tr key={v.id} className="hover:bg-zinc-50/80 transition-colors">
                    <td className="py-3 px-4 font-sans">
                      <Link href={`/vessels/${v.id}`} className="font-bold text-zinc-950 hover:underline font-mono">
                        {v.name}
                      </Link>
                      <div className="text-[10px] text-zinc-400 font-mono">IMO {v.imo}</div>
                    </td>
                    <td className="py-3 px-4 font-sans text-zinc-700">
                      {v.type}
                    </td>
                    <td className="py-3 px-4 text-zinc-900 font-bold">
                      {formatDwt(v.dwt)}
                    </td>
                    <td className="py-3 px-4 text-zinc-700">
                      {v.maxDraft}m
                    </td>
                    <td className="py-3 px-4 text-zinc-700">
                      {formatKnots(v.aisPosition.speedKnots)}
                    </td>
                    <td className="py-3 px-4 font-sans">
                      <div className="text-zinc-900">{v.aisPosition.destination}</div>
                      <div className="text-[10px] text-zinc-400 font-mono">ETA: {v.aisPosition.eta.split('T')[0]}</div>
                    </td>
                    <td className="py-3 px-4 text-zinc-900 font-bold">
                      {formatCurrency(v.dailyCharterRateUsd)}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${statusStyle.bg} ${statusStyle.text} ${statusStyle.border}`}>
                        {v.aisPosition.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-sans">
                      <Link href={`/vessels/match?vesselId=${v.id}`}>
                        <Button variant="outline" size="sm">
                          Match Cargo
                        </Button>
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* Cargo Opportunities Banner */}
      <section className="bg-zinc-50 border border-zinc-200 rounded p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-zinc-200">
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-950 font-mono">
              Open Cargo Tenders Matching Your Fleet
            </h3>
            <p className="text-xs text-zinc-600 mt-0.5">Direct procurement inquiries from Indian public & private steel plants</p>
          </div>
          <Link href="/cargo/marketplace">
            <Button variant="primary" size="sm">
              <span>View All Tenders</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {opportunities.slice(0, 2).map((opp) => (
            <div key={opp.id} className="p-4 bg-white border border-zinc-200 rounded space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-bold text-zinc-950 font-mono text-sm">{opp.commodity}</span>
                <span className="font-mono text-xs font-bold text-zinc-900">${opp.targetFreightRateUsdPerMt}/MT Budget</span>
              </div>
              <p className="text-xs text-zinc-600">
                {formatDwt(opp.quantityMt)} • {opp.originPortName} → {opp.destinationPortName}
              </p>
              <div className="flex items-center justify-between pt-2 border-t border-zinc-100 text-xs">
                <span className="text-zinc-500 font-mono text-[11px]">Laycan: {opp.laycanStart} to {opp.laycanEnd}</span>
                <Link href="/cargo/marketplace">
                  <Button variant="primary" size="sm">Submit Bid</Button>
                </Link>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
