'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth';
import { UserRole } from '@/types';
import { 
  Bell, 
  Search, 
  Ship, 
  ShieldCheck, 
  ChevronDown, 
  LogOut, 
  Sparkles, 
  Zap, 
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
    { role: 'PROCUREMENT_OFFICER', label: 'Procurement Officer', desc: 'Manage bulk cargo, charter decisions & optimization' },
    { role: 'SHIP_OWNER', label: 'Ship Owner', desc: 'Fleet management, cargo marketplace & offers' },
    { role: 'PORT_OWNER', label: 'Port Owner', desc: 'Berths, port capacity & congestion monitoring' },
    { role: 'ADMIN', label: 'System Admin', desc: 'Platform analytics, ports, vessels & security' },
  ];

  return (
    <header className="sticky top-0 z-40 h-16 w-full border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between">
      {/* Brand & Search */}
      <div className="flex items-center gap-6">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-sky-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-sky-600/30 group-hover:scale-105 transition-transform">
            <Ship className="h-5 w-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-base tracking-tight text-white">NAVIQ</span>
              <span className="text-[10px] uppercase font-bold tracking-widest px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-400 border border-sky-500/30">
                SIH26006
              </span>
            </div>
            <p className="text-[10px] text-slate-400 font-medium leading-none">Intelligent Freight & Chartering</p>
          </div>
        </Link>

        {/* Global Search Bar */}
        <div className="hidden md:flex items-center relative w-72 lg:w-96">
          <Search className="absolute left-3 h-4 w-4 text-slate-400 pointer-events-none" />
          <input
            type="text"
            placeholder="Search vessels, ports, cargo, IMO, contracts..."
            className="w-full bg-slate-900/90 border border-slate-800 rounded-lg pl-9 pr-12 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
          />
          <span className="absolute right-2.5 text-[10px] text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded border border-slate-700">
            ⌘K
          </span>
        </div>
      </div>

      {/* Right Tools: Live/Demo Switch, Role Quick-Switch, Notifications, User Menu */}
      <div className="flex items-center gap-3">
        {/* Live vs Demo Simulation Mode Switcher */}
        <button
          onClick={() => toggleDemoMode()}
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border transition-all ${
            isDemoMode
              ? 'bg-amber-500/10 text-amber-300 border-amber-500/30 hover:bg-amber-500/20'
              : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20'
          }`}
          title="Toggle between Live FastAPI backend & High-Fidelity Demo Simulation mode"
        >
          {isDemoMode ? (
            <>
              <Zap className="h-3.5 w-3.5 text-amber-400 fill-amber-400/30 animate-pulse" />
              <span>DEMO SIMULATION</span>
            </>
          ) : (
            <>
              <Radio className="h-3.5 w-3.5 text-emerald-400 animate-pulse" />
              <span>LIVE API</span>
            </>
          )}
        </button>

        {/* Judge / Fast Role Switcher */}
        <div className="relative">
          <button
            onClick={() => {
              setShowRoleSelector(!showRoleSelector);
              setShowNotifications(false);
              setShowUserMenu(false);
            }}
            className="flex items-center gap-1.5 bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-800 hover:border-slate-700 px-3 py-1.5 rounded-lg text-xs font-medium transition"
          >
            <SlidersHorizontal className="h-3.5 w-3.5 text-sky-400" />
            <span className="hidden sm:inline">Role:</span>
            <span className="text-sky-400 font-semibold">{user?.role?.replace('_', ' ') || 'Procurement'}</span>
            <ChevronDown className="h-3 w-3 text-slate-400" />
          </button>

          {showRoleSelector && (
            <div className="absolute right-0 mt-2 w-72 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl p-2 z-50 animate-in fade-in zoom-in-95">
              <div className="px-3 py-2 border-b border-slate-800">
                <p className="text-xs font-bold text-slate-200">Switch Demonstration Role</p>
                <p className="text-[11px] text-slate-400">Instantly test role-based workflows & access control</p>
              </div>
              <div className="py-1 space-y-1">
                {roles.map((r) => (
                  <button
                    key={r.role}
                    onClick={() => {
                      quickLogin(r.role);
                      setShowRoleSelector(false);
                    }}
                    className={`w-full text-left px-3 py-2 rounded-lg transition text-xs flex flex-col ${
                      user?.role === r.role ? 'bg-sky-600/20 text-sky-300 border border-sky-500/40' : 'hover:bg-slate-800 text-slate-300'
                    }`}
                  >
                    <span className="font-semibold">{r.label}</span>
                    <span className="text-[10px] text-slate-400">{r.desc}</span>
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
            className="relative p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-900 rounded-lg transition"
            aria-label="Notifications"
          >
            <Bell className="h-4 w-4" />
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-sky-400 animate-ping" />
            )}
            {unreadCount > 0 && (
              <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-sky-500" />
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl p-2 z-50">
              <div className="flex items-center justify-between px-3 py-2 border-b border-slate-800">
                <span className="text-xs font-bold text-slate-200">Notifications ({unreadCount} new)</span>
                <Link
                  href="/notifications"
                  onClick={() => setShowNotifications(false)}
                  className="text-[11px] text-sky-400 hover:text-sky-300 font-medium"
                >
                  View all
                </Link>
              </div>
              <div className="max-h-72 overflow-y-auto divide-y divide-slate-800/60 py-1">
                {DEMO_NOTIFICATIONS.map((n) => (
                  <div key={n.id} className={`p-2.5 text-xs hover:bg-slate-800/50 rounded-lg transition ${!n.isRead ? 'bg-sky-950/20' : ''}`}>
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-slate-200">{n.title}</span>
                      <span className="text-[10px] text-slate-500">{n.createdAt}</span>
                    </div>
                    <p className="text-slate-400 text-[11px] mt-0.5 leading-relaxed">{n.message}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* User Profile / Menu */}
        <div className="relative">
          <button
            onClick={() => {
              setShowUserMenu(!showUserMenu);
              setShowRoleSelector(false);
              setShowNotifications(false);
            }}
            className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-slate-900 border border-transparent hover:border-slate-800 transition"
          >
            <div className="h-7 w-7 rounded-full bg-gradient-to-tr from-slate-700 to-slate-600 flex items-center justify-center font-bold text-xs text-sky-300 border border-sky-500/30">
              {user?.name ? user.name[0] : 'U'}
            </div>
            <div className="hidden lg:block text-left">
              <p className="text-xs font-medium text-slate-200 leading-none">{user?.name || 'User'}</p>
              <p className="text-[10px] text-slate-400 leading-none mt-1">{user?.companyName || 'Enterprise'}</p>
            </div>
            <ChevronDown className="h-3 w-3 text-slate-400" />
          </button>

          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-56 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl p-2 z-50">
              <div className="px-3 py-2 border-b border-slate-800">
                <p className="text-xs font-bold text-slate-200">{user?.name}</p>
                <p className="text-[11px] text-slate-400 truncate">{user?.email}</p>
                <span className="inline-block mt-1 text-[10px] px-2 py-0.5 rounded bg-sky-500/20 text-sky-300 border border-sky-500/30">
                  {user?.role}
                </span>
              </div>
              <div className="py-1">
                <button
                  onClick={() => {
                    logout();
                    setShowUserMenu(false);
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-xs text-rose-400 hover:bg-rose-950/30 rounded-lg transition"
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
