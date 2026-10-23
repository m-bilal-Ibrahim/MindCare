// ============================================================
// MindCare — Therapist Console: AI alert layer (read-only)
// Shows the attention level, the rule-based flags and, when the
// low-sleep rule overrides it, the final risk class next to the
// model's own class. Rendered straight from the live AI response:
// nothing is stored and this is never shown to a patient.
// The thresholds are drafts pending psychologist review.
// ============================================================

import React from 'react';
import type { AlertFlag, AnxietyPrediction, AttentionLevel } from '../../services/psychologist.service';

const LEVEL_STYLES: Record<AttentionLevel, { badge: string; label: string }> = {
  urgent: { badge: 'bg-red-600 text-white ring-2 ring-red-200', label: 'Urgent' },
  elevated: { badge: 'bg-orange-100 text-orange-800', label: 'Elevated' },
  notice: { badge: 'bg-amber-50 text-amber-800 border border-amber-200', label: 'Notice' },
  clear: { badge: 'bg-gray-100 text-gray-600', label: 'Clear' },
};

// Short chip text per flag name; unknown names fall back to the feature name.
const FLAG_LABELS: Record<string, (v: number) => string> = {
  low_sleep: (v) => `Sleep ${v} h`,
  high_stress: (v) => `Stress ${v}/10`,
  high_heart_rate: (v) => `Heart rate ${Math.round(v)} bpm`,
  high_breathing_rate: (v) => `Breathing ${Math.round(v)}/min`,
  high_caffeine: (v) => `Caffeine ${Math.round(v)} mg`,
  low_diet_quality: (v) => `Diet ${v}/10`,
};

export function flagChipLabel(flag: AlertFlag): string {
  const label = FLAG_LABELS[flag.name];
  return label ? label(flag.value) : `${flag.feature} ${flag.value}`;
}

const AlertSummary: React.FC<{ result: AnxietyPrediction }> = ({ result }) => {
  // An AI deploy without the alert layer sends none of these fields.
  if (!result.attention_level) return null;
  const level = LEVEL_STYLES[result.attention_level];
  const flags = result.alert_flags ?? [];
  const modelClass = result.model_class ?? result.predicted_class;
  const overridden = result.final_risk_class && result.final_risk_class !== modelClass;

  return (
    <div className="bg-white border border-gray-200 rounded-xl px-3 py-3 mb-5" aria-label="Alert summary">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase">Attention</span>
        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold tracking-wide uppercase ${level.badge}`}>
          {level.label}
        </span>
      </div>

      {flags.length > 0 && (
        <ul className="flex flex-wrap gap-1.5 mt-2.5" aria-label="Alert flags">
          {flags.map((flag) => (
            <li
              key={flag.name}
              title={`${flag.feature}: ${flag.value} (threshold ${flag.threshold})`}
              className="px-2 py-0.5 rounded-md bg-gray-100 text-gray-700 text-xs font-medium"
            >
              {flagChipLabel(flag)}
            </li>
          ))}
        </ul>
      )}

      <p className="text-xs text-gray-600 mt-2.5">
        Model class <span className="font-semibold text-gray-900">{modelClass}</span>
        {overridden && (
          <>
            {' · '}Final risk class <span className="font-semibold text-red-700">{result.final_risk_class}</span>{' '}
            <span className="text-gray-500">(rule override: sleep ≤ 3 h)</span>
          </>
        )}
      </p>
      <p className="text-[11px] text-gray-400 mt-1">Rule-based flags with draft thresholds, pending psychologist review.</p>
    </div>
  );
};

export default AlertSummary;
