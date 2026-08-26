import React from 'react';
import { cn } from '@/lib/utils';

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'purple' | 'outline';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = 'default',
  size = 'md',
  children,
  ...props
}) => {
  const variants = {
    default: 'bg-slate-800 text-slate-300 border-slate-700',
    success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    warning: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    danger: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    info: 'bg-sky-500/10 text-sky-400 border-sky-500/30',
    purple: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
    outline: 'bg-transparent text-slate-300 border-slate-700',
  };

  const sizes = {
    sm: 'text-[10px] px-2 py-0.5 font-semibold',
    md: 'text-xs px-2.5 py-1 font-medium',
  };

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1 rounded-full border tracking-wide uppercase',
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

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  isGlow?: boolean;
}

export const Card: React.FC<CardProps> = ({ className, isGlow = false, children, ...props }) => {
  return (
    <div
      className={cn(
        'bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-sm transition-all',
        isGlow ? 'shadow-glow border-sky-500/30' : 'hover:border-slate-700',
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

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
  maxWidth = 'max-w-2xl',
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/75 backdrop-blur-sm transition-opacity" onClick={onClose} />
      <div className={cn('relative w-full bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden z-10', maxWidth)}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
          <div>
            <h3 className="text-lg font-bold text-slate-100">{title}</h3>
            {description && <p className="text-xs text-slate-400 mt-0.5">{description}</p>}
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 rounded-lg p-1.5 hover:bg-slate-800 transition"
          >
            ✕
          </button>
        </div>
        <div className="p-6 max-h-[80vh] overflow-y-auto">{children}</div>
      </div>
    </div>
  );
};

export const Skeleton: React.FC<{ className?: string }> = ({ className }) => {
  return <div className={cn('animate-pulse bg-slate-800/60 rounded-md', className)} />;
};
