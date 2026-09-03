'use client';

import React from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/Button';
import { getPorts } from '@/services/ports';
import { getCongestionBadgeColor } from '@/lib/utils';
import { ArrowRight } from 'lucide-react';
import { BackButton } from '@/components/ui/BackButton';

export default function PortsDirectoryPage() {
  const { data: ports = [] } = useQuery({
    queryKey: ['ports'],
    queryFn: getPorts,
  });

  return (
    <div className="space-y-6">
      <BackButton href="/" label="Back to Home" />

      <PageHeader
        title="Ports Infrastructure & Berth Terminals"
        description="Global bulk terminal registry, channel bathymetry depths, draft restrictions, and live berth allocations."
        badge={`${ports.length} Monitored Ports`}
        badgeVariant="default"
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {ports.map((port) => {
          const badge = getCongestionBadgeColor(port.congestionLevel);

          return (
            <div
              key={port.id}
              className="bg-white border border-zinc-200 rounded p-6 shadow-sm space-y-4 hover:border-zinc-300 transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-base font-bold text-zinc-950 font-mono">{port.name}</h3>
                    <p className="text-xs text-zinc-500 font-mono mt-0.5">{port.country} • UN/LOCODE: {port.code}</p>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${badge.bg} ${badge.text} ${badge.border}`}>
                    {port.congestionLevel}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 p-3.5 rounded bg-zinc-50 border border-zinc-200 text-xs font-mono my-4">
                  <div>
                    <span className="text-zinc-400 block text-[10px] uppercase font-sans">Channel Max Depth:</span>
                    <strong className="text-zinc-950">{port.channelMaxDepth}m</strong>
                  </div>
                  <div>
                    <span className="text-zinc-400 block text-[10px] uppercase font-sans">Max Vessel DWT:</span>
                    <strong className="text-zinc-950">{port.maxVesselDwt.toLocaleString()} MT</strong>
                  </div>
                  <div>
                    <span className="text-zinc-400 block text-[10px] uppercase font-sans">Total Berths:</span>
                    <span className="text-zinc-800">{port.berthsCount} Berths</span>
                  </div>
                  <div>
                    <span className="text-zinc-400 block text-[10px] uppercase font-sans">Avg Waiting:</span>
                    <span className="text-zinc-950 font-bold">{port.averageWaitingTimeHours}h</span>
                  </div>
                </div>
              </div>

              <div className="pt-2 flex items-center justify-between border-t border-zinc-100">
                <span className="text-xs font-mono text-zinc-500">
                  Current Vessels: <strong className="text-zinc-950">{port.currentVesselsInPort}</strong>
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