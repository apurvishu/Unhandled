'use client';

import React from 'react';
import { PortCall } from '@/types';
import { Anchor, CheckCircle2, Clock, Navigation, Ship, MapPin } from 'lucide-react';
import { formatDateTime } from '@/lib/utils';

export interface PortCallTimelineProps {
  portCalls: PortCall[];
  currentMilestone: string;
}

export const PortCallTimeline: React.FC<PortCallTimelineProps> = ({
  portCalls,
  currentMilestone,
}) => {
  const steps = [
    { title: 'Loading Port', desc: 'Hay Point Coal Terminal', status: 'COMPLETED' },
    { title: 'Departure', desc: 'Underway to Indian Ocean', status: 'COMPLETED' },
    { title: 'At Sea / Navigation', desc: 'Timor Sea Passage (Speed 13.4 kn)', status: 'IN_PROGRESS' },
    { title: 'Port Arrival', desc: 'Paradip Port Anchorage', status: 'SCHEDULED' },
    { title: 'Berth Allocation', desc: 'Central Bulk Berth CB-1', status: 'SCHEDULED' },
    { title: 'Discharge Cargo', desc: 'Mechanized Coal Discharger', status: 'SCHEDULED' },
    { title: 'Cargo Delivered', desc: 'National Steel & Power Authority', status: 'SCHEDULED' },
  ];

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 space-y-6">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
            <Navigation className="h-4 w-4 text-sky-400" />
            <span>Voyage Port Call Milestones & Operation Timeline</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">End-to-End Operational Lifecycle</p>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 rounded bg-sky-500/20 text-sky-300 border border-sky-500/30">
          Current: {currentMilestone}
        </span>
      </div>

      {/* Steps Visual Pipeline */}
      <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
        {steps.map((step, idx) => {
          const isDone = step.status === 'COMPLETED';
          const isCurrent = step.status === 'IN_PROGRESS';

          return (
            <div key={idx} className="relative flex items-start gap-4">
              <div
                className={`absolute -left-6 top-0.5 h-5 w-5 rounded-full flex items-center justify-center border text-[10px] font-bold ${
                  isDone
                    ? 'bg-emerald-500 text-white border-emerald-400'
                    : isCurrent
                    ? 'bg-sky-500 text-white border-sky-300 animate-pulse'
                    : 'bg-slate-900 text-slate-500 border-slate-700'
                }`}
              >
                {isDone ? '✓' : idx + 1}
              </div>

              <div className="flex-1 bg-slate-950/70 border border-slate-800/80 rounded-lg p-3 text-xs">
                <div className="flex items-center justify-between">
                  <h4 className={`font-bold ${isCurrent ? 'text-sky-300' : isDone ? 'text-emerald-300' : 'text-slate-300'}`}>
                    {step.title}
                  </h4>
                  <span className={`text-[10px] uppercase font-semibold px-2 py-0.5 rounded ${
                    isDone ? 'bg-emerald-500/10 text-emerald-400' : isCurrent ? 'bg-sky-500/10 text-sky-400' : 'bg-slate-800 text-slate-400'
                  }`}>
                    {step.status}
                  </span>
                </div>
                <p className="text-slate-400 mt-1">{step.desc}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Port Call Metrics Table */}
      <div className="pt-4 border-t border-slate-800">
        <h4 className="text-xs font-bold text-slate-300 mb-3 uppercase tracking-wider">
          Port Call Timestamps & Turnaround Metrics
        </h4>
        <div className="w-full overflow-x-auto rounded-lg border border-slate-800">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950 text-[10px] uppercase text-slate-400 font-bold border-b border-slate-800">
              <tr>
                <th className="p-2.5">Port Terminal</th>
                <th className="p-2.5">Operation</th>
                <th className="p-2.5">ETA / ATA</th>
                <th className="p-2.5">ETD / ATD</th>
                <th className="p-2.5">Anchorage Wait</th>
                <th className="p-2.5">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium">
              {portCalls.map((call, index) => (
                <tr key={index} className="hover:bg-slate-800/30">
                  <td className="p-2.5 font-semibold text-white">{call.portName}</td>
                  <td className="p-2.5">
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-sky-300 text-[10px] font-bold">
                      {call.operation}
                    </span>
                  </td>
                  <td className="p-2.5">{call.ata ? `${call.ata.split('T')[0]} (ATA)` : `${call.eta.split('T')[0]} (ETA)`}</td>
                  <td className="p-2.5">{call.atd ? `${call.atd.split('T')[0]} (ATD)` : `${call.etd.split('T')[0]} (ETD)`}</td>
                  <td className="p-2.5 font-mono">{call.waitingTimeHours} hrs</td>
                  <td className="p-2.5">
                    <span className="text-[10px] font-bold uppercase text-emerald-400">{call.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
