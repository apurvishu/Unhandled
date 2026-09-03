'use client';

import { BackButton } from '@/components/ui/BackButton';
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { KpiCard } from '@/components/dashboard/KpiCard';
import { FreightForecastChart } from '@/components/charts/FreightForecastChart';
import { Button } from '@/components/ui/Button';
import { Select } from '@/components/ui/Input';
import { getFreightForecast } from '@/services/forecasts';
import { VesselType } from '@/types';
import { VESSEL_TYPES } from '@/config/constants';
import { formatCurrency } from '@/lib/utils';
import { 
  TrendingDown, 
  TrendingUp, 
  Calendar, 
  CheckCircle2, 
  Clock, 
  Sparkles,
  Info
} from 'lucide-react';

export default function ForecastsPage() {
  const [selectedRoute, setSelectedRoute] = useState('route-aus-paradip');
  const [selectedVesselType, setSelectedVesselType] = useState<VesselType>('Panamax');
  const [horizonDays, setHorizonDays] = useState(14);

  const { data: forecast, isLoading } = useQuery({
    queryKey: ['freightForecast', selectedRoute, selectedVesselType, horizonDays],
    queryFn: () => getFreightForecast(selectedRoute, selectedVesselType, horizonDays),
  });

  const routes = [
    { value: 'route-aus-paradip', label: 'Australia (Hay Point) → India (Paradip) — Coal' },
    { value: 'route-aus-vizag', label: 'Australia (Port Hedland) → India (Visakhapatnam) — Iron Ore' },
    { value: 'route-indo-haldia', label: 'Indonesia (Taboneo) → India (Haldia) — Thermal Coal' },
    { value: 'route-safrica-dhamra', label: 'South Africa (Richards Bay) → India (Dhamra) — Coal' },
  ];

  return (
    <div className="space-y-8">
      <BackButton href="/" label="Back to Home" />

      <PageHeader
        title="ML Freight Rate Forecasting Engine"
        description="Probabilistic deep learning rate trajectory models with 87% prediction interval bands and actionable laycan timing signals."
        badge="Maritime-Transformer-v4.2"
        badgeVariant="default"
      />

      {/* Control Filters Bar */}
      <div className="bg-white border border-zinc-200 rounded p-4 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex-1 max-w-lg">
          <Select
            label="Shipping Corridor"
            value={selectedRoute}
            onChange={(e) => setSelectedRoute(e.target.value)}
            options={routes}
          />
        </div>

        <div className="flex items-center gap-4 flex-wrap">
          <div className="w-36">
            <Select
              label="Vessel Class"
              value={selectedVesselType}
              onChange={(e) => setSelectedVesselType(e.target.value as VesselType)}
              options={VESSEL_TYPES.map((t) => ({ value: t, label: t }))}
            />
          </div>

          <div className="space-y-1">
            <label className="block text-xs font-semibold uppercase tracking-wider text-zinc-600">
              Horizon
            </label>
            <div className="flex items-center gap-1">
              {[7, 14, 30].map((d) => (
                <Button
                  key={d}
                  variant={horizonDays === d ? 'primary' : 'outline'}
                  size="sm"
                  onClick={() => setHorizonDays(d)}
                >
                  {d}D
                </Button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 4 Core Forecast KPI Cards */}
      {forecast && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            title="Current Spot Rate"
            value={`$${(forecast.currentRateUsdPerMt || 24.8).toFixed(2)}/MT`}
            subtitle="Today's Market Benchmark"
            icon={TrendingDown}
          />

          <KpiCard
            title="14-Day Forecast Rate"
            value={`$${(forecast.predictedRateUsdPerMt || 23.75).toFixed(2)}/MT`}
            subtitle="Projected Rate Low"
            icon={TrendingDown}
            change={{
              value: `${(forecast.expectedChangePercent || -4.2).toFixed(1)}%`,
              trend: 'DOWN',
              isPositive: true,
            }}
          />

          <KpiCard
            title="Optimal Charter Window"
            value="Sep 18 - 21"
            subtitle="Peak Rate Cost Minimum"
            icon={Calendar}
          />

          <KpiCard
            title="Projected Savings"
            value={formatCurrency(forecast.estimatedPotentialSavingsUsd || 78750)}
            subtitle="On 75,000 MT Bulk Cargo"
            icon={Clock}
          />
        </div>
      )}


      {/* Forecast Chart */}
      <section className="bg-white border border-zinc-200 rounded p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-zinc-100">
          <div>
            <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-950 font-mono">
              Historical Spot vs. Machine Learning Predicted Trajectory
            </h3>
            <p className="text-xs text-zinc-500">Includes upper and lower 87% confidence interval boundaries</p>
          </div>
          <span className="text-xs font-mono text-zinc-500">Unit: USD / Metric Ton</span>
        </div>

        {forecast ? (
          <FreightForecastChart data={forecast.timeSeries} height={360} />
        ) : (
          <div className="h-[360px] flex items-center justify-center text-xs font-mono text-zinc-400">
            Running ML inference...
          </div>
        )}
      </section>

      {/* ML Decision Rationale Block */}
      {forecast && (
        <section className="bg-zinc-50 border border-zinc-200 rounded p-6 space-y-4">
          <div className="flex items-center gap-2">
            <Info className="h-4 w-4 text-zinc-900" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-950 font-mono">
              Machine Learning Driver Analysis & Timing Strategy
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-white border border-zinc-200 rounded space-y-2">
              <h4 className="font-bold text-zinc-950 font-mono">Key Macro Drivers Influencing Forecast:</h4>
              <ul className="space-y-1 text-zinc-700 list-disc list-inside">
                <li>Singapore VLSFO bunker fuel prices down 2.8% week-over-week ($615/MT).</li>
                <li>East Coast India port queues easing by 13.5 hours over the next 3 days.</li>
                <li>Pacific basin ballast vessel supply expanding by +4 Panamax carriers.</li>
              </ul>
            </div>

            <div className="p-4 bg-white border border-zinc-200 rounded space-y-2">
              <h4 className="font-bold text-zinc-950 font-mono">Actionable Procurement Advice:</h4>
              <p className="text-zinc-700 leading-relaxed">
                <strong>RECOMMENDATION: DELAY CHARTER BY 3 DAYS.</strong> Lock in laycan window starting Sep 18-21 to capture the estimated $3.20/MT rate drop, saving up to $240,000 on a 75,000 MT tender.
              </p>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
