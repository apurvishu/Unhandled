'use client';

import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { CongestionPoint } from '@/types';

export interface PortCongestionChartProps {
  data: CongestionPoint[];
  height?: number;
}

export const PortCongestionChart: React.FC<PortCongestionChartProps> = ({
  data,
  height = 260,
}) => {
  return (
    <div className="w-full bg-slate-900/60 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
        <div>
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Average Waiting Time (Hours) Trend & 7-Day Forecast
          </h4>
          <p className="text-[11px] text-slate-400">Historical vs ML Expected Anchorage Delay</p>
        </div>
      </div>

      <div style={{ width: '100%', height }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="waitingHoursGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis dataKey="date" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 10 }} tickLine={false} />
            <YAxis stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 10 }} tickLine={false} unit="h" />
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', fontSize: '12px' }}
              labelStyle={{ color: '#cbd5e1', fontWeight: 'bold' }}
            />
            <Area
              type="monotone"
              dataKey="waitingTimeHours"
              stroke="#f59e0b"
              strokeWidth={2.5}
              fill="url(#waitingHoursGrad)"
              name="Waiting Time (Hours)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
