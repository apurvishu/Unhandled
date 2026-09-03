'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { 
  LayoutDashboard, 
  Package, 
  TrendingUp, 
  Compass, 
  Anchor, 
  FileText, 
  Navigation, 
  BarChart3, 
  Radio, 
  Scale, 
  Settings,
  Bell
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const { user } = useAuth();

  const role = user?.role || 'PROCUREMENT_OFFICER';

  const roleNavItems = [
    {
      title: 'Procurement Intelligence',
      role: 'PROCUREMENT_OFFICER',
      items: [
        { href: '/dashboard/procurement', label: 'Procurement Dashboard', icon: LayoutDashboard },
        { href: '/optimization', label: 'AI Charter Decision', icon: Scale },
        { href: '/cargo', label: 'Cargo Requirements', icon: Package },
        { href: '/forecasts', label: 'ML Freight Forecaster', icon: TrendingUp },
        { href: '/vessels', label: 'AIS Fleet Directory', icon: Compass },
        { href: '/congestion', label: 'Port Congestion', icon: Anchor },
        { href: '/charters', label: 'Charter Contracts', icon: FileText },
        { href: '/voyages', label: 'Voyage Tracking', icon: Navigation },
        { href: '/market', label: 'Market Benchmarks', icon: BarChart3 },
      ],
    },
    {
      title: 'Ship Owner Fleet Desk',
      role: 'SHIP_OWNER',
      items: [
        { href: '/dashboard/ship-owner', label: 'Fleet Overview', icon: LayoutDashboard },
        { href: '/cargo/marketplace', label: 'Cargo Opportunities', icon: Package },
        { href: '/charters', label: 'Charter Party Bids', icon: FileText },
        { href: '/voyages', label: 'Fleet Underway', icon: Navigation },
        { href: '/market', label: 'Bunker Fuel & Indices', icon: BarChart3 },
      ],
    },
    {
      title: 'Port Authority Control',
      role: 'PORT_OWNER',
      items: [
        { href: '/dashboard/port-owner', label: 'Terminal Berths', icon: LayoutDashboard },
        { href: '/congestion', label: 'Anchorage Queues', icon: Anchor },
        { href: '/ports', label: 'Port Registry & UKC', icon: Radio },
      ],
    },
    {
      title: 'System & Admin',
      role: 'ADMIN',
      items: [
        { href: '/dashboard/admin', label: 'Platform Telemetry', icon: Settings },
        { href: '/notifications', label: 'System Alerts', icon: Bell },
      ],
    },
  ];

  // Active section based on user role
  const activeSection = roleNavItems.find((s) => s.role === role) || roleNavItems[0];

  return (
    <aside className="w-60 shrink-0 border-r border-zinc-200 bg-white min-h-[calc(100vh-3.5rem)] flex flex-col justify-between p-3">
      <div className="space-y-6">
        {/* Active Role Portal Navigation */}
        <div className="space-y-1">
          <div className="px-2 pb-2 text-[10px] uppercase font-bold tracking-wider text-zinc-400 font-mono">
            {activeSection.title}
          </div>
          <nav className="space-y-0.5">
            {activeSection.items.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2.5 px-2.5 py-1.5 rounded text-xs transition font-medium ${
                    isActive
                      ? 'bg-zinc-900 text-white font-semibold shadow-sm'
                      : 'text-zinc-600 hover:text-zinc-950 hover:bg-zinc-100'
                  }`}
                >
                  <Icon className={`h-4 w-4 shrink-0 ${isActive ? 'text-white' : 'text-zinc-500'}`} />
                  <span className="truncate">{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Global Tools Section */}
        <div className="space-y-1 pt-4 border-t border-zinc-100">
          <div className="px-2 pb-1.5 text-[10px] uppercase font-bold tracking-wider text-zinc-400 font-mono">
            Direct Portals
          </div>
          <nav className="space-y-0.5">
            <Link
              href="/dashboard/procurement"
              className={`flex items-center gap-2 px-2.5 py-1 rounded text-xs transition ${
                pathname === '/dashboard/procurement' ? 'text-black font-semibold bg-zinc-100' : 'text-zinc-500 hover:text-zinc-900 hover:bg-zinc-50'
              }`}
            >
              <span className="h-1.5 w-1.5 rounded-full bg-zinc-400" />
              <span>Procurement Portal</span>
            </Link>
            <Link
              href="/dashboard/ship-owner"
              className={`flex items-center gap-2 px-2.5 py-1 rounded text-xs transition ${
                pathname === '/dashboard/ship-owner' ? 'text-black font-semibold bg-zinc-100' : 'text-zinc-500 hover:text-zinc-900 hover:bg-zinc-50'
              }`}
            >
              <span className="h-1.5 w-1.5 rounded-full bg-zinc-400" />
              <span>Ship Owner Portal</span>
            </Link>
            <Link
              href="/dashboard/port-owner"
              className={`flex items-center gap-2 px-2.5 py-1 rounded text-xs transition ${
                pathname === '/dashboard/port-owner' ? 'text-black font-semibold bg-zinc-100' : 'text-zinc-500 hover:text-zinc-900 hover:bg-zinc-50'
              }`}
            >
              <span className="h-1.5 w-1.5 rounded-full bg-zinc-400" />
              <span>Port Owner Portal</span>
            </Link>
          </nav>
        </div>
      </div>

      {/* System Status Footprint */}
      <div className="pt-4 border-t border-zinc-100 px-2 text-[11px] text-zinc-500 space-y-1">
        <div className="flex items-center justify-between">
          <span className="font-mono text-[10px] text-zinc-400">STATUS</span>
          <span className="flex items-center gap-1 font-mono text-[10px] text-emerald-800 font-semibold">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" />
            OPERATIONAL
          </span>
        </div>
        <p className="text-[10px] text-zinc-400 font-mono">v1.0.0 • SIH26006</p>
      </div>
    </aside>
  );
};
