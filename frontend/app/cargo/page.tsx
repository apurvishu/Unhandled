'use client';

import React from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { CargoTable } from '@/components/cargo/CargoTable';
import { Button } from '@/components/ui/Button';
import { getCargoRequirements } from '@/services/cargo';
import { PackagePlus, Boxes, Sparkles } from 'lucide-react';

export default function CargoRequirementsPage() {
  const { data: cargoList = [], isLoading } = useQuery({
    queryKey: ['cargoRequirements'],
    queryFn: getCargoRequirements,
  });

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <PageHeader
        title="Bulk Cargo Requirements & Tenders"
        description="Active procurement tenders, laycan schedules, and matching status for bulk commodities."
        badge={`${cargoList.length} Active Tenders`}
        badgeVariant="info"
      >
        <Link href="/cargo/new">
          <Button variant="primary" size="md" className="font-bold">
            <PackagePlus className="h-4 w-4" />
            <span>Create New Cargo Need</span>
          </Button>
        </Link>
      </PageHeader>

      <div className="space-y-4">
        <CargoTable items={cargoList} />
      </div>
    </div>
  );
}
