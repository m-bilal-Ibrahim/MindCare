// ============================================================
// MindCare — Therapist Console: Patients ("Your people.") — live
// Current patients (accepted relationships, real identity, age
// only) and past patients (ended, pseudonym only).
// ============================================================

import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Globe, Languages, MapPin, Phone, Users, X } from 'lucide-react';
import TherapistLayout from '../components/therapist/TherapistLayout';
import Avatar from '../components/common/Avatar';
import ConfirmSheet from '../components/therapist/ConfirmSheet';
import { ErrorPanel, LoadingPanel, formatDate } from '../components/therapist/ApiStates';
import { CONSOLE_ROUTES } from '../constants/therapistConsole';
import {
  END_REASONS,
  endRelationship,
  getHistory,
  getPatients,
  type AssignedPatient,
  type EndReason,
  type HistoryItem,
} from '../services/psychologist.service';

const AVATAR_COLORS = ['bg-amber-600', 'bg-emerald-700', 'bg-sky-600', 'bg-rose-500', 'bg-violet-600', 'bg-orange-500'];

const initialsOf = (name: string) =>
  name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('') || '?';

const capitalize = (s: string | null) => (s ? s[0].toUpperCase() + s.slice(1).replace(/_/g, ' ') : null);

const END_REASON_LABELS: Record<string, string> = {
  treatment_completed: 'Treatment completed',
  referred_elsewhere: 'Referred elsewhere',
  other: 'Other',
  patient_ended: 'Ended by the patient',
  account_unavailable: 'Account unavailable',
  subscription_lapsed: 'Subscription lapsed',
};

type Tab = 'current' | 'past';

const TherapistPatientsPage: React.FC = () => {
  const [tab, setTab] = useState<Tab>('current');
  const [patients, setPatients] = useState<AssignedPatient[] | null>(null);
  const [history, setHistory] = useState<HistoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ending, setEnding] = useState<AssignedPatient | null>(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    setPatients(null);
    setHistory(null);
    const [current, past] = await Promise.all([getPatients(), getHistory()]);
    if (current.data) setPatients(current.data);
    else setError(current.error ?? 'Couldn’t load patients.');
    setHistory(past.data ?? []);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleEnd = async (reason: string | null) => {
    if (!ending || !reason) return;
    setBusy(true);
    setActionError(null);
    const res = await endRelationship(ending.relationship_id, reason as EndReason);
    setBusy(false);
    if (!res.data) {
      setActionError(res.error ?? 'That didn’t work. Please try again.');
      return;
    }
    const ended = res.data;
    setPatients((prev) => prev?.filter((p) => p.relationship_id !== ending.relationship_id) ?? prev);
    setHistory((prev) => [ended, ...(prev ?? [])]);
    setNotice(`Care with ${ending.full_name} has ended.`);
    setEnding(null);
  };

  const tabButton = (id: Tab, label: string, count: number | undefined) => (
    <button
      type="button"
      onClick={() => setTab(id)}
      className={`text-sm font-semibold px-4 py-2 rounded-full transition-colors ${
        tab === id ? 'bg-gray-900 text-white' : 'bg-white border border-gray-200 text-gray-700 hover:border-gray-400'
      }`}
    >
      {label}
      {count !== undefined && ` · ${count}`}
    </button>
  );

  return (
    <TherapistLayout breadcrumb={['Practice', 'Patients']}>
      <h1 className="text-5xl font-black text-gray-900 mb-2">
        Your <span className="italic font-serif font-normal">people.</span>
      </h1>
      <p className="text-gray-500 mb-6">
        Patients whose requests you accepted. New requests arrive in{' '}
        <Link to={CONSOLE_ROUTES.REQUESTS} className="font-semibold text-gray-900 underline">
          Requests
        </Link>
        .
      </p>

      {notice && (
        <div
          role="status"
          className="flex items-start justify-between gap-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm rounded-xl px-4 py-3 mb-6"
        >
          <span>{notice}</span>
          <button type="button" onClick={() => setNotice(null)} aria-label="Dismiss" className="shrink-0">
            <X size={14} />
          </button>
        </div>
      )}

      {error ? (
        <ErrorPanel message={error} onRetry={load} />
      ) : !patients ? (
        <LoadingPanel label="Loading patients…" />
      ) : (
        <>
          <div className="flex flex-wrap gap-2 mb-6">
            {tabButton('current', 'Current', patients.length)}
            {tabButton('past', 'Past', history?.length)}
          </div>

          {tab === 'current' ? (
            patients.length === 0 ? (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center">
                <Users size={22} className="mx-auto mb-3 text-gray-400" aria-hidden="true" />
                <p className="text-gray-900 font-semibold">No current patients.</p>
                <p className="text-sm text-gray-500">Accepted requests show up here.</p>
              </div>
            ) : (
              <div className="grid gap-4 lg:grid-cols-2">
                {patients.map((p, i) => {
                  const facts = [p.age != null ? `${p.age} yrs` : null, capitalize(p.gender)].filter(Boolean).join(' · ');
                  const place = [p.city?.name, p.country?.name].filter(Boolean).join(', ');
                  return (
                    <div key={p.relationship_id} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 flex flex-col">
                      <div className="flex items-start gap-4 mb-4">
                        <Avatar initials={initialsOf(p.full_name)} color={AVATAR_COLORS[i % AVATAR_COLORS.length]} />
                        <div className="min-w-0">
                          <p className="font-bold text-gray-900 truncate">{p.full_name}</p>
                          <p className="text-sm text-gray-500">
                            {facts}
                            {facts && ' · '}
                            <span className="text-gray-400">aka {p.pseudonym}</span>
                          </p>
                        </div>
                      </div>

                      <dl className="space-y-2 text-sm text-gray-600 mb-5">
                        {place && (
                          <div className="flex items-center gap-2">
                            <MapPin size={14} aria-hidden="true" className="text-gray-400" />
                            <dt className="sr-only">Location</dt>
                            <dd>{place}</dd>
                          </div>
                        )}
                        {p.phone_number && (
                          <div className="flex items-center gap-2">
                            <Phone size={14} aria-hidden="true" className="text-gray-400" />
                            <dt className="sr-only">Phone</dt>
                            <dd>{p.phone_number}</dd>
                          </div>
                        )}
                        {p.preferred_language && (
                          <div className="flex items-center gap-2">
                            <Languages size={14} aria-hidden="true" className="text-gray-400" />
                            <dt className="sr-only">Preferred language</dt>
                            <dd>{p.preferred_language.name}</dd>
                          </div>
                        )}
                        {p.timezone && (
                          <div className="flex items-center gap-2">
                            <Globe size={14} aria-hidden="true" className="text-gray-400" />
                            <dt className="sr-only">Time zone</dt>
                            <dd>{p.timezone}</dd>
                          </div>
                        )}
                      </dl>

                      <div className="mt-auto flex items-center justify-between gap-3 pt-4 border-t border-gray-100">
                        <span className="text-xs text-gray-400">Patient since {formatDate(p.accepted_at)}</span>
                        <button
                          type="button"
                          onClick={() => {
                            setActionError(null);
                            setEnding(p);
                          }}
                          className="text-sm font-semibold text-red-700 border border-red-200 bg-red-50 px-4 py-2 rounded-xl hover:bg-red-100"
                        >
                          End care
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )
          ) : !history || history.length === 0 ? (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center text-gray-500">
              No past patients yet.
            </div>
          ) : (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[11px] font-semibold tracking-widest text-gray-500 uppercase border-b border-gray-100">
                    <th className="px-6 py-3">Patient</th>
                    <th className="px-6 py-3">Accepted</th>
                    <th className="px-6 py-3">Ended</th>
                    <th className="px-6 py-3">Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((h) => (
                    <tr key={h.relationship_id} className="border-b border-gray-50 last:border-0">
                      <td className="px-6 py-3 font-semibold text-gray-900">{h.pseudonym}</td>
                      <td className="px-6 py-3 text-gray-600">{formatDate(h.accepted_at)}</td>
                      <td className="px-6 py-3 text-gray-600">{formatDate(h.ended_at)}</td>
                      <td className="px-6 py-3 text-gray-600">{END_REASON_LABELS[h.end_reason] ?? capitalize(h.end_reason)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      <ConfirmSheet
        open={!!ending}
        title={`End care with ${ending?.full_name ?? ''}?`}
        body="The patient is told the relationship has ended and can choose a new psychologist. This can’t be undone."
        confirmLabel="End care"
        tone="danger"
        reasons={END_REASONS}
        reasonRequired
        busy={busy}
        error={actionError}
        onConfirm={handleEnd}
        onClose={() => !busy && setEnding(null)}
      />
    </TherapistLayout>
  );
};

export default TherapistPatientsPage;
