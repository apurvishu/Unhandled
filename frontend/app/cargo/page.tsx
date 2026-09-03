'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { CargoTable } from '@/components/cargo/CargoTable';
import { Button } from '@/components/ui/Button';
import { getCargoRequirements } from '@/services/cargo';
import { Plus, Search, Filter } from 'lucide-react';
import { BackButton } from '@/components/ui/BackButton';

export default function CargoRequirementsPage() {
  const { data: cargoList = [] } = useQuery({
    queryKey: ['cargoRequirements'],
    queryFn: getCargoRequirements,
  });

  const [searchTerm, setSearchTerm] = useState('');
  const [commodityFilter, setCommodityFilter] = useState('ALL');

  const filteredCargo = cargoList.filter((c) => {
    const matchesSearch = c.commodity.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.originPortName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.destinationPortName.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCommodity = commodityFilter === 'ALL' || c.commodity === commodityFilter;
    return matchesSearch && matchesCommodity;
  });

  return (
    <div className="space-y-6">
      <BackButton href="/" label="Back to Home" />

      <PageHeader
        title="Dry Bulk Cargo Requirements & Tenders"
        description="Active procurement schedules, laycan delivery windows, volume allocations, and destination terminals."
        badge={`${cargoList.length} Active Requirements`}
        badgeVariant="default"
      >
        <Link href="/cargo/new">
          <Button variant="primary" size="md">
            <Plus className="h-4 w-4" />
            <span>Create Requirement</span>
          </Button>
        </Link>
      </PageHeader>

      {/* Filter & Search Bar */}
      <div className="bg-white border border-zinc-200 rounded p-4 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-zinc-400 pointer-events-none" />
          <input
            type="text"
            placeholder="Search by commodity, origin, or destination..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-zinc-50 border border-zinc-200 rounded pl-8 pr-4 py-1.5 text-xs text-zinc-900 placeholder-zinc-400 focus:outline-none focus:border-black focus:bg-white"
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-zinc-500">Commodity:</span>
          <select
            value={commodityFilter}
            onChange={(e) => setCommodityFilter(e.target.value)}
            className="bg-zinc-50 border border-zinc-200 rounded px-2.5 py-1.5 text-xs text-zinc-900 focus:outline-none focus:border-black"
          >
            <option value="ALL">All Commodities</option>
            <option value="Coking Coal">Coking Coal</option>
            <option value="Thermal Coal">Thermal Coal</option>
            <option value="Iron Ore">Iron Ore</option>
            <option value="Grain">Grain</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <CargoTable cargoList={filteredCargo} />
    </div>
  );
}
