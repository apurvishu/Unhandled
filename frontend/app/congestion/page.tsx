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
import { Clock, Anchor, AlertTriangle, ArrowRight, ShieldCheck, Ship } from 'lucide-react';

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
    <div className="space-y-8 animate-in fade-in duration-300">
      <PageHeader
        title="Global Port Congestion & Anchorage Delays"
        description="Real-time and 7-day predicted congestion, anchorage queues, and turnaround time forecasts across major bulk ports."
        badge="Spatial Congestion GNN"
        badgeVariant="warning"
      />

      {/* PORT CONGESTION CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {ports.map((port) => {
          const badge = getCongestionBadgeColor(port.congestionLevel);

          return (
            <div
              key={port.id}
              className="bg-slate-900/70 border border-slate-800 rounded-2xl p-5 shadow-xl hover:border-slate-700 transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center justify-between">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${badge.bg} ${badge.text} ${badge.border}`}>
                    {port.congestionLevel} CONGESTION
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">{port.code}</span>
                </div>

                <h3 className="text-lg font-bold text-white mt-2">{port.name}</h3>
                <p className="text-xs text-slate-400">{port.country}</p>

                <div className="grid grid-cols-2 gap-2 my-4 p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs">
                  <div>
                    <span className="text-[10px] text-slate-400 block uppercase">Anchorage Wait:</span>
                    <strong className="text-white font-mono text-sm">{port.averageWaitingTimeHours}h</strong>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block uppercase">Queue Vessels:</span>
                    <strong className="text-sky-300 font-mono text-sm">{port.vesselsInQueue}</strong>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block uppercase">Max Channel Depth:</span>
                    <span className="text-slate-200 font-mono">{port.channelMaxDepth}m</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block uppercase">Berth Occupancy:</span>
                    <span className="text-slate-200 font-mono">{port.berthUtilizationPercent}%</span>
                  </div>
                </div>
              </div>

              <Link href={`/congestion/${port.id}`}>
                <Button variant="outline" size="sm" className="w-full">
                  <span>View 7-Day Prediction</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            </div>
          );
        })}
      </div>

      {/* DETAILED PARADIP 7-DAY FORECAST */}
      {paradipCongestion && (
        <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800">
            <div>
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-amber-400" />
                <h3 className="text-lg font-bold text-white">
                  Paradip Port Terminal (IN PRT) — Congestion Forecast
                </h3>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Current: <strong className="text-amber-400">HIGH (34.5h wait)</strong> → Predicted: <strong className="text-emerald-400">MEDIUM (21.0h wait in 3 days)</strong>
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
