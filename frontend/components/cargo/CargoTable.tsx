'use client';

import React from 'react';
import Link from 'next/link';
import { CargoRequirement } from '@/types';
import { formatDwt, formatCurrency, getStatusBadgeColor } from '@/lib/utils';
import { Button } from '@/components/ui/Button';
import { Sparkles, ArrowRight } from 'lucide-react';

interface CargoTableProps {
  cargoList: CargoRequirement[];
  onFindVessels?: (cargoId: string) => void;
}

export const CargoTable: React.FC<CargoTableProps> = ({ cargoList, onFindVessels }) => {
  return (
    <div className="w-full overflow-x-auto border border-zinc-200 rounded bg-white shadow-sm">
      <table className="w-full text-left text-xs text-zinc-800">
        <thead className="bg-zinc-50 text-[10px] uppercase font-bold text-zinc-500 border-b border-zinc-200 tracking-wider">
          <tr>
            <th className="py-3 px-4">Commodity / ID</th>
            <th className="py-3 px-4">Quantity (MT)</th>
            <th className="py-3 px-4">Origin / Load Port</th>
            <th className="py-3 px-4">Discharge Port</th>
            <th className="py-3 px-4">Laycan Window</th>
            <th className="py-3 px-4">Target Rate</th>
            <th className="py-3 px-4">Status</th>
            <th className="py-3 px-4 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-100 font-medium">
          {cargoList.map((cargo) => {
            const statusStyle = getStatusBadgeColor(cargo.status);

            return (
              <tr key={cargo.id} className="hover:bg-zinc-50/80 transition-colors">
                <td className="py-3 px-4 font-mono">
                  <div className="font-bold text-zinc-950 font-sans text-xs">{cargo.commodity}</div>
                  <div className="text-[10px] text-zinc-400 font-mono">{cargo.id}</div>
                </td>
                <td className="py-3 px-4 font-mono font-bold text-zinc-900">
                  {formatDwt(cargo.quantityMt)}
                </td>
                <td className="py-3 px-4 text-zinc-700">
                  {cargo.originPortName}
                </td>
                <td className="py-3 px-4 text-zinc-700">
                  {cargo.destinationPortName}
                </td>
                <td className="py-3 px-4 font-mono text-[11px] text-zinc-600">
                  {cargo.laycanStart} → {cargo.laycanEnd}
                </td>
                <td className="py-3 px-4 font-mono text-zinc-900">
                  ${cargo.targetFreightRateUsdPerMt}/MT
                </td>
                <td className="py-3 px-4">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${statusStyle.bg} ${statusStyle.text} ${statusStyle.border}`}>
                    {cargo.status}
                  </span>
                </td>
                <td className="py-3 px-4 text-right">
                  <Link href={`/vessels/match?cargoId=${cargo.id}`}>
                    <Button variant="primary" size="sm">
                      <span>Find Vessels</span>
                      <ArrowRight className="h-3 w-3" />
                    </Button>
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
