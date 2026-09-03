'use client';

import React from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { KpiCard } from '@/components/dashboard/KpiCard';
import { PortCongestionChart } from '@/components/charts/PortCongestionChart';
import { Button } from '@/components/ui/Button';
import { getPortCongestion } from '@/services/congestion';
import { getPortById } from '@/services/ports';
import { Clock, ArrowLeft, Anchor, AlertTriangle, Layers, Ship } from 'lucide-react';

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
    return <div className="p-8 text-xs font-mono text-zinc-500">Loading port congestion model...</div>;
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-2">
        <Link href="/congestion">
          <Button variant="ghost" size="sm" className="text-zinc-500">
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
        />

        <KpiCard
          title="Predicted in 3 Days"
          value={congestion.predictedCongestionIn3Days}
          subtitle="Expected improvement"
          icon={Clock}
          change={{ value: '-13.5h wait', trend: 'DOWN', isPositive: true }}
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
        />
      </div>

      {/* 7-DAY WAITING TIME FORECAST */}
      <section className="bg-white border border-zinc-200 rounded p-6 shadow-sm space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-950 font-mono flex items-center gap-2">
          <Clock className="h-4 w-4 text-zinc-800" />
          <span>7-Day Expected Anchorage Waiting Time Horizon</span>
        </h3>
        <PortCongestionChart data={congestion.timeSeries} height={300} />
      </section>

      {/* ANCHORAGE QUEUE LIST */}
      <section className="bg-white border border-zinc-200 rounded p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-zinc-100">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-950 font-mono flex items-center gap-2">
              <Layers className="h-4 w-4 text-zinc-800" />
              <span>Current Anchorage Queue & Berthing Sequence</span>
            </h3>
            <p className="text-xs text-zinc-500 mt-0.5">Vessels awaiting pilotage and mechanized discharge</p>
          </div>
          <span className="text-xs font-mono text-zinc-900 font-semibold">{congestion.queueVessels.length} vessels anchored</span>
        </div>

        <div className="w-full overflow-x-auto rounded border border-zinc-200">
          <table className="w-full text-left text-xs text-zinc-800 font-mono">
            <thead className="bg-zinc-50 text-[10px] uppercase font-bold text-zinc-500 border-b border-zinc-200 font-sans">
              <tr>
                <th className="p-3">Vessel Name / IMO</th>
                <th className="p-3">Cargo Specification</th>
                <th className="p-3">Anchorage Arrival</th>
                <th className="p-3">Predicted Berthing</th>
                <th className="p-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100 font-medium">
              {congestion.queueVessels.map((v, i) => (
                <tr key={i} className="hover:bg-zinc-50/80">
                  <td className="p-3 font-bold text-zinc-950">
                    {v.vesselName}
                    <div className="text-[10px] text-zinc-400 font-normal">IMO {v.imo}</div>
                  </td>
                  <td className="p-3">
                    <span className="font-bold text-zinc-950">{v.quantityMt.toLocaleString()} MT</span> {v.cargo}
                  </td>
                  <td className="p-3 text-zinc-600">{v.arrivalDate}</td>
                  <td className="p-3 text-emerald-800 font-bold">{v.expectedBerthDate}</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-50 text-amber-900 border border-amber-300">
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
