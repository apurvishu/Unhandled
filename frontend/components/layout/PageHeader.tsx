import React from 'react';
import { cn } from '@/lib/utils';

export interface PageHeaderProps {
  title: string;
  description?: string;
  badge?: string;
  badgeVariant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'purple';
  children?: React.ReactNode; // Action buttons
  className?: string;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  badge,
  badgeVariant = 'info',
  children,
  className,
}) => {
  return (
    <div className={cn('flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-800/80 mb-6', className)}>
      <div>
        <div className="flex items-center gap-2.5 flex-wrap">
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">{title}</h1>
          {badge && (
            <span
              className={cn(
                'text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border',
                badgeVariant === 'info' && 'bg-sky-500/10 text-sky-400 border-sky-500/30',
                badgeVariant === 'success' && 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
                badgeVariant === 'warning' && 'bg-amber-500/10 text-amber-400 border-amber-500/30',
                badgeVariant === 'purple' && 'bg-purple-500/10 text-purple-400 border-purple-500/30',
                badgeVariant === 'danger' && 'bg-rose-500/10 text-rose-400 border-rose-500/30'
              )}
            >
              {badge}
            </span>
          )}
        </div>
        {description && <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-3xl">{description}</p>}
      </div>
      {children && <div className="flex items-center gap-2.5 shrink-0 flex-wrap">{children}</div>}
    </div>
  );
};
