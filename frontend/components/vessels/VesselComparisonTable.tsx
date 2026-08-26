'use client';

import React from 'react';
import { VesselMatch } from '@/types';
import { Button } from '@/components/ui/Button';
import { formatCurrency, formatDwt, formatNauticalMiles, getCongestionBadgeColor } from '@/lib/utils';
import { Check, X, Sparkles, ArrowRight } from 'lucide-react';

export interface VesselComparisonTableProps {
  matches: VesselMatch[];
  onRequestOffer?: (match: VesselMatch) => void;
}

export const VesselComparisonTable: React.FC<VesselComparisonTableProps> = ({
  matches,
  onRequestOffer,
}) => {
  return (
    <div className="w-full overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60 shadow-xl">
      <table className="w-full text-left text-xs text-slate-300">
        <thead className="bg-slate-950 text-[10px] uppercase font-bold text-slate-400 border-b border-slate-800 tracking-wider">
          <tr>
            <th className="py-4 px-4 sticky left-0 bg-slate-950 z-10 w-48">Feature / Metric</th>
            {matches.map((m, idx) => (
              <th key={m.vessel.id} className="py-4 px-4 min-w-[200px]">
                <div className="flex items-center justify-between">
                  <span className="font-extrabold text-white text-sm">{m.vessel.name}</span>
                  {idx === 0 && (
                    <span className="px-2 py-0.5 rounded bg-sky-500/20 text-sky-400 border border-sky-500/30 text-[9px]">
                      RECOMMENDED
                    </span>
                  )}
                </div>
                <p className="text-[10px] text-slate-400 font-normal mt-0.5">{m.vessel.type} • IMO {m.vessel.imo}</p>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60 font-medium">
          {/* Match Score */}
          <tr className="hover:bg-slate-800/30">
            <td className="py-3 px-4 font-bold text-slate-300 sticky left-0 bg-slate-900/90 z-10">AI Match Score</td>
            {matches.map((m) => (
              <td key={m.vessel.id} className="py-3 px-4">
                <span className="text-base font-black font-mono text-emerald-400">{m.matchScorePercent}%</span>
              </td>
            ))}
          </tr>

          {/* Freight Rate */}
          <tr className="hover:bg-slate-800/30">
            <td className="py-3 px-4 font-bold text-slate-300 sticky left-0 bg-slate-900/90 z-10">Freight Rate ($/MT)</td>
            {matches.map((m) => (
              <td key={m.vessel.id} className="py-3 px-4 font-mono font-bold text-white text-sm">
                {formatCurrency(m.freightRateUsdPerMt, 2)}
              </td>
            ))}
          </tr>

          {/* Estimated Total Voyage Cost */}
          <tr className="hover:bg-slate-800/30">
            <td className="py-3 px-4 font-bold text-slate-300 sticky left-0 bg-slate-900/90 z-10">Est. Total Cost</td>
            {matches.map((m) => (
              <td key={m.vessel.id} className="py-3 px-4 font-mono font-semibold text-slate-200">
                {formatCurrency(m.estimatedTotalCostUsd)}
              </td>
            ))}
          </tr>

          {/* Target ETA */}
          <tr className="hover:bg-slate-800/30">
            <td className="py-3 px-4 font-bold text-slate-300 sticky left-0 bg-slate-900/90 z-10">Estimated Arrival (ETA)</td>
            {matches.map((m) => (
              <td key={m.vessel.id} className="py-3 px-4 text-slate-100 font-semibold">
                {m.eta}
              </td>
            ))}
          </tr>

          {/* DWT Capacity */}
          <tr className="hover:bg-slate-800/30">
            <td className="py-3 px-4 font-bold text-slate-300 sticky left-0 bg-slate-900/90 z-10">Deadweight (DWT)</td>
            {matches.map((m) => (
              <td key={m.vessel.id} className="py-3 px-4 font-mono text-slate-200">
                {formatDwt(m.vessel.dwt)}
              </td>
            ))}
          </tr>

          {/* Distance */}
          <tr className="hover:bg-slate-800/30">
            <td className="py-3 px-4 font-bold text-slate-300 sticky left-0 bg-slate-900/90 z-10">Distance to Origin</td>
            {matches.map((m) => (
              <td key={m.vessel.id} className="py-3 px-4 font-mono text-slate-200">
                {formatNauticalMiles(m.distanceNauticalMiles)}
              </td>
            ))}
          </tr>

          {/* Congestion Risk */}
          <tr className="hover:bg-slate-800/30">
            <td className="py-3 px-4 font-bold text-slate-300 sticky left-0 bg-slate-900/90 z-10">Congestion Risk</td>
            {matches.map((m) => {
              const b = getCongestionBadgeColor(m.congestionRisk);
              return (
                <td key={m.vessel.id} className="py-3 px-4">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${b.bg} ${b.text} ${b.border}`}>
                    {m.congestionRisk}
                  </span>
                </td>
              );
            })}
          </tr>

          {/* Draft Fit */}
          <tr className="hover:bg-slate-800/30">
            <td className="py-3 px-4 font-bold text-slate-300 sticky left-0 bg-slate-900/90 z-10">Draft / Channel Fit</td>
            {matches.map((m) => (
              <td key={m.vessel.id} className="py-3 px-4 text-emerald-400 font-semibold flex items-center gap-1">
                <Check className="h-4 w-4" /> <span>Fit ({m.vessel.maxDraft}m)</span>
              </td>
            ))}
          </tr>

          {/* Fuel Consumption */}
          <tr className="hover:bg-slate-800/30">
            <td className="py-3 px-4 font-bold text-slate-300 sticky left-0 bg-slate-900/90 z-10">Fuel Consumption</td>
            {matches.map((m) => (
              <td key={m.vessel.id} className="py-3 px-4 text-slate-200">
                {m.vessel.fuelConsumptionMtPerDay} MT / day
              </td>
            ))}
          </tr>

          {/* Direct Request Action */}
          <tr className="bg-slate-950/40">
            <td className="py-4 px-4 sticky left-0 bg-slate-950 z-10 font-bold text-slate-300">Action</td>
            {matches.map((m, idx) => (
              <td key={m.vessel.id} className="py-4 px-4">
                <Button
                  variant={idx === 0 ? 'primary' : 'secondary'}
                  size="sm"
                  className="w-full"
                  onClick={() => onRequestOffer ? onRequestOffer(m) : null}
                >
                  <span>Select & Request</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </td>
            ))}
          </tr>
        </tbody>
      </table>
    </div>
  );
};
