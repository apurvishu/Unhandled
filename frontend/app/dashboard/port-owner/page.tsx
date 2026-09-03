'use client';

import React from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { KpiCard } from '@/components/dashboard/KpiCard';
import { PortCongestionChart } from '@/components/charts/PortCongestionChart';
import { Button } from '@/components/ui/Button';
import { BackButton } from '@/components/ui/BackButton';
import { getPorts, getBerthsByPort } from '@/services/ports';
import { getPortCongestion } from '@/services/congestion';
import { formatDwt } from '@/lib/utils';
import { Anchor, Clock, ArrowRight, ShieldCheck, Ship, Layers } from 'lucide-react';

export default function PortOwnerDashboard() {
  const { data: ports = [] } = useQuery({
    queryKey: ['ports'],
    queryFn: getPorts,
  });

  const { data: berths = [] } = useQuery({
    queryKey: ['berths', 'port-paradip'],
    queryFn: () => getBerthsByPort('port-paradip'),
  });

  const { data: congestion } = useQuery({
    queryKey: ['portCongestion', 'port-paradip'],
    queryFn: () => getPortCongestion('port-paradip'),
  });

  const paradip = ports.find((p) => p.id === 'port-paradip') || ports[0];

  return (
    <div className="space-y-8">
      <BackButton href="/" label="Back to Home" />

      <PageHeader
        title="Port Authority & Terminal Operations Control"
        description="Monitor berth occupancy, mechanized unloader throughput, UKC bathymetry, and 7-day anchorage congestion."
        badge="Paradip Port Terminal (IN PRT)"
        badgeVariant="default"
      >
        <Link href="/congestion">
          <Button variant="primary" size="md">
            <span>Global Congestion Matrix</span>
          </Button>
        </Link>
      </PageHeader>

      {/* 4 Essential Port KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Berth Utilization"
          value={`${paradip?.berthUtilizationPercent || 78}%`}
          subtitle="4 of 6 Mechanized Berths Busy"
          icon={Anchor}
        />

        <KpiCard
          title="Anchorage Queue"
          value={`${paradip?.vesselsInQueue || 14} Vessels`}
          subtitle="Waiting for pilotage"
          icon={Ship}
        />

        <KpiCard
          title="Avg Anchorage Waiting"
          value={`${paradip?.averageWaitingTimeHours || 34.5}h`}
          subtitle="Predicted to decline to 21h"
          icon={Clock}
          change={{ value: '-13.5h (in 3 days)', trend: 'DOWN', isPositive: true }}
        />

        <KpiCard
          title="Max Channel Depth"
          value={`${paradip?.channelMaxDepth || 17.5}m`}
          subtitle="Accommodates up to Capesize"
          icon={ShieldCheck}
        />
      </div>

      {/* Berth Occupancy Board */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 font-mono">
            Terminal Berth Allocation & Operations Board
          </h3>
          <span className="text-xs font-mono text-zinc-500">{berths.length} Monitored Berths</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {berths.map((b) => {
            const isOccupied = b.status === 'OCCUPIED';

            return (
              <div
                key={b.id}
                className="bg-white border border-zinc-200 rounded p-4 space-y-3 shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-zinc-950 font-mono text-sm">{b.name}</h4>
                    <span className="text-[10px] text-zinc-500 uppercase font-mono">{b.code}</span>
                  </div>

                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${
                    isOccupied
                      ? 'bg-amber-50 text-amber-900 border-amber-300'
                      : 'bg-emerald-50 text-emerald-900 border-emerald-300'
                  }`}>
                    {b.status}
                  </span>
                </div>

                <div className="space-y-1 text-xs font-mono pt-2 border-t border-zinc-100">
                  <div className="flex justify-between text-zinc-600">
                    <span className="font-sans">Max Draft:</span>
                    <strong className="text-zinc-900">{b.maxDraftMeters}m</strong>
                  </div>
                  <div className="flex justify-between text-zinc-600">
                    <span className="font-sans">Max DWT:</span>
                    <span className="text-zinc-900">{formatDwt(b.maxDwt)}</span>
                  </div>
                  <div className="flex justify-between text-zinc-600">
                    <span className="font-sans">Handling Rate:</span>
                    <span className="text-zinc-900">{b.handlingRateMtPerHour} MT/h</span>
                  </div>
                </div>

                {isOccupied && b.currentVesselName && (
                  <div className="p-2.5 bg-zinc-50 border border-zinc-200 rounded text-xs space-y-0.5">
                    <div className="flex items-center justify-between font-mono">
                      <strong className="text-zinc-950">{b.currentVesselName}</strong>
                      <span className="text-emerald-700 font-bold">{b.dischargeProgressPercent}%</span>
                    </div>
                    <p className="text-[11px] text-zinc-500 font-mono">Discharge ETD: {b.etdExpected?.split('T')[0]}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* 7-Day Congestion Forecast */}
      {congestion && (
        <section className="bg-white border border-zinc-200 rounded p-6 space-y-4 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-zinc-100">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-950 font-mono">
                Paradip Terminal 7-Day Congestion & Queue Forecast
              </h3>
              <p className="text-xs text-zinc-500">Spatial GNN model predicting anchorage wait progression</p>
            </div>
            <Link href="/congestion/port-paradip">
              <Button variant="outline" size="sm">
                <span>View Full Queue</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>

          <PortCongestionChart data={congestion.timeSeries} height={260} />
        </section>
      )}
    </div>
  );
}
