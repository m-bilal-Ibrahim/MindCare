// ============================================================
// MindCare — Badge / Pill Component
// ============================================================

import React from 'react';
import { cn } from '../../utils/cn';

interface BadgeProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'green' | 'orange' | 'muted';
}

const variantMap = {
  default: 'bg-gray-100 text-gray-700',
  green: 'bg-emerald-100 text-emerald-700',
  orange: 'bg-orange-100 text-orange-700',
  muted: 'bg-gray-50 text-gray-500',
};

const Badge: React.FC<BadgeProps> = ({ children, className, variant = 'default' }) => (
  <span
    className={cn(
      'inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold tracking-wide uppercase',
      variantMap[variant],
      className
    )}
  >
    {children}
  </span>
);

export default Badge;
