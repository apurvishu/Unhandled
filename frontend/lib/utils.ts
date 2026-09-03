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

/**
 * Functional status indicators with disciplined, high-contrast monochrome & functional accents.
 * Never uses purple, violet, blue, or cyan.
 */
export function getCongestionBadgeColor(level: string): { bg: string; text: string; border: string } {
  switch (level?.toUpperCase()) {
    case 'LOW':
      return { bg: 'bg-emerald-50', text: 'text-emerald-800', border: 'border-emerald-300' };
    case 'MEDIUM':
      return { bg: 'bg-amber-50', text: 'text-amber-900', border: 'border-amber-300' };
    case 'HIGH':
      return { bg: 'bg-orange-50', text: 'text-orange-900', border: 'border-orange-300' };
    case 'CRITICAL':
      return { bg: 'bg-red-50', text: 'text-red-900', border: 'border-red-300' };
    default:
      return { bg: 'bg-zinc-100', text: 'text-zinc-800', border: 'border-zinc-300' };
  }
}

export function getStatusBadgeColor(status: string): { bg: string; text: string; border: string } {
  switch (status) {
    case 'Underway':
    case 'IN_PROGRESS':
    case 'CONTRACTED':
      return { bg: 'bg-zinc-900', text: 'text-white', border: 'border-zinc-900' };
    case 'AVAILABLE':
    case 'OPEN':
    case 'COMPLETED':
    case 'SELECTED':
      return { bg: 'bg-emerald-50', text: 'text-emerald-800', border: 'border-emerald-300' };
    case 'OCCUPIED':
    case 'OFFERED':
    case 'NEGOTIATING':
    case 'MATCHING':
      return { bg: 'bg-amber-50', text: 'text-amber-900', border: 'border-amber-300' };
    case 'At Anchor':
    case 'Awaiting Berth':
      return { bg: 'bg-zinc-100', text: 'text-zinc-900', border: 'border-zinc-300' };
    case 'CANCELLED':
    case 'MAINTENANCE':
      return { bg: 'bg-red-50', text: 'text-red-900', border: 'border-red-300' };
    default:
      return { bg: 'bg-zinc-100', text: 'text-zinc-800', border: 'border-zinc-200' };
  }
}
