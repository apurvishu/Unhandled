import React from 'react';
import { cn } from '@/lib/utils';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'accent' | 'outline' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading = false, children, disabled, ...props }, ref) => {
    const base = 'inline-flex items-center justify-center font-medium transition-colors duration-100 focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-zinc-950 disabled:opacity-50 disabled:pointer-events-none select-none tracking-tight rounded';

    const variants: Record<string, string> = {
      primary: 'bg-black hover:bg-zinc-800 active:bg-zinc-900 text-white border border-black shadow-sm',
      secondary: 'bg-white hover:bg-zinc-50 active:bg-zinc-100 text-zinc-900 border border-zinc-300 shadow-sm',
      accent: 'bg-accent hover:bg-accent-hover text-white border border-accent shadow-sm',
      outline: 'bg-transparent hover:bg-zinc-100 text-zinc-800 border border-zinc-300',
      danger: 'bg-red-700 hover:bg-red-800 text-white border border-red-700 shadow-sm',
      ghost: 'bg-transparent hover:bg-zinc-100 text-zinc-600 hover:text-zinc-900 border border-transparent',
    };

    const sizes: Record<string, string> = {
      sm: 'text-xs h-8 px-2.5 gap-1.5',
      md: 'text-xs h-9 px-3.5 gap-2 font-medium',
      lg: 'text-sm h-10 px-4 gap-2 font-medium',
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(base, variants[variant], sizes[size], className)}
        {...props}
      >
        {isLoading && (
          <svg className="animate-spin -ml-0.5 mr-1.5 h-3.5 w-3.5 text-current" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        )}
        {children}
      </button>
    );
  }
);
Button.displayName = 'Button';
