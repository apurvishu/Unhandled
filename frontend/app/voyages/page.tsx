'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { PageHeader } from '@/components/layout/PageHeader';
import { PortCallTimeline } from '@/components/voyages/PortCallTimeline';
import { WeatherCard } from '@/components/voyages/WeatherCard';
import { AisVesselMap } from '@/components/maps/AisVesselMap';
import { Button } from '@/components/ui/Button';
import { DEMO_VOYAGES } from '@/lib/demoData';
import { formatCurrency, formatDwt, formatKnots, formatNauticalMiles } from '@/lib/utils';
import { Navigation, Ship, Anchor, Clock, Wind, ArrowRight, ShieldCheck, MapPin } from 'lucide-react';

export default function VoyagesPage() {
  const [selectedVoyage, setSelectedVoyage] = useState(DEMO_VOYAGES[0]);

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <PageHeader
        title="Live Voyage Tracking & Port Call Timeline"
        description="End-to-end voyage monitoring, real-time AIS navigation corridor, milestone timestamps, and marine weather alerts."
        badge="Voyage Active: VOY-2026-042"
        badgeVariant="success"
      />

      {/* VOYAGE KPI BAR */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-slate-900/80 border border-slate-800 rounded-2xl p-5 text-xs text-slate-300">
        <div>
          <span className="text-[10px] text-slate-400 uppercase block font-semibold">Active Vessel:</span>
          <strong className="text-white text-sm font-bold flex items-center gap-1.5 mt-0.5">
            <Ship className="h-4 w-4 text-sky-400" />
            {selectedVoyage.vesselName}
          </strong>
          <span className="text-[10px] text-slate-500 font-mono">IMO: {selectedVoyage.imo}</span>
        </div>

        <div>
          <span className="text-[10px] text-slate-400 uppercase block font-semibold">Bulk Cargo:</span>
          <strong className="text-slate-100 text-sm font-bold mt-0.5 block">
            {formatDwt(selectedVoyage.quantityMt)} {selectedVoyage.cargoType}
          </strong>
          <span className="text-[10px] text-slate-500">{selectedVoyage.originPort.split(' ')[0]} → {selectedVoyage.destinationPort.split(' ')[0]}</span>
        </div>

        <div>
          <span className="text-[10px] text-slate-400 uppercase block font-semibold">Current Speed / Progress:</span>
          <strong className="text-emerald-400 text-sm font-mono mt-0.5 block">
            {formatKnots(selectedVoyage.speedKnots)} ({selectedVoyage.milestonesProgressPercent}% Completed)
          </strong>
          <span className="text-[10px] text-slate-500">Remaining: {formatNauticalMiles(selectedVoyage.remainingNauticalMiles)}</span>
        </div>

        <div>
          <span className="text-[10px] text-slate-400 uppercase block font-semibold">Target Discharge ETA:</span>
          <strong className="text-sky-300 text-sm font-bold mt-0.5 block">
            {selectedVoyage.eta.split('T')[0]} 08:00 UTC
          </strong>
          <span className="text-[10px] text-emerald-400 font-medium">On Schedule</span>
        </div>
      </div>

      {/* MAP & WEATHER */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <Navigation className="h-4 w-4 text-sky-400" />
              <span>Great Circle Route & Navigation Corridor</span>
            </h3>
            <span className="text-xs text-slate-400 font-mono">Total: {formatNauticalMiles(selectedVoyage.totalNauticalMiles)}</span>
          </div>
          <AisVesselMap height="460px" selectedVesselId={selectedVoyage.vesselId} />
        </div>

        <div className="space-y-4">
          <WeatherCard weather={selectedVoyage.weather} />

          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 text-xs space-y-3">
            <h4 className="font-bold text-slate-200 uppercase tracking-wider text-[11px] flex items-center gap-1.5">
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              <span>Underway Safety Telemetry</span>
            </h4>
            <div className="space-y-2 text-slate-300">
              <div className="flex items-center justify-between">
                <span>Under Keel Clearance (UKC):</span>
                <strong className="text-emerald-400 font-mono">3.4m Safety Margin</strong>
              </div>
              <div className="flex items-center justify-between">
                <span>Channel Bathymetry Check:</span>
                <strong className="text-emerald-400">PASSED (Paradip 17.5m)</strong>
              </div>
              <div className="flex items-center justify-between">
                <span>Daily Fuel Burn Rate:</span>
                <span className="font-mono text-slate-200">26 MT / day</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* PORT CALL MILESTONE TIMELINE */}
      <section>
        <PortCallTimeline
          portCalls={selectedVoyage.portCalls}
          currentMilestone={selectedVoyage.currentMilestone}
        />
      </section>
    </div>
  );
}
