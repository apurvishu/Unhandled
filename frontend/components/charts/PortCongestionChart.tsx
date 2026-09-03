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

interface PortCongestionChartProps {
  data: any[];
  height?: number;
}

export const PortCongestionChart: React.FC<PortCongestionChartProps> = ({
  data,
  height = 240,
}) => {
  const normalizedData = (data || []).map((d) => ({
    date: d.date,
    waitingHours: d.waitingTimeHours !== undefined ? d.waitingTimeHours : (d.waitingHours || 0),
    vesselsInQueue: d.vesselsInQueue || 0,
    level: d.congestionLevel || d.level || 'MEDIUM',
  }));

  return (
    <div className="w-full" style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={normalizedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid stroke="#e4e4e7" strokeDasharray="2 2" vertical={false} />

          <XAxis
            dataKey="date"
            tick={{ fill: '#71717a', fontSize: 10, fontFamily: 'monospace' }}
            tickLine={{ stroke: '#e4e4e7' }}
            axisLine={{ stroke: '#d4d4d8' }}
          />

          <YAxis
            tick={{ fill: '#71717a', fontSize: 10, fontFamily: 'monospace' }}
            tickLine={{ stroke: '#e4e4e7' }}
            axisLine={{ stroke: '#d4d4d8' }}
            tickFormatter={(val) => `${val}h`}
          />

          <Tooltip
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                const item = payload[0].payload;
                return (
                  <div className="bg-white border border-zinc-300 rounded p-2.5 text-xs font-mono shadow-md">
                    <p className="font-bold text-zinc-950 border-b border-zinc-100 pb-1 mb-1">{label}</p>
                    <p className="text-zinc-800">
                      Average Anchorage Wait: <strong>{item.waitingHours} Hours</strong>
                    </p>
                    {item.vesselsInQueue > 0 && <p className="text-zinc-600">Queue: {item.vesselsInQueue} Vessels</p>}
                    <p className="text-zinc-500 text-[10px] mt-1">Status: {item.level} Congestion</p>
                  </div>
                );
              }
              return null;
            }}
          />

          <Area
            type="monotone"
            dataKey="waitingHours"
            stroke="#18181b"
            strokeWidth={1.5}
            fill="#f4f4f5"
            fillOpacity={0.8}
            dot={{ r: 3, fill: '#18181b', strokeWidth: 0 }}
            name="Anchorage Waiting (Hours)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
