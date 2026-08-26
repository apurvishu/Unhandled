'use client';

import React from 'react';
import Link from 'next/link';
import { PageHeader } from '@/components/layout/PageHeader';
import { KpiCard } from '@/components/dashboard/KpiCard';
import { AisVesselMap } from '@/components/maps/AisVesselMap';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/lib/auth';
import { 
  ShieldCheck, 
  Users, 
  Ship, 
  Anchor, 
  Navigation, 
  FileText, 
  Cpu, 
  Zap, 
  Radio, 
  CheckCircle2, 
  AlertTriangle 
} from 'lucide-react';

export default function AdminDashboardPage() {
  const { isDemoMode, toggleDemoMode } = useAuth();

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      <PageHeader
        title="System Administration & Telemetry"
        description="Global platform metrics, AI inference latency, active fleets, and security monitoring."
        badge="Admin Authority"
        badgeVariant="purple"
      >
        <Button
          variant={isDemoMode ? 'warning' : 'success'}
          size="md"
          onClick={() => toggleDemoMode()}
        >
          {isDemoMode ? <Zap className="h-4 w-4" /> : <Radio className="h-4 w-4" />}
          <span>{isDemoMode ? 'Toggle Live API Mode' : 'Toggle Demo Simulation Mode'}</span>
        </Button>
      </PageHeader>

      {/* KPI Section */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
        <KpiCard
          title="Total Users"
          value="1,420"
          subtitle="4 active roles"
          icon={Users}
        />

        <KpiCard
          title="Tracked Vessels"
          value="8,540"
          subtitle="AIS active"
          icon={Ship}
          variant="primary"
        />

        <KpiCard
          title="Ports Monitored"
          value="48"
          subtitle="Global major bulk"
          icon={Anchor}
        />

        <KpiCard
          title="Active Charters"
          value="64"
          subtitle="In negotiation"
          icon={FileText}
          variant="success"
        />

        <KpiCard
          title="ML Latency"
          value="42ms"
          subtitle="Inference avg"
          icon={Cpu}
          variant="success"
        />

        <KpiCard
          title="System Health"
          value="99.98%"
          subtitle="FastAPI + PostGIS"
          icon={ShieldCheck}
          variant="success"
        />
      </div>

      {/* SYSTEM TELEMETRY & HEALTH */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">AI Model & Subsystem Health</h3>

          <div className="space-y-3 text-xs">
            <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
              <div>
                <strong className="text-slate-200">Freight Forecaster (Transformer-v4.2)</strong>
                <p className="text-[10px] text-slate-400">MAE: 0.42 • RMSE: 0.61 • 87% Confidence</p>
              </div>
              <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                OPERATIONAL
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
              <div>
                <strong className="text-slate-200">Port Congestion Predictor (Spatial GNN)</strong>
                <p className="text-[10px] text-slate-400">7-Day Horizon • PostGIS Topology</p>
              </div>
              <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                OPERATIONAL
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
              <div>
                <strong className="text-slate-200">AIS WebSocket Streaming Ticker</strong>
                <p className="text-[10px] text-slate-400">Throughput: 1,200 msgs/sec</p>
              </div>
              <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
                ACTIVE
              </span>
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-3">
          <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
            <Ship className="h-4 w-4 text-sky-400" />
            <span>Global AIS Fleet Tracking Coverage</span>
          </h3>
          <AisVesselMap height="360px" />
        </div>
      </div>
    </div>
  );
}
