'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { KpiCard } from '@/components/dashboard/KpiCard';
import { FreightForecastChart } from '@/components/charts/FreightForecastChart';
import { Button } from '@/components/ui/Button';
import { Select } from '@/components/ui/Input';
import { getFreightForecast } from '@/services/forecasts';
import { VesselType } from '@/types';
import { VESSEL_TYPES, MAJOR_PORTS } from '@/config/constants';
import { formatCurrency } from '@/lib/utils';
import { 
  TrendingDown, 
  TrendingUp, 
  Sparkles, 
  ShieldCheck, 
  Clock, 
  Cpu, 
  DollarSign, 
  Calendar,
  AlertTriangle,
  Layers,
  ArrowRight
} from 'lucide-react';
import Link from 'next/link';

export default function FreightForecastingPage() {
  const [origin, setOrigin] = useState('port-haypoint');
  const [destination, setDestination] = useState('port-paradip');
  const [vesselType, setVesselType] = useState<VesselType>('Panamax');
  const [horizon, setHorizon] = useState<number>(14);

  const { data: forecast, isLoading, refetch } = useQuery({
    queryKey: ['freightForecast', origin, destination, vesselType, horizon],
    queryFn: () => getFreightForecast({ vesselType, horizonDays: horizon }),
  });

  const isWait = forecast?.recommendation === 'WAIT';
  const confidence = forecast ? Math.round(forecast.confidenceScore * 100) : 87;

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <PageHeader
        title="ML Freight Rate Forecasting Engine"
        description="Probabilistic deep learning model predicting bulk freight rates, confidence intervals, and optimal charter timing."
        badge={`ML Model: ${forecast?.modelMetadata.modelName || 'Maritime-Transformer-v4.2'}`}
        badgeVariant="purple"
      >
        <Link href="/optimization">
          <Button variant="primary" size="md" className="font-bold">
            <Sparkles className="h-4 w-4" />
            <span>Apply to Charter Decision</span>
          </Button>
        </Link>
      </PageHeader>

      {/* PARAMETER CONTROLS */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-xl backdrop-blur-md">
        <div className="flex items-center gap-2 mb-4 text-xs font-bold uppercase tracking-wider text-slate-300">
          <Cpu className="h-4 w-4 text-sky-400" />
          <span>Forecasting Parameters & Route Selection</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Select
            label="Origin Port (Loading)"
            value={origin}
            onChange={(e) => setOrigin(e.target.value)}
            options={MAJOR_PORTS.map((p) => ({ value: p.id, label: `${p.name} (${p.country})` }))}
          />

          <Select
            label="Destination Port (Discharge)"
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            options={MAJOR_PORTS.map((p) => ({ value: p.id, label: `${p.name} (${p.country})` }))}
          />

          <Select
            label="Vessel Class"
            value={vesselType}
            onChange={(e) => setVesselType(e.target.value as VesselType)}
            options={VESSEL_TYPES.map((t) => ({ value: t, label: t }))}
          />

          <Select
            label="Forecast Horizon"
            value={String(horizon)}
            onChange={(e) => setHorizon(parseInt(e.target.value))}
            options={[
              { value: '7', label: '7 Days Ahead' },
              { value: '14', label: '14 Days Ahead' },
              { value: '30', label: '30 Days Ahead' },
            ]}
          />
        </div>
      </div>

      {/* 5 KEY FORECAST METRICS */}
      {forecast && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          <KpiCard
            title="Current Spot Freight"
            value={formatCurrency(forecast.currentRateUsdPerMt, 2)}
            subtitle="USD / Metric Ton"
            icon={DollarSign}
          />

          <KpiCard
            title="Predicted Freight"
            value={formatCurrency(forecast.predictedRateUsdPerMt, 2)}
            subtitle={`In ${horizon} Days`}
            icon={TrendingDown}
            variant={isWait ? 'success' : 'warning'}
          />

          <KpiCard
            title="Expected Delta"
            value={`${forecast.expectedChangePercent > 0 ? '+' : ''}${forecast.expectedChangePercent.toFixed(1)}%`}
            subtitle="Price movement"
            icon={forecast.trend === 'DECREASING' ? TrendingDown : TrendingUp}
            change={{
              value: `${forecast.expectedChangePercent.toFixed(1)}%`,
              trend: forecast.trend === 'DECREASING' ? 'DOWN' : 'UP',
              isPositive: forecast.trend === 'DECREASING',
            }}
            variant="primary"
          />

          <KpiCard
            title="Model Confidence"
            value={`${confidence}%`}
            subtitle="MAE: 0.42 • RMSE: 0.61"
            icon={ShieldCheck}
            variant="success"
          />

          <KpiCard
            title="Market Trend"
            value={forecast.trend}
            subtitle="Probabilistic signal"
            icon={Sparkles}
            variant={isWait ? 'warning' : 'primary'}
          />
        </div>
      )}

      {/* RECHARTS ML FORECAST VISUALIZATION */}
      {forecast && (
        <FreightForecastChart
          data={forecast.timeSeries}
          currentRate={forecast.currentRateUsdPerMt}
          predictedRate={forecast.predictedRateUsdPerMt}
          height={400}
        />
      )}

      {/* EXPLAINABLE AI CHARTER RECOMMENDATION CARD */}
      {forecast && (
        <div className={`rounded-2xl border p-6 bg-gradient-to-b from-slate-900 to-slate-950 shadow-2xl space-y-4 ${
          isWait ? 'border-amber-500/40 shadow-glow-amber' : 'border-emerald-500/40 shadow-glow-green'
        }`}>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
            <div className="flex items-center gap-3">
              <div className={`p-2.5 rounded-xl border ${
                isWait ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
              }`}>
                <Clock className="h-6 w-6" />
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">AI Timing Strategy</span>
                <h3 className={`text-2xl font-black ${isWait ? 'text-amber-300' : 'text-emerald-300'}`}>
                  {isWait ? `WAIT ${forecast.recommendationDaysToWait || 3} DAYS BEFORE CHARTERING` : 'BOOK NOW IMMEDIATELY'}
                </h3>
              </div>
            </div>

            <div className="text-right">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Est. Cost Savings</span>
              <span className="text-xl font-extrabold text-emerald-400 font-mono">
                +{formatCurrency(forecast.estimatedPotentialSavingsUsd)}
              </span>
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
              Explainable AI: Model Rationale & Drivers
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-slate-300">
              {forecast.reasons.map((reason, idx) => (
                <div key={idx} className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl flex items-start gap-2.5">
                  <span className="h-4 w-4 rounded-full bg-sky-500/20 text-sky-400 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                    {idx + 1}
                  </span>
                  <p className="leading-relaxed">{reason}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
