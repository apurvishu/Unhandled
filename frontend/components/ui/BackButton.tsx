'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

interface BackButtonProps {
  href?: string;
  label?: string;
}

export const BackButton: React.FC<BackButtonProps> = ({
  href = '/',
  label = 'Back to Home',
}) => {
  return (
    <Link
      href={href}
      className="inline-flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-900 transition font-mono group"
    >
      <ArrowLeft className="h-3.5 w-3.5 group-hover:-translate-x-0.5 transition-transform" />
      <span>{label}</span>
    </Link>
  );
};
