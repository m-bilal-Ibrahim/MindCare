// ============================================================
// MindCare — Console loading / error panels for live API data
// The backend sleeps when idle: the first request can take ~40s,
// so the loader explains the wait after a few seconds.
// ============================================================

import React, { useEffect, useState } from 'react';
import { AlertCircle, Clock, RotateCw } from 'lucide-react';
import { NOT_APPROVED_MESSAGE } from '../../services/psychologist.service';

const SLOW_AFTER_MS = 4000;

/** True once `active` has stayed true for a few seconds. */
export function useSlowHint(active: boolean) {
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    if (!active) {
      setSlow(false);
      return;
    }
    const t = window.setTimeout(() => setSlow(true), SLOW_AFTER_MS);
    return () => window.clearTimeout(t);
  }, [active]);
  return slow;
}

export const WakingHint: React.FC<{ active: boolean }> = ({ active }) =>
  useSlowHint(active) ? (
    <p className="text-sm text-gray-500 max-w-sm mx-auto">
      Waking up the MindCare server — the first request after a quiet spell can take up to a minute.
    </p>
  ) : null;

export const LoadingPanel: React.FC<{ label?: string }> = ({ label = 'Loading…' }) => (
  <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center" aria-live="polite">
    <div className="w-8 h-8 border-2 border-gray-900 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
    <p className="text-gray-900 font-semibold mb-1">{label}</p>
    <WakingHint active />
  </div>
);

export const ErrorPanel: React.FC<{ message: string; onRetry?: () => void; title?: string }> = ({ message, onRetry, title }) => {
  const pending = message === NOT_APPROVED_MESSAGE;
  const Icon = pending ? Clock : AlertCircle;
  return (
    <div
      role="alert"
      className={`rounded-2xl border p-8 text-center ${pending ? 'bg-amber-50 border-amber-200' : 'bg-red-50 border-red-200'}`}
    >
      <Icon size={22} className={`mx-auto mb-3 ${pending ? 'text-amber-700' : 'text-red-700'}`} aria-hidden="true" />
      <p className={`font-semibold mb-1 ${pending ? 'text-amber-900' : 'text-red-800'}`}>
        {title ?? (pending ? 'Awaiting approval' : 'Something went wrong')}
      </p>
      <p className={`text-sm max-w-md mx-auto ${pending ? 'text-amber-800' : 'text-red-700'}`}>{message}</p>
      {onRetry && !pending && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 inline-flex items-center gap-2 border border-red-200 bg-white text-red-700 text-sm font-semibold px-4 py-2 rounded-xl hover:border-red-400"
        >
          <RotateCw size={14} aria-hidden="true" /> Try again
        </button>
      )}
    </div>
  );
};

/** "2 hours ago" / "in 3 days" from an ISO timestamp. */
export function relativeTime(iso: string | null | undefined): string {
  if (!iso) return '';
  const diff = new Date(iso).getTime() - Date.now();
  if (Number.isNaN(diff)) return '';
  const abs = Math.abs(diff);
  const units: [Intl.RelativeTimeFormatUnit, number][] = [
    ['day', 86_400_000],
    ['hour', 3_600_000],
    ['minute', 60_000],
  ];
  const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
  for (const [unit, ms] of units) {
    if (abs >= ms) return rtf.format(Math.round(diff / ms), unit);
  }
  return 'just now';
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '—' : d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}
