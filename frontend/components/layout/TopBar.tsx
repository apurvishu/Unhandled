'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth';
import { UserRole } from '@/types';
import { 
  Bell, 
  Search, 
  ChevronDown, 
  LogOut, 
  Radio,
  SlidersHorizontal
} from 'lucide-react';
import { DEMO_NOTIFICATIONS } from '@/lib/demoData';

export const TopBar: React.FC = () => {
  const { user, isDemoMode, toggleDemoMode, quickLogin, logout } = useAuth();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showRoleSelector, setShowRoleSelector] = useState(false);

  const unreadCount = DEMO_NOTIFICATIONS.filter((n) => !n.isRead).length;

  const roles: { role: UserRole; label: string; desc: string }[] = [
    { role: 'PROCUREMENT_OFFICER', label: 'Procurement Officer', desc: 'Cargo matching, charter decisions & freight optimization' },
    { role: 'SHIP_OWNER', label: 'Ship Owner', desc: 'Fleet management, cargo marketplace & offers' },
    { role: 'PORT_OWNER', label: 'Port Owner', desc: 'Berths, port capacity & congestion monitoring' },
    { role: 'ADMIN', label: 'System Admin', desc: 'Platform telemetry, vessels & analytics' },
  ];

  return (
    <header className="sticky top-0 z-40 h-14 w-full border-b border-zinc-200 bg-white px-4 sm:px-6 flex items-center justify-between">
      {/* Brand & Search */}
      <div className="flex items-center gap-6">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="h-7 w-7 rounded bg-black flex items-center justify-center text-white font-mono text-xs font-bold">
            N
          </div>
          <div>
            <div className="flex items-center gap-1.5 leading-none">
              <span className="font-bold text-sm tracking-tight text-zinc-950">NAVIQ</span>
              <span className="text-[10px] uppercase font-mono px-1 py-0.2 text-zinc-500 border border-zinc-200 rounded">
                SIH26006
              </span>
            </div>
          </div>
        </Link>

        {/* Global Search Bar */}
        <div className="hidden md:flex items-center relative w-64 lg:w-80">
          <Search className="absolute left-2.5 h-3.5 w-3.5 text-zinc-400 pointer-events-none" />
          <input
            type="text"
            placeholder="Search vessels, ports, cargo, IMO..."
            className="w-full bg-zinc-50 border border-zinc-200 rounded pl-8 pr-10 py-1 text-xs text-zinc-900 placeholder-zinc-400 focus:outline-none focus:border-black focus:bg-white"
          />
          <span className="absolute right-2 text-[10px] font-mono text-zinc-400 border border-zinc-200 px-1 rounded bg-white">
            /
          </span>
        </div>
      </div>

      {/* Right Tools: Live/Demo Switch, Role Quick-Switch, Notifications, User Menu */}
      <div className="flex items-center gap-2">
        {/* Live vs Demo Simulation Switcher */}
        <button
          onClick={() => toggleDemoMode()}
          className={`flex items-center gap-1.5 px-2 py-1 rounded text-[11px] font-mono uppercase tracking-tight border transition-colors ${
            isDemoMode
              ? 'bg-amber-50 text-amber-900 border-amber-300 hover:bg-amber-100'
              : 'bg-emerald-50 text-emerald-900 border-emerald-300 hover:bg-emerald-100'
          }`}
          title="Toggle between Live API and Simulation mode"
        >
          <span className={`h-1.5 w-1.5 rounded-full ${isDemoMode ? 'bg-amber-600' : 'bg-emerald-600'}`} />
          <span>{isDemoMode ? 'SIMULATION' : 'LIVE API'}</span>
        </button>

        {/* Role Switcher */}
        <div className="relative">
          <button
            onClick={() => {
              setShowRoleSelector(!showRoleSelector);
              setShowNotifications(false);
              setShowUserMenu(false);
            }}
            className="flex items-center gap-1.5 bg-white hover:bg-zinc-50 text-zinc-900 border border-zinc-300 px-2.5 py-1 rounded text-xs font-medium transition"
          >
            <SlidersHorizontal className="h-3 w-3 text-zinc-500" />
            <span className="hidden sm:inline text-zinc-500">Role:</span>
            <span className="font-semibold">{user?.role?.replace('_', ' ') || 'Procurement'}</span>
            <ChevronDown className="h-3 w-3 text-zinc-400" />
          </button>

          {showRoleSelector && (
            <div className="absolute right-0 mt-1.5 w-64 bg-white border border-zinc-200 rounded shadow-lg p-1 z-50">
              <div className="px-3 py-1.5 border-b border-zinc-100 text-[11px] font-bold text-zinc-600 uppercase tracking-wider">
                Select Persona
              </div>
              <div className="py-1">
                {roles.map((r) => (
                  <button
                    key={r.role}
                    onClick={() => {
                      quickLogin(r.role);
                      setShowRoleSelector(false);
                    }}
                    className={`w-full text-left px-2.5 py-1.5 rounded transition text-xs flex flex-col ${
                      user?.role === r.role ? 'bg-zinc-900 text-white font-medium' : 'hover:bg-zinc-100 text-zinc-800'
                    }`}
                  >
                    <span className="font-semibold">{r.label}</span>
                    <span className={`text-[10px] ${user?.role === r.role ? 'text-zinc-400' : 'text-zinc-500'}`}>{r.desc}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Notifications Popover */}
        <div className="relative">
          <button
            onClick={() => {
              setShowNotifications(!showNotifications);
              setShowRoleSelector(false);
              setShowUserMenu(false);
            }}
            className="relative p-1.5 text-zinc-600 hover:text-zinc-950 hover:bg-zinc-100 rounded transition border border-transparent"
            aria-label="Notifications"
          >
            <Bell className="h-4 w-4" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 h-1.5 w-1.5 rounded-full bg-accent" />
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-1.5 w-80 bg-white border border-zinc-300 rounded shadow-xl p-1 z-50">
              <div className="flex items-center justify-between px-3 py-2 border-b border-zinc-100">
                <span className="text-xs font-bold uppercase tracking-wider text-zinc-700">Notifications ({unreadCount})</span>
                <Link
                  href="/notifications"
                  onClick={() => setShowNotifications(false)}
                  className="text-[11px] text-zinc-900 hover:underline font-medium"
                >
                  View all
                </Link>
              </div>
              <div className="max-h-64 overflow-y-auto divide-y divide-zinc-100 py-1">
                {DEMO_NOTIFICATIONS.map((n) => (
                  <div key={n.id} className="p-2.5 text-xs hover:bg-zinc-50 transition">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-zinc-900">{n.title}</span>
                      <span className="text-[10px] font-mono text-zinc-400">{n.createdAt}</span>
                    </div>
                    <p className="text-zinc-600 text-[11px] mt-0.5 leading-relaxed">{n.message}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* User Menu */}
        <div className="relative">
          <button
            onClick={() => {
              setShowUserMenu(!showUserMenu);
              setShowRoleSelector(false);
              setShowNotifications(false);
            }}
            className="flex items-center gap-1.5 p-1 rounded hover:bg-zinc-100 transition"
          >
            <div className="h-6 w-6 rounded bg-zinc-200 text-zinc-800 flex items-center justify-center font-bold text-xs">
              {user?.name ? user.name[0] : 'U'}
            </div>
            <ChevronDown className="h-3 w-3 text-zinc-400" />
          </button>

          {showUserMenu && (
            <div className="absolute right-0 mt-1.5 w-48 bg-white border border-zinc-200 rounded shadow-xl p-1 z-50">
              <div className="px-3 py-2 border-b border-zinc-100">
                <p className="text-xs font-bold text-zinc-900">{user?.name}</p>
                <p className="text-[10px] text-zinc-500 truncate">{user?.email}</p>
              </div>
              <div className="py-1">
                <button
                  onClick={() => {
                    logout();
                    setShowUserMenu(false);
                  }}
                  className="w-full flex items-center gap-2 px-3 py-1.5 text-xs text-red-700 hover:bg-red-50 rounded transition"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  <span>Log out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
