'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { Button } from '@/components/ui/Button';
import { Input, Select } from '@/components/ui/Input';
import { UserRole } from '@/types';

export default function RegisterPage() {
  const router = useRouter();
  const { register: registerUser, isLoading } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>('PROCUREMENT_OFFICER');
  const [organization, setOrganization] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await registerUser(name, email, password, role, organization);
      router.push('/dashboard/procurement');
    } catch (err: any) {
      setError(err?.response?.data?.message || 'Registration failed. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-zinc-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white border border-zinc-200 rounded p-8 shadow-sm space-y-6">
        <div className="space-y-1 text-center">
          <div className="inline-flex h-8 w-8 rounded bg-black text-white font-mono font-bold text-xs items-center justify-center mb-2">
            N
          </div>
          <h1 className="text-xl font-bold tracking-tight text-zinc-950">Register for NAVIQ</h1>
          <p className="text-xs text-zinc-500">Enterprise Maritime Logistics Access</p>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-300 rounded text-xs text-red-900 font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Full Name"
            placeholder="Rajesh Varma"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />

          <Input
            label="Email Address"
            type="email"
            placeholder="r.varma@steelauthority.in"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <Input
            label="Organization Name"
            placeholder="National Steel & Mining Corp"
            value={organization}
            onChange={(e) => setOrganization(e.target.value)}
            required
          />

          <Select
            label="Operational Role"
            value={role}
            onChange={(e) => setRole(e.target.value as UserRole)}
            options={[
              { value: 'PROCUREMENT_OFFICER', label: 'Procurement Officer' },
              { value: 'SHIP_OWNER', label: 'Ship Owner / Carrier' },
              { value: 'PORT_OWNER', label: 'Port Authority Terminal Operator' },
              { value: 'ADMIN', label: 'Platform Administrator' },
            ]}
          />

          <Input
            label="Password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <Button type="submit" variant="primary" size="md" className="w-full" isLoading={isLoading}>
            Create Account
          </Button>
        </form>

        <div className="text-center text-xs text-zinc-500 pt-2 border-t border-zinc-200">
          Already have an account?{' '}
          <Link href="/login" className="font-semibold text-black hover:underline">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}
