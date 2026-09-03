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
  CartesianGrid,
  Legend,
} from 'recharts';

interface FreightForecastChartProps {
  data: any[];
  height?: number | string;
  showConfidenceInterval?: boolean;
}

export const FreightForecastChart: React.FC<FreightForecastChartProps> = ({
  data = [],
  height = 320,
  showConfidenceInterval = true,
}) => {
  const chartData = (data || []).map((d: any) => {
    const lower = d.lowerConfidenceBound !== undefined ? d.lowerConfidenceBound : (d.lowerConfidenceBoundUsd || 0);
    const upper = d.upperConfidenceBound !== undefined ? d.upperConfidenceBound : (d.upperConfidenceBoundUsd || 0);
    const actual = d.actualRate !== undefined ? d.actualRate : d.actualRateUsd;
    const predicted = d.forecastRate !== undefined ? d.forecastRate : (d.predictedRateUsd !== undefined ? d.predictedRateUsd : null);

    return {
      date: d.date,
      actualRate: actual,
      forecastRate: predicted,
      lowerBound: lower,
      upperBound: upper,
      confidenceRange: [lower, upper],
    };
  });

  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid stroke="#e4e4e7" strokeDasharray="2 2" vertical={false} />

          <XAxis
            dataKey="date"
            tick={{ fill: '#71717a', fontSize: 10, fontFamily: 'monospace' }}
            tickLine={{ stroke: '#e4e4e7' }}
            axisLine={{ stroke: '#d4d4d8' }}
          />

          <YAxis
            domain={['auto', 'auto']}
            tick={{ fill: '#71717a', fontSize: 10, fontFamily: 'monospace' }}
            tickLine={{ stroke: '#e4e4e7' }}
            axisLine={{ stroke: '#d4d4d8' }}
            tickFormatter={(val) => `$${val}`}
          />

          <Tooltip
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                const item = payload[0].payload;
                return (
                  <div className="bg-white border border-zinc-300 rounded p-2.5 shadow-md text-xs font-mono">
                    <p className="font-bold text-zinc-950 mb-1 border-b border-zinc-100 pb-1">{label}</p>
                    {item.actualRate !== undefined && item.actualRate !== null && (
                      <p className="text-zinc-800">
                        Actual Spot Rate: <strong>${Number(item.actualRate).toFixed(2)}/MT</strong>
                      </p>
                    )}
                    {item.forecastRate !== undefined && item.forecastRate !== null && (
                      <p className="text-zinc-950 font-bold">
                        ML Predicted Rate: ${Number(item.forecastRate).toFixed(2)}/MT
                      </p>
                    )}
                    <p className="text-zinc-500 text-[10px] mt-1">
                      87% Confidence: ${Number(item.lowerBound).toFixed(2)} - ${Number(item.upperBound).toFixed(2)}
                    </p>
                  </div>
                );
              }
              return null;
            }}
          />

          <Legend
            verticalAlign="top"
            align="right"
            iconType="line"
            wrapperStyle={{ paddingBottom: 8, fontSize: 11, fontFamily: 'sans-serif' }}
          />

          {/* 87% Confidence Interval Band */}
          {showConfidenceInterval && (
            <Area
              dataKey="confidenceRange"
              stroke="none"
              fill="#e4e4e7"
              fillOpacity={0.6}
              name="87% Prediction Band"
            />
          )}

          {/* Historical Actual Freight Rate */}
          <Line
            type="monotone"
            dataKey="actualRate"
            stroke="#18181b"
            strokeWidth={2}
            dot={{ r: 3, fill: '#18181b', strokeWidth: 0 }}
            activeDot={{ r: 4 }}
            name="Actual Spot Rate ($/MT)"
            connectNulls={false}
          />

          {/* Machine Learning Predicted Rate */}
          <Line
            type="monotone"
            dataKey="forecastRate"
            stroke="#000000"
            strokeWidth={2}
            strokeDasharray="4 3"
            dot={{ r: 3, fill: '#000000', strokeWidth: 0 }}
            name="ML Predicted Rate ($/MT)"
            connectNulls={false}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};
