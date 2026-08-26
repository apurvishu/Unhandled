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
import { getCargoRequirements } from '@/services/cargo';
import { getOptimizationRecommendation } from '@/services/optimization';
import { getFreightForecast } from '@/services/forecasts';
import { 
  PackagePlus, 
  Boxes, 
  FileText, 
  TrendingDown, 
  Clock, 
  DollarSign, 
  Sparkles, 
  Ship, 
  ArrowRight,
  Scale
} from 'lucide-react';
import { formatCurrency } from '@/lib/utils';

export default function ProcurementDashboardPage() {
  const router = useRouter();

  // Fetch cargo requirements
  const { data: cargoList = [], isLoading: isLoadingCargo } = useQuery({
    queryKey: ['cargoRequirements'],
    queryFn: getCargoRequirements,
  });

  // Fetch AI optimization recommendation for prime cargo (75k MT Coal)
  const { data: optimizationData, isLoading: isLoadingOpt } = useQuery({
    queryKey: ['optimizationRecommendation', 'req-coal-75k'],
    queryFn: () => getOptimizationRecommendation('req-coal-75k'),
  });

  // Fetch Freight forecast
  const { data: forecastData } = useQuery({
    queryKey: ['freightForecast'],
    queryFn: () => getFreightForecast(),
  });

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <PageHeader
        title="Procurement Officer Intelligence Center"
        description="Optimize bulk cargo procurement, AI charter recommendations, and real-time voyage matching."
        badge="Decision Engine Active"
        badgeVariant="success"
      >
        <Link href="/cargo/new">
          <Button variant="primary" size="md" className="font-bold">
            <PackagePlus className="h-4 w-4" />
            <span>Create Cargo Requirement</span>
          </Button>
        </Link>
        <Link href="/charters/compare">
          <Button variant="secondary" size="md">
            <Scale className="h-4 w-4" />
            <span>Compare Vessels</span>
          </Button>
        </Link>
      </PageHeader>

      {/* 7 KPI SECTION */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
        <KpiCard
          title="Active Cargo"
          value={cargoList.length || 2}
          subtitle="Open tenders"
          icon={Boxes}
          variant="primary"
        />

        <KpiCard
          title="Open Charters"
          value="3"
          subtitle="Offers pending"
          icon={FileText}
        />

        <KpiCard
          title="Current Freight"
          value="$24.80"
          subtitle="USD / MT (Panamax)"
          icon={DollarSign}
        />

        <KpiCard
          title="Forecast Freight"
          value="$23.75"
          subtitle="Expected in 3 days"
          icon={TrendingDown}
          change={{ value: '-4.2%', trend: 'DOWN', isPositive: true, label: 'decline' }}
          variant="success"
        />

        <KpiCard
          title="Avg Congestion"
          value="34.5h"
          subtitle="Paradip discharge"
          icon={Clock}
          change={{ value: '-13.5h', trend: 'DOWN', isPositive: true, label: 'improving' }}
          variant="warning"
        />

        <KpiCard
          title="Est. Savings"
          value="+$78.7K"
          subtitle="Via AI timing"
          icon={Sparkles}
          variant="success"
        />
      </div>

      {/* THE MOST IMPORTANT COMPONENT: AI CHARTER DECISION RECOMMENDATION */}
      {optimizationData && (
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-sky-400" />
              <span>Priority Charter Recommendation</span>
            </h2>
            <span className="text-xs text-slate-400">Generated from ML Forecasting & Vessel Matching Engine</span>
          </div>

          <DecisionRecommendation
            data={optimizationData}
            onRequestOffer={(vesselMatch) => {
              router.push(`/charters?createForCargo=${optimizationData.cargoRequirement.id}&vesselId=${vesselMatch.vessel.id}`);
            }}
          />
        </section>
      )}

      {/* ACTIVE CARGO REQUIREMENTS TABLE */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Boxes className="h-4 w-4 text-sky-400" />
              <span>Active Bulk Cargo Requirements</span>
            </h2>
            <p className="text-xs text-slate-400">Manage tenders and trigger AI vessel matching</p>
          </div>

          <Link href="/cargo/new">
            <Button variant="outline" size="sm">
              <PackagePlus className="h-3.5 w-3.5" />
              <span>Add Requirement</span>
            </Button>
          </Link>
        </div>

        <CargoTable items={cargoList} />
      </section>

      {/* INTERACTIVE AIS MAP & FORECAST PREVIEW */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Ship className="h-4 w-4 text-sky-400" />
              <span>Live AIS Fleet & Route Tracking</span>
            </h3>
            <Link href="/vessels" className="text-xs text-sky-400 hover:text-sky-300">
              Full Map →
            </Link>
          </div>
          <AisVesselMap height="360px" />
        </section>

        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <TrendingDown className="h-4 w-4 text-teal-400" />
              <span>14-Day Freight Rate ML Forecast</span>
            </h3>
            <Link href="/forecasts" className="text-xs text-sky-400 hover:text-sky-300">
              Full Model →
            </Link>
          </div>
          {forecastData && (
            <FreightForecastChart
              data={forecastData.timeSeries}
              currentRate={forecastData.currentRateUsdPerMt}
              predictedRate={forecastData.predictedRateUsdPerMt}
              height={300}
            />
          )}
        </section>
      </div>
    </div>
  );
}
