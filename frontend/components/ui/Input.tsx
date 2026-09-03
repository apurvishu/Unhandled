import React from 'react';
import { cn } from '@/lib/utils';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, hint, id, ...props }, ref) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');
    return (
      <div className="space-y-1">
        {label && (
          <label htmlFor={inputId} className="block text-xs font-semibold uppercase tracking-wider text-zinc-600">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={cn(
            'w-full bg-white border border-zinc-300 rounded px-3 py-1.5 text-xs text-zinc-950 placeholder-zinc-400',
            'focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-colors',
            'disabled:bg-zinc-100 disabled:text-zinc-500',
            error && 'border-red-600 focus:border-red-600 focus:ring-red-600',
            className
          )}
          {...props}
        />
        {error && <p className="text-[11px] text-red-600 font-medium">{error}</p>}
        {hint && !error && <p className="text-[11px] text-zinc-500">{hint}</p>}
      </div>
    );
  }
);
Input.displayName = 'Input';

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: { value: string; label: string }[];
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, options, id, ...props }, ref) => {
    const selectId = id || label?.toLowerCase().replace(/\s+/g, '-');
    return (
      <div className="space-y-1">
        {label && (
          <label htmlFor={selectId} className="block text-xs font-semibold uppercase tracking-wider text-zinc-600">
            {label}
          </label>
        )}
        <select
          ref={ref}
          id={selectId}
          className={cn(
            'w-full bg-white border border-zinc-300 rounded px-3 py-1.5 text-xs text-zinc-950',
            'focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-colors',
            error && 'border-red-600',
            className
          )}
          {...props}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        {error && <p className="text-[11px] text-red-600 font-medium">{error}</p>}
      </div>
    );
  }
);
Select.displayName = 'Select';
