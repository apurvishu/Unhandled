'use client';

import React from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { KpiCard } from '@/components/dashboard/KpiCard';
import { DecisionRecommendation } from '@/components/dashboard/DecisionRecommendation';
import { CargoTable } from '@/components/cargo/CargoTable';
import { AisVesselMap } from '@/components/maps/AisVesselMap';
import { FreightForecastChart } from '@/components/charts/FreightForecastChart';
import { Button } from '@/components/ui/Button';
import { BackButton } from '@/components/ui/BackButton';
import { getProcurementKpis } from '@/services/kpis';
import { getCargoRequirements } from '@/services/cargo';
import { getVessels } from '@/services/vessels';
import { getFreightForecast } from '@/services/forecasts';
import { getOptimizationRecommendation } from '@/services/optimization';
import { formatCurrency } from '@/lib/utils';
import { 
  Package, 
  TrendingUp, 
  DollarSign, 
  Scale, 
  Compass, 
  Plus, 
  ArrowRight,
  ShieldCheck,
  Ship,
  Clock
} from 'lucide-react';

export default function ProcurementDashboard() {
  const router = useRouter();

  // Queries
  const { data: kpis } = useQuery({
    queryKey: ['procurementKpis'],
    queryFn: getProcurementKpis,
  });

  const { data: cargoList = [] } = useQuery({
    queryKey: ['cargoRequirements'],
    queryFn: getCargoRequirements,
  });

  const { data: vessels = [] } = useQuery({
    queryKey: ['vessels'],
    queryFn: getVessels,
  });

  const { data: forecastData } = useQuery({
    queryKey: ['freightForecast', 'route-aus-paradip', 'Panamax'],
    queryFn: () => getFreightForecast('route-aus-paradip', 'Panamax', 14),
  });

  const { data: priorityRecommendation } = useQuery({
    queryKey: ['optimizationRecommendation', 'req-coal-75k'],
    queryFn: () => getOptimizationRecommendation('req-coal-75k'),
  });

  return (
    <div className="space-y-8">
      <BackButton href="/" label="Back to Home" />

      {/* Editorial Header */}
      <PageHeader
        title="Procurement Officer Intelligence Center"
        description="Dry bulk cargo matching, multi-objective charter recommendations, and freight rate timing predictions."
        badge="Active Operational Session"
        badgeVariant="default"
      >
        <Link href="/cargo/new">
          <Button variant="primary" size="md">
            <Plus className="h-4 w-4" />
            <span>Create Cargo Requirement</span>
          </Button>
        </Link>
      </PageHeader>

      {/* 4 Essential KPI Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Active Cargo Tenders"
          value={kpis?.activeCargoRequirements || 4}
          subtitle="245,000 MT Total In-Market"
          icon={Package}
        />

        <KpiCard
          title="Recommended Vessel"
          value={kpis?.matchedVesselsAvailable || 3}
          subtitle="MV PACIFIC STAR (94% Fit)"
          icon={Ship}
        />

        <KpiCard
          title="Benchmark Spot Rate"
          value={kpis ? `$${kpis.currentMarketSpotRateUsdPerMt}/MT` : '$24.50/MT'}
          subtitle="Hay Point → Paradip"
          icon={TrendingUp}
          change={{ value: '-$3.20/MT (3-day dip)', trend: 'DOWN', isPositive: true }}
        />

        <KpiCard
          title="Projected Charter Savings"
          value={kpis ? formatCurrency(kpis.projectedSavingsUsd) : '$240,000'}
          subtitle="By executing on optimal laycan"
          icon={DollarSign}
        />
      </div>

      {/* Primary Centerpiece: AI Charter Decision */}
      {priorityRecommendation && (
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-500 font-mono">
              Priority Charter Recommendation • 75k MT Coking Coal
            </h2>
            <Link href="/optimization" className="text-xs font-semibold text-black hover:underline flex items-center gap-1">
              <span>Full Decision Engine</span>
              <ArrowRight className="h-3 w-3" />
            </Link>
          </div>

          <DecisionRecommendation
            data={priorityRecommendation}
            onRequestOffer={(vesselMatch) => {
              router.push(`/charters?createForCargo=req-coal-75k&vesselId=${vesselMatch.vessel.id}`);
            }}
            onViewAlternativeVessels={() => {
              router.push('/charters/compare');
            }}
          />
        </section>
      )}

      {/* Active Cargo Tenders Table */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-bold uppercase tracking-wider text-zinc-500 font-mono">
            Active Cargo Requirements
          </h2>
          <Link href="/cargo" className="text-xs font-semibold text-black hover:underline">
            View All ({cargoList.length})
          </Link>
        </div>

        <CargoTable cargoList={cargoList} />
      </section>

      {/* GIS Nautical Map & ML Forecast Chart Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Real-Time AIS Fleet Map */}
        <div className="bg-white border border-zinc-200 rounded p-5 space-y-4 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-zinc-100">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-950 font-mono">
                Live AIS Ballast Locations & Navigational Corridor
              </h3>
              <p className="text-[11px] text-zinc-500">Bay of Bengal & Indian Ocean AIS Coordinates</p>
            </div>
            <Link href="/vessels">
              <Button variant="outline" size="sm">
                Full AIS Map
              </Button>
            </Link>
          </div>

          <AisVesselMap vessels={vessels} height="320px" />
        </div>

        {/* 14-Day Machine Learning Rate Forecast */}
        <div className="bg-white border border-zinc-200 rounded p-5 space-y-4 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-zinc-100">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-950 font-mono">
                ML Freight Rate Trajectory & 87% Confidence Band
              </h3>
              <p className="text-[11px] text-zinc-500">Australia FOB → Paradip (Panamax 75k DWT)</p>
            </div>
            <Link href="/forecasts">
              <Button variant="outline" size="sm">
                Forecaster Model
              </Button>
            </Link>
          </div>

          {forecastData ? (
            <FreightForecastChart data={forecastData.timeSeries} height={320} />
          ) : (
            <div className="h-[320px] flex items-center justify-center text-xs font-mono text-zinc-400">
              Loading probabilistic forecasting curve...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
