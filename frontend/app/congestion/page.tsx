'use client';

import React from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { PortCongestionChart } from '@/components/charts/PortCongestionChart';
import { Button } from '@/components/ui/Button';
import { getPorts } from '@/services/ports';
import { getPortCongestion } from '@/services/congestion';
import { getCongestionBadgeColor } from '@/lib/utils';
import { Clock, ArrowRight } from 'lucide-react';
import { BackButton } from '@/components/ui/BackButton';

export default function GlobalCongestionPage() {
  const { data: ports = [] } = useQuery({
    queryKey: ['ports'],
    queryFn: getPorts,
  });

  const { data: paradipCongestion } = useQuery({
    queryKey: ['portCongestion', 'port-paradip'],
    queryFn: () => getPortCongestion('port-paradip'),
  });

  return (
    <div className="space-y-8">
      <BackButton href="/" label="Back to Home" />

      <PageHeader
        title="Global Port Congestion & Anchorage Delays"
        description="Real-time and 7-day predicted congestion, anchorage queues, and turnaround time forecasts across major bulk ports."
        badge="Spatial Congestion GNN"
        badgeVariant="default"
      />

      {/* PORT CONGESTION CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {ports.map((port) => {
          const badge = getCongestionBadgeColor(port.congestionLevel);

          return (
            <div
              key={port.id}
              className="bg-white border border-zinc-200 rounded p-5 shadow-sm hover:border-zinc-300 transition flex flex-col justify-between space-y-4"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${badge.bg} ${badge.text} ${badge.border}`}>
                    {port.congestionLevel} CONGESTION
                  </span>
                  <span className="text-[10px] text-zinc-400 font-mono">{port.code}</span>
                </div>

                <h3 className="text-sm font-bold text-zinc-950 mt-2">{port.name}</h3>
                <p className="text-xs text-zinc-500">{port.country}</p>

                <div className="grid grid-cols-2 gap-2 my-4 p-3 rounded bg-zinc-50 border border-zinc-200 text-xs font-mono">
                  <div>
                    <span className="text-[10px] text-zinc-400 block uppercase font-sans">Anchorage Wait:</span>
                    <strong className="text-zinc-950">{port.averageWaitingTimeHours}h</strong>
                  </div>
                  <div>
                    <span className="text-[10px] text-zinc-400 block uppercase font-sans">Queue:</span>
                    <strong className="text-zinc-950">{port.vesselsInQueue} Vessels</strong>
                  </div>
                  <div>
                    <span className="text-[10px] text-zinc-400 block uppercase font-sans">Max Depth:</span>
                    <span className="text-zinc-800">{port.channelMaxDepth}m</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-zinc-400 block uppercase font-sans">Occupancy:</span>
                    <span className="text-zinc-800">{port.berthUtilizationPercent}%</span>
                  </div>
                </div>
              </div>

              <Link href={`/congestion/${port.id}`}>
                <Button variant="outline" size="sm" className="w-full">
                  <span>View 7-Day Forecast</span>
                  <ArrowRight className="h-3 w-3" />
                </Button>
              </Link>
            </div>
          );
        })}
      </div>

      {/* DETAILED PARADIP 7-DAY FORECAST */}
      {paradipCongestion && (
        <section className="bg-white border border-zinc-200 rounded p-6 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-zinc-100">
            <div>
              <div className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-zinc-900" />
                <h3 className="text-sm font-bold text-zinc-950 font-mono uppercase tracking-wider">
                  Paradip Port Terminal (IN PRT) — 7-Day Queue Projection
                </h3>
              </div>
              <p className="text-xs text-zinc-500 mt-0.5 font-mono">
                Current: <strong className="text-zinc-950">HIGH (34.5h wait)</strong> → Predicted: <strong className="text-emerald-800 font-bold">MEDIUM (21.0h wait in 3 days)</strong>
              </p>
            </div>

            <Link href="/congestion/port-paradip">
              <Button variant="primary" size="sm">
                <span>Open Terminal Detail</span>
              </Button>
            </Link>
          </div>

          <PortCongestionChart data={paradipCongestion.timeSeries} height={280} />
        </section>
      )}
    </div>
  );
}
