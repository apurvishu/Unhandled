'use client';

import React, { useState } from 'react';
import { PageHeader } from '@/components/layout/PageHeader';
import { PortCallTimeline } from '@/components/voyages/PortCallTimeline';
import { WeatherCard } from '@/components/voyages/WeatherCard';
import { AisVesselMap } from '@/components/maps/AisVesselMap';
import { DEMO_VOYAGES } from '@/lib/demoData';
import { formatDwt, formatKnots, formatNauticalMiles } from '@/lib/utils';
import { Navigation, Ship, ShieldCheck } from 'lucide-react';
import { BackButton } from '@/components/ui/BackButton';

export default function VoyagesPage() {
  const [selectedVoyage] = useState(DEMO_VOYAGES[0]);

  return (
    <div className="space-y-8">
      <BackButton href="/" label="Back to Home" />

      <PageHeader
        title="Live Voyage Tracking & Port Call Timeline"
        description="End-to-end voyage monitoring, real-time AIS navigation corridor, milestone timestamps, and marine weather alerts."
        badge="Voyage Active: VOY-2026-042"
        badgeVariant="default"
      />

      {/* VOYAGE STATS BAR */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-white border border-zinc-200 rounded p-5 text-xs text-zinc-800 shadow-sm font-mono">
        <div>
          <span className="text-[10px] text-zinc-400 uppercase block font-sans">Active Vessel:</span>
          <strong className="text-zinc-950 text-sm font-bold flex items-center gap-1.5 mt-0.5 font-mono">
            <Ship className="h-4 w-4 text-zinc-800" />
            {selectedVoyage.vesselName}
          </strong>
          <span className="text-[10px] text-zinc-400 font-mono">IMO {selectedVoyage.imo}</span>
        </div>

        <div>
          <span className="text-[10px] text-zinc-400 uppercase block font-sans">Bulk Cargo:</span>
          <strong className="text-zinc-950 text-sm font-bold mt-0.5 block font-mono">
            {formatDwt(selectedVoyage.quantityMt)} {selectedVoyage.cargoType}
          </strong>
          <span className="text-[10px] text-zinc-500 font-sans">{selectedVoyage.originPort.split(' ')[0]} → {selectedVoyage.destinationPort.split(' ')[0]}</span>
        </div>

        <div>
          <span className="text-[10px] text-zinc-400 uppercase block font-sans">Speed / Progress:</span>
          <strong className="text-zinc-950 text-sm font-mono mt-0.5 block font-bold">
            {formatKnots(selectedVoyage.speedKnots)} ({selectedVoyage.milestonesProgressPercent}%)
          </strong>
          <span className="text-[10px] text-zinc-500 font-sans">Remaining: {formatNauticalMiles(selectedVoyage.remainingNauticalMiles)}</span>
        </div>

        <div>
          <span className="text-[10px] text-zinc-400 uppercase block font-sans">Discharge ETA:</span>
          <strong className="text-zinc-950 text-sm font-bold mt-0.5 block font-mono">
            {selectedVoyage.eta.split('T')[0]} 08:00 UTC
          </strong>
          <span className="text-[10px] text-emerald-800 font-sans font-bold">On Schedule</span>
        </div>
      </div>

      {/* MAP & WEATHER */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 font-mono flex items-center gap-2">
              <Navigation className="h-4 w-4 text-zinc-800" />
              <span>Great Circle Route & Navigation Corridor</span>
            </h3>
            <span className="text-xs text-zinc-500 font-mono">Total: {formatNauticalMiles(selectedVoyage.totalNauticalMiles)}</span>
          </div>
          <AisVesselMap height="460px" selectedVesselId={selectedVoyage.vesselId} />
        </div>

        <div className="space-y-4">
          <WeatherCard weather={selectedVoyage.weather} />

          <div className="bg-white border border-zinc-200 rounded p-4 text-xs space-y-3 shadow-sm font-mono">
            <h4 className="font-bold text-zinc-950 uppercase tracking-wider text-[11px] flex items-center gap-1.5 font-sans">
              <ShieldCheck className="h-4 w-4 text-emerald-700" />
              <span>Underway Safety Telemetry</span>
            </h4>
            <div className="space-y-2 text-zinc-700 text-[11px]">
              <div className="flex items-center justify-between">
                <span className="font-sans">Under Keel Clearance (UKC):</span>
                <strong className="text-zinc-950">3.4m Safety Margin</strong>
              </div>
              <div className="flex items-center justify-between">
                <span className="font-sans">Channel Depth Check:</span>
                <strong className="text-emerald-800">PASSED (17.5m)</strong>
              </div>
              <div className="flex items-center justify-between">
                <span className="font-sans">Daily Fuel Burn Rate:</span>
                <span className="text-zinc-900">26 MT / day</span>
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
