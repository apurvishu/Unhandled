'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { AisVesselMap } from '@/components/maps/AisVesselMap';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Card';
import { Input, Select } from '@/components/ui/Input';
import { getVessels, createVessel } from '@/services/vessels';
import { VESSEL_TYPES } from '@/config/constants';
import { VesselType } from '@/types';
import { formatCurrency, formatDwt, formatKnots, getStatusBadgeColor } from '@/lib/utils';
import { Plus, Compass, Search } from 'lucide-react';
import { BackButton } from '@/components/ui/BackButton';

export default function VesselsDirectoryPage() {
  const { data: vessels = [], refetch } = useQuery({
    queryKey: ['vessels'],
    queryFn: getVessels,
  });

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  // New Vessel Form State
  const [name, setName] = useState('');
  const [imo, setImo] = useState('');
  const [type, setType] = useState<VesselType>('Panamax');
  const [dwt, setDwt] = useState(82000);
  const [maxDraft, setMaxDraft] = useState(14.5);
  const [rate, setRate] = useState(19500);

  const filteredVessels = vessels.filter((v) => {
    const matchesSearch = v.name.toLowerCase().includes(searchTerm.toLowerCase()) || v.imo.includes(searchTerm);
    const matchesType = selectedType === 'ALL' || v.type === selectedType;
    return matchesSearch && matchesType;
  });

  const handleCreateVessel = async (e: React.FormEvent) => {
    e.preventDefault();
    await createVessel({
      name,
      imo,
      type,
      dwt,
      maxDraft,
      dailyCharterRateUsd: rate,
    });
    setIsAddModalOpen(false);
    refetch();
  };

  return (
    <div className="space-y-6">
      <BackButton href="/" label="Back to Home" />

      <PageHeader
        title="Vessels & AIS Fleet Directory"
        description="Global bulk carrier tracking, specifications, draft limitations, and real-time navigation telemetry."
        badge={`${vessels.length} Active Vessels`}
        badgeVariant="default"
      >
        <Button variant="primary" size="md" onClick={() => setIsAddModalOpen(true)}>
          <Plus className="h-4 w-4" />
          <span>Register New Vessel</span>
        </Button>
      </PageHeader>

      {/* AIS MAP */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 font-mono flex items-center gap-2">
            <Compass className="h-4 w-4 text-zinc-800" />
            <span>Interactive AIS Live Map & Channel Navigation</span>
          </h3>
          <span className="text-xs text-emerald-800 font-mono flex items-center gap-1.5 font-bold">
            <span className="h-2 w-2 rounded-full bg-emerald-600 animate-pulse" />
            Streaming AIS Telemetry
          </span>
        </div>
        <AisVesselMap vessels={filteredVessels} height="400px" />
      </section>

      {/* SEARCH & FILTERS */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white border border-zinc-200 p-4 rounded shadow-sm">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-zinc-400 pointer-events-none" />
          <input
            type="text"
            placeholder="Filter by vessel name, IMO number, or destination..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-zinc-50 border border-zinc-200 rounded pl-8 pr-4 py-1.5 text-xs text-zinc-900 placeholder-zinc-400 focus:outline-none focus:border-black focus:bg-white"
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-500 font-medium">Class:</span>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="bg-zinc-50 border border-zinc-200 rounded px-2.5 py-1.5 text-xs text-zinc-900 focus:outline-none focus:border-black"
          >
            <option value="ALL">All Vessel Types</option>
            {VESSEL_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
      </div>

      {/* FLEET TABLE */}
      <div className="w-full overflow-x-auto rounded border border-zinc-200 bg-white shadow-sm">
        <table className="w-full text-left text-xs text-zinc-800 font-mono">
          <thead className="bg-zinc-50 text-[10px] uppercase font-bold text-zinc-500 border-b border-zinc-200 font-sans tracking-wider">
            <tr>
              <th className="py-3 px-4">Vessel Name / IMO</th>
              <th className="py-3 px-4">Class</th>
              <th className="py-3 px-4">DWT Capacity</th>
              <th className="py-3 px-4">Max Draft</th>
              <th className="py-3 px-4">Speed & Heading</th>
              <th className="py-3 px-4">Destination / ETA</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4 text-right">Daily Rate</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100 font-medium">
            {filteredVessels.map((v) => {
              const statusStyle = getStatusBadgeColor(v.aisPosition.status);

              return (
                <tr key={v.id} className="hover:bg-zinc-50/80 transition">
                  <td className="py-3 px-4 font-sans">
                    <Link href={`/vessels/${v.id}`} className="font-bold text-zinc-950 hover:underline text-sm font-mono">
                      {v.name}
                    </Link>
                    <div className="text-[10px] text-zinc-400 font-mono">IMO {v.imo} • Flag: {v.flag}</div>
                  </td>
                  <td className="py-3 px-4 font-sans text-zinc-700">
                    {v.type}
                  </td>
                  <td className="py-3 px-4 font-bold text-zinc-950">
                    {formatDwt(v.dwt)}
                  </td>
                  <td className="py-3 px-4 text-zinc-700">
                    {v.maxDraft}m
                  </td>
                  <td className="py-3 px-4 text-zinc-700">
                    {formatKnots(v.aisPosition.speedKnots)} @ {v.aisPosition.headingDegrees}°
                  </td>
                  <td className="py-3 px-4 font-sans">
                    <div className="text-zinc-900">{v.aisPosition.destination}</div>
                    <div className="text-[10px] text-zinc-400 font-mono">ETA: {v.aisPosition.eta.split('T')[0]}</div>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${statusStyle.bg} ${statusStyle.text} ${statusStyle.border}`}>
                      {v.aisPosition.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right font-bold text-zinc-950">
                    {formatCurrency(v.dailyCharterRateUsd)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Register Vessel Modal */}
      {isAddModalOpen && (
        <Modal
          isOpen={isAddModalOpen}
          onClose={() => setIsAddModalOpen(false)}
          title="Register Bulk Carrier Vessel"
          description="Enter vessel registry information and structural dimensions"
        >
          <form onSubmit={handleCreateVessel} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Vessel Name"
                placeholder="e.g. MV PACIFIC STAR"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
              <Input
                label="IMO Number (7 Digits)"
                placeholder="e.g. 9845120"
                value={imo}
                onChange={(e) => setImo(e.target.value)}
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Select
                label="Vessel Class"
                value={type}
                onChange={(e) => setType(e.target.value as VesselType)}
                options={VESSEL_TYPES.map((t) => ({ value: t, label: t }))}
              />
              <Input
                label="Deadweight Tonnage (DWT)"
                type="number"
                value={dwt}
                onChange={(e) => setDwt(parseInt(e.target.value))}
                required
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Maximum Draft (m)"
                type="number"
                step="0.1"
                value={maxDraft}
                onChange={(e) => setMaxDraft(parseFloat(e.target.value))}
                required
              />
              <Input
                label="Daily Charter Rate (USD)"
                type="number"
                value={rate}
                onChange={(e) => setRate(parseInt(e.target.value))}
                required
              />
            </div>

            <div className="pt-4 border-t border-zinc-200 flex items-center justify-end gap-3">
              <Button variant="secondary" size="md" onClick={() => setIsAddModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="md">
                Register Vessel
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
