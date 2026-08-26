import React from 'react';
import { VesselMatch } from '@/types';
import { Button } from '@/components/ui/Button';
import { formatCurrency, formatDwt, formatNauticalMiles, getCongestionBadgeColor } from '@/lib/utils';
import { 
  Ship, 
  Sparkles, 
  Check, 
  Clock, 
  Compass, 
  Anchor, 
  AlertTriangle, 
  DollarSign,
  ArrowRight,
  Info
} from 'lucide-react';

export interface VesselCardProps {
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
  const { vessel, matchScorePercent, freightRateUsdPerMt, eta, distanceNauticalMiles, congestionRisk } = match;
  const congestionBadge = getCongestionBadgeColor(congestionRisk);

  return (
    <div
      className={`rounded-xl border p-5 transition-all duration-200 relative overflow-hidden bg-slate-900/80 ${
        isBestMatch
          ? 'border-sky-500/50 shadow-glow bg-gradient-to-b from-sky-950/20 to-slate-900'
          : 'border-slate-800 hover:border-slate-700'
      }`}
    >
      {isBestMatch && (
        <div className="absolute top-0 right-0">
          <div className="bg-gradient-to-l from-sky-500 to-blue-600 text-white text-[10px] font-extrabold uppercase px-3 py-1 rounded-bl-lg tracking-wider flex items-center gap-1 shadow-md">
            <Sparkles className="h-3 w-3" /> BEST MATCH
          </div>
        </div>
      )}

      {/* Title & Match Score */}
      <div className="flex items-start justify-between pr-16">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Ship className="h-4 w-4 text-sky-400" />
            <span>{vessel.name}</span>
          </h3>
          <div className="flex items-center gap-2 text-xs text-slate-400 mt-1">
            <span className="font-semibold text-slate-300">{vessel.type}</span>
            <span>•</span>
            <span>IMO: {vessel.imo}</span>
            <span>•</span>
            <span>{formatDwt(vessel.dwt)}</span>
          </div>
        </div>

        <div className="text-right">
          <div className="text-2xl font-black font-mono text-emerald-400">{matchScorePercent}%</div>
          <span className="text-[10px] uppercase font-bold text-slate-400">Match Score</span>
        </div>
      </div>

      {/* Grid of Attributes */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 my-4 p-3.5 rounded-lg bg-slate-950/70 border border-slate-800/80 text-xs">
        <div>
          <span className="text-[10px] text-slate-400 uppercase block font-semibold">Freight Quote</span>
          <span className="font-extrabold font-mono text-white text-sm">
            {formatCurrency(freightRateUsdPerMt, 2)} <span className="text-[10px] text-slate-400 font-normal">/ MT</span>
          </span>
        </div>
        <div>
          <span className="text-[10px] text-slate-400 uppercase block font-semibold">Target ETA</span>
          <span className="font-semibold text-slate-200 text-sm">{eta}</span>
        </div>
        <div>
          <span className="text-[10px] text-slate-400 uppercase block font-semibold">Distance</span>
          <span className="font-semibold text-slate-200 font-mono">{formatNauticalMiles(distanceNauticalMiles)}</span>
        </div>
        <div>
          <span className="text-[10px] text-slate-400 uppercase block font-semibold">Congestion</span>
          <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${congestionBadge.bg} ${congestionBadge.text}`}>
            {congestionRisk}
          </span>
        </div>
      </div>

      {/* Compatibility Check Badges */}
      <div className="flex items-center gap-4 text-xs text-slate-300 py-2 border-t border-slate-800/60 flex-wrap">
        <div className="flex items-center gap-1.5">
          <span className="h-4 w-4 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-[10px] font-bold">✓</span>
          <span>Draft Fit ({vessel.maxDraft}m)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-4 w-4 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-[10px] font-bold">✓</span>
          <span>Laycan Ready</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-4 w-4 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-[10px] font-bold">✓</span>
          <span>Channel UKC OK</span>
        </div>
      </div>

      {/* Actions */}
      <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between gap-3">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onViewDetails ? onViewDetails(match) : null}
        >
          <Info className="h-3.5 w-3.5" />
          <span>View Specs & Route</span>
        </Button>

        <Button
          variant={isBestMatch ? 'primary' : 'secondary'}
          size="sm"
          onClick={() => onRequestOffer ? onRequestOffer(match) : null}
        >
          <span>Request Charter Offer</span>
          <ArrowRight className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  );
};
