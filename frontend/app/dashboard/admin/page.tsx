'use client';

import React from 'react';
import { PageHeader } from '@/components/layout/PageHeader';
import { KpiCard } from '@/components/dashboard/KpiCard';
import { Button } from '@/components/ui/Button';
import { BackButton } from '@/components/ui/BackButton';
import { 
  Activity, 
  Database, 
  Radio, 
  Cpu, 
  CheckCircle2, 
  RefreshCw,
  Server
} from 'lucide-react';

export default function AdminDashboard() {
  const subsystems = [
    { name: 'FastAPI REST Core Engine', status: 'HEALTHY', latency: '42ms', uptime: '99.98%' },
    { name: 'Maritime-Transformer-v4.2 (Freight)', status: 'HEALTHY', latency: '118ms', uptime: '99.95%' },
    { name: 'Spatial Port Congestion GNN', status: 'HEALTHY', latency: '95ms', uptime: '99.91%' },
    { name: 'PostGIS GIS Spatial Matcher', status: 'HEALTHY', latency: '28ms', uptime: '99.99%' },
    { name: 'Live AIS WebSocket Streaming', status: 'STREAMING', latency: '15ms', uptime: '100.0%' },
    { name: 'Redis Cache Layer', status: 'CONNECTED', latency: '2ms', uptime: '99.99%' },
  ];

  return (
    <div className="space-y-8">
      <BackButton href="/" label="Back to Home" />

      <PageHeader
        title="Platform Administration & System Telemetry"
        description="Global system health, ML inference latency, AIS message throughput, and data pipeline audit."
        badge="System Status: All Operational"
        badgeVariant="default"
      >
        <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
          <RefreshCw className="h-3.5 w-3.5" />
          <span>Refresh Telemetry</span>
        </Button>
      </PageHeader>

      {/* 4 Core Admin Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Tracked AIS Fleet"
          value="1,248 Vessels"
          subtitle="Real-time global coverage"
          icon={Radio}
        />

        <KpiCard
          title="ML Inference Latency"
          value="118 ms"
          subtitle="P95 forecast response"
          icon={Cpu}
        />

        <KpiCard
          title="AIS Ingestion Rate"
          value="4,820 msg/s"
          subtitle="Zero dropped packets"
          icon={Activity}
        />

        <KpiCard
          title="System Availability"
          value="99.98%"
          subtitle="Past 30 days continuous"
          icon={Server}
        />
      </div>

      {/* Subsystem Health Audit Table */}
      <section className="space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 font-mono">
          Subsystem Health & Ingestion Matrix
        </h3>

        <div className="w-full overflow-x-auto border border-zinc-200 rounded bg-white shadow-sm">
          <table className="w-full text-left text-xs text-zinc-800 font-mono">
            <thead className="bg-zinc-50 text-[10px] uppercase font-bold text-zinc-500 border-b border-zinc-200 font-sans tracking-wider">
              <tr>
                <th className="py-3 px-4">Subsystem Component</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">P95 Latency</th>
                <th className="py-3 px-4">Uptime (30d)</th>
                <th className="py-3 px-4 text-right">Audit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {subsystems.map((sub, i) => (
                <tr key={i} className="hover:bg-zinc-50/80 transition-colors">
                  <td className="py-3 px-4 font-bold text-zinc-950 font-sans">
                    {sub.name}
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-50 text-emerald-800 border border-emerald-300">
                      {sub.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-zinc-900">{sub.latency}</td>
                  <td className="py-3 px-4 text-zinc-900 font-bold">{sub.uptime}</td>
                  <td className="py-3 px-4 text-right text-emerald-800 font-bold flex items-center justify-end gap-1 font-sans">
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    <span>Verified</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
