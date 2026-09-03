'use client';

import React from 'react';
import { VesselMatch } from '@/types';
import { formatCurrency, formatDwt, formatNauticalMiles } from '@/lib/utils';
import { Button } from '@/components/ui/Button';
import { ArrowRight } from 'lucide-react';

interface VesselComparisonTableProps {
  matches: VesselMatch[];
  onRequestOffer?: (match: VesselMatch) => void;
}

export const VesselComparisonTable: React.FC<VesselComparisonTableProps> = ({
  matches,
  onRequestOffer,
}) => {
  return (
    <div className="w-full overflow-x-auto border border-zinc-200 rounded bg-white shadow-sm">
      <table className="w-full text-left text-xs text-zinc-800">
        <thead className="bg-zinc-50 text-[10px] uppercase font-bold text-zinc-500 border-b border-zinc-200 tracking-wider">
          <tr>
            <th className="py-3 px-4">Candidate Vessel</th>
            <th className="py-3 px-4">Class</th>
            <th className="py-3 px-4">Match Score</th>
            <th className="py-3 px-4">DWT Capacity</th>
            <th className="py-3 px-4">Max Draft</th>
            <th className="py-3 px-4">Ballast Distance</th>
            <th className="py-3 px-4">ETA Load Port</th>
            <th className="py-3 px-4">Freight Rate</th>
            <th className="py-3 px-4">Total Outlay</th>
            <th className="py-3 px-4 text-right">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-100 font-mono">
          {matches.map((m, idx) => {
            const etaDisplay = (m as any).estimatedArrivalDate || m.eta || '14 Sep 2026';
            const totalCost = (m as any).totalVoyageCostUsd || m.estimatedTotalCostUsd || 1781250;

            return (
              <tr key={m.vessel.id} className={`hover:bg-zinc-50/80 transition-colors ${idx === 0 ? 'bg-zinc-50/40' : ''}`}>
                <td className="py-3 px-4 font-sans">
                  <div className="font-bold text-zinc-950 text-xs font-mono">{m.vessel.name}</div>
                  <div className="text-[10px] text-zinc-400">IMO {m.vessel.imo}</div>
                </td>
                <td className="py-3 px-4 text-zinc-700 font-sans">
                  {m.vessel.type}
                </td>
                <td className="py-3 px-4 font-bold text-zinc-950">
                  {m.matchScorePercent}%
                </td>
                <td className="py-3 px-4 text-zinc-800">
                  {formatDwt(m.vessel.dwt)}
                </td>
                <td className="py-3 px-4 text-zinc-700">
                  {m.vessel.maxDraft}m
                </td>
                <td className="py-3 px-4 text-zinc-700">
                  {formatNauticalMiles(m.distanceNauticalMiles)}
                </td>
                <td className="py-3 px-4 text-zinc-700">
                  {etaDisplay.split('T')[0]}
                </td>
                <td className="py-3 px-4 text-zinc-900 font-bold">
                  ${m.freightRateUsdPerMt}/MT
                </td>
                <td className="py-3 px-4 font-bold text-zinc-950">
                  {formatCurrency(totalCost)}
                </td>
                <td className="py-3 px-4 text-right font-sans">
                  {onRequestOffer && (
                    <Button variant={idx === 0 ? 'primary' : 'secondary'} size="sm" onClick={() => onRequestOffer(m)}>
                      <span>Select</span>
                      <ArrowRight className="h-3 w-3" />
                    </Button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
