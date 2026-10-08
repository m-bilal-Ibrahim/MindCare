// ============================================================
// MindCare — Therapist Console: AI anxiety-risk assessment
// Decision support for approved psychologists. The psychologist
// enters a patient's answers; the backend forwards them to the AI
// service (POST /ai/anxiety-prediction/). Nothing is stored and the
// result is never shown to the patient.
// ============================================================

import React, { useState } from 'react';
import { AlertTriangle, Info, RotateCcw, Sparkles } from 'lucide-react';
import TherapistLayout from '../components/therapist/TherapistLayout';
import { ErrorPanel, WakingHint } from '../components/therapist/ApiStates';
import {
  AI_OCCUPATIONS,
  AI_WAKING_MESSAGE,
  NOT_APPROVED_MESSAGE,
  predictAnxiety,
  type AnxietyPrediction,
  type AnxietyPredictionInput,
  type RiskClass,
} from '../services/psychologist.service';

type NumericKey = Exclude<keyof AnxietyPredictionInput, 'Occupation' | 'Family History of Anxiety'>;

interface NumberField {
  key: NumericKey;
  label: string;
  hint?: string;
  min: number;
  max?: number;
  step: number;
}

const BASICS: NumberField[] = [
  { key: 'Age', label: 'Age', hint: 'The model supports ages 18–49', min: 18, max: 120, step: 1 },
  { key: 'Sleep Hours', label: 'Sleep (hours/night)', min: 0, max: 24, step: 0.5 },
  { key: 'Physical Activity (hrs/week)', label: 'Physical activity (hours/week)', min: 0, max: 168, step: 0.5 },
  { key: 'Diet Quality (1-10)', label: 'Diet quality (1–10)', min: 1, max: 10, step: 1 },
  { key: 'Therapy Sessions (per month)', label: 'Therapy sessions (per month)', min: 0, max: 31, step: 1 },
];

const VITALS: NumberField[] = [
  { key: 'Heart Rate (bpm)', label: 'Resting heart rate (bpm)', min: 30, max: 220, step: 1 },
  { key: 'Breathing Rate (breaths/min)', label: 'Breathing rate (breaths/min)', min: 5, max: 60, step: 1 },
];

const CAFFEINE: NumberField[] = [
  { key: 'cups_of_coffee', label: 'Cups of coffee', min: 0, max: 20, step: 1 },
  { key: 'cups_of_tea', label: 'Cups of tea', min: 0, max: 20, step: 1 },
  { key: 'energy_drinks', label: 'Energy drinks', min: 0, max: 20, step: 1 },
  { key: 'cans_of_soda', label: 'Cans of soda', min: 0, max: 20, step: 1 },
];

const PSS_QUESTIONS: { key: NumericKey; text: string }[] = [
  { key: 'pss_uncontrollable', text: 'felt that they were unable to control the important things in their life?' },
  { key: 'pss_confident', text: 'felt confident about their ability to handle personal problems?' },
  { key: 'pss_going_your_way', text: 'felt that things were going their way?' },
  { key: 'pss_difficulties_piling_up', text: 'felt difficulties were piling up so high that they could not overcome them?' },
];

const PSS_ANSWERS = ['Never', 'Almost never', 'Sometimes', 'Fairly often', 'Very often'];

type FormState = Record<NumericKey, string> & {
  Occupation: string;
  'Family History of Anxiety': string;
};

const EMPTY_FORM: FormState = {
  Age: '',
  'Sleep Hours': '',
  'Physical Activity (hrs/week)': '',
  cups_of_coffee: '0',
  cups_of_tea: '0',
  energy_drinks: '0',
  cans_of_soda: '0',
  pss_uncontrollable: '',
  pss_confident: '',
  pss_going_your_way: '',
  pss_difficulties_piling_up: '',
  'Heart Rate (bpm)': '',
  'Breathing Rate (breaths/min)': '',
  'Therapy Sessions (per month)': '0',
  'Diet Quality (1-10)': '',
  Occupation: '',
  'Family History of Anxiety': '',
};

const ALL_NUMBER_FIELDS = [...BASICS, ...VITALS, ...CAFFEINE];

/** Client-side check mirroring the backend's bounds; returns errors by key. */
function validate(form: FormState): Record<string, string> {
  const errors: Record<string, string> = {};
  for (const f of ALL_NUMBER_FIELDS) {
    const raw = form[f.key].trim();
    const n = Number(raw);
    if (raw === '' || Number.isNaN(n)) errors[f.key] = 'Required';
    else if (n < f.min || (f.max !== undefined && n > f.max)) errors[f.key] = `Between ${f.min} and ${f.max}`;
    else if (f.step === 1 && !Number.isInteger(n)) errors[f.key] = 'Whole number';
  }
  for (const q of PSS_QUESTIONS) if (form[q.key] === '') errors[q.key] = 'Choose an answer';
  if (!form.Occupation) errors.Occupation = 'Required';
  if (!form['Family History of Anxiety']) errors['Family History of Anxiety'] = 'Required';
  return errors;
}

function toPayload(form: FormState): AnxietyPredictionInput {
  const out: Record<string, unknown> = {};
  for (const f of ALL_NUMBER_FIELDS) out[f.key] = Number(form[f.key]);
  for (const q of PSS_QUESTIONS) out[q.key] = Number(form[q.key]);
  out.Occupation = form.Occupation;
  out['Family History of Anxiety'] = form['Family History of Anxiety'];
  return out as unknown as AnxietyPredictionInput;
}

const RISK_STYLES: Record<RiskClass, { card: string; bar: string; text: string }> = {
  Low: { card: 'bg-emerald-50 border-emerald-200', bar: 'bg-emerald-500', text: 'text-emerald-800' },
  Medium: { card: 'bg-amber-50 border-amber-200', bar: 'bg-amber-500', text: 'text-amber-800' },
  High: { card: 'bg-red-50 border-red-200', bar: 'bg-red-500', text: 'text-red-800' },
};

const pct = (v: number) => `${(v * 100).toFixed(1)}%`;

const inputClass =
  'w-full rounded-xl border bg-white px-4 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-900';

const Section: React.FC<{ title: string; note?: string; children: React.ReactNode }> = ({ title, note, children }) => (
  <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
    <h2 className="font-bold text-gray-900">{title}</h2>
    {note && <p className="text-sm text-gray-500 mt-0.5">{note}</p>}
    <div className="mt-4">{children}</div>
  </section>
);

const AiAssessmentPage: React.FC = () => {
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [result, setResult] = useState<AnxietyPrediction | null>(null);

  const set = (key: keyof FormState, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setErrors((prev) => {
      if (!prev[key]) return prev;
      const next = { ...prev };
      delete next[key];
      return next;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const found = validate(form);
    setErrors(found);
    if (Object.keys(found).length) {
      setApiError('Some answers are missing or out of range — see the highlighted fields.');
      return;
    }
    setSubmitting(true);
    setApiError(null);
    setResult(null);
    const res = await predictAnxiety(toPayload(form));
    setSubmitting(false);
    if (res.data) {
      setResult(res.data);
      requestAnimationFrame(() => document.getElementById('ai-result')?.scrollIntoView({ behavior: 'smooth', block: 'start' }));
    } else {
      setApiError(res.error ?? 'The prediction failed. Please try again.');
    }
  };

  const reset = () => {
    setForm(EMPTY_FORM);
    setErrors({});
    setApiError(null);
    setResult(null);
  };

  const numberInput = (f: NumberField) => (
    <label key={f.key} className="block">
      <span className="block text-sm font-medium text-gray-700 mb-1.5">{f.label}</span>
      <input
        type="number"
        inputMode="decimal"
        min={f.min}
        max={f.max}
        step={f.step}
        value={form[f.key]}
        onChange={(e) => set(f.key, e.target.value)}
        aria-invalid={!!errors[f.key]}
        className={`${inputClass} ${errors[f.key] ? 'border-red-400' : 'border-gray-200'}`}
      />
      {errors[f.key] ? (
        <span className="block text-xs text-red-600 mt-1">{errors[f.key]}</span>
      ) : (
        f.hint && <span className="block text-xs text-gray-400 mt-1">{f.hint}</span>
      )}
    </label>
  );

  const notApproved = apiError === NOT_APPROVED_MESSAGE;
  const waking = apiError === AI_WAKING_MESSAGE;

  return (
    <TherapistLayout breadcrumb={['Care', 'AI assessment']}>
      <h1 className="text-5xl font-black text-gray-900 mb-2">
        Anxiety-risk <span className="italic font-serif font-normal">assessment.</span>
      </h1>
      <p className="text-gray-500 mb-4 max-w-2xl">
        Enter a patient’s answers to get the AI model’s anxiety-risk estimate. It supports your judgement — it doesn’t
        replace it.
      </p>
      <div className="flex items-start gap-3 bg-white/70 border border-gray-200 rounded-xl px-4 py-3 mb-8 max-w-3xl text-sm text-gray-600">
        <Info size={16} className="shrink-0 mt-0.5 text-gray-500" aria-hidden="true" />
        <span>
          Decision support only. Nothing you enter is saved, and the result is never shown to the patient. Every
          prediction needs your clinical review.
        </span>
      </div>

      {notApproved ? (
        <ErrorPanel message={apiError} />
      ) : (
        <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_380px] items-start">
          <form onSubmit={handleSubmit} noValidate className="space-y-5">
            <Section title="About the patient">
              <div className="grid gap-4 sm:grid-cols-2">
                {BASICS.map(numberInput)}
                <label className="block">
                  <span className="block text-sm font-medium text-gray-700 mb-1.5">Occupation</span>
                  <select
                    value={form.Occupation}
                    onChange={(e) => set('Occupation', e.target.value)}
                    aria-invalid={!!errors.Occupation}
                    className={`${inputClass} ${errors.Occupation ? 'border-red-400' : 'border-gray-200'}`}
                  >
                    <option value="">Choose…</option>
                    {AI_OCCUPATIONS.map((o) => (
                      <option key={o} value={o}>
                        {o}
                      </option>
                    ))}
                  </select>
                  {errors.Occupation && <span className="block text-xs text-red-600 mt-1">{errors.Occupation}</span>}
                </label>
                <div>
                  <span className="block text-sm font-medium text-gray-700 mb-1.5">Family history of anxiety</span>
                  <div className="flex gap-2" role="radiogroup" aria-label="Family history of anxiety">
                    {(['Yes', 'No'] as const).map((v) => (
                      <button
                        key={v}
                        type="button"
                        role="radio"
                        aria-checked={form['Family History of Anxiety'] === v}
                        onClick={() => set('Family History of Anxiety', v)}
                        className={`flex-1 text-sm font-semibold px-4 py-2.5 rounded-xl border transition-colors ${
                          form['Family History of Anxiety'] === v
                            ? 'bg-gray-900 text-white border-gray-900'
                            : `bg-white text-gray-700 hover:border-gray-400 ${
                                errors['Family History of Anxiety'] ? 'border-red-400' : 'border-gray-200'
                              }`
                        }`}
                      >
                        {v}
                      </button>
                    ))}
                  </div>
                  {errors['Family History of Anxiety'] && (
                    <span className="block text-xs text-red-600 mt-1">{errors['Family History of Anxiety']}</span>
                  )}
                </div>
              </div>
            </Section>

            <Section title="Vitals">
              <div className="grid gap-4 sm:grid-cols-2">{VITALS.map(numberInput)}</div>
            </Section>

            <Section title="Caffeine per day" note="Typical servings on an ordinary day.">
              <div className="grid gap-4 grid-cols-2 sm:grid-cols-4">{CAFFEINE.map(numberInput)}</div>
            </Section>

            <Section title="Perceived stress (PSS-4)" note="In the last month, how often has the patient…">
              <div className="space-y-5">
                {PSS_QUESTIONS.map((q, i) => (
                  <div key={q.key} role="radiogroup" aria-label={`Question ${i + 1}: ${q.text}`}>
                    <p className="text-sm text-gray-800 mb-2">
                      <span className="font-semibold">{i + 1}.</span> …{q.text}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {PSS_ANSWERS.map((label, value) => {
                        const selected = form[q.key] === String(value);
                        return (
                          <button
                            key={label}
                            type="button"
                            role="radio"
                            aria-checked={selected}
                            onClick={() => set(q.key, String(value))}
                            className={`text-xs sm:text-sm font-semibold px-3 py-2 rounded-full border transition-colors ${
                              selected
                                ? 'bg-gray-900 text-white border-gray-900'
                                : `bg-white text-gray-700 hover:border-gray-400 ${errors[q.key] ? 'border-red-400' : 'border-gray-200'}`
                            }`}
                          >
                            {label}
                          </button>
                        );
                      })}
                    </div>
                    {errors[q.key] && <span className="block text-xs text-red-600 mt-1">{errors[q.key]}</span>}
                  </div>
                ))}
              </div>
            </Section>

            {apiError && !notApproved && (
              <div
                role="alert"
                className={`rounded-xl border px-4 py-3 text-sm ${
                  waking ? 'bg-amber-50 border-amber-200 text-amber-800' : 'bg-red-50 border-red-200 text-red-700'
                }`}
              >
                {apiError}
              </div>
            )}

            <div className="flex flex-wrap items-center gap-3">
              <button
                type="submit"
                disabled={submitting}
                className="inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-6 py-3 rounded-xl hover:bg-gray-800 disabled:opacity-50"
              >
                {submitting ? (
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" aria-hidden="true" />
                ) : (
                  <Sparkles size={15} aria-hidden="true" />
                )}
                {submitting ? 'Assessing…' : waking ? 'Try again' : 'Get assessment'}
              </button>
              <button
                type="button"
                onClick={reset}
                disabled={submitting}
                className="inline-flex items-center gap-2 border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-5 py-3 rounded-xl hover:border-gray-400 disabled:opacity-50"
              >
                <RotateCcw size={14} aria-hidden="true" /> Clear form
              </button>
            </div>
            {submitting && <WakingHint active />}
          </form>

          <aside id="ai-result" className="xl:sticky xl:top-8 scroll-mt-8" aria-live="polite">
            {result ? (
              <ResultCard result={result} />
            ) : (
              <div className="bg-white/60 border border-dashed border-gray-300 rounded-2xl p-8 text-center text-sm text-gray-500">
                <Sparkles size={20} className="mx-auto mb-3 text-gray-400" aria-hidden="true" />
                Fill in all 17 answers and select <span className="font-semibold">Get assessment</span>. The result
                appears here.
              </div>
            )}
          </aside>
        </div>
      )}
    </TherapistLayout>
  );
};

const ResultCard: React.FC<{ result: AnxietyPrediction }> = ({ result }) => {
  const style = RISK_STYLES[result.predicted_class];
  const classes: RiskClass[] = ['Low', 'Medium', 'High'];
  return (
    <div className={`rounded-2xl border p-6 ${style.card}`}>
      <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-1">Predicted anxiety risk</p>
      <p className={`text-5xl font-black mb-1 ${style.text}`}>{result.predicted_class}</p>
      <p className="text-sm text-gray-700 mb-5">
        Confidence <span className="font-bold">{pct(result.confidence)}</span>
        {' · '}
        <span className={result.confidence_label === 'borderline' ? 'font-semibold text-amber-700' : ''}>
          {result.confidence_label === 'borderline' ? 'Borderline' : 'Confident'}
        </span>
      </p>

      <div className="space-y-2.5 mb-5">
        {classes.map((c) => (
          <div key={c}>
            <div className="flex justify-between text-xs font-semibold text-gray-600 mb-1">
              <span>{c}</span>
              <span>{pct(result.probabilities[c])}</span>
            </div>
            <div className="h-2 rounded-full bg-white/80 overflow-hidden">
              <div className={`h-full rounded-full ${RISK_STYLES[c].bar}`} style={{ width: pct(result.probabilities[c]) }} />
            </div>
          </div>
        ))}
      </div>

      {result.uncertainty_flag && (
        <div className="flex items-start gap-2 bg-white border border-red-200 text-red-800 rounded-xl px-3 py-2.5 text-sm mb-3">
          <AlertTriangle size={15} className="shrink-0 mt-0.5" aria-hidden="true" />
          <span>
            <span className="font-semibold">Priority review recommended</span> — the model sees a meaningful chance of
            High anxiety.
          </span>
        </div>
      )}

      {result.confidence_label === 'borderline' && result.borderline_between && (
        <p className="text-sm text-amber-800 mb-3">
          The model is unsure between <span className="font-semibold">{result.borderline_between.join(' and ')}</span>.
        </p>
      )}

      {result.warnings.length > 0 && (
        <div className="bg-white border border-amber-200 rounded-xl px-3 py-2.5 mb-3">
          <p className="text-xs font-semibold tracking-widest text-amber-700 uppercase mb-1">Warnings</p>
          <ul className="list-disc pl-4 space-y-1 text-sm text-amber-900">
            {result.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      <dl className="grid grid-cols-2 gap-3 pt-4 mt-1 border-t border-black/5 text-sm">
        <div>
          <dt className="text-xs text-gray-500">Estimated caffeine</dt>
          <dd className="font-semibold text-gray-900">{Math.round(result.estimated_caffeine_mg)} mg/day</dd>
        </div>
        <div>
          <dt className="text-xs text-gray-500">Stress level used</dt>
          <dd className="font-semibold text-gray-900">{result.estimated_stress_level} / 10</dd>
        </div>
      </dl>
      <p className="text-xs text-gray-500 mt-4">
        A “confident” result means the model is sure of its top class, not that the patient is safe.
      </p>
    </div>
  );
};

export default AiAssessmentPage;
