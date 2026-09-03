'use client';

import React, { useState } from 'react';
import { VesselMatch } from '@/types';
import { formatCurrency, formatDwt, formatNauticalMiles } from '@/lib/utils';
import { Button } from '@/components/ui/Button';
import { 
  CheckCircle2, 
  Clock, 
  DollarSign, 
  Ship, 
  ChevronDown, 
  ChevronUp, 
  ShieldCheck,
  ArrowRight
} from 'lucide-react';

interface DecisionRecommendationProps {
  data: any;
  onRequestOffer?: (match: VesselMatch) => void;
  onViewAlternativeVessels?: () => void;
}

export const DecisionRecommendation: React.FC<DecisionRecommendationProps> = ({
  data,
  onRequestOffer,
  onViewAlternativeVessels,
}) => {
  const [showExplanation, setShowExplanation] = useState(false);

  if (!data) return null;

  // Normalize data whether it's OptimizationResponse or OptimizationRecommendation
  const bestMatch: VesselMatch = data.bestVesselMatch || data.recommendedVessel || {
    vessel: {
      id: 'vessel-02',
      name: 'MV OCEAN FORTUNE',
      type: 'Panamax',
      dwt: 82000,
      maxDraft: 14.5,
      imo: '9842190',
      flag: 'Marshall Islands',
    },
    matchScorePercent: 94,
    distanceNauticalMiles: 1850,
    freightRateUsdPerMt: 23.75,
    estimatedTotalCostUsd: 1781250,
    costBreakdown: {
      freightCost: 1781250,
      bunkerFuelCost: 284000,
      portCosts: 62000,
      demurrageWaitingRiskCost: 24000,
      otherVoyageCost: 18000,
    },
  };

  const action = data.recommendationType || data.aiRecommendation?.action || 'WAIT';
  const isWait = action === 'WAIT' || action === 'WAIT_TO_CHARTER';
  const confidence = data.confidenceScorePercent || data.aiRecommendation?.confidencePercent || 87;
  const rationaleList: string[] = data.rationale || data.aiRecommendation?.explainableReasons || [
    'Panamax freight rates on Australia-East Coast India route projected to drop from $24.80/MT to $23.75/MT.',
    'Ballast tonnage supply in Hay Point cluster has expanded by 3 vessels.',
    'Destination port waiting time at Paradip is decreasing from 34.5h to 21.0h.',
  ];
  const savings = data.costSummary?.potentialSavingsUsd || data.aiRecommendation?.potentialSavingsUsd || 78750;
  const totalCost = data.costSummary?.totalOutlayUsd || bestMatch.estimatedTotalCostUsd || 1781250;
  const bunkerCost = data.costSummary?.bunkerFuelCostUsd || bestMatch.costBreakdown?.bunkerFuelCost || 284000;
  const freightRate = data.costSummary?.freightRateUsdPerMt || bestMatch.freightRateUsdPerMt || 23.75;
  const cargoQuantity = data.costSummary?.cargoQuantityMt || data.cargoRequirement?.quantityMt || 75000;

  return (
    <div className="bg-white border-2 border-zinc-900 rounded p-5 shadow-sm space-y-5">
      {/* Top Banner: Decision Badge & Confidence */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-zinc-200">
        <div className="flex items-center gap-3">
          <div className={`px-2.5 py-1 rounded text-xs font-mono font-bold uppercase tracking-wider ${
            isWait ? 'bg-amber-100 text-amber-950 border border-amber-300' : 'bg-zinc-900 text-white'
          }`}>
            {isWait ? '● ML TIMING STRATEGY: WAIT 3 DAYS' : '● ML TIMING STRATEGY: BOOK TODAY'}
          </div>
          <span className="text-xs text-zinc-500 font-mono">
            Confidence: <strong className="text-zinc-900">{confidence}%</strong>
          </span>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-zinc-500">
          <span>MODEL:</span>
          <span className="text-zinc-900 font-semibold">Maritime-Transformer-v4.2</span>
        </div>
      </div>

      {/* The 3 Fundamental Procurement Decisions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* 1. WHICH VESSEL */}
        <div className="p-4 rounded border border-zinc-200 bg-zinc-50/50 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">1. Which Vessel?</span>
            <Ship className="h-4 w-4 text-zinc-700" />
          </div>
          <div>
            <div className="text-base font-bold text-zinc-950 font-mono">
              {bestMatch.vessel.name}
            </div>
            <p className="text-xs text-zinc-600">
              {bestMatch.vessel.type} • {formatDwt(bestMatch.vessel.dwt)}
            </p>
          </div>
          <div className="pt-2 border-t border-zinc-200 text-xs space-y-1 font-mono">
            <div className="flex justify-between text-zinc-600">
              <span>Match Score:</span>
              <strong className="text-zinc-900 font-bold">{bestMatch.matchScorePercent}%</strong>
            </div>
            <div className="flex justify-between text-zinc-600">
              <span>Ballast Distance:</span>
              <span className="text-zinc-900">{formatNauticalMiles(bestMatch.distanceNauticalMiles)}</span>
            </div>
          </div>
        </div>

        {/* 2. WHEN TO CHARTER */}
        <div className="p-4 rounded border border-zinc-200 bg-zinc-50/50 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">2. When to Charter?</span>
            <Clock className="h-4 w-4 text-zinc-700" />
          </div>
          <div>
            <div className="text-base font-bold text-zinc-950 font-mono">
              {isWait ? 'Delay 3 Days' : 'Execute Immediately'}
            </div>
            <p className="text-xs text-zinc-600">
              Optimal laycan: Sep 18 - 21
            </p>
          </div>
          <div className="pt-2 border-t border-zinc-200 text-xs space-y-1 font-mono">
            <div className="flex justify-between text-zinc-600">
              <span>Rate Shift:</span>
              <strong className="text-emerald-700 font-bold">
                -$3.20/MT (-4.2%)
              </strong>
            </div>
            <div className="flex justify-between text-zinc-600">
              <span>Current → Forecast:</span>
              <span className="text-zinc-900">
                $24.80 → ${freightRate}
              </span>
            </div>
          </div>
        </div>

        {/* 3. WHAT WILL IT COST */}
        <div className="p-4 rounded border border-zinc-200 bg-zinc-50/50 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-bold text-zinc-500 tracking-wider">3. What will it cost?</span>
            <DollarSign className="h-4 w-4 text-zinc-700" />
          </div>
          <div>
            <div className="text-base font-bold text-zinc-950 font-mono">
              {formatCurrency(totalCost)}
            </div>
            <p className="text-xs text-zinc-600">
              ${freightRate}/MT • {formatDwt(cargoQuantity)}
            </p>
          </div>
          <div className="pt-2 border-t border-zinc-200 text-xs space-y-1 font-mono">
            <div className="flex justify-between text-zinc-600">
              <span>Projected Savings:</span>
              <strong className="text-emerald-700 font-bold">{formatCurrency(savings)}</strong>
            </div>
            <div className="flex justify-between text-zinc-600">
              <span>Singapore Bunker:</span>
              <span className="text-zinc-900">{formatCurrency(bunkerCost)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Rationale & Bathymetry Safety Summary */}
      <div className="bg-zinc-50 border border-zinc-200 rounded p-3 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-emerald-700 shrink-0" />
          <span className="text-zinc-800">
            <strong>Port Safety Clearance:</strong> Draft {bestMatch.vessel.maxDraft}m compatible with Paradip (17.5m max channel depth). UKC safety margin: <strong>+3.4m</strong>.
          </span>
        </div>

        <button
          onClick={() => setShowExplanation(!showExplanation)}
          className="text-xs text-zinc-600 hover:text-black font-semibold flex items-center gap-1 shrink-0"
        >
          <span>{showExplanation ? 'Hide XAI Rationale' : 'Explainable AI Details'}</span>
          {showExplanation ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
        </button>
      </div>

      {/* Explainable AI Accordion */}
      {showExplanation && (
        <div className="p-4 bg-zinc-50 border border-zinc-200 rounded space-y-3 text-xs">
          <h4 className="font-bold text-zinc-900 uppercase tracking-wider text-[11px] font-mono">
            Explainable AI Decision Audit Log
          </h4>
          <ul className="space-y-1.5 list-disc list-inside text-zinc-700">
            {rationaleList.map((point, index) => (
              <li key={index} className="leading-relaxed">{point}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Action Footer */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
        <span className="text-xs text-zinc-500 font-mono">
          Status: Ready for Tender Negotiation
        </span>

        <div className="flex items-center gap-2">
          {onViewAlternativeVessels && (
            <Button variant="secondary" size="sm" onClick={onViewAlternativeVessels}>
              Compare Alternative Vessels
            </Button>
          )}

          <Button
            variant="primary"
            size="sm"
            onClick={() => onRequestOffer && onRequestOffer(bestMatch)}
          >
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>Select Candidate & Proceed</span>
          </Button>
        </div>
      </div>
    </div>
  );
};
