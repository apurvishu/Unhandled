'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { KpiCard } from '@/components/dashboard/KpiCard';
import { Button } from '@/components/ui/Button';
import { getMarketData } from '@/services/market';
import { formatCurrency } from '@/lib/utils';
import { BarChart3, Fuel, Flame, ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { BackButton } from '@/components/ui/BackButton';

export default function MarketDashboardPage() {
  const { data: marketData } = useQuery({
    queryKey: ['marketData'],
    queryFn: getMarketData,
  });

  if (!marketData) {
    return <div className="p-8 text-xs font-mono text-zinc-500">Loading market intelligence...</div>;
  }

  return (
    <div className="space-y-8">
      <BackButton href="/" label="Back to Home" />

      <PageHeader
        title="Maritime Freight & Commodity Market Intelligence"
        description="Live freight indices, bunker fuel benchmarks, and bulk commodity prices integrated into ML forecasting features."
        badge="Market Intel Feed"
        badgeVariant="default"
      >
        <Link href="/forecasts">
          <Button variant="primary" size="md">
            <span>Open ML Freight Forecaster</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Button>
        </Link>
      </PageHeader>

      {/* FREIGHT INDICES */}
      <section className="space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 font-mono flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-zinc-800" />
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
          />

          <KpiCard
            title="Singapore VLSFO Bunker"
            value={formatCurrency(marketData.bunkerFuelVlsfoUsdPerMt.singapore, 2)}
            subtitle="USD / Metric Ton"
            icon={Fuel}
            change={{ value: '-$18.50', trend: 'DOWN', isPositive: true, label: 'declining' }}
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
        <div className="bg-white border border-zinc-200 rounded p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-zinc-100">
            <h4 className="text-xs font-bold text-zinc-950 uppercase tracking-wider font-mono flex items-center gap-2">
              <Fuel className="h-4 w-4 text-zinc-800" />
              <span>Marine Bunker Fuel Price Index (VLSFO / MGO)</span>
            </h4>
            <span className="text-[10px] text-zinc-500 font-mono font-bold">Updated Today</span>
          </div>

          <div className="space-y-2 text-xs font-mono">
            <div className="p-3 rounded bg-zinc-50 border border-zinc-200 flex items-center justify-between">
              <div>
                <strong className="text-zinc-950 font-sans">Singapore Hub (VLSFO 0.5%)</strong>
                <p className="text-[10px] text-zinc-500 font-sans">Primary Pacific Bunkering Port</p>
              </div>
              <div className="text-right">
                <span className="text-sm font-bold text-zinc-950">
                  {formatCurrency(marketData.bunkerFuelVlsfoUsdPerMt.singapore, 2)}
                </span>
                <span className="text-[10px] text-zinc-400 block font-sans">USD/MT</span>
              </div>
            </div>

            <div className="p-3 rounded bg-zinc-50 border border-zinc-200 flex items-center justify-between">
              <div>
                <strong className="text-zinc-950 font-sans">Rotterdam Port (VLSFO 0.5%)</strong>
                <p className="text-[10px] text-zinc-500 font-sans">European Benchmark</p>
              </div>
              <div className="text-right">
                <span className="text-sm font-bold text-zinc-950">
                  {formatCurrency(marketData.bunkerFuelVlsfoUsdPerMt.rotterdam, 2)}
                </span>
                <span className="text-[10px] text-zinc-400 block font-sans">USD/MT</span>
              </div>
            </div>

            <div className="p-3 rounded bg-zinc-50 border border-zinc-200 flex items-center justify-between">
              <div>
                <strong className="text-zinc-950 font-sans">Fujairah Anchorage (VLSFO 0.5%)</strong>
                <p className="text-[10px] text-zinc-500 font-sans">Middle East Bunkering Hub</p>
              </div>
              <div className="text-right">
                <span className="text-sm font-bold text-zinc-950">
                  {formatCurrency(marketData.bunkerFuelVlsfoUsdPerMt.fujairah, 2)}
                </span>
                <span className="text-[10px] text-zinc-400 block font-sans">USD/MT</span>
              </div>
            </div>
          </div>
        </div>

        {/* Commodity Prices */}
        <div className="bg-white border border-zinc-200 rounded p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-zinc-100">
            <h4 className="text-xs font-bold text-zinc-950 uppercase tracking-wider font-mono flex items-center gap-2">
              <Flame className="h-4 w-4 text-zinc-800" />
              <span>Bulk Commodity Benchmark Prices</span>
            </h4>
            <span className="text-[10px] text-zinc-500 font-mono">FOB Spot Basis</span>
          </div>

          <div className="space-y-2 text-xs font-mono">
            <div className="p-3 rounded bg-zinc-50 border border-zinc-200 flex items-center justify-between">
              <div>
                <strong className="text-zinc-950 font-sans">Premium Coking Coal (Australia FOB)</strong>
                <p className="text-[10px] text-zinc-500 font-sans">Steel Metallurgical Grade</p>
              </div>
              <div className="text-right">
                <span className="text-sm font-bold text-zinc-950">
                  {formatCurrency(marketData.commoditiesUsdPerMt.cokingCoal, 2)}
                </span>
                <span className="text-[10px] text-zinc-400 block font-sans">USD/MT</span>
              </div>
            </div>

            <div className="p-3 rounded bg-zinc-50 border border-zinc-200 flex items-center justify-between">
              <div>
                <strong className="text-zinc-950 font-sans">Thermal Coal (Newcastle FOB 6,000 kcal)</strong>
                <p className="text-[10px] text-zinc-500 font-sans">Power Generation Grade</p>
              </div>
              <div className="text-right">
                <span className="text-sm font-bold text-zinc-950">
                  {formatCurrency(marketData.commoditiesUsdPerMt.thermalCoal, 2)}
                </span>
                <span className="text-[10px] text-zinc-400 block font-sans">USD/MT</span>
              </div>
            </div>

            <div className="p-3 rounded bg-zinc-50 border border-zinc-200 flex items-center justify-between">
              <div>
                <strong className="text-zinc-950 font-sans">Iron Ore Fines 62% Fe (CFR China)</strong>
                <p className="text-[10px] text-zinc-500 font-sans">High Grade Sinter Fines</p>
              </div>
              <div className="text-right">
                <span className="text-sm font-bold text-zinc-950">
                  {formatCurrency(marketData.commoditiesUsdPerMt.ironOre62Percent, 2)}
                </span>
                <span className="text-[10px] text-zinc-400 block font-sans">USD/MT</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
