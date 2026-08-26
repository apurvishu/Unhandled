'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import Link from 'next/link';
import { Ship, Sparkles, TrendingDown, Clock, ShieldCheck, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export default function HomePage() {
  const { user, isAuthenticated, isLoading, quickLogin, getDashboardPathForRole } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isAuthenticated && user) {
      router.push(getDashboardPathForRole(user.role));
    }
  }, [isAuthenticated, isLoading, user, router, getDashboardPathForRole]);

  return (
    <div className="min-h-screen flex flex-col justify-between bg-gradient-to-b from-slate-950 via-[#080e1a] to-slate-950 px-4 sm:px-6">
      {/* Hero Header */}
      <header className="max-w-7xl w-full mx-auto py-6 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-sky-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-sky-600/30">
            <Ship className="h-6 w-6 text-white" />
          </div>
          <div>
            <span className="font-extrabold text-lg tracking-tight text-white">NAVIQ</span>
            <span className="text-[10px] ml-2 uppercase font-bold tracking-widest px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-400 border border-sky-500/30">
              SIH26006
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/login">
            <Button variant="outline" size="sm">
              Log In
            </Button>
          </Link>
          <Link href="/register">
            <Button variant="primary" size="sm">
              Register
            </Button>
          </Link>
        </div>
      </header>

      {/* Main Hero */}
      <main className="max-w-5xl mx-auto text-center py-16 sm:py-24 space-y-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 border border-sky-500/30 text-sky-300 text-xs font-semibold">
          <Sparkles className="h-3.5 w-3.5 text-sky-400" />
          <span>Intelligent Maritime Freight Forecasting & Bulk Chartering Platform</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-black text-white tracking-tight leading-tight">
          AI Decisions for <span className="text-transparent bg-clip-text bg-gradient-to-r from-sky-400 via-teal-300 to-cyan-400">Bulk Chartering</span> & Freight
        </h1>

        <p className="text-base sm:text-lg text-slate-400 max-w-3xl mx-auto leading-relaxed">
          Assisting bulk procurement officers, ship owners, and port authorities in answering three critical questions:
          <strong className="text-slate-200"> WHICH VESSEL TO CHARTER</strong>, <strong className="text-slate-200">WHEN TO CHARTER IT</strong>, and <strong className="text-slate-200">WHAT WILL IT COST</strong>.
        </p>

        {/* 1-Click Role Direct Launches for SIH Judges */}
        <div className="pt-8 max-w-3xl mx-auto bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-2xl backdrop-blur-md">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4">
            ⚡ Quick-Launch Demo Portals (1-Click Judge Access)
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <Button
              variant="primary"
              size="md"
              className="flex-col h-auto py-3 text-xs"
              onClick={() => quickLogin('PROCUREMENT_OFFICER')}
            >
              <span className="font-bold">Procurement Officer</span>
              <span className="text-[10px] opacity-80 mt-0.5">Cargo, Matching & AI</span>
            </Button>

            <Button
              variant="secondary"
              size="md"
              className="flex-col h-auto py-3 text-xs"
              onClick={() => quickLogin('SHIP_OWNER')}
            >
              <span className="font-bold">Ship Owner</span>
              <span className="text-[10px] text-slate-400 mt-0.5">Fleet & Offers</span>
            </Button>

            <Button
              variant="secondary"
              size="md"
              className="flex-col h-auto py-3 text-xs"
              onClick={() => quickLogin('PORT_OWNER')}
            >
              <span className="font-bold">Port Owner</span>
              <span className="text-[10px] text-slate-400 mt-0.5">Berths & Congestion</span>
            </Button>

            <Button
              variant="secondary"
              size="md"
              className="flex-col h-auto py-3 text-xs"
              onClick={() => quickLogin('ADMIN')}
            >
              <span className="font-bold">System Admin</span>
              <span className="text-[10px] text-slate-400 mt-0.5">Global Telemetry</span>
            </Button>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="max-w-7xl w-full mx-auto py-6 border-t border-slate-900 text-center text-xs text-slate-400">
        SIH26006 Intelligent Freight Forecasting Platform • Next.js + FastAPI + PostGIS + AIS Telemetry
      </footer>
    </div>
  );
}
