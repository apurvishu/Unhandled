'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { UserRole } from '@/types';
import { Ship, Lock, Mail, User as UserIcon, Building2, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input, Select } from '@/components/ui/Input';

export default function RegisterPage() {
  const { login, isLoading } = useAuth();
  const [name, setName] = useState('Capt. Rajesh Sharma');
  const [email, setEmail] = useState('procurement@steelcorp.com');
  const [password, setPassword] = useState('password123');
  const [confirmPassword, setConfirmPassword] = useState('password123');
  const [companyName, setCompanyName] = useState('National Steel & Power Authority');
  const [role, setRole] = useState<UserRole>('PROCUREMENT_OFFICER');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await login(email, role);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-950 via-[#080e1a] to-slate-950 p-4">
      <div className="max-w-lg w-full bg-slate-900/80 border border-slate-800 rounded-2xl p-8 shadow-2xl backdrop-blur-md">
        <div className="text-center space-y-2 mb-6">
          <div className="h-12 w-12 rounded-xl bg-gradient-to-tr from-sky-600 to-cyan-400 flex items-center justify-center mx-auto shadow-lg shadow-sky-600/30">
            <Ship className="h-7 w-7 text-white" />
          </div>
          <h2 className="text-2xl font-extrabold text-white tracking-tight">Create Organization Account</h2>
          <p className="text-xs text-slate-400">SIH26006 Maritime Intelligence Network</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Full Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              leftIcon={<UserIcon className="h-4 w-4" />}
              required
            />

            <Input
              label="Work Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              leftIcon={<Mail className="h-4 w-4" />}
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Company / Authority"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              leftIcon={<Building2 className="h-4 w-4" />}
              required
            />

            <Select
              label="Organizational Role"
              value={role}
              onChange={(e) => setRole(e.target.value as UserRole)}
              options={[
                { value: 'PROCUREMENT_OFFICER', label: 'Procurement Officer' },
                { value: 'SHIP_OWNER', label: 'Ship Owner / Carrier' },
                { value: 'PORT_OWNER', label: 'Port Owner / Terminal' },
                { value: 'ADMIN', label: 'System Administrator' },
              ]}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              leftIcon={<Lock className="h-4 w-4" />}
              required
            />

            <Input
              label="Confirm Password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              leftIcon={<Lock className="h-4 w-4" />}
              required
            />
          </div>

          <Button type="submit" variant="primary" size="md" className="w-full font-bold mt-2" isLoading={isLoading}>
            <span>Register & Initialize Workspace</span>
            <ArrowRight className="h-4 w-4" />
          </Button>
        </form>

        <div className="mt-6 pt-4 border-t border-slate-800/80 text-center text-xs text-slate-400">
          Already registered?{' '}
          <Link href="/login" className="text-sky-400 hover:underline font-semibold">
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}
