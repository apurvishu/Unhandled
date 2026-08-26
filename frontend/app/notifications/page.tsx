'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/Button';
import { DEMO_NOTIFICATIONS } from '@/lib/demoData';
import { AppNotification, NotificationType } from '@/types';
import { 
  Bell, 
  TrendingDown, 
  Clock, 
  Ship, 
  FileText, 
  AlertTriangle, 
  CheckCircle2, 
  Filter,
  ArrowRight
} from 'lucide-react';

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<AppNotification[]>(DEMO_NOTIFICATIONS);
  const [filterType, setFilterType] = useState<string>('ALL');

  const handleMarkAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, isRead: true })));
  };

  const getIcon = (type: NotificationType) => {
    switch (type) {
      case 'FREIGHT_ALERT':
        return <TrendingDown className="h-5 w-5 text-teal-400" />;
      case 'CONGESTION_ALERT':
        return <Clock className="h-5 w-5 text-amber-400" />;
      case 'CHARTER_OFFER':
        return <FileText className="h-5 w-5 text-emerald-400" />;
      case 'VESSEL_ETA_CHANGE':
        return <Ship className="h-5 w-5 text-sky-400" />;
      case 'WEATHER_WARNING':
        return <AlertTriangle className="h-5 w-5 text-rose-400" />;
      default:
        return <Bell className="h-5 w-5 text-slate-400" />;
    }
  };

  const filteredNotifications = notifications.filter(
    (n) => filterType === 'ALL' || n.type === filterType
  );

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <PageHeader
        title="Notifications & Real-Time Maritime Alerts"
        description="Streaming alerts for ML freight shifts, port congestion spikes, AIS ETA revisions, and charter offer submissions."
        badge={`${notifications.filter((n) => !n.isRead).length} Unread Alerts`}
        badgeVariant="info"
      >
        <Button variant="outline" size="sm" onClick={handleMarkAllRead}>
          <CheckCircle2 className="h-3.5 w-3.5" />
          <span>Mark All as Read</span>
        </Button>
      </PageHeader>

      {/* FILTER TABS */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2">
        {['ALL', 'FREIGHT_ALERT', 'CONGESTION_ALERT', 'CHARTER_OFFER', 'VESSEL_ETA_CHANGE'].map((t) => (
          <button
            key={t}
            onClick={() => setFilterType(t)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition ${
              filterType === t
                ? 'bg-sky-600/20 text-sky-300 border border-sky-500/40'
                : 'bg-slate-900 hover:bg-slate-800 text-slate-400 border border-slate-800'
            }`}
          >
            {t.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* NOTIFICATIONS LIST */}
      <div className="space-y-3">
        {filteredNotifications.map((notif) => (
          <div
            key={notif.id}
            className={`p-4 rounded-xl border transition flex items-start justify-between gap-4 ${
              !notif.isRead
                ? 'bg-slate-900/90 border-sky-500/30 shadow-glow'
                : 'bg-slate-900/40 border-slate-800/80 hover:border-slate-700'
            }`}
          >
            <div className="flex items-start gap-3.5">
              <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 shrink-0 mt-0.5">
                {getIcon(notif.type)}
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h4 className="font-bold text-white text-sm">{notif.title}</h4>
                  {!notif.isRead && (
                    <span className="h-2 w-2 rounded-full bg-sky-400" />
                  )}
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">{notif.message}</p>
                <span className="text-[10px] text-slate-500 font-mono block">{notif.createdAt}</span>
              </div>
            </div>

            {notif.linkUrl && (
              <Link href={notif.linkUrl} className="shrink-0">
                <Button variant="ghost" size="sm" className="text-sky-400 hover:text-sky-300 text-xs">
                  <span>View</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
