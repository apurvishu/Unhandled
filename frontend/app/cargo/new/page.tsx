'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { PageHeader } from '@/components/layout/PageHeader';
import { CargoRequirementForm, CargoFormData } from '@/components/cargo/CargoRequirementForm';
import { createCargoRequirement } from '@/services/cargo';
import { MAJOR_PORTS } from '@/config/constants';
import { CommodityType, VesselType } from '@/types';
import { Sparkles, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';

export default function CreateCargoRequirementPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (data: CargoFormData) => {
    setIsSubmitting(true);
    try {
      const originPort = MAJOR_PORTS.find((p) => p.id === data.originPortId)?.name || 'Hay Point';
      const destPort = MAJOR_PORTS.find((p) => p.id === data.destinationPortId)?.name || 'Paradip Port';

      const created = await createCargoRequirement({
        procurementOfficerId: 'usr-proc-01',
        procurementOfficerName: 'Capt. Rajesh Sharma',
        commodity: data.commodity as CommodityType,
        quantityMt: data.quantityMt,
        originPortId: data.originPortId,
        originPortName: originPort,
        destinationPortId: data.destinationPortId,
        destinationPortName: destPort,
        requiredArrivalDate: data.requiredArrivalDate,
        preferredVesselType: data.preferredVesselType as VesselType,
        minDwt: data.minDwt,
        maxDraft: data.maxDraft,
        laycanStart: data.laycanStart,
        laycanEnd: data.laycanEnd,
      });

      // Flow step: Navigate directly to Vessel Matching & AI Decision screen
      router.push(`/vessels/match?cargoId=${created.id}`);
    } catch (err) {
      console.error('Failed to create cargo requirement:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto animate-in fade-in duration-300">
      <div className="flex items-center gap-2">
        <Link href="/cargo">
          <Button variant="ghost" size="sm" className="text-slate-400">
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Cargo List</span>
          </Button>
        </Link>
      </div>

      <PageHeader
        title="Create Bulk Cargo Requirement"
        description="Specify cargo volume, origin/destination ports, laycan window, and vessel draft constraints to trigger AI vessel matching and freight forecasting."
        badge="Procurement Workflow: Step 1"
        badgeVariant="info"
      />

      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl backdrop-blur-md">
        <CargoRequirementForm onSubmit={handleSubmit} isLoading={isSubmitting} />
      </div>
    </div>
  );
}
