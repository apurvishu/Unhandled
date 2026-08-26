import React from 'react';
import { WeatherCondition } from '@/types';
import { CloudRain, Wind, Waves, Eye, AlertTriangle, CheckCircle } from 'lucide-react';

export interface WeatherCardProps {
  weather: WeatherCondition;
}

export const WeatherCard: React.FC<WeatherCardProps> = ({ weather }) => {
  return (
    <div className={`rounded-xl border p-4 bg-slate-900/60 ${
      weather.isRiskCondition ? 'border-amber-500/40 bg-amber-950/10' : 'border-slate-800'
    }`}>
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
        <div>
          <span className="text-[10px] uppercase font-bold text-slate-400 block">Maritime Weather & Sea State</span>
          <h4 className="text-sm font-bold text-white mt-0.5">{weather.location}</h4>
        </div>
        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
          weather.isRiskCondition
            ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
            : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
        }`}>
          {weather.condition}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3 text-xs">
        <div className="flex items-center gap-2">
          <Wind className="h-4 w-4 text-sky-400 shrink-0" />
          <div>
            <span className="text-[10px] text-slate-400 block">Wind</span>
            <strong className="text-slate-200">{weather.windSpeedKnots} kn {weather.windDirection}</strong>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Waves className="h-4 w-4 text-teal-400 shrink-0" />
          <div>
            <span className="text-[10px] text-slate-400 block">Wave Ht.</span>
            <strong className="text-slate-200">{weather.waveHeightMeters} m</strong>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Eye className="h-4 w-4 text-indigo-400 shrink-0" />
          <div>
            <span className="text-[10px] text-slate-400 block">Visibility</span>
            <strong className="text-slate-200">{weather.visibilityNauticalMiles} NM</strong>
          </div>
        </div>
      </div>

      {weather.warningMessage && (
        <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center gap-2 text-xs text-amber-300">
          <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0" />
          <span>{weather.warningMessage}</span>
        </div>
      )}
    </div>
  );
};
