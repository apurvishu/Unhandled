'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { 
  LayoutDashboard, 
  Ship, 
  Anchor, 
  PackagePlus, 
  FileText, 
  TrendingUp, 
  Layers, 
  Compass, 
  Navigation, 
  BarChart3, 
  Scale, 
  Sparkles, 
  Cpu, 
  Clock, 
  ShieldCheck, 
  Boxes
} from 'lucide-react';
import { cn } from '@/lib/utils';

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const { user } = useAuth();

  const role = user?.role || 'PROCUREMENT_OFFICER';

  // Role-specific navigation definitions
  const getNavSections = () => {
    switch (role) {
      case 'PROCUREMENT_OFFICER':
        return [
          {
            title: 'Procurement Core',
            items: [
              { label: 'Overview', href: '/dashboard/procurement', icon: LayoutDashboard },
              { label: 'Create Cargo Need', href: '/cargo/new', icon: PackagePlus, highlight: true },
              { label: 'Cargo Requirements', href: '/cargo', icon: Boxes },
              { label: 'Vessel Matching', href: '/vessels/match', icon: Compass },
              { label: 'AI Charter Decision', href: '/optimization', icon: Sparkles, badge: 'AI' },
              { label: 'Compare Vessels', href: '/charters/compare', icon: Scale },
            ],
          },
          {
            title: 'Intelligence & Tracking',
            items: [
              { label: 'ML Freight Forecast', href: '/forecasts', icon: TrendingUp },
              { label: 'Port Congestion', href: '/congestion', icon: Clock },
              { label: 'AIS Fleet Map', href: '/vessels', icon: Ship },
              { label: 'Voyage Tracking', href: '/voyages', icon: Navigation },
              { label: 'Charter Contracts', href: '/charters', icon: FileText },
              { label: 'Market Analytics', href: '/market', icon: BarChart3 },
            ],
          },
        ];

      case 'SHIP_OWNER':
        return [
          {
            title: 'Fleet Operations',
            items: [
              { label: 'Owner Dashboard', href: '/dashboard/ship-owner', icon: LayoutDashboard },
              { label: 'My Fleet', href: '/vessels', icon: Ship },
              { label: 'Cargo Marketplace', href: '/cargo/marketplace', icon: Boxes, badge: 'Opportunities' },
              { label: 'Charter Offers & Bids', href: '/charters', icon: FileText },
              { label: 'Active Voyages', href: '/voyages', icon: Navigation },
            ],
          },
          {
            title: 'Market & AIS',
            items: [
              { label: 'ML Freight Trends', href: '/forecasts', icon: TrendingUp },
              { label: 'Port Congestion Monitor', href: '/congestion', icon: Clock },
              { label: 'Live AIS Map', href: '/vessels', icon: Compass },
              { label: 'Fuel & Market Intel', href: '/market', icon: BarChart3 },
            ],
          },
        ];

      case 'PORT_OWNER':
        return [
          {
            title: 'Port Management',
            items: [
              { label: 'Port Overview', href: '/dashboard/port-owner', icon: LayoutDashboard },
              { label: 'Berth Operations', href: '/ports', icon: Anchor },
              { label: 'Congestion AI Forecast', href: '/congestion', icon: Clock, badge: 'ML' },
              { label: 'Vessel Traffic / AIS', href: '/vessels', icon: Ship },
              { label: 'Arriving Voyages', href: '/voyages', icon: Navigation },
            ],
          },
          {
            title: 'Analytics',
            items: [
              { label: 'Turnaround & Capacity', href: '/ports/port-paradip', icon: BarChart3 },
              { label: 'Weather & Risk', href: '/market', icon: Compass },
            ],
          },
        ];

      case 'ADMIN':
        return [
          {
            title: 'System Administration',
            items: [
              { label: 'Admin Telemetry', href: '/dashboard/admin', icon: LayoutDashboard },
              { label: 'Vessel Registry', href: '/vessels', icon: Ship },
              { label: 'Port Infrastructure', href: '/ports', icon: Anchor },
              { label: 'Cargo Database', href: '/cargo', icon: Boxes },
              { label: 'Charter Contracts', href: '/charters', icon: FileText },
              { label: 'ML Model Insights', href: '/forecasts', icon: Cpu, badge: 'v4.2' },
              { label: 'System Security', href: '/notifications', icon: ShieldCheck },
            ],
          },
        ];

      default:
        return [];
    }
  };

  const sections = getNavSections();

  return (
    <aside className="w-64 shrink-0 hidden md:flex flex-col border-r border-slate-800/80 bg-slate-950/60 backdrop-blur-md min-h-[calc(100vh-4rem)] p-4 select-none">
      <div className="space-y-6 flex-1">
        {sections.map((section, idx) => (
          <div key={idx}>
            <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-3 mb-2">
              {section.title}
            </p>
            <nav className="space-y-1">
              {section.items.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href) && item.href !== '/dashboard');

                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      'flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all group',
                      isActive
                        ? 'bg-sky-600/15 text-sky-300 border border-sky-500/30 font-semibold'
                        : 'text-slate-300 hover:text-white hover:bg-slate-900/80',
                      item.highlight && !isActive
                        ? 'bg-gradient-to-r from-sky-500/10 to-blue-500/10 text-sky-300 border border-sky-500/20'
                        : ''
                    )}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon
                        className={cn(
                          'h-4 w-4 transition-colors',
                          isActive ? 'text-sky-400' : 'text-slate-400 group-hover:text-slate-200',
                          item.highlight ? 'text-sky-400' : ''
                        )}
                      />
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-300 border border-sky-500/30">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </nav>
          </div>
        ))}
      </div>

      {/* Role Pill Footer */}
      <div className="mt-auto pt-4 border-t border-slate-800/80 px-2">
        <div className="flex items-center justify-between text-[11px] text-slate-400">
          <span className="truncate">Role: <strong className="text-sky-300">{role}</strong></span>
          <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Online
          </span>
        </div>
      </div>
    </aside>
  );
};
