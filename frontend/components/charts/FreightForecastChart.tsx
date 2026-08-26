'use client';

import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';
import { ForecastDataPoint } from '@/types';
import { formatCurrency } from '@/lib/utils';

export interface FreightForecastChartProps {
  data: ForecastDataPoint[];
  currentRate: number;
  predictedRate: number;
  height?: number;
}

export const FreightForecastChart: React.FC<FreightForecastChartProps> = ({
  data,
  currentRate,
  predictedRate,
  height = 360,
}) => {
  // Custom tooltip for chart
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const pData = payload[0].payload as ForecastDataPoint;
      return (
        <div className="bg-slate-900 border border-slate-700 rounded-xl p-3 shadow-2xl text-xs space-y-1.5 backdrop-blur-md">
          <p className="font-bold text-slate-200 border-b border-slate-800 pb-1">{label}</p>
          {pData.actualRate !== undefined && (
            <p className="text-sky-400 flex items-center justify-between gap-4">
              <span>Historical Actual:</span>
              <strong className="font-mono">{formatCurrency(pData.actualRate, 2)}/MT</strong>
            </p>
          )}
          <p className="text-teal-300 flex items-center justify-between gap-4">
            <span>ML Predicted:</span>
            <strong className="font-mono">{formatCurrency(pData.forecastRate, 2)}/MT</strong>
          </p>
          <div className="pt-1 border-t border-slate-800 text-[10px] text-slate-400 flex items-center justify-between gap-4">
            <span>Confidence Range (87%):</span>
            <span className="font-mono text-slate-300">
              {formatCurrency(pData.lowerConfidenceBound, 2)} - {formatCurrency(pData.upperConfidenceBound, 2)}
            </span>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-lg">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-800/80 mb-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span>ML Freight Rate Forecasting & Prediction Interval</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Model: Maritime-Transformer-v4.2 with 87% confidence interval band
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-sky-400" />
            <span className="text-slate-300">Actual Rates</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-teal-400" />
            <span className="text-slate-300">Forecast Curve</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-6 rounded bg-teal-500/20 border border-teal-500/40" />
            <span className="text-slate-300">Confidence Band</span>
          </div>
        </div>
      </div>

      <div style={{ width: '100%', height }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
            <defs>
              <linearGradient id="confidenceBand" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.05} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />

            <XAxis
              dataKey="date"
              stroke="#64748b"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: '#334155' }}
            />

            <YAxis
              domain={['auto', 'auto']}
              stroke="#64748b"
              tick={{ fill: '#94a3b8', fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: '#334155' }}
              tickFormatter={(v) => `$${v}`}
            />

            <Tooltip content={<CustomTooltip />} />

            {/* Confidence Band Area */}
            <Area
              type="monotone"
              dataKey="upperConfidenceBound"
              stroke="transparent"
              fill="url(#confidenceBand)"
              fillOpacity={1}
              name="Upper Bound"
            />
            <Area
              type="monotone"
              dataKey="lowerConfidenceBound"
              stroke="transparent"
              fill="#080e1a"
              fillOpacity={1}
              name="Lower Bound"
            />

            {/* Historical Actual Rate Line (Solid) */}
            <Line
              type="monotone"
              dataKey="actualRate"
              stroke="#38bdf8"
              strokeWidth={3}
              dot={{ r: 4, fill: '#38bdf8', strokeWidth: 1, stroke: '#080e1a' }}
              activeDot={{ r: 6, fill: '#38bdf8' }}
              name="Actual Rate ($/MT)"
            />

            {/* ML Forecast Line (Dashed) */}
            <Line
              type="monotone"
              dataKey="forecastRate"
              stroke="#2dd4bf"
              strokeWidth={2.5}
              strokeDasharray="5 5"
              dot={{ r: 4, fill: '#2dd4bf', strokeWidth: 1, stroke: '#080e1a' }}
              activeDot={{ r: 6, fill: '#2dd4bf' }}
              name="ML Forecast ($/MT)"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-2 text-center">
        <p className="text-[11px] text-slate-400">
          * Forecast is probabilistic and generated by the backend ML service. The shaded region denotes the 87% prediction interval.
        </p>
      </div>
    </div>
  );
};
