'use client';

import React from 'react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from 'recharts';
import { formatCurrency } from '@/lib/utils';

export interface CostBreakdownChartProps {
  breakdown: {
    freightCost: number;
    bunkerFuelCost: number;
    portCosts: number;
    demurrageWaitingRiskCost: number;
    otherVoyageCost: number;
  };
  height?: number;
}

export const CostBreakdownChart: React.FC<CostBreakdownChartProps> = ({
  breakdown,
  height = 240,
}) => {
  const data = [
    { name: 'Freight Base Cost', value: breakdown.freightCost, color: '#0284c7' },
    { name: 'Bunker Fuel (VLSFO)', value: breakdown.bunkerFuelCost, color: '#06b6d4' },
    { name: 'Port Dues & Tug Pilotage', value: breakdown.portCosts, color: '#6366f1' },
    { name: 'Demurrage Waiting Risk', value: breakdown.demurrageWaitingRiskCost, color: '#f59e0b' },
    { name: 'Insurance & Canal/Other', value: breakdown.otherVoyageCost, color: '#64748b' },
  ];

  const total = data.reduce((acc, item) => acc + item.value, 0);

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const item = payload[0];
      const pct = ((item.value / total) * 100).toFixed(1);
      return (
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-2.5 shadow-xl text-xs">
          <p className="font-bold text-slate-200">{item.name}</p>
          <p className="text-sky-300 font-mono mt-0.5">
            {formatCurrency(item.value)} ({pct}%)
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full bg-slate-900/60 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-2">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
          Estimated Voyage Cost Breakdown
        </h4>
        <span className="text-xs font-mono font-bold text-white">Total: {formatCurrency(total)}</span>
      </div>

      <div style={{ width: '100%', height }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={80}
              paddingAngle={3}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }}
              layout="horizontal"
              verticalAlign="bottom"
              align="center"
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
