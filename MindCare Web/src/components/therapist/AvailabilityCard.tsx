// ============================================================
// MindCare — "Accepting new patients" switch (live)
// GET/PUT /psychologists/me/availability/. Turning it off needs a
// reason; while off, patients can't send new requests.
// ============================================================

import React, { useCallback, useEffect, useState } from 'react';
import { ErrorPanel, WakingHint } from './ApiStates';
import {
  NOT_ACCEPTING_REASONS,
  getAvailability,
  setAvailability,
  type Availability,
  type NotAcceptingReason,
} from '../../services/psychologist.service';

const AvailabilityCard: React.FC = () => {
  const [value, setValue] = useState<Availability | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [choosingReason, setChoosingReason] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoadError(null);
    const res = await getAvailability();
    if (res.data) setValue(res.data);
    else setLoadError(res.error ?? 'Couldn’t load your availability.');
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const save = async (next: Availability) => {
    setSaving(true);
    setSaveError(null);
    const res = await setAvailability(next);
    setSaving(false);
    if (res.data) {
      setValue(res.data);
      setChoosingReason(false);
    } else {
      setSaveError(res.error ?? 'Couldn’t save. Please try again.');
    }
  };

  if (loadError) return <ErrorPanel message={loadError} onRetry={load} />;

  const accepting = value?.accepting ?? false;
  const reasonLabel = NOT_ACCEPTING_REASONS.find((r) => r.value === value?.reason)?.label;

  const handleToggle = () => {
    if (!value || saving) return;
    if (accepting) setChoosingReason(true); // turning off needs a reason first
    else save({ accepting: true, reason: null });
  };

  return (
    <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6" aria-labelledby="availability-title">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 id="availability-title" className="font-bold text-gray-900">
            Accepting new patients
          </h2>
          <p className="text-sm text-gray-500 mt-0.5">
            {!value
              ? 'Loading…'
              : accepting
              ? 'You appear as available in the app’s psychologist directory.'
              : `Patients can’t send you new requests${reasonLabel ? ` · ${reasonLabel}` : ''}. Current patients aren’t affected.`}
          </p>
        </div>
        <button
          type="button"
          role="switch"
          aria-checked={accepting}
          aria-labelledby="availability-title"
          onClick={handleToggle}
          disabled={!value || saving}
          className={`relative w-14 h-8 rounded-full shrink-0 transition-colors disabled:opacity-50 ${
            accepting ? 'bg-emerald-600' : 'bg-gray-300'
          }`}
        >
          <span
            className={`absolute top-1 left-1 w-6 h-6 rounded-full bg-white shadow transition-transform ${
              accepting ? 'translate-x-6' : ''
            }`}
          />
        </button>
      </div>

      {!value && (
        <div className="mt-3">
          <WakingHint active />
        </div>
      )}

      {choosingReason && (
        <div className="mt-5 pt-5 border-t border-gray-100">
          <p className="text-sm font-semibold text-gray-900 mb-3">Why are you pausing new requests?</p>
          <div className="flex flex-wrap gap-2">
            {NOT_ACCEPTING_REASONS.map((r) => (
              <button
                key={r.value}
                type="button"
                disabled={saving}
                onClick={() => save({ accepting: false, reason: r.value as NotAcceptingReason })}
                className="text-sm font-semibold px-4 py-2 rounded-full border border-gray-200 text-gray-700 hover:border-gray-900 disabled:opacity-50"
              >
                {r.label}
              </button>
            ))}
            <button
              type="button"
              disabled={saving}
              onClick={() => setChoosingReason(false)}
              className="text-sm font-semibold px-4 py-2 text-gray-500 hover:text-gray-900"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {saveError && (
        <p role="alert" className="mt-4 text-sm text-red-700">
          {saveError}
        </p>
      )}
    </section>
  );
};

export default AvailabilityCard;
