// ============================================================
// MindCare — Therapist Console: therapy notes for one patient
// /therapist/patients/:rel/notes (rel = relationship id).
// Notes are editable for 24 h, then locked: only addenda after that.
// No delete. Progress chart from the rated notes, and the summary
// the patient reads word for word in the app.
// ============================================================

import React, { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Lock, Pencil, Plus } from 'lucide-react';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import TherapistLayout from '../components/therapist/TherapistLayout';
import { ErrorPanel, LoadingPanel, formatDate } from '../components/therapist/ApiStates';
import { CONSOLE_ROUTES } from '../constants/therapistConsole';
import { flattenFieldErrors } from '../services/api.service';
import type { ApiResponse } from '../types';
import type { AssignedPatient } from '../services/psychologist.service';
import {
  addAddendum,
  createNote,
  getNoteSessions,
  getPatient,
  getProgress,
  getSummary,
  listNotes,
  saveSummary,
  updateNote,
  type NoteInput,
  type PatientSummary,
  type ProgressPoint,
  type PsychologistSession,
  type RiskLevel,
  type TherapyNote,
} from '../services/notes.service';

const RISK_STYLES: Record<RiskLevel, string> = {
  low: 'bg-emerald-100 text-emerald-700',
  medium: 'bg-amber-100 text-amber-700',
  high: 'bg-red-100 text-red-700',
};

const SECTIONS = [
  { key: 'observations', label: 'Observations' },
  { key: 'interventions', label: 'Interventions' },
  { key: 'plan', label: 'Plan' },
] as const;

const textarea =
  'w-full rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-900';
const select = 'rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-900';

const dateTime = (iso: string | null) =>
  iso ? new Date(iso).toLocaleString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }) : '';

/** "Editable for 5 h 12 min" until locked_at. */
function lockCountdown(lockedAt: string, now: number) {
  const ms = new Date(lockedAt).getTime() - now;
  if (ms <= 0) return null;
  const h = Math.floor(ms / 3_600_000);
  const m = Math.floor((ms % 3_600_000) / 60_000);
  return h ? `${h} h ${m} min` : `${Math.max(1, m)} min`;
}

/** Backend 400/403/… message, keyed by field ("_" = whole form). */
function errorsOf<T>(res: ApiResponse<T>): Record<string, string> {
  if (res.status === 400 && res.errorBody) return flattenFieldErrors(res.errorBody);
  return { _: res.error ?? 'That didn’t work. Please try again.' };
}

const ErrorText: React.FC<{ msg?: string }> = ({ msg }) =>
  msg ? (
    <p role="alert" className="text-xs text-red-600 mt-1.5">
      {msg}
    </p>
  ) : null;

// ——— Create / edit form ———

const NoteForm: React.FC<{
  note?: TherapyNote;
  sessions: PsychologistSession[] | null;
  onSave: (body: NoteInput) => Promise<Record<string, string> | null>;
  onCancel: () => void;
}> = ({ note, sessions, onSave, onCancel }) => {
  const [form, setForm] = useState({
    session: '',
    observations: note?.observations ?? '',
    interventions: note?.interventions ?? '',
    plan: note?.plan ?? '',
    progress_rating: note?.progress_rating?.toString() ?? '',
    risk_level: note?.risk_level ?? '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof form) => (v: string) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const body: NoteInput = {
      observations: form.observations,
      interventions: form.interventions,
      plan: form.plan,
      progress_rating: form.progress_rating ? Number(form.progress_rating) : null,
      risk_level: (form.risk_level || null) as RiskLevel | null,
    };
    if (!note && form.session) body.session = Number(form.session);
    setBusy(true);
    const errs = await onSave(body);
    setBusy(false);
    setErrors(errs ?? {});
  };

  return (
    <form onSubmit={submit} noValidate className="space-y-4">
      {!note && (
        <label className="block">
          <span className="block text-xs font-bold text-gray-700 uppercase tracking-wide mb-2">Session (optional)</span>
          <select value={form.session} onChange={(e) => set('session')(e.target.value)} className={`${select} w-full`}>
            <option value="">Not linked to a session</option>
            {sessions?.map((s) => (
              <option key={s.id} value={s.id}>
                {dateTime(s.starts_at)} · {s.status.replace('_', '-')}
              </option>
            ))}
          </select>
          <ErrorText msg={errors.session} />
        </label>
      )}
      {SECTIONS.map(({ key, label }) => (
        <label key={key} className="block">
          <span className="block text-xs font-bold text-gray-700 uppercase tracking-wide mb-2">{label}</span>
          <textarea rows={3} value={form[key]} onChange={(e) => set(key)(e.target.value)} className={textarea} />
          <ErrorText msg={errors[key]} />
        </label>
      ))}
      <div className="flex flex-wrap gap-4">
        <label className="block">
          <span className="block text-xs font-bold text-gray-700 uppercase tracking-wide mb-2">Progress (1–10)</span>
          <select value={form.progress_rating} onChange={(e) => set('progress_rating')(e.target.value)} className={select}>
            <option value="">—</option>
            {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
          <ErrorText msg={errors.progress_rating} />
        </label>
        <label className="block">
          <span className="block text-xs font-bold text-gray-700 uppercase tracking-wide mb-2">Risk level</span>
          <select value={form.risk_level} onChange={(e) => set('risk_level')(e.target.value)} className={select}>
            <option value="">—</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
          <ErrorText msg={errors.risk_level} />
        </label>
      </div>
      <p className="text-xs text-gray-500">Every part is optional. Add a progress rating so the note appears on the chart.</p>
      {errors._ && (
        <p role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
          {errors._}
        </p>
      )}
      <div className="flex gap-3 justify-end">
        <button type="button" onClick={onCancel} disabled={busy} className="border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 disabled:opacity-50">
          Cancel
        </button>
        <button type="submit" disabled={busy} className="bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 disabled:opacity-50">
          {busy ? 'Saving…' : note ? 'Save changes' : 'Save note'}
        </button>
      </div>
    </form>
  );
};

// ——— One note ———

const NoteCard: React.FC<{
  note: TherapyNote;
  now: number;
  sessions: PsychologistSession[] | null;
  onEdit: (body: NoteInput) => Promise<Record<string, string> | null>;
  onAddendum: (text: string) => Promise<Record<string, string> | null>;
}> = ({ note, now, sessions, onEdit, onAddendum }) => {
  const [editing, setEditing] = useState(false);
  const [adding, setAdding] = useState(false);
  const [text, setText] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const left = note.is_locked ? null : lockCountdown(note.locked_at, now);

  const saveAddendum = async () => {
    setBusy(true);
    const errs = await onAddendum(text);
    setBusy(false);
    setErrors(errs ?? {});
    if (!errs) {
      setText('');
      setAdding(false);
    }
  };

  return (
    <article className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
        <div>
          <p className="font-bold text-gray-900">{dateTime(note.created_at)}</p>
          <p className="text-xs text-gray-500">
            {note.session_starts_at ? `Session ${dateTime(note.session_starts_at)}` : 'Not linked to a session'}
            {note.version > 1 && ` · edited (v${note.version})`}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {note.progress_rating != null && (
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-gray-100 text-gray-700">Progress {note.progress_rating}/10</span>
          )}
          {note.risk_level && (
            <span className={`text-xs font-semibold px-2.5 py-1 rounded-full capitalize ${RISK_STYLES[note.risk_level]}`}>
              {note.risk_level} risk
            </span>
          )}
          {left ? (
            <span className="text-xs text-gray-500">Editable for {left}</span>
          ) : (
            <span className="inline-flex items-center gap-1 text-xs text-gray-500">
              <Lock size={12} aria-hidden="true" /> Locked
            </span>
          )}
        </div>
      </div>

      {editing ? (
        <NoteForm
          note={note}
          sessions={sessions}
          onCancel={() => setEditing(false)}
          onSave={async (body) => {
            const errs = await onEdit(body);
            if (!errs) setEditing(false);
            return errs;
          }}
        />
      ) : (
        <>
          <dl className="space-y-3">
            {SECTIONS.filter(({ key }) => note[key]).map(({ key, label }) => (
              <div key={key}>
                <dt className="text-xs font-semibold tracking-widest text-gray-500 uppercase">{label}</dt>
                <dd className="text-sm text-gray-800 whitespace-pre-line">{note[key]}</dd>
              </div>
            ))}
          </dl>

          {note.addenda.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-100 space-y-2">
              <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase">Addenda</p>
              {note.addenda.map((a) => (
                <div key={a.id} className="bg-[#F5F0E8] rounded-xl px-4 py-2.5">
                  <p className="text-sm text-gray-800 whitespace-pre-line">{a.text}</p>
                  <p className="text-xs text-gray-500 mt-1">{dateTime(a.created_at)}</p>
                </div>
              ))}
            </div>
          )}

          {adding && (
            <div className="mt-4">
              <label htmlFor={`addendum-${note.id}`} className="block text-xs font-bold text-gray-700 uppercase tracking-wide mb-2">
                Addendum (can’t be edited later)
              </label>
              <textarea id={`addendum-${note.id}`} rows={3} value={text} onChange={(e) => setText(e.target.value)} className={textarea} />
              <ErrorText msg={errors.text ?? errors._} />
              <div className="flex gap-3 justify-end mt-3">
                <button type="button" onClick={() => setAdding(false)} disabled={busy} className="border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 disabled:opacity-50">
                  Cancel
                </button>
                <button type="button" onClick={saveAddendum} disabled={busy} className="bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 disabled:opacity-50">
                  {busy ? 'Saving…' : 'Add addendum'}
                </button>
              </div>
            </div>
          )}

          {!adding && (
            <div className="flex justify-end mt-4">
              {note.is_locked ? (
                <button type="button" onClick={() => setAdding(true)} className="inline-flex items-center gap-1.5 border border-gray-200 bg-white text-gray-700 text-xs font-semibold px-3 py-2 rounded-lg hover:border-gray-400">
                  <Plus size={12} aria-hidden="true" /> Add addendum
                </button>
              ) : (
                <button type="button" onClick={() => setEditing(true)} className="inline-flex items-center gap-1.5 border border-gray-200 bg-white text-gray-700 text-xs font-semibold px-3 py-2 rounded-lg hover:border-gray-400">
                  <Pencil size={12} aria-hidden="true" /> Edit
                </button>
              )}
            </div>
          )}
        </>
      )}
    </article>
  );
};

// ——— Summary for the patient ———

const SummaryCard: React.FC<{ rel: number }> = ({ rel }) => {
  const [summary, setSummary] = useState<PatientSummary | null>(null);
  const [text, setText] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    getSummary(rel).then((res) => {
      if (res.data) {
        setSummary(res.data);
        setText(res.data.text ?? '');
      } else setErrors(errorsOf(res));
    });
  }, [rel]);

  const save = async () => {
    setBusy(true);
    setSaved(false);
    const res = await saveSummary(rel, text);
    setBusy(false);
    if (res.data) {
      setSummary(res.data);
      setErrors({});
      setSaved(true);
    } else setErrors(errorsOf(res));
  };

  return (
    <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6" aria-labelledby="summary-title">
      <h2 id="summary-title" className="font-bold text-gray-900">
        Summary for the patient
      </h2>
      <p className="text-xs text-gray-500 mt-0.5 mb-3">The patient reads this word for word in the MindCare app. Notes stay private.</p>
      <textarea rows={5} value={text} onChange={(e) => { setText(e.target.value); setSaved(false); }} aria-labelledby="summary-title" className={textarea} />
      <ErrorText msg={errors.text ?? errors._} />
      <div className="flex items-center justify-between gap-3 mt-3">
        <span className="text-xs text-gray-500">
          {saved ? 'Saved.' : summary?.updated_at ? `Last saved ${dateTime(summary.updated_at)}` : 'Not written yet'}
        </span>
        <button type="button" onClick={save} disabled={busy || !summary} className="bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 disabled:opacity-50">
          {busy ? 'Saving…' : 'Save summary'}
        </button>
      </div>
    </section>
  );
};

// ——— Page ———

const TherapistNotesPage: React.FC = () => {
  const rel = Number(useParams().rel);
  const [patient, setPatient] = useState<AssignedPatient | null>(null);
  const [notes, setNotes] = useState<TherapyNote[] | null>(null);
  const [progress, setProgress] = useState<ProgressPoint[] | null>(null);
  const [sessions, setSessions] = useState<PsychologistSession[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [now, setNow] = useState(() => Date.now());

  // Re-render every minute so "Editable for …" counts down and notes lock on time.
  useEffect(() => {
    const t = window.setInterval(() => setNow(Date.now()), 60_000);
    return () => window.clearInterval(t);
  }, []);

  const loadProgress = useCallback(() => getProgress(rel).then((r) => setProgress(r.data ?? [])), [rel]);

  const load = useCallback(async () => {
    setError(null);
    setNotes(null);
    const [p, n] = await Promise.all([getPatient(rel), listNotes(rel)]);
    if (!p.data) return setError(p.status === 404 ? 'This person isn’t one of your current patients.' : p.error ?? 'Couldn’t load this patient.');
    if (!n.data) return setError(n.error ?? 'Couldn’t load notes.');
    setPatient(p.data);
    setNotes(n.data);
    loadProgress();
    getNoteSessions(rel).then(setSessions);
  }, [rel, loadProgress]);

  useEffect(() => {
    load();
  }, [load]);

  const replace = (note: TherapyNote) => setNotes((prev) => prev?.map((n) => (n.id === note.id ? note : n)) ?? prev);

  const create = async (body: NoteInput) => {
    const res = await createNote(rel, body);
    if (!res.data) return errorsOf(res);
    setNotes((prev) => [res.data!, ...(prev ?? [])]);
    setCreating(false);
    loadProgress();
    return null;
  };

  const chart = (progress ?? []).filter((p) => p.progress_rating != null).map((p) => ({ date: formatDate(p.date), rating: p.progress_rating }));

  return (
    <TherapistLayout breadcrumb={['Practice', 'Patients', 'Notes']}>
      <Link to={CONSOLE_ROUTES.PATIENTS} className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-900 mb-4">
        <ArrowLeft size={14} aria-hidden="true" /> Patients
      </Link>
      <h1 className="text-5xl font-black text-gray-900 mb-2">
        {patient ? patient.full_name : 'Therapy'} <span className="italic font-serif font-normal">notes.</span>
      </h1>
      <p className="text-gray-500 mb-6 max-w-2xl">
        Only you can see these notes. A note can be edited for 24 hours; after that it’s locked and you can add an addendum. Notes are never deleted.
      </p>

      {error ? (
        <ErrorPanel message={error} onRetry={load} />
      ) : !notes ? (
        <LoadingPanel label="Loading notes…" />
      ) : (
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_380px] items-start">
          <div className="space-y-4">
            {creating ? (
              <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6" aria-label="New note">
                <h2 className="font-bold text-gray-900 mb-4">New note</h2>
                <NoteForm sessions={sessions} onSave={create} onCancel={() => setCreating(false)} />
              </section>
            ) : (
              <button type="button" onClick={() => setCreating(true)} className="inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800">
                <Plus size={15} aria-hidden="true" /> New note
              </button>
            )}

            {notes.length === 0 && !creating ? (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center text-gray-500">No notes yet.</div>
            ) : (
              notes.map((n) => (
                <NoteCard
                  key={n.id}
                  note={n}
                  now={now}
                  sessions={sessions}
                  onEdit={async (body) => {
                    const res = await updateNote(rel, n.id, body);
                    if (!res.data) return errorsOf(res);
                    replace(res.data);
                    loadProgress();
                    return null;
                  }}
                  onAddendum={async (text) => {
                    const res = await addAddendum(rel, n.id, text);
                    if (!res.data) return errorsOf(res);
                    replace({ ...n, addenda: [...n.addenda, res.data] });
                    return null;
                  }}
                />
              ))
            )}
          </div>

          <div className="space-y-6">
            <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6" aria-labelledby="progress-title">
              <h2 id="progress-title" className="font-bold text-gray-900 mb-3">
                Progress
              </h2>
              {chart.length === 0 ? (
                <p className="text-sm text-gray-500">No rated notes yet. Add a progress rating to a note to see it here.</p>
              ) : (
                <div className="h-56" role="img" aria-label={`Progress ratings: ${chart.map((c) => `${c.date} ${c.rating}/10`).join(', ')}`}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chart} margin={{ top: 8, right: 8, bottom: 0, left: -24 }}>
                      <CartesianGrid stroke="#f0f0f0" vertical={false} />
                      <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                      <YAxis domain={[1, 10]} ticks={[1, 4, 7, 10]} tick={{ fontSize: 11 }} />
                      <Tooltip formatter={(v) => [`${v}/10`, 'Progress']} />
                      <Line type="monotone" dataKey="rating" stroke="#111827" strokeWidth={2} dot={{ r: 3 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </section>
            <SummaryCard rel={rel} />
          </div>
        </div>
      )}
    </TherapistLayout>
  );
};

export default TherapistNotesPage;
