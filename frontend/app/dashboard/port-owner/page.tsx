'use client';

import React from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { KpiCard } from '@/components/dashboard/KpiCard';
import { PortCongestionChart } from '@/components/charts/PortCongestionChart';
import { AisVesselMap } from '@/components/maps/AisVesselMap';
import { Button } from '@/components/ui/Button';
import { getPortById } from '@/services/ports';
import { getPortCongestion } from '@/services/congestion';
import { getCongestionBadgeColor } from '@/lib/utils';
import { 
  Anchor, 
  Clock, 
  Ship, 
  Layers, 
  BarChart3, 
  TrendingDown, 
  AlertTriangle,
  ArrowRight,
  ShieldCheck
} from 'lucide-react';

export default function PortOwnerDashboardPage() {
  const { data: portData } = useQuery({
    queryKey: ['port', 'port-paradip'],
    queryFn: () => getPortById('port-paradip'),
  });

  const { data: congestionData } = useQuery({
    queryKey: ['portCongestion', 'port-paradip'],
    queryFn: () => getPortCongestion('port-paradip'),
  });

  const berths = portData?.berths || [];
  const occupiedBerths = berths.filter((b) => b.status === 'OCCUPIED').length;

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <PageHeader
        title="Paradip Port Authority Operations Center"
        description="Monitor bulk terminal capacity, berth utilization, vessel queue, and AI port congestion predictions."
        badge="Port: IN PRT (Paradip)"
        badgeVariant="info"
      >
        <Link href="/congestion/port-paradip">
          <Button variant="primary" size="md">
            <Clock className="h-4 w-4" />
            <span>View Congestion Predictor</span>
          </Button>
        </Link>
        <Link href="/ports">
          <Button variant="secondary" size="md">
            <Anchor className="h-4 w-4" />
            <span>Manage Berths</span>
          </Button>
        </Link>
      </PageHeader>

      {/* KPI Section */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
        <KpiCard
          title="In-Port Vessels"
          value={portData?.currentVesselsInPort || 12}
          subtitle="At berths & anchorage"
          icon={Ship}
          variant="primary"
        />

        <KpiCard
          title="Vessels in Queue"
          value={portData?.vesselsInQueue || 7}
          subtitle="Awaiting berthing"
          icon={Layers}
          variant="warning"
        />

        <KpiCard
          title="Berth Occupancy"
          value="84.5%"
          subtitle={`${occupiedBerths}/${berths.length || 4} Berths Busy`}
          icon={Anchor}
          variant="warning"
        />

        <KpiCard
          title="Avg Waiting Time"
          value="34.5h"
          subtitle="Current anchorage wait"
          icon={Clock}
          change={{ value: '-13.5h', trend: 'DOWN', isPositive: true, label: 'improving' }}
          variant="success"
        />

        <KpiCard
          title="Congestion Level"
          value="HIGH"
          subtitle="Easing to MEDIUM in 3d"
          icon={AlertTriangle}
          variant="warning"
        />

        <KpiCard
          title="Channel Depth"
          value="17.5m"
          subtitle="Capesize compatible"
          icon={ShieldCheck}
          variant="success"
        />
      </div>

      {/* BERTH OCCUPANCY STATUS BOARD */}
      <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Anchor className="h-4 w-4 text-sky-400" />
              <span>Live Berth Occupancy & Operational Schedule</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">Real-time status of mechanized coal & iron ore berths</p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded bg-sky-500/20 text-sky-300 border border-sky-500/30">
            Channel UKC: 17.5m Depth
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {berths.map((berth) => {
            const isOccupied = berth.status === 'OCCUPIED';

            return (
              <div
                key={berth.id}
                className={`rounded-xl border p-4 text-xs space-y-2.5 transition ${
                  isOccupied
                    ? 'bg-slate-950/80 border-amber-500/40'
                    : 'bg-slate-950/40 border-slate-800'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-extrabold text-white text-sm">{berth.berthNumber}</span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                      isOccupied
                        ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                        : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    }`}
                  >
                    {berth.status}
                  </span>
                </div>

                <p className="text-slate-300 font-medium text-[11px] truncate">{berth.name}</p>

                {isOccupied ? (
                  <div className="pt-2 border-t border-slate-800/80 space-y-1 text-slate-300">
                    <p>
                      Vessel: <strong className="text-sky-300">{berth.currentVesselName}</strong>
                    </p>
                    <p>
                      Cargo: <strong className="text-slate-200">{berth.cargoQuantityMt?.toLocaleString()} MT {berth.cargoType}</strong>
                    </p>
                    <p className="text-[10px] text-slate-400">
                      ETD: {berth.expectedDeparture?.split('T')[0]} 18:00 UTC
                    </p>
                  </div>
                ) : (
                  <div className="pt-2 border-t border-slate-800/80 text-emerald-400 text-[11px]">
                    ✓ Available for Panamax / Capesize Berthing
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* CONGESTION PREDICTION & MAP */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Clock className="h-4 w-4 text-amber-400" />
              <span>7-Day ML Congestion & Waiting Time Forecast</span>
            </h3>
            <Link href="/congestion/port-paradip" className="text-xs text-sky-400 hover:text-sky-300">
              Details →
            </Link>
          </div>
          {congestionData && (
            <PortCongestionChart data={congestionData.timeSeries} height={300} />
          )}
        </section>

        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Ship className="h-4 w-4 text-sky-400" />
              <span>Port Approaching Vessel Traffic Map</span>
            </h3>
            <Link href="/vessels" className="text-xs text-sky-400 hover:text-sky-300">
              Full Map →
            </Link>
          </div>
          <AisVesselMap height="360px" />
        </section>
      </div>
    </div>
  );
}
