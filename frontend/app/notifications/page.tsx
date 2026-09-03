'use client';

import { BackButton } from '@/components/ui/BackButton';
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
        return <TrendingDown className="h-4 w-4 text-zinc-900" />;
      case 'CONGESTION_ALERT':
        return <Clock className="h-4 w-4 text-zinc-900" />;
      case 'CHARTER_OFFER':
        return <FileText className="h-4 w-4 text-zinc-900" />;
      case 'VESSEL_ETA_CHANGE':
        return <Ship className="h-4 w-4 text-zinc-900" />;
      case 'WEATHER_WARNING':
        return <AlertTriangle className="h-4 w-4 text-red-700" />;
      default:
        return <Bell className="h-4 w-4 text-zinc-600" />;
    }
  };

  const filteredNotifications = notifications.filter(
    (n) => filterType === 'ALL' || n.type === filterType
  );

  return (
    <div className="space-y-6">
      <BackButton href="/" label="Back to Home" />

      <PageHeader
        title="Notifications & Real-Time Maritime Alerts"
        description="Streaming alerts for ML freight shifts, port congestion spikes, AIS ETA revisions, and charter offer submissions."
        badge={`${notifications.filter((n) => !n.isRead).length} Unread Alerts`}
        badgeVariant="default"
      >
        <Button variant="outline" size="sm" onClick={handleMarkAllRead}>
          <CheckCircle2 className="h-3.5 w-3.5" />
          <span>Mark All as Read</span>
        </Button>
      </PageHeader>

      {/* FILTER TABS */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
        {['ALL', 'FREIGHT_ALERT', 'CONGESTION_ALERT', 'CHARTER_OFFER', 'VESSEL_ETA_CHANGE'].map((t) => (
          <button
            key={t}
            onClick={() => setFilterType(t)}
            className={`px-3 py-1 rounded text-xs font-mono uppercase tracking-tight transition ${
              filterType === t
                ? 'bg-zinc-900 text-white font-bold'
                : 'bg-white hover:bg-zinc-100 text-zinc-600 border border-zinc-200'
            }`}
          >
            {t.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* NOTIFICATIONS LIST */}
      <div className="space-y-2">
        {filteredNotifications.map((notif) => (
          <div
            key={notif.id}
            className={`p-4 rounded border transition flex items-start justify-between gap-4 ${
              !notif.isRead
                ? 'bg-zinc-50 border-zinc-300'
                : 'bg-white border-zinc-200 hover:border-zinc-300'
            }`}
          >
            <div className="flex items-start gap-3.5">
              <div className="p-2 rounded bg-white border border-zinc-200 shrink-0 mt-0.5">
                {getIcon(notif.type)}
              </div>
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h4 className="font-bold text-zinc-950 text-xs font-mono">{notif.title}</h4>
                  {!notif.isRead && (
                    <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                  )}
                </div>
                <p className="text-xs text-zinc-600 leading-relaxed font-sans">{notif.message}</p>
                <span className="text-[10px] text-zinc-400 font-mono block">{notif.createdAt}</span>
              </div>
            </div>

            {notif.linkUrl && (
              <Link href={notif.linkUrl} className="shrink-0">
                <Button variant="ghost" size="sm" className="text-xs">
                  <span>View</span>
                  <ArrowRight className="h-3 w-3" />
                </Button>
              </Link>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
