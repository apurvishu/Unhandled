'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth';
import { UserRole } from '@/types';
import { Ship, Lock, Mail, Sparkles, ArrowRight, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input, Select } from '@/components/ui/Input';

export default function LoginPage() {
  const { login, quickLogin, isLoading } = useAuth();
  const [email, setEmail] = useState('procurement@steelcorp.com');
  const [password, setPassword] = useState('password123');
  const [role, setRole] = useState<UserRole>('PROCUREMENT_OFFICER');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await login(email, role);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-950 via-[#080e1a] to-slate-950 p-4">
      <div className="max-w-md w-full bg-slate-900/80 border border-slate-800 rounded-2xl p-8 shadow-2xl backdrop-blur-md">
        {/* Header */}
        <div className="text-center space-y-2 mb-6">
          <div className="h-12 w-12 rounded-xl bg-gradient-to-tr from-sky-600 to-cyan-400 flex items-center justify-center mx-auto shadow-lg shadow-sky-600/30">
            <Ship className="h-7 w-7 text-white" />
          </div>
          <h2 className="text-2xl font-extrabold text-white tracking-tight">Welcome to NAVIQ</h2>
          <p className="text-xs text-slate-400">SIH26006 Intelligent Maritime Platform</p>
        </div>

        {/* 1-Click Role Direct Launches for Instant Testing */}
        <div className="mb-6 p-3 bg-slate-950/60 border border-slate-800 rounded-xl space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-sky-400">
            <Sparkles className="h-3.5 w-3.5" />
            <span>Fast Role Selection (SIH Evaluation):</span>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => quickLogin('PROCUREMENT_OFFICER')}
              className="px-2.5 py-2 text-xs rounded-lg bg-sky-950/50 hover:bg-sky-900/50 text-sky-200 border border-sky-500/30 text-left font-medium transition"
            >
              <strong className="block text-sky-400">Procurement</strong>
              <span className="text-[10px] text-slate-400">Charter & Optimization</span>
            </button>
            <button
              type="button"
              onClick={() => quickLogin('SHIP_OWNER')}
              className="px-2.5 py-2 text-xs rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 text-left font-medium transition"
            >
              <strong className="block text-slate-300">Ship Owner</strong>
              <span className="text-[10px] text-slate-400">Fleet & Tender Offers</span>
            </button>
            <button
              type="button"
              onClick={() => quickLogin('PORT_OWNER')}
              className="px-2.5 py-2 text-xs rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 text-left font-medium transition"
            >
              <strong className="block text-slate-300">Port Owner</strong>
              <span className="text-[10px] text-slate-400">Berths & Congestion</span>
            </button>
            <button
              type="button"
              onClick={() => quickLogin('ADMIN')}
              className="px-2.5 py-2 text-xs rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 text-left font-medium transition"
            >
              <strong className="block text-slate-300">System Admin</strong>
              <span className="text-[10px] text-slate-400">Full Platform Telemetry</span>
            </button>
          </div>
        </div>

        {/* Standard Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Email Address"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            leftIcon={<Mail className="h-4 w-4" />}
            required
          />

          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            leftIcon={<Lock className="h-4 w-4" />}
            required
          />

          <Select
            label="User Role"
            value={role}
            onChange={(e) => setRole(e.target.value as UserRole)}
            options={[
              { value: 'PROCUREMENT_OFFICER', label: 'Procurement Officer' },
              { value: 'SHIP_OWNER', label: 'Ship Owner / Carrier' },
              { value: 'PORT_OWNER', label: 'Port Owner / Terminal Operator' },
              { value: 'ADMIN', label: 'System Administrator' },
            ]}
          />

          <Button type="submit" variant="primary" size="md" className="w-full font-bold" isLoading={isLoading}>
            <span>Sign In to Dashboard</span>
            <ArrowRight className="h-4 w-4" />
          </Button>
        </form>

        <div className="mt-6 pt-4 border-t border-slate-800/80 text-center text-xs text-slate-400">
          Don&apos;t have an account?{' '}
          <Link href="/register" className="text-sky-400 hover:underline font-semibold">
            Register Organization
          </Link>
        </div>
      </div>
    </div>
  );
}
