'use client';

import React from 'react';
import { PortCall } from '@/types';
import { formatDateTime } from '@/lib/utils';

interface PortCallTimelineProps {
  portCalls: PortCall[];
  currentMilestone?: string;
}

export const PortCallTimeline: React.FC<PortCallTimelineProps> = ({
  portCalls = [],
  currentMilestone = 'UNDERWAY',
}) => {
  return (
    <div className="bg-white border border-zinc-200 rounded p-6 shadow-sm space-y-6">
      <div className="flex items-center justify-between pb-4 border-b border-zinc-200">
        <div>
          <h3 className="text-sm font-bold text-zinc-950 uppercase tracking-wider font-mono">
            Voyage Milestones & Port Calls
          </h3>
          <p className="text-xs text-zinc-500 mt-0.5">
            Sequential tracking from loading terminal berth to discharge anchorage
          </p>
        </div>
        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-zinc-900 text-white">
          Active Status: {currentMilestone}
        </span>
      </div>

      {/* Structured Milestone Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {portCalls.map((pc, idx) => {
          const isCompleted = pc.status === 'DEPARTED';
          const isInProgress = pc.status === 'ARRIVED' || pc.status === 'BERTHED';

          return (
            <div
              key={pc.portId || idx}
              className={`p-4 rounded border text-xs space-y-3 ${
                isInProgress
                  ? 'border-2 border-zinc-950 bg-zinc-50/50'
                  : isCompleted
                  ? 'border-zinc-200 bg-white'
                  : 'border-zinc-200 bg-zinc-50/30 opacity-70'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="h-5 w-5 rounded bg-zinc-900 text-white font-mono text-[10px] flex items-center justify-center font-bold">
                    {idx + 1}
                  </span>
                  <div>
                    <h4 className="font-bold text-zinc-950">{pc.portName}</h4>
                    <span className="text-[10px] text-zinc-500 uppercase font-mono">{pc.operation}</span>
                  </div>
                </div>

                <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border ${
                  isCompleted
                    ? 'bg-emerald-50 text-emerald-900 border-emerald-300'
                    : isInProgress
                    ? 'bg-zinc-900 text-white border-zinc-900'
                    : 'bg-zinc-100 text-zinc-600 border-zinc-200'
                }`}>
                  {pc.status}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-zinc-200 font-mono text-[11px]">
                <div>
                  <span className="text-[10px] text-zinc-400 uppercase block font-sans">Arrival (ETA / ATA):</span>
                  <span className="text-zinc-800">{pc.ata ? formatDateTime(pc.ata) : formatDateTime(pc.eta)}</span>
                </div>
                <div>
                  <span className="text-[10px] text-zinc-400 uppercase block font-sans">Departure (ETD / ATD):</span>
                  <span className="text-zinc-800">{pc.atd ? formatDateTime(pc.atd) : formatDateTime(pc.etd)}</span>
                </div>
                <div>
                  <span className="text-[10px] text-zinc-400 uppercase block font-sans">Operation:</span>
                  <span className="text-zinc-900 font-bold">{pc.operation}</span>
                </div>
                <div>
                  <span className="text-[10px] text-zinc-400 uppercase block font-sans">Anchorage Waiting:</span>
                  <span className="text-zinc-800">{pc.waitingTimeHours ? `${pc.waitingTimeHours} Hours` : 'Zero Delay'}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
