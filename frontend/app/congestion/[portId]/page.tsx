'use client';

import React from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { KpiCard } from '@/components/dashboard/KpiCard';
import { PortCongestionChart } from '@/components/charts/PortCongestionChart';
import { AisVesselMap } from '@/components/maps/AisVesselMap';
import { Button } from '@/components/ui/Button';
import { getPortCongestion } from '@/services/congestion';
import { getPortById } from '@/services/ports';
import { getCongestionBadgeColor } from '@/lib/utils';
import { Clock, ArrowLeft, Anchor, AlertTriangle, Layers, Ship, CheckCircle2 } from 'lucide-react';

export default function PortCongestionDetailPage() {
  const params = useParams();
  const portId = (params.portId as string) || 'port-paradip';

  const { data: port } = useQuery({
    queryKey: ['port', portId],
    queryFn: () => getPortById(portId),
  });

  const { data: congestion } = useQuery({
    queryKey: ['portCongestion', portId],
    queryFn: () => getPortCongestion(portId),
  });

  if (!congestion || !port) {
    return <div className="p-8 text-slate-400">Loading port congestion model...</div>;
  }

  const badge = getCongestionBadgeColor(congestion.currentCongestion);

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <div className="flex items-center gap-2">
        <Link href="/congestion">
          <Button variant="ghost" size="sm" className="text-slate-400">
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Global Congestion</span>
          </Button>
        </Link>
      </div>

      <PageHeader
        title={`${port.name} (${port.code}) — Congestion Intelligence`}
        description="Spatial GNN analysis of anchored queues, channel bathymetry, and expected berthing delay timeline."
        badge={`${congestion.currentCongestion} CONGESTION`}
        badgeVariant={congestion.currentCongestion === 'LOW' ? 'success' : 'warning'}
      >
        <Link href="/vessels">
          <Button variant="primary" size="md">
            <Ship className="h-4 w-4" />
            <span>View Inbound Vessels</span>
          </Button>
        </Link>
      </PageHeader>

      {/* 4 KPI CARDS */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <KpiCard
          title="Current Congestion"
          value={congestion.currentCongestion}
          subtitle="Anchorage queue active"
          icon={AlertTriangle}
          variant="warning"
        />

        <KpiCard
          title="Predicted in 3 Days"
          value={congestion.predictedCongestionIn3Days}
          subtitle="Expected improvement"
          icon={Clock}
          change={{ value: '-13.5h wait', trend: 'DOWN', isPositive: true }}
          variant="success"
        />

        <KpiCard
          title="Avg Waiting Time"
          value={`${congestion.currentWaitingTimeHours}h`}
          subtitle="Anchorage to berth"
          icon={Clock}
        />

        <KpiCard
          title="Berth Utilization"
          value={`${congestion.berthUtilizationPercent}%`}
          subtitle="Operational load"
          icon={Anchor}
          variant="primary"
        />
      </div>

      {/* 7-DAY WAITING TIME & CONGESTION FORECAST */}
      <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <Clock className="h-4 w-4 text-amber-400" />
          <span>7-Day Expected Anchorage Waiting Time Horizon</span>
        </h3>
        <PortCongestionChart data={congestion.timeSeries} height={300} />
      </section>

      {/* ANCHORAGE QUEUE LIST */}
      <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Layers className="h-4 w-4 text-sky-400" />
              <span>Current Anchorage Queue & Berthing Sequence</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">Vessels awaiting pilotage and mechanized discharge</p>
          </div>
          <span className="text-xs font-mono text-sky-400">{congestion.queueVessels.length} vessels anchored</span>
        </div>

        <div className="w-full overflow-x-auto rounded-xl border border-slate-800">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-[10px] uppercase font-bold text-slate-400 border-b border-slate-800">
              <tr>
                <th className="p-3">Vessel Name / IMO</th>
                <th className="p-3">Cargo Specification</th>
                <th className="p-3">Anchorage Arrival</th>
                <th className="p-3">Predicted Berthing</th>
                <th className="p-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium">
              {congestion.queueVessels.map((v, i) => (
                <tr key={i} className="hover:bg-slate-800/30">
                  <td className="p-3 font-bold text-white">
                    {v.vesselName}
                    <div className="text-[10px] text-slate-500 font-mono">IMO: {v.imo}</div>
                  </td>
                  <td className="p-3">
                    <span className="font-semibold text-slate-200">{v.quantityMt.toLocaleString()} MT</span> {v.cargo}
                  </td>
                  <td className="p-3 text-slate-300">{v.arrivalDate}</td>
                  <td className="p-3 text-emerald-400 font-semibold">{v.expectedBerthDate}</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-500/10 text-amber-400 border border-amber-500/30">
                      Anchored
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
