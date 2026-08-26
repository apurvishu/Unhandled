'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { KpiCard } from '@/components/dashboard/KpiCard';
import { Button } from '@/components/ui/Button';
import { getMarketData } from '@/services/market';
import { formatCurrency } from '@/lib/utils';
import { BarChart3, TrendingDown, TrendingUp, Fuel, Flame, Sparkles, Layers, DollarSign } from 'lucide-react';
import Link from 'next/link';

export default function MarketDashboardPage() {
  const { data: marketData } = useQuery({
    queryKey: ['marketData'],
    queryFn: getMarketData,
  });

  if (!marketData) {
    return <div className="p-8 text-slate-400">Loading market intelligence...</div>;
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <PageHeader
        title="Maritime Freight & Commodity Market Intelligence"
        description="Live freight indices, bunker fuel benchmarks, and bulk commodity prices integrated into ML forecasting features."
        badge="Market Intel Feed"
        badgeVariant="info"
      >
        <Link href="/forecasts">
          <Button variant="primary" size="md">
            <Sparkles className="h-4 w-4" />
            <span>Open ML Freight Forecaster</span>
          </Button>
        </Link>
      </PageHeader>

      {/* FREIGHT INDICES */}
      <section className="space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-sky-400" />
          <span>Baltic Exchange Freight Benchmark Indices</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            title="Baltic Dry Index (BDI)"
            value={marketData.balticDryIndex.current.toLocaleString()}
            subtitle="Benchmark Dry Bulk"
            icon={BarChart3}
            change={{
              value: `${marketData.balticDryIndex.change} (${marketData.balticDryIndex.changePercent}%)`,
              trend: 'DOWN',
              isPositive: true,
            }}
            variant="primary"
          />

          <KpiCard
            title="Baltic Panamax Index (BPI)"
            value={marketData.balticPanamaxIndex.current.toLocaleString()}
            subtitle="70k-85k MT Grain/Coal"
            icon={BarChart3}
            change={{
              value: `${marketData.balticPanamaxIndex.change} (${marketData.balticPanamaxIndex.changePercent}%)`,
              trend: 'DOWN',
              isPositive: true,
            }}
            variant="primary"
          />

          <KpiCard
            title="Singapore VLSFO Bunker"
            value={formatCurrency(marketData.bunkerFuelVlsfoUsdPerMt.singapore, 2)}
            subtitle="USD / Metric Ton"
            icon={Fuel}
            change={{ value: '-$18.50', trend: 'DOWN', isPositive: true, label: 'declining' }}
            variant="success"
          />

          <KpiCard
            title="Coking Coal (Australia FOB)"
            value={formatCurrency(marketData.commoditiesUsdPerMt.cokingCoal, 2)}
            subtitle="USD / Metric Ton"
            icon={Flame}
          />
        </div>
      </section>

      {/* BUNKER FUEL & COMMODITY PRICING TABLES */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bunker Fuel Matrix */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h4 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Fuel className="h-4 w-4 text-sky-400" />
              <span>Marine Bunker Fuel Price Index (VLSFO / MGO)</span>
            </h4>
            <span className="text-[10px] text-emerald-400 font-mono">Updated Today</span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
              <div>
                <strong className="text-white text-sm">Singapore Hub (VLSFO 0.5%)</strong>
                <p className="text-[10px] text-slate-400">Primary Pacific Bunkering Port</p>
              </div>
              <div className="text-right">
                <span className="text-sm font-black font-mono text-emerald-400">
                  {formatCurrency(marketData.bunkerFuelVlsfoUsdPerMt.singapore, 2)}
                </span>
                <span className="text-[10px] text-slate-400 block">USD/MT</span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
              <div>
                <strong className="text-white text-sm">Rotterdam Port (VLSFO 0.5%)</strong>
                <p className="text-[10px] text-slate-400">European Benchmark</p>
              </div>
              <div className="text-right">
                <span className="text-sm font-black font-mono text-slate-200">
                  {formatCurrency(marketData.bunkerFuelVlsfoUsdPerMt.rotterdam, 2)}
                </span>
                <span className="text-[10px] text-slate-400 block">USD/MT</span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
              <div>
                <strong className="text-white text-sm">Fujairah Anchorage (VLSFO 0.5%)</strong>
                <p className="text-[10px] text-slate-400">Middle East Bunkering Hub</p>
              </div>
              <div className="text-right">
                <span className="text-sm font-black font-mono text-slate-200">
                  {formatCurrency(marketData.bunkerFuelVlsfoUsdPerMt.fujairah, 2)}
                </span>
                <span className="text-[10px] text-slate-400 block">USD/MT</span>
              </div>
            </div>
          </div>
        </div>

        {/* Commodity Prices */}
        <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h4 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Flame className="h-4 w-4 text-amber-400" />
              <span>Bulk Commodity Benchmark Prices</span>
            </h4>
            <span className="text-[10px] text-slate-400 font-mono">FOB Spot Basis</span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
              <div>
                <strong className="text-white text-sm">Premium Coking Coal (Australia FOB)</strong>
                <p className="text-[10px] text-slate-400">Steel Metallurgical Grade</p>
              </div>
              <div className="text-right">
                <span className="text-sm font-black font-mono text-white">
                  {formatCurrency(marketData.commoditiesUsdPerMt.cokingCoal, 2)}
                </span>
                <span className="text-[10px] text-slate-400 block">USD/MT</span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
              <div>
                <strong className="text-white text-sm">Thermal Coal (Newcastle FOB 6,000 kcal)</strong>
                <p className="text-[10px] text-slate-400">Power Generation Grade</p>
              </div>
              <div className="text-right">
                <span className="text-sm font-black font-mono text-white">
                  {formatCurrency(marketData.commoditiesUsdPerMt.thermalCoal, 2)}
                </span>
                <span className="text-[10px] text-slate-400 block">USD/MT</span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
              <div>
                <strong className="text-white text-sm">Iron Ore Fines 62% Fe (CFR China)</strong>
                <p className="text-[10px] text-slate-400">High Grade Sinter Fines</p>
              </div>
              <div className="text-right">
                <span className="text-sm font-black font-mono text-white">
                  {formatCurrency(marketData.commoditiesUsdPerMt.ironOre62Percent, 2)}
                </span>
                <span className="text-[10px] text-slate-400 block">USD/MT</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
