import React from 'react';
import Link from 'next/link';
import { CargoRequirement } from '@/types';
import { Badge } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Sparkles, Calendar, MapPin, Ship, ArrowRight, Eye } from 'lucide-react';
import { formatDwt, getStatusBadgeColor } from '@/lib/utils';

export interface CargoTableProps {
  items: CargoRequirement[];
  onFindVessels?: (cargo: CargoRequirement) => void;
}

export const CargoTable: React.FC<CargoTableProps> = ({ items, onFindVessels }) => {
  return (
    <div className="w-full overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60">
      <table className="w-full text-left text-xs text-slate-300">
        <thead className="bg-slate-950/80 text-[10px] uppercase font-bold text-slate-400 border-b border-slate-800 tracking-wider">
          <tr>
            <th className="py-3.5 px-4">Commodity / ID</th>
            <th className="py-3.5 px-4">Quantity</th>
            <th className="py-3.5 px-4">Route (Origin → Destination)</th>
            <th className="py-3.5 px-4">Laycan Window</th>
            <th className="py-3.5 px-4">Preferred Vessel</th>
            <th className="py-3.5 px-4">Status</th>
            <th className="py-3.5 px-4 text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60 font-medium">
          {items.map((cargo) => {
            const statusStyle = getStatusBadgeColor(cargo.status);

            return (
              <tr key={cargo.id} className="hover:bg-slate-800/40 transition">
                <td className="py-3.5 px-4">
                  <div className="font-bold text-white text-sm">{cargo.commodity}</div>
                  <div className="text-[10px] text-slate-500 font-mono mt-0.5">{cargo.id}</div>
                </td>
                <td className="py-3.5 px-4">
                  <span className="font-bold text-slate-100 font-mono text-xs">{formatDwt(cargo.quantityMt)}</span>
                </td>
                <td className="py-3.5 px-4">
                  <div className="flex items-center gap-1.5 text-slate-200">
                    <span>{cargo.originPortName.split(' ')[0]}</span>
                    <span className="text-sky-400">→</span>
                    <span>{cargo.destinationPortName.split(' ')[0]}</span>
                  </div>
                  <div className="text-[10px] text-slate-500 mt-0.5">Max Draft: {cargo.maxDraft}m</div>
                </td>
                <td className="py-3.5 px-4 text-slate-300">
                  <div>{cargo.laycanStart}</div>
                  <div className="text-[10px] text-slate-500">to {cargo.laycanEnd}</div>
                </td>
                <td className="py-3.5 px-4">
                  <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-sky-300 text-[11px] font-semibold">
                    {cargo.preferredVesselType}
                  </span>
                </td>
                <td className="py-3.5 px-4">
                  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border ${statusStyle.bg} ${statusStyle.text} ${statusStyle.border}`}>
                    {cargo.status}
                  </span>
                </td>
                <td className="py-3.5 px-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <Link href={`/vessels/match?cargoId=${cargo.id}`}>
                      <Button variant="primary" size="sm">
                        <Sparkles className="h-3 w-3" />
                        <span>Find Vessels</span>
                      </Button>
                    </Link>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
