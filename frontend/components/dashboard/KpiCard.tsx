import React from 'react';
import { LucideIcon, TrendingDown, TrendingUp, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  change?: {
    value: string | number;
    trend: 'UP' | 'DOWN' | 'NEUTRAL';
    isPositive?: boolean; // If true, UP is green; if false, DOWN is green (like lower freight/cost)
    label?: string;
  };
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'purple';
  onClick?: () => void;
  className?: string;
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  change,
  variant = 'default',
  onClick,
  className,
}) => {
  const getTrendColor = () => {
    if (!change) return '';
    if (change.trend === 'NEUTRAL') return 'text-slate-400';
    const isGood = change.isPositive !== undefined ? (change.trend === 'UP' ? change.isPositive : !change.isPositive) : change.trend === 'UP';
    return isGood ? 'text-emerald-400' : 'text-rose-400';
  };

  const getBorderAndBg = () => {
    switch (variant) {
      case 'primary':
        return 'border-sky-500/30 bg-gradient-to-b from-sky-950/20 to-slate-900/90 shadow-glow';
      case 'success':
        return 'border-emerald-500/30 bg-gradient-to-b from-emerald-950/20 to-slate-900/90 shadow-glow-green';
      case 'warning':
        return 'border-amber-500/30 bg-gradient-to-b from-amber-950/20 to-slate-900/90 shadow-glow-amber';
      case 'purple':
        return 'border-purple-500/30 bg-gradient-to-b from-purple-950/20 to-slate-900/90';
      default:
        return 'border-slate-800 bg-slate-900/80 hover:border-slate-700';
    }
  };

  return (
    <div
      onClick={onClick}
      className={cn(
        'rounded-xl p-5 border transition-all duration-200 relative overflow-hidden',
        getBorderAndBg(),
        onClick ? 'cursor-pointer hover:scale-[1.01]' : '',
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</p>
          <h3 className="text-2xl sm:text-3xl font-extrabold text-white mt-1.5 tracking-tight font-mono">
            {value}
          </h3>
        </div>
        <div className="p-2.5 rounded-lg bg-slate-800/80 border border-slate-700 text-sky-400">
          <Icon className="h-5 w-5" />
        </div>
      </div>

      {(subtitle || change) && (
        <div className="mt-3.5 flex items-center justify-between text-xs pt-3 border-t border-slate-800/60">
          {change && (
            <div className={cn('flex items-center gap-1 font-semibold', getTrendColor())}>
              {change.trend === 'UP' ? (
                <TrendingUp className="h-3.5 w-3.5" />
              ) : change.trend === 'DOWN' ? (
                <TrendingDown className="h-3.5 w-3.5" />
              ) : (
                <Minus className="h-3.5 w-3.5" />
              )}
              <span>{change.value}</span>
              {change.label && <span className="text-slate-400 font-normal ml-0.5">{change.label}</span>}
            </div>
          )}
          {subtitle && <span className="text-slate-400 text-[11px] truncate max-w-[200px]">{subtitle}</span>}
        </div>
      )}
    </div>
  );
};
