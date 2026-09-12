// ============================================================
// MindCare — Avatar / Initials Badge Component
// ============================================================

import React from 'react';
import { cn } from '../../utils/cn';

interface AvatarProps {
  initials: string;
  color?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeClasses = {
  sm: 'w-9 h-9 text-xs',
  md: 'w-11 h-11 text-sm',
  lg: 'w-14 h-14 text-base',
};

const Avatar: React.FC<AvatarProps> = ({ initials, color = 'bg-gray-700', size = 'md', className }) => (
  <span
    className={cn(
      'inline-flex items-center justify-center rounded-full font-bold text-white shrink-0',
      sizeClasses[size],
      color,
      className
    )}
    aria-hidden="true"
  >
    {initials}
  </span>
);

export default Avatar;