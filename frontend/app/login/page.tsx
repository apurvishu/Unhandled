'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { UserRole } from '@/types';
import { ArrowRight } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const { login, quickLogin, isLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(email, password);
      router.push('/dashboard/procurement');
    } catch (err: any) {
      setError(err?.response?.data?.message || 'Invalid credentials. Please try again or use Quick Persona Login.');
    }
  };

  const handleQuick = (role: UserRole) => {
    quickLogin(role);
    if (role === 'SHIP_OWNER') router.push('/dashboard/ship-owner');
    else if (role === 'PORT_OWNER') router.push('/dashboard/port-owner');
    else if (role === 'ADMIN') router.push('/dashboard/admin');
    else router.push('/dashboard/procurement');
  };

  return (
    <div className="min-h-screen bg-zinc-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white border border-zinc-200 rounded p-8 shadow-sm space-y-6">
        {/* Header */}
        <div className="space-y-1 text-center">
          <div className="inline-flex h-8 w-8 rounded bg-black text-white font-mono font-bold text-xs items-center justify-center mb-2">
            N
          </div>
          <h1 className="text-xl font-bold tracking-tight text-zinc-950">Sign in to NAVIQ</h1>
          <p className="text-xs text-zinc-500">Maritime Logistics & Bulk Procurement Platform</p>
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-300 rounded text-xs text-red-900 font-medium">
            {error}
          </div>
        )}

        {/* Credentials Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Email Address"
            type="email"
            placeholder="officer@steelauthority.in"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
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
            Sign In with Email
          </Button>
        </form>

        {/* Quick Persona Logins */}
        <div className="space-y-3 pt-4 border-t border-zinc-200">
          <div className="text-[11px] font-mono font-bold text-zinc-400 uppercase tracking-wider text-center">
            Or Quick 1-Click Role Login
          </div>

          <div className="grid grid-cols-2 gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => handleQuick('PROCUREMENT_OFFICER')}
            >
              Procurement Officer
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => handleQuick('SHIP_OWNER')}
            >
              Ship Owner
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => handleQuick('PORT_OWNER')}
            >
              Port Authority
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => handleQuick('ADMIN')}
            >
              System Admin
            </Button>
          </div>
        </div>

        <div className="text-center text-xs text-zinc-500 pt-2">
          Don&apos;t have an account?{' '}
          <Link href="/register" className="font-semibold text-black hover:underline">
            Register new account
          </Link>
        </div>
      </div>
    </div>
  );
}
