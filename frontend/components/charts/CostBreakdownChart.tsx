'use client';

import React from 'react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
} from 'recharts';
import { formatCurrency } from '@/lib/utils';

interface CostBreakdownChartProps {
  costSummary: {
    totalOutlayUsd: number;
    baseFreightCostUsd: number;
    bunkerFuelCostUsd: number;
    portDuesAndHandlingUsd: number;
    canalAndTollsUsd: number;
    demurrageRiskCostUsd: number;
  };
  height?: number;
}

export const CostBreakdownChart: React.FC<CostBreakdownChartProps> = ({
  costSummary,
  height = 240,
}) => {
  const data = [
    { name: 'Base Vessel Hire', value: costSummary.baseFreightCostUsd, color: '#18181b' },
    { name: 'Singapore VLSFO Bunker', value: costSummary.bunkerFuelCostUsd, color: '#52525b' },
    { name: 'Port Dues & Pilotage', value: costSummary.portDuesAndHandlingUsd, color: '#a1a1aa' },
    { name: 'Canal & Transit Tolls', value: costSummary.canalAndTollsUsd, color: '#d4d4d8' },
    { name: 'Demurrage Congestion Risk', value: costSummary.demurrageRiskCostUsd, color: '#ea580c' },
  ];

  return (
    <div className="flex flex-col sm:flex-row items-center gap-6" style={{ minHeight: height }}>
      <div className="w-48 h-48 relative shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              innerRadius={50}
              outerRadius={75}
              paddingAngle={2}
              dataKey="value"
              stroke="#ffffff"
              strokeWidth={1}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const item = payload[0];
                  const percent = ((Number(item.value) / costSummary.totalOutlayUsd) * 100).toFixed(1);
                  return (
                    <div className="bg-white border border-zinc-300 rounded p-2 text-xs font-mono shadow-md">
                      <p className="font-bold text-zinc-900">{item.name}</p>
                      <p className="text-zinc-700">{formatCurrency(Number(item.value))} ({percent}%)</p>
                    </div>
                  );
                }
                return null;
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-[10px] text-zinc-400 font-mono uppercase">Total</span>
          <span className="text-xs font-bold text-zinc-950 font-mono">
            {formatCurrency(costSummary.totalOutlayUsd)}
          </span>
        </div>
      </div>

      {/* Structured Cost Item Legend */}
      <div className="flex-1 w-full space-y-2 text-xs font-mono">
        {data.map((item) => {
          const percent = ((item.value / costSummary.totalOutlayUsd) * 100).toFixed(1);
          return (
            <div key={item.name} className="flex items-center justify-between pb-1 border-b border-zinc-100">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-sm shrink-0" style={{ backgroundColor: item.color }} />
                <span className="text-zinc-700 font-sans">{item.name}</span>
              </div>
              <div className="text-right">
                <span className="font-bold text-zinc-900">{formatCurrency(item.value)}</span>
                <span className="text-[10px] text-zinc-400 ml-1">({percent}%)</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
