import React from 'react';
import { Badge } from '@/components/ui/Card';

export interface PageHeaderProps {
  title: string;
  description?: string;
  badge?: string;
  badgeVariant?: 'default' | 'success' | 'warning' | 'danger' | 'accent' | 'outline';
  children?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  badge,
  badgeVariant = 'default',
  children,
}) => {
  return (
    <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-4 border-b border-zinc-200">
      <div className="space-y-1">
        <div className="flex items-center gap-2.5">
          <h1 className="text-xl font-bold text-zinc-950 tracking-tight leading-tight">{title}</h1>
          {badge && <Badge variant={badgeVariant}>{badge}</Badge>}
        </div>
        {description && <p className="text-xs text-zinc-500 max-w-3xl leading-relaxed">{description}</p>}
      </div>
      {children && <div className="flex items-center gap-2 shrink-0">{children}</div>}
    </div>
  );
};
