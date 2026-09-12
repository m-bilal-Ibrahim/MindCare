// ============================================================
// MindCare — Role Selection Card (used in Onboarding Screen 2)
// ============================================================

import React from 'react';
import { ArrowRight, Check } from 'lucide-react';
import { cn } from '../../utils/cn';
import type { UserRole } from '../../types';

interface RoleCardProps {
  role: UserRole;
  eyebrow: string;
  headline: React.ReactNode;
  description: string;
  benefits: string[];
  footer: string;
  dark?: boolean;
  icon: React.ReactNode;
  primaryCta: string;
  secondaryCta?: string;
  onSelect: (role: UserRole) => void;
  onSecondaryCta?: () => void;
}

const RoleCard: React.FC<RoleCardProps> = ({
  role,
  eyebrow,
  headline,
  description,
  benefits,
  footer,
  dark = false,
  icon,
  primaryCta,
  secondaryCta,
  onSelect,
  onSecondaryCta,
}) => (
  <article
    className={cn(
      'relative rounded-3xl p-8 border flex flex-col h-full transition-all duration-200 cursor-pointer group',
      dark
        ? 'bg-gray-900 border-gray-800 text-white hover:ring-2 hover:ring-gray-600'
        : 'bg-white border-gray-200 text-gray-900 hover:ring-2 hover:ring-gray-300 shadow-sm'
    )}
    role="button"
    tabIndex={0}
    aria-label={`Select role: ${role}`}
    onClick={() => onSelect(role)}
    onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && onSelect(role)}
  >
    {/* Arrow top-right */}
    <div
      className={cn(
        'absolute top-6 right-6 w-9 h-9 rounded-full flex items-center justify-center transition-transform group-hover:translate-x-0.5',
        dark ? 'bg-gray-800' : 'bg-gray-100'
      )}
    >
      <ArrowRight size={16} className={dark ? 'text-gray-400' : 'text-gray-600'} />
    </div>

    {/* Icon */}
    <div
      className={cn(
        'w-14 h-14 rounded-2xl flex items-center justify-center mb-6',
        dark ? 'bg-gray-800' : 'bg-rose-100'
      )}
      aria-hidden="true"
    >
      {icon}
    </div>

    {/* Eyebrow */}
    <p
      className={cn(
        'text-[10px] font-black tracking-[0.2em] uppercase mb-2',
        dark ? 'text-orange-400' : 'text-gray-500'
      )}
    >
      {eyebrow}
    </p>

    {/* Headline */}
    <h2 className="text-2xl sm:text-3xl font-black mb-4 leading-tight">{headline}</h2>

    {/* Description */}
    <p className={cn('text-sm leading-relaxed mb-6', dark ? 'text-gray-300' : 'text-gray-600')}>
      {description}
    </p>

    {/* Benefits */}
    <ul className="space-y-2 mb-8 flex-1" role="list">
      {benefits.map((b) => (
        <li
          key={b}
          className={cn('flex items-start gap-2 text-sm', dark ? 'text-gray-300' : 'text-gray-600')}
        >
          <Check
            size={14}
            className={cn('shrink-0 mt-0.5', dark ? 'text-orange-400' : 'text-emerald-500')}
            aria-hidden="true"
          />
          {b}
        </li>
      ))}
    </ul>

    {/* Footer note */}
    <p className={cn('text-xs mb-6', dark ? 'text-gray-500' : 'text-gray-400')}>{footer}</p>

    {/* CTAs */}
    <div className="flex flex-col sm:flex-row gap-3">
      <button
        onClick={(e) => {
          e.stopPropagation();
          onSelect(role);
        }}
        className={cn(
          'flex-1 py-3.5 px-6 rounded-xl font-bold text-sm transition-all',
          dark
            ? 'bg-orange-500 text-white hover:bg-orange-400'
            : 'bg-gray-900 text-white hover:bg-gray-800'
        )}
      >
        {primaryCta}
      </button>
      {secondaryCta && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onSecondaryCta?.();
          }}
          className={cn(
            'flex-1 py-3.5 px-6 rounded-xl font-bold text-sm border transition-all',
            dark
              ? 'border-gray-700 text-gray-300 hover:bg-gray-800'
              : 'border-gray-200 text-gray-700 hover:bg-gray-50'
          )}
        >
          {secondaryCta}
        </button>
      )}
    </div>
  </article>
);

export default RoleCard;
