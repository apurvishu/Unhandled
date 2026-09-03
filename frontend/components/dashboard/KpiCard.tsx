import React from 'react';
import { LucideIcon, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  change?: {
    value: string | number;
    trend: 'UP' | 'DOWN' | 'NEUTRAL';
    isPositive?: boolean;
    label?: string;
  };
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'accent';
  className?: string;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  change,
  className,
}) => {
  return (
    <div className={cn('bg-white border border-zinc-200 rounded p-4 shadow-sm space-y-2', className)}>
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider">{title}</span>
        {Icon && <Icon className="h-3.5 w-3.5 text-zinc-400" />}
      </div>

      <div className="flex items-baseline justify-between gap-2">
        <span className="text-2xl font-bold tracking-tight text-zinc-950 font-mono tabular-nums">
          {value}
        </span>

        {change && (
          <div
            className={cn(
              'flex items-center gap-0.5 text-[11px] font-mono font-medium',
              change.isPositive ? 'text-emerald-700' : 'text-zinc-600'
            )}
          >
            {change.trend === 'UP' && <ArrowUpRight className="h-3 w-3" />}
            {change.trend === 'DOWN' && <ArrowDownRight className="h-3 w-3" />}
            <span>{change.value}</span>
          </div>
        )}
      </div>

      {subtitle && <p className="text-[11px] text-zinc-500 truncate">{subtitle}</p>}
    </div>
  );
};
