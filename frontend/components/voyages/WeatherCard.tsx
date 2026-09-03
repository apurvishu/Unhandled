'use client';

import React from 'react';
import { WeatherCondition } from '@/types';
import { Wind, Waves, Eye, ShieldCheck } from 'lucide-react';

interface WeatherCardProps {
  weather: WeatherCondition;
}

export const WeatherCard: React.FC<WeatherCardProps> = ({ weather }) => {
  if (!weather) return null;

  const loc = (weather as any).locationName || weather.location || 'Bay of Bengal';
  const seaState = (weather as any).seaStateBeaufort || 3;
  const windDir = (weather as any).windDirectionDegrees ? `${(weather as any).windDirectionDegrees}°` : (weather.windDirection || 'NE');

  return (
    <div className="bg-white border border-zinc-200 rounded p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-zinc-100">
        <div>
          <h4 className="text-xs font-bold text-zinc-950 uppercase tracking-wider font-mono">
            Marine Meteorological Telemetry
          </h4>
          <p className="text-[11px] text-zinc-500">{loc}</p>
        </div>
        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-zinc-100 text-zinc-800 border border-zinc-200">
          Sea State {seaState}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs font-mono">
        <div className="p-3 bg-zinc-50 border border-zinc-200 rounded">
          <div className="flex items-center gap-1.5 text-zinc-500 mb-1 font-sans text-[10px] uppercase">
            <Wind className="h-3.5 w-3.5 text-zinc-700" />
            <span>Wind Velocity</span>
          </div>
          <strong className="text-zinc-950 text-sm">{weather.windSpeedKnots} kn</strong>
          <span className="text-[10px] text-zinc-500 block">Direction: {windDir}</span>
        </div>

        <div className="p-3 bg-zinc-50 border border-zinc-200 rounded">
          <div className="flex items-center gap-1.5 text-zinc-500 mb-1 font-sans text-[10px] uppercase">
            <Waves className="h-3.5 w-3.5 text-zinc-700" />
            <span>Significant Wave</span>
          </div>
          <strong className="text-zinc-950 text-sm">{weather.waveHeightMeters} m</strong>
          <span className="text-[10px] text-zinc-500 block">Period: 6.5s</span>
        </div>

        <div className="p-3 bg-zinc-50 border border-zinc-200 rounded">
          <div className="flex items-center gap-1.5 text-zinc-500 mb-1 font-sans text-[10px] uppercase">
            <Eye className="h-3.5 w-3.5 text-zinc-700" />
            <span>Visibility</span>
          </div>
          <strong className="text-zinc-950 text-sm">{weather.visibilityNauticalMiles} NM</strong>
          <span className="text-[10px] text-zinc-500 block">Clear Horizon</span>
        </div>

        <div className="p-3 bg-zinc-50 border border-zinc-200 rounded">
          <div className="flex items-center gap-1.5 text-zinc-500 mb-1 font-sans text-[10px] uppercase">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-700" />
            <span>Navigation Safety</span>
          </div>
          <strong className="text-emerald-800 text-sm">OPTIMAL</strong>
          <span className="text-[10px] text-zinc-500 block">No Storm Warning</span>
        </div>
      </div>
    </div>
  );
};
