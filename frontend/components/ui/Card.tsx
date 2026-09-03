import React from 'react';
import { cn } from '@/lib/utils';

/* ── Badge ── */
export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'accent' | 'outline';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = 'default',
  size = 'md',
  children,
  ...props
}) => {
  const variants: Record<string, string> = {
    default: 'bg-zinc-100 text-zinc-800 border-zinc-200',
    success: 'bg-emerald-50 text-emerald-800 border-emerald-300',
    warning: 'bg-amber-50 text-amber-900 border-amber-300',
    danger: 'bg-red-50 text-red-900 border-red-300',
    accent: 'bg-orange-50 text-orange-950 border-orange-300 font-semibold',
    outline: 'bg-transparent text-zinc-700 border-zinc-300',
  };

  const sizes: Record<string, string> = {
    sm: 'text-[10px] px-1.5 py-0.5 font-medium tracking-tight',
    md: 'text-[11px] px-2 py-0.5 font-medium tracking-tight',
  };

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1 rounded border tabular-nums select-none',
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

/* ── Card ── */
export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  bordered?: boolean;
}

export const Card: React.FC<CardProps> = ({ className, bordered = true, children, ...props }) => {
  return (
    <div
      className={cn(
        'bg-white rounded',
        bordered && 'border border-zinc-200 shadow-sm',
        'p-5',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

/* ── Modal ── */
export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  maxWidth?: string;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  maxWidth = 'max-w-xl',
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/60 transition-opacity" onClick={onClose} />
      <div className={cn('relative w-full bg-white border border-zinc-300 rounded shadow-xl overflow-hidden z-10', maxWidth)}>
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-zinc-200 bg-zinc-50">
          <div>
            <h3 className="text-sm font-bold text-zinc-950 tracking-tight">{title}</h3>
            {description && <p className="text-xs text-zinc-500 mt-0.5">{description}</p>}
          </div>
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-zinc-700 text-sm font-semibold p-1 transition"
          >
            ✕
          </button>
        </div>
        <div className="p-5 max-h-[80vh] overflow-y-auto">{children}</div>
      </div>
    </div>
  );
};

/* ── Skeleton ── */
export const Skeleton: React.FC<{ className?: string }> = ({ className }) => {
  return <div className={cn('animate-pulse bg-zinc-100 rounded', className)} />;
};
