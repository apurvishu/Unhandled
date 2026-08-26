'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { 
  Sparkles, 
  Clock, 
  Ship, 
  DollarSign, 
  Calendar, 
  Anchor, 
  CheckCircle2, 
  ChevronRight, 
  HelpCircle, 
  TrendingDown, 
  TrendingUp, 
  AlertTriangle, 
  ShieldCheck,
  Scale,
  ArrowRight
} from 'lucide-react';
import { OptimizationResponse, VesselMatch } from '@/types';
import { formatCurrency, formatDwt, formatNauticalMiles, getCongestionBadgeColor } from '@/lib/utils';
import { Button } from '@/components/ui/Button';

export interface DecisionRecommendationProps {
  data: OptimizationResponse;
  onRequestOffer?: (vesselMatch: VesselMatch) => void;
  className?: string;
}

export const DecisionRecommendation: React.FC<DecisionRecommendationProps> = ({
  data,
  onRequestOffer,
  className,
}) => {
  const [showExplanation, setShowExplanation] = useState(true);

  const { recommendedVessel, aiRecommendation, cargoRequirement } = data;
  const isWait = aiRecommendation.action === 'WAIT';
  const confidence = Math.round(aiRecommendation.confidencePercent);
  const congestionBadge = getCongestionBadgeColor(recommendedVessel.congestionRisk);

  return (
    <div className={`rounded-2xl border bg-gradient-to-b from-slate-900 via-slate-900/95 to-slate-950 p-6 shadow-2xl relative overflow-hidden transition-all ${
      isWait ? 'border-amber-500/40 shadow-glow-amber' : 'border-emerald-500/40 shadow-glow-green'
    } ${className || ''}`}>
      {/* Background Ambience Glow */}
      <div className={`absolute -right-20 -top-20 h-64 w-64 rounded-full blur-3xl pointer-events-none opacity-20 ${
        isWait ? 'bg-amber-500' : 'bg-emerald-500'
      }`} />

      {/* Header & Confidence Badge */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-slate-800/80">
        <div className="flex items-center gap-2.5">
          <div className={`p-2 rounded-lg border ${
            isWait ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
          }`}>
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-white tracking-tight">AI CHARTER DECISION ENGINE</h2>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 border border-sky-500/30">
                ML OPTIMIZATION
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Optimal charter matching for <strong className="text-slate-200">{cargoRequirement.quantityMt.toLocaleString()} MT {cargoRequirement.commodity}</strong> ({cargoRequirement.originPortName.split(' ')[0]} → {cargoRequirement.destinationPortName.split(' ')[0]})
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="text-right">
            <span className="text-[10px] text-slate-400 uppercase font-semibold block">Model Confidence</span>
            <span className="text-sm font-bold font-mono text-emerald-400">{confidence}%</span>
          </div>
          <div className="w-12 bg-slate-800 h-2 rounded-full overflow-hidden border border-slate-700">
            <div className="bg-gradient-to-r from-teal-400 to-emerald-400 h-full rounded-full" style={{ width: `${confidence}%` }} />
          </div>
        </div>
      </div>

      {/* THE 3 CORE DECISION ANSWERS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 my-6">
        {/* 1. WHICH VESSEL? */}
        <div className="bg-slate-950/60 border border-slate-800/90 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
          <div>
            <span className="text-[10px] font-bold tracking-wider text-sky-400 uppercase flex items-center gap-1">
              <Ship className="h-3.5 w-3.5" /> 1. WHICH VESSEL?
            </span>
            <h4 className="text-lg font-extrabold text-white mt-1 truncate">
              {recommendedVessel.vessel.name}
            </h4>
            <div className="flex items-center gap-2 mt-1 text-xs text-slate-300">
              <span className="font-semibold text-sky-300">{recommendedVessel.vessel.type}</span>
              <span>•</span>
              <span>{formatDwt(recommendedVessel.vessel.dwt)}</span>
            </div>
          </div>
          <div className="mt-3 pt-2.5 border-t border-slate-800/60 flex items-center justify-between text-xs">
            <span className="text-slate-400">Match Score:</span>
            <span className="font-bold text-emerald-400 font-mono text-sm">{recommendedVessel.matchScorePercent}%</span>
          </div>
        </div>

        {/* 2. WHEN TO CHARTER? */}
        <div className={`border rounded-xl p-4 flex flex-col justify-between transition ${
          isWait ? 'bg-amber-950/20 border-amber-500/40' : 'bg-emerald-950/20 border-emerald-500/40'
        }`}>
          <div>
            <span className={`text-[10px] font-bold tracking-wider uppercase flex items-center gap-1 ${
              isWait ? 'text-amber-400' : 'text-emerald-400'
            }`}>
              <Clock className="h-3.5 w-3.5" /> 2. WHEN TO CHARTER?
            </span>
            <h4 className={`text-xl font-black mt-1 ${isWait ? 'text-amber-300' : 'text-emerald-300'}`}>
              {isWait ? `WAIT ${aiRecommendation.waitDays || 3} DAYS` : 'BOOK NOW'}
            </h4>
            <p className="text-xs text-slate-300 mt-1">
              {isWait
                ? `Forecast rate drop: ${Math.abs(aiRecommendation.expectedRateDeltaPercent)}%`
                : 'Rates projected to increase shortly'}
            </p>
          </div>
          <div className="mt-3 pt-2.5 border-t border-slate-800/60 flex items-center justify-between text-xs">
            <span className="text-slate-400">Est. Savings:</span>
            <span className="font-bold text-emerald-400 font-mono text-sm">
              +{formatCurrency(aiRecommendation.potentialSavingsUsd)}
            </span>
          </div>
        </div>

        {/* 3. WHAT WILL IT COST? */}
        <div className="bg-slate-950/60 border border-slate-800/90 rounded-xl p-4 flex flex-col justify-between hover:border-slate-700 transition">
          <div>
            <span className="text-[10px] font-bold tracking-wider text-teal-400 uppercase flex items-center gap-1">
              <DollarSign className="h-3.5 w-3.5" /> 3. WHAT WILL IT COST?
            </span>
            <h4 className="text-xl font-extrabold text-white font-mono mt-1">
              {formatCurrency(recommendedVessel.freightRateUsdPerMt, 2)} <span className="text-xs text-slate-400 font-sans font-normal">/ MT</span>
            </h4>
            <p className="text-xs text-slate-400 mt-1">
              Total: <strong className="text-slate-200">{formatCurrency(recommendedVessel.estimatedTotalCostUsd)}</strong>
            </p>
          </div>
          <div className="mt-3 pt-2.5 border-t border-slate-800/60 flex items-center justify-between text-xs">
            <span className="text-slate-400">Target ETA:</span>
            <span className="font-semibold text-slate-200">{recommendedVessel.eta}</span>
          </div>
        </div>
      </div>

      {/* DETAILED METRICS BAR */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-950/80 border border-slate-800 rounded-xl p-3.5 text-xs text-slate-300 mb-5">
        <div>
          <span className="text-[10px] text-slate-400 uppercase block">Port Congestion</span>
          <span className={`font-semibold inline-flex items-center gap-1 mt-0.5 px-2 py-0.5 rounded ${congestionBadge.bg} ${congestionBadge.text}`}>
            {recommendedVessel.congestionRisk} Risk
          </span>
        </div>
        <div>
          <span className="text-[10px] text-slate-400 uppercase block">Draft Fit (UKC)</span>
          <span className="font-semibold text-emerald-400 inline-flex items-center gap-1 mt-0.5">
            <CheckCircle2 className="h-3.5 w-3.5" /> Suitable ({recommendedVessel.vessel.maxDraft}m Draft)
          </span>
        </div>
        <div>
          <span className="text-[10px] text-slate-400 uppercase block">Voyage Distance</span>
          <span className="font-semibold text-slate-200 mt-0.5 block font-mono">
            {formatNauticalMiles(recommendedVessel.distanceNauticalMiles)}
          </span>
        </div>
        <div>
          <span className="text-[10px] text-slate-400 uppercase block">Laycan Window</span>
          <span className="font-semibold text-slate-200 mt-0.5 block">
            {cargoRequirement.laycanStart} to {cargoRequirement.laycanEnd}
          </span>
        </div>
      </div>

      {/* EXPLAINABLE AI REASONS ACCORDION */}
      <div className="border border-slate-800 rounded-xl overflow-hidden bg-slate-950/40 mb-5">
        <button
          onClick={() => setShowExplanation(!showExplanation)}
          className="w-full px-4 py-3 bg-slate-900/60 hover:bg-slate-900 flex items-center justify-between text-xs font-semibold text-slate-200 transition"
        >
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-sky-400" />
            <span>Explainable AI: Why does the model recommend {isWait ? 'WAITING' : 'BOOKING'}?</span>
          </div>
          <span className="text-sky-400 text-xs font-normal">
            {showExplanation ? 'Hide rationale' : 'View rationale'}
          </span>
        </button>

        {showExplanation && (
          <div className="p-4 space-y-2 border-t border-slate-800/60 text-xs text-slate-300">
            {aiRecommendation.explainableReasons.map((reason, index) => (
              <div key={index} className="flex items-start gap-2.5">
                <span className="h-4 w-4 rounded-full bg-sky-500/20 text-sky-400 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                  {index + 1}
                </span>
                <p className="leading-relaxed">{reason}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ACTION BUTTONS */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <Link href="/charters/compare" className="w-full sm:w-auto">
            <Button variant="outline" size="sm" className="w-full">
              <Scale className="h-3.5 w-3.5" />
              <span>Compare All Vessels</span>
            </Button>
          </Link>
          <Link href="/forecasts" className="w-full sm:w-auto">
            <Button variant="ghost" size="sm" className="w-full text-slate-300">
              <span>View Full ML Forecast</span>
              <ChevronRight className="h-3.5 w-3.5" />
            </Button>
          </Link>
        </div>

        <Button
          variant="primary"
          size="md"
          className="w-full sm:w-auto font-bold"
          onClick={() => onRequestOffer ? onRequestOffer(recommendedVessel) : null}
        >
          <span>Request Charter Offer</span>
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
};
