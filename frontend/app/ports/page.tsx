'use client';

import React from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/Button';
import { getPorts } from '@/services/ports';
import { getCongestionBadgeColor } from '@/lib/utils';
import { Anchor, Ship, Clock, ArrowRight, ShieldCheck } from 'lucide-react';

export default function PortsDirectoryPage() {
  const { data: ports = [] } = useQuery({
    queryKey: ['ports'],
    queryFn: getPorts,
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <PageHeader
        title="Ports Infrastructure & Berth Terminals"
        description="Global bulk terminal registry, channel bathymetry depths, draft restrictions, and live berth allocations."
        badge={`${ports.length} Monitored Ports`}
        badgeVariant="info"
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {ports.map((port) => {
          const badge = getCongestionBadgeColor(port.congestionLevel);

          return (
            <div
              key={port.id}
              className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4 hover:border-slate-700 transition"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-xl font-extrabold text-white">{port.name}</h3>
                  <p className="text-xs text-slate-400 font-mono mt-0.5">{port.country} • UN/LOCODE: {port.code}</p>
                </div>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${badge.bg} ${badge.text} ${badge.border}`}>
                  {port.congestionLevel}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 text-xs">
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase">Channel Max Depth:</span>
                  <strong className="text-emerald-400 font-mono text-sm">{port.channelMaxDepth}m</strong>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase">Max Vessel DWT:</span>
                  <strong className="text-slate-100 font-mono text-sm">{port.maxVesselDwt.toLocaleString()} MT</strong>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase">Total Berths:</span>
                  <span className="text-slate-200 font-semibold">{port.berthsCount} Berths</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px] uppercase">Avg Waiting:</span>
                  <span className="text-amber-400 font-mono font-semibold">{port.averageWaitingTimeHours}h</span>
                </div>
              </div>

              <div className="pt-2 flex items-center justify-between">
                <span className="text-xs text-slate-400">
                  Current Vessels: <strong className="text-sky-300">{port.currentVesselsInPort}</strong>
                </span>

                <Link href={`/congestion/${port.id}`}>
                  <Button variant="outline" size="sm">
                    <span>Terminal Details</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Button>
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
