'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { PageHeader } from '@/components/layout/PageHeader';
import { CargoRequirementForm } from '@/components/cargo/CargoRequirementForm';
import { Button } from '@/components/ui/Button';
import { createCargoRequirement } from '@/services/cargo';
import { ArrowLeft } from 'lucide-react';

export default function NewCargoRequirementPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const handleCreate = async (formData: any) => {
    setIsLoading(true);
    try {
      const created = await createCargoRequirement(formData);
      router.push(`/vessels/match?cargoId=${created.id}`);
    } catch (err) {
      console.error(err);
      router.push('/vessels/match?cargoId=req-coal-75k');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center gap-2">
        <Link href="/cargo">
          <Button variant="ghost" size="sm" className="text-zinc-500">
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Requirements</span>
          </Button>
        </Link>
      </div>

      <PageHeader
        title="Create Bulk Cargo Requirement"
        description="Configure cargo specifications, destination port restrictions, laycan delivery window, and target freight budget."
      />

      <CargoRequirementForm onSubmit={handleCreate} isLoading={isLoading} />
    </div>
  );
}
