import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number, digits = 0): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(amount);
}

export function formatDwt(dwt: number): string {
  return `${new Intl.NumberFormat('en-US').format(dwt)} MT`;
}

export function formatNauticalMiles(nm: number): string {
  return `${new Intl.NumberFormat('en-US').format(nm)} NM`;
}

export function formatKnots(knots: number): string {
  return `${knots.toFixed(1)} kn`;
}

export function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return dateString;
  }
}

export function formatDateTime(dateString: string): string {
  try {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateString;
  }
}

export function getCongestionBadgeColor(level: string): { bg: string; text: string; border: string } {
  switch (level) {
    case 'LOW':
      return { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/30' };
    case 'MEDIUM':
      return { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/30' };
    case 'HIGH':
      return { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/30' };
    case 'CRITICAL':
      return { bg: 'bg-rose-500/10', text: 'text-rose-400', border: 'border-rose-500/30' };
    default:
      return { bg: 'bg-slate-500/10', text: 'text-slate-400', border: 'border-slate-500/30' };
  }
}

export function getStatusBadgeColor(status: string): { bg: string; text: string; border: string } {
  switch (status) {
    case 'Underway':
    case 'IN_PROGRESS':
    case 'CONTRACTED':
      return { bg: 'bg-cyan-500/10', text: 'text-cyan-400', border: 'border-cyan-500/30' };
    case 'AVAILABLE':
    case 'OPEN':
    case 'COMPLETED':
    case 'SELECTED':
      return { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/30' };
    case 'OCCUPIED':
    case 'OFFERED':
    case 'NEGOTIATING':
    case 'MATCHING':
      return { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/30' };
    case 'At Anchor':
    case 'Awaiting Berth':
      return { bg: 'bg-indigo-500/10', text: 'text-indigo-400', border: 'border-indigo-500/30' };
    case 'CANCELLED':
    case 'MAINTENANCE':
      return { bg: 'bg-rose-500/10', text: 'text-rose-400', border: 'border-rose-500/30' };
    default:
      return { bg: 'bg-slate-500/10', text: 'text-slate-400', border: 'border-slate-500/30' };
  }
}
