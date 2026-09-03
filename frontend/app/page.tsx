'use client';

import React from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/lib/auth';
import { 
  ArrowRight, 
  CheckCircle2, 
  Compass, 
  TrendingUp, 
  Scale, 
  Anchor, 
  Radio, 
  ShieldCheck,
  Ship,
  Database
} from 'lucide-react';

export default function LandingPage() {
  const { quickLogin } = useAuth();

  return (
    <div className="min-h-screen bg-white text-zinc-950 flex flex-col justify-between selection:bg-black selection:text-white">
      {/* Editorial Navigation Header */}
      <header className="h-14 border-b border-zinc-200 px-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-7 w-7 rounded bg-black flex items-center justify-center text-white font-mono text-xs font-bold">
            N
          </div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-sm tracking-tight">NAVIQ</span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 border border-zinc-300 rounded text-zinc-600">
              SIH26006
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/login">
            <Button variant="ghost" size="sm">Sign In</Button>
          </Link>
          <Link href="/dashboard/procurement">
            <Button variant="primary" size="sm">Launch Platform</Button>
          </Link>
        </div>
      </header>

      {/* Main Editorial Hero */}
      <main className="max-w-6xl mx-auto px-6 py-16 lg:py-24 space-y-16">
        <div className="space-y-6 max-w-4xl">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded border border-zinc-300 bg-zinc-50 text-[11px] font-mono uppercase text-zinc-800">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" />
            <span>AI Freight Forecasting & Multi-Objective Vessel Chartering</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-zinc-950 leading-[1.08]">
            Maritime logistics intelligence for dry bulk cargo procurement.
          </h1>

          <p className="text-base sm:text-lg text-zinc-600 max-w-2xl leading-relaxed">
            Directly answers <strong>Which Vessel</strong> to charter, <strong>When to Charter</strong> based on ML freight timing forecasts, and <strong>What It Costs</strong> with itemized bunker, port dues, and UKC bathymetry safety models.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Link href="/dashboard/procurement">
              <Button variant="primary" size="lg">
                <span>Enter Procurement Intelligence</span>
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/forecasts">
              <Button variant="secondary" size="lg">
                View 14-Day Freight Forecasts
              </Button>
            </Link>
          </div>
        </div>

        {/* The 3 Questions Core Philosophy Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 border border-zinc-200 divide-y md:divide-y-0 md:divide-x divide-zinc-200 bg-white">
          <div className="p-6 space-y-2">
            <div className="text-[10px] font-mono uppercase font-bold text-zinc-400">Question 01</div>
            <h3 className="text-lg font-bold text-zinc-950">Which Vessel?</h3>
            <p className="text-xs text-zinc-600 leading-relaxed">
              Spatial PostGIS matching against real-time AIS ballast positions, DWT suitability, max draft limits, and berth compatibility.
            </p>
          </div>

          <div className="p-6 space-y-2">
            <div className="text-[10px] font-mono uppercase font-bold text-zinc-400">Question 02</div>
            <h3 className="text-lg font-bold text-zinc-950">When to Charter?</h3>
            <p className="text-xs text-zinc-600 leading-relaxed">
              Deep learning rate trajectory model generating actionable timing signals: <strong>WAIT 3 DAYS</strong> for projected rate dip vs. <strong>BOOK NOW</strong>.
            </p>
          </div>

          <div className="p-6 space-y-2">
            <div className="text-[10px] font-mono uppercase font-bold text-zinc-400">Question 03</div>
            <h3 className="text-lg font-bold text-zinc-950">What will it cost?</h3>
            <p className="text-xs text-zinc-600 leading-relaxed">
              Complete voyage outlay calculator: Base freight, Singapore VLSFO bunker consumption, port handling dues, and demurrage congestion risk.
            </p>
          </div>
        </div>

        {/* 1-Click Role Direct Launch Matrix */}
        <div className="space-y-4 pt-4 border-t border-zinc-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-zinc-950 font-mono">
                Direct Role Access
              </h2>
              <p className="text-xs text-zinc-500">Select your operational workflow to test real-time intelligence</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Link
              href="/dashboard/procurement"
              onClick={() => quickLogin('PROCUREMENT_OFFICER')}
              className="p-5 border border-zinc-200 rounded hover:border-black transition bg-white space-y-3 group"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono uppercase font-bold text-zinc-400">Role 01</span>
                <ArrowRight className="h-4 w-4 text-zinc-400 group-hover:text-black transition" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-zinc-950">Procurement Officer</h3>
                <p className="text-xs text-zinc-600 mt-1 leading-relaxed">
                  Cargo requirement submission, AI charter recommendations, tender bids.
                </p>
              </div>
            </Link>

            <Link
              href="/dashboard/ship-owner"
              onClick={() => quickLogin('SHIP_OWNER')}
              className="p-5 border border-zinc-200 rounded hover:border-black transition bg-white space-y-3 group"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono uppercase font-bold text-zinc-400">Role 02</span>
                <ArrowRight className="h-4 w-4 text-zinc-400 group-hover:text-black transition" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-zinc-950">Ship Owner</h3>
                <p className="text-xs text-zinc-600 mt-1 leading-relaxed">
                  Fleet telemetry, cargo opportunity marketplace, charter offer submission.
                </p>
              </div>
            </Link>

            <Link
              href="/dashboard/port-owner"
              onClick={() => quickLogin('PORT_OWNER')}
              className="p-5 border border-zinc-200 rounded hover:border-black transition bg-white space-y-3 group"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono uppercase font-bold text-zinc-400">Role 03</span>
                <ArrowRight className="h-4 w-4 text-zinc-400 group-hover:text-black transition" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-zinc-950">Port Authority</h3>
                <p className="text-xs text-zinc-600 mt-1 leading-relaxed">
                  Berth allocations, anchorage queues, 7-day port congestion forecasts.
                </p>
              </div>
            </Link>

            <Link
              href="/dashboard/admin"
              onClick={() => quickLogin('ADMIN')}
              className="p-5 border border-zinc-200 rounded hover:border-black transition bg-white space-y-3 group"
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono uppercase font-bold text-zinc-400">Role 04</span>
                <ArrowRight className="h-4 w-4 text-zinc-400 group-hover:text-black transition" />
              </div>
              <div>
                <h3 className="font-bold text-sm text-zinc-950">System Admin</h3>
                <p className="text-xs text-zinc-600 mt-1 leading-relaxed">
                  Platform telemetry, ML inference latency, model accuracy audit.
                </p>
              </div>
            </Link>
          </div>
        </div>
      </main>

      {/* Minimal Footer */}
      <footer className="border-t border-zinc-200 py-6 px-6 text-xs text-zinc-500 font-mono flex flex-col sm:flex-row items-center justify-between gap-2">
        <span>NAVIQ • Smart India Hackathon (SIH 2026) Problem Statement SIH26006</span>
        <span>Version 1.0.0 Production-Ready</span>
      </footer>
    </div>
  );
}
