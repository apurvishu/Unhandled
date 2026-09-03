'use client';

import React from 'react';
import { VesselMatch } from '@/types';
import { formatCurrency, formatDwt, formatNauticalMiles } from '@/lib/utils';
import { Button } from '@/components/ui/Button';
import { CheckCircle2 } from 'lucide-react';

interface VesselCardProps {
  match: VesselMatch;
  isBestMatch?: boolean;
  onRequestOffer?: (match: VesselMatch) => void;
  onViewDetails?: (match: VesselMatch) => void;
}

export const VesselCard: React.FC<VesselCardProps> = ({
  match,
  isBestMatch = false,
  onRequestOffer,
  onViewDetails,
}) => {
  const { vessel, matchScorePercent, distanceNauticalMiles, freightRateUsdPerMt } = match;
  const etaDisplay = (match as any).estimatedArrivalDate || match.eta || '14 Sep 2026';
  const totalCost = (match as any).totalVoyageCostUsd || match.estimatedTotalCostUsd || 1781250;

  return (
    <div
      className={`bg-white border rounded p-5 space-y-4 shadow-sm transition ${
        isBestMatch ? 'border-2 border-zinc-950' : 'border-zinc-200 hover:border-zinc-300'
      }`}
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-zinc-950 font-mono">{vessel.name}</h3>
            {isBestMatch && (
              <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-zinc-900 text-white">
                TOP CANDIDATE
              </span>
            )}
          </div>
          <p className="text-xs text-zinc-500 font-mono mt-0.5">
            IMO {vessel.imo} • {vessel.type} • Flag: {vessel.flag}
          </p>
        </div>

        <div className="text-right">
          <span className="text-[10px] text-zinc-400 font-mono uppercase block">Match Score</span>
          <span className="text-lg font-bold text-zinc-950 font-mono">{matchScorePercent}%</span>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-2 p-3 bg-zinc-50 border border-zinc-200 rounded text-xs font-mono">
        <div>
          <span className="text-[10px] text-zinc-400 block uppercase font-sans">Capacity:</span>
          <strong className="text-zinc-900">{formatDwt(vessel.dwt)}</strong>
        </div>
        <div>
          <span className="text-[10px] text-zinc-400 block uppercase font-sans">Max Draft:</span>
          <span className="text-zinc-900">{vessel.maxDraft} m</span>
        </div>
        <div>
          <span className="text-[10px] text-zinc-400 block uppercase font-sans">Ballast Distance:</span>
          <span className="text-zinc-900">{formatNauticalMiles(distanceNauticalMiles)}</span>
        </div>
        <div>
          <span className="text-[10px] text-zinc-400 block uppercase font-sans">Load Port ETA:</span>
          <span className="text-zinc-900">{etaDisplay.split('T')[0]}</span>
        </div>
      </div>

      {/* Cost Summary */}
      <div className="flex items-center justify-between pt-2 border-t border-zinc-100 text-xs">
        <div>
          <span className="text-[10px] text-zinc-400 block uppercase font-mono">Quoted Freight Rate</span>
          <strong className="text-sm font-mono text-zinc-950">${freightRateUsdPerMt}/MT</strong>
        </div>
        <div className="text-right">
          <span className="text-[10px] text-zinc-400 block uppercase font-mono">Total Voyage Cost</span>
          <span className="text-sm font-bold font-mono text-zinc-950">{formatCurrency(totalCost)}</span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-2 pt-2">
        {onViewDetails && (
          <Button variant="secondary" size="sm" onClick={() => onViewDetails(match)}>
            Specifications
          </Button>
        )}
        {onRequestOffer && (
          <Button variant="primary" size="sm" onClick={() => onRequestOffer(match)}>
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>Select Vessel</span>
          </Button>
        )}
      </div>
    </div>
  );
};
