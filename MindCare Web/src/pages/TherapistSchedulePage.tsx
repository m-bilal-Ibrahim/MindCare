// ============================================================
// MindCare — Therapist Console: Schedule (live)
// Session requests / upcoming / past with confirm, propose another
// time, cancel and completed / no-show; plus booking settings (fee,
// length, video link), weekly hours and days off.
// Backend: MindCare Backend/docs/handoff/booking-fees.md.
// ============================================================

import React, { useCallback, useEffect, useState } from 'react';
import { Check, Plus, Trash2, X } from 'lucide-react';
import TherapistLayout from '../components/therapist/TherapistLayout';
import ConfirmSheet from '../components/therapist/ConfirmSheet';
import Sheet from '../components/common/Sheet';
import { ErrorPanel, LoadingPanel, formatDate } from '../components/therapist/ApiStates';
import { flattenFieldErrors } from '../services/api.service';
import type { ApiResponse } from '../types';
import {
  addDayOff,
  cancelSession,
  confirmSession,
  getDaysOff,
  getHours,
  getSettings,
  getSlots,
  listSessions,
  markOutcome,
  proposeSession,
  removeDayOff,
  saveHours,
  saveSettings,
  type BookingSession,
  type BookingSettings,
  type DayOff,
  type HoursWindow,
  type SessionView,
} from '../services/booking.service';

const WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const STATUS_STYLES: Record<string, string> = {
  requested: 'bg-amber-100 text-amber-700',
  proposed: 'bg-violet-100 text-violet-700',
  confirmed: 'bg-emerald-100 text-emerald-700',
  completed: 'bg-gray-100 text-gray-700',
  no_show: 'bg-red-100 text-red-700',
  cancelled: 'bg-gray-100 text-gray-500',
  expired: 'bg-gray-100 text-gray-500',
};
const STATUS_LABEL: Record<string, string> = { no_show: 'No-show' };
const REASONS: Record<string, string> = {
  no_fee: 'Set your session fee',
  no_video_link: 'Add your Zoom or Google Meet link',
  no_working_hours: 'Add your weekly hours',
};

const input = 'rounded-xl border border-gray-200 bg-white px-3 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-900';
const when = (iso: string) =>
  new Date(iso).toLocaleString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });

/** The backend's message for a failed call (first field error, else the generic one). */
function messageOf<T>(res: ApiResponse<T>) {
  if (res.status === 400 && res.errorBody) return Object.values(flattenFieldErrors(res.errorBody))[0] ?? res.error ?? '';
  return res.error ?? 'That didn’t work. Please try again.';
}

const Banner: React.FC<{ tone: 'ok' | 'err'; text: string; onClose: () => void }> = ({ tone, text, onClose }) => (
  <div
    role={tone === 'ok' ? 'status' : 'alert'}
    className={`flex items-start justify-between gap-3 border text-sm rounded-xl px-4 py-3 mb-6 ${
      tone === 'ok' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-700'
    }`}
  >
    <span>{text}</span>
    <button type="button" onClick={onClose} aria-label="Dismiss" className="shrink-0">
      <X size={14} />
    </button>
  </div>
);

// ——— Sessions ———

type Action = { kind: 'confirm' | 'cancel' | 'completed' | 'no_show'; session: BookingSession } | null;

const SessionsTab: React.FC<{ view: SessionView; onChanged: (msg: string) => void; onError: (msg: string) => void }> = ({ view, onChanged, onError }) => {
  const [sessions, setSessions] = useState<BookingSession[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [action, setAction] = useState<Action>(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [proposing, setProposing] = useState<BookingSession | null>(null);

  const load = useCallback(async () => {
    setError(null);
    setSessions(null);
    const res = await listSessions(view);
    if (res.data) setSessions(res.data);
    else setError(res.error ?? 'Couldn’t load sessions.');
  }, [view]);

  useEffect(() => {
    load();
  }, [load]);

  const run = async () => {
    if (!action) return;
    setBusy(true);
    setActionError(null);
    const { kind, session } = action;
    const res =
      kind === 'confirm'
        ? await confirmSession(session.id)
        : kind === 'cancel'
        ? await cancelSession(session.id)
        : await markOutcome(session.id, kind);
    setBusy(false);
    if (!res.data) return setActionError(messageOf(res));
    setAction(null);
    onChanged(
      kind === 'confirm' ? 'Session confirmed.' : kind === 'cancel' ? 'Session cancelled.' : kind === 'completed' ? 'Marked as completed.' : 'Marked as no-show.'
    );
    load();
  };

  if (error) return <ErrorPanel message={error} onRetry={load} />;
  if (!sessions) return <LoadingPanel label="Loading sessions…" />;
  if (!sessions.length)
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center text-gray-500">
        {view === 'requests' ? 'No requests waiting for you.' : view === 'upcoming' ? 'No upcoming sessions.' : 'No past sessions yet.'}
      </div>
    );

  const now = Date.now();
  return (
    <>
      <ul className="space-y-3">
        {sessions.map((s) => {
          const ended = new Date(s.ends_at).getTime() <= now;
          const canCancel = ['requested', 'proposed', 'confirmed'].includes(s.status) && new Date(s.starts_at).getTime() > now;
          return (
            <li key={s.id} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 flex flex-wrap items-center gap-4">
              <div className="min-w-0 flex-1">
                <p className="font-bold text-gray-900">
                  {s.patient.display_name}
                  {!s.patient.is_real_name && <span className="ml-2 text-xs font-medium text-gray-400">(care ended)</span>}
                </p>
                <p className="text-sm text-gray-600">
                  {when(s.starts_at)} · {s.duration_minutes} min{s.fee_pkr != null && ` · PKR ${s.fee_pkr.toLocaleString()}`}
                </p>
                {s.status === 'proposed' && <p className="text-xs text-violet-700 mt-0.5">You proposed this time; waiting for the patient.</p>}
                {s.is_late_cancellation && <p className="text-xs text-red-600 mt-0.5">Late cancellation</p>}
              </div>
              <span className={`text-xs font-semibold px-2.5 py-1 rounded-full capitalize ${STATUS_STYLES[s.status] ?? 'bg-gray-100 text-gray-600'}`}>
                {STATUS_LABEL[s.status] ?? s.status}
              </span>
              <div className="flex flex-wrap gap-2">
                {s.status === 'requested' && (
                  <>
                    <SmallButton onClick={() => setProposing(s)}>Propose another time</SmallButton>
                    <SmallButton dark onClick={() => { setActionError(null); setAction({ kind: 'confirm', session: s }); }}>
                      <Check size={12} aria-hidden="true" /> Confirm
                    </SmallButton>
                  </>
                )}
                {s.status === 'confirmed' && ended && !s.outcome_marked_at && (
                  <>
                    <SmallButton onClick={() => { setActionError(null); setAction({ kind: 'no_show', session: s }); }}>No-show</SmallButton>
                    <SmallButton dark onClick={() => { setActionError(null); setAction({ kind: 'completed', session: s }); }}>Completed</SmallButton>
                  </>
                )}
                {canCancel && (
                  <SmallButton danger onClick={() => { setActionError(null); setAction({ kind: 'cancel', session: s }); }}>
                    Cancel
                  </SmallButton>
                )}
              </div>
            </li>
          );
        })}
      </ul>

      {action && (
        <ConfirmSheet
          open
          title={
            action.kind === 'confirm'
              ? `Confirm the session with ${action.session.patient.display_name}?`
              : action.kind === 'cancel'
              ? 'Cancel this session?'
              : action.kind === 'completed'
              ? 'Mark this session as completed?'
              : 'Mark this session as a no-show?'
          }
          body={`${when(action.session.starts_at)} · ${action.session.duration_minutes} min.${
            action.kind === 'confirm' ? ' The patient sees your video link once it’s confirmed.' : action.kind === 'cancel' ? ' The patient is told by email.' : ''
          }`}
          confirmLabel={action.kind === 'confirm' ? 'Confirm session' : action.kind === 'cancel' ? 'Cancel session' : 'Save'}
          tone={action.kind === 'cancel' ? 'danger' : 'default'}
          busy={busy}
          error={actionError}
          onConfirm={run}
          onClose={() => !busy && setAction(null)}
        />
      )}

      <ProposeSheet
        session={proposing}
        onClose={() => setProposing(null)}
        onDone={() => {
          setProposing(null);
          onChanged('New time proposed. The patient needs to accept it.');
          load();
        }}
        onError={onError}
      />
    </>
  );
};

const SmallButton: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement> & { dark?: boolean; danger?: boolean }> = ({ dark, danger, className, ...rest }) => (
  <button
    type="button"
    {...rest}
    className={`inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-lg border transition-colors disabled:opacity-50 ${
      dark ? 'bg-gray-900 border-gray-900 text-white hover:bg-gray-800' : danger ? 'border-red-200 text-red-700 bg-red-50 hover:bg-red-100' : 'border-gray-200 text-gray-700 bg-white hover:border-gray-400'
    } ${className ?? ''}`}
  />
);

/** Pick one of your free slots (sent back exactly as received). */
const ProposeSheet: React.FC<{ session: BookingSession | null; onClose: () => void; onDone: () => void; onError: (m: string) => void }> = ({ session, onClose, onDone }) => {
  const [slots, setSlots] = useState<string[] | null>(null);
  const [chosen, setChosen] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSlots = useCallback(async () => {
    setSlots(null);
    setChosen('');
    const res = await getSlots();
    if (res.data) setSlots(res.data.slots);
    else setError(messageOf(res));
  }, []);

  useEffect(() => {
    if (session) {
      setError(null);
      loadSlots();
    }
  }, [session, loadSlots]);

  const submit = async () => {
    if (!session || !chosen) return;
    setBusy(true);
    setError(null);
    const res = await proposeSession(session.id, chosen);
    setBusy(false);
    if (res.data) return onDone();
    setError(messageOf(res));
    if (res.status === 400) loadSlots(); // "That time isn't available any more": someone took it
  };

  return (
    <Sheet open={!!session} onClose={() => !busy && onClose()} labelledBy="propose-title">
      <div className="p-6 sm:p-8">
        <h2 id="propose-title" className="text-2xl font-black text-gray-900 mb-2 pr-8">
          Propose another time
        </h2>
        <p className="text-sm text-gray-600 mb-5">Your free times from 12 hours to 30 days ahead. The patient must accept the new time.</p>
        {!slots ? (
          <p className="text-sm text-gray-500">{error ? '' : 'Loading your free times…'}</p>
        ) : slots.length === 0 ? (
          <p className="text-sm text-gray-500">No free times. Add weekly hours in Booking settings.</p>
        ) : (
          <label className="block">
            <span className="block text-xs font-bold text-gray-700 uppercase tracking-wide mb-2">New time</span>
            <select value={chosen} onChange={(e) => setChosen(e.target.value)} className={`${input} w-full`}>
              <option value="">Choose a time…</option>
              {slots.map((s) => (
                <option key={s} value={s}>
                  {when(s)}
                </option>
              ))}
            </select>
          </label>
        )}
        {error && (
          <p role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl px-4 py-3 mt-4">
            {error}
          </p>
        )}
        <div className="flex gap-3 justify-end mt-6">
          <button type="button" onClick={onClose} disabled={busy} className="border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-5 py-3 rounded-xl hover:border-gray-400 disabled:opacity-50">
            Cancel
          </button>
          <button type="button" onClick={submit} disabled={busy || !chosen} className="bg-gray-900 text-white text-sm font-semibold px-5 py-3 rounded-xl hover:bg-gray-800 disabled:opacity-40">
            {busy ? 'Sending…' : 'Propose this time'}
          </button>
        </div>
      </div>
    </Sheet>
  );
};

// ——— Booking settings ———

const SettingsTab: React.FC<{ onSaved: (msg: string) => void }> = ({ onSaved }) => {
  const [settings, setSettings] = useState<BookingSettings | null>(null);
  const [form, setForm] = useState({ session_minutes: '50', fee_pkr: '', video_link: '' });
  const [windows, setWindows] = useState<HoursWindow[] | null>(null);
  const [timezone, setTimezone] = useState('');
  const [daysOff, setDaysOff] = useState<DayOff[] | null>(null);
  const [newDay, setNewDay] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoadError(null);
    const [s, h, d] = await Promise.all([getSettings(), getHours(), getDaysOff()]);
    if (!s.data || !h.data || !d.data) return setLoadError(s.error ?? h.error ?? d.error ?? 'Couldn’t load your booking settings.');
    setSettings(s.data);
    setForm({ session_minutes: String(s.data.session_minutes), fee_pkr: s.data.fee_pkr?.toString() ?? '', video_link: s.data.video_link ?? '' });
    setWindows(h.data.windows);
    setTimezone(h.data.timezone);
    setDaysOff(d.data);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const fail = <T,>(res: ApiResponse<T>) => setErrors(res.status === 400 && res.errorBody ? flattenFieldErrors(res.errorBody) : { _: res.error ?? 'That didn’t work.' });

  const saveBasics = async () => {
    setBusy('basics');
    setErrors({});
    const res = await saveSettings({
      session_minutes: Number(form.session_minutes) as 30 | 50 | 60,
      fee_pkr: form.fee_pkr.trim() === '' ? null : Number(form.fee_pkr),
      video_link: form.video_link.trim(),
    });
    setBusy(null);
    if (!res.data) return fail(res);
    setSettings(res.data);
    onSaved('Booking settings saved.');
  };

  const saveWindows = async () => {
    if (!windows) return;
    setBusy('hours');
    setErrors({});
    const res = await saveHours(windows);
    setBusy(null);
    if (!res.data) return fail(res);
    setWindows(res.data.windows);
    const s = await getSettings();
    if (s.data) setSettings(s.data);
    onSaved('Weekly hours saved.');
  };

  const addDay = async () => {
    if (!newDay) return;
    setBusy('day');
    setErrors({});
    const res = await addDayOff(newDay);
    setBusy(null);
    if (!res.data) return fail(res);
    setDaysOff((prev) => [...(prev ?? []), res.data!].sort((a, b) => a.date.localeCompare(b.date)));
    setNewDay('');
  };

  const deleteDay = async (d: DayOff) => {
    setBusy(`day-${d.id}`);
    const res = await removeDayOff(d.id);
    setBusy(null);
    if (res.status && res.status < 300) setDaysOff((prev) => prev?.filter((x) => x.id !== d.id) ?? prev);
    else fail(res);
  };

  if (loadError) return <ErrorPanel message={loadError} onRetry={load} />;
  if (!settings || !windows || !daysOff) return <LoadingPanel label="Loading booking settings…" />;

  const setWindow = (i: number, patch: Partial<HoursWindow>) => setWindows((w) => w!.map((x, j) => (j === i ? { ...x, ...patch } : x)));

  return (
    <div className="space-y-6 max-w-3xl">
      {!settings.is_bookable && settings.not_bookable_reason && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5">
          <p className="font-semibold text-amber-900 mb-1">Patients can’t book you yet</p>
          <p className="text-sm text-amber-800">To open bookings: {REASONS[settings.not_bookable_reason] ?? settings.not_bookable_reason}.</p>
        </div>
      )}
      {errors._ && <p role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl px-4 py-3">{errors._}</p>}

      <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6" aria-labelledby="basics-title">
        <h2 id="basics-title" className="font-bold text-gray-900 mb-4">Fee, length and video link</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block">
            <span className="block text-xs font-bold text-gray-700 uppercase tracking-wide mb-2">Session length</span>
            <select value={form.session_minutes} onChange={(e) => setForm((f) => ({ ...f, session_minutes: e.target.value }))} className={`${input} w-full`}>
              {[30, 50, 60].map((m) => (
                <option key={m} value={m}>{m} minutes</option>
              ))}
            </select>
            {errors.session_minutes && <p role="alert" className="text-xs text-red-600 mt-1.5">{errors.session_minutes}</p>}
          </label>
          <label className="block">
            <span className="block text-xs font-bold text-gray-700 uppercase tracking-wide mb-2">Fee per session (PKR)</span>
            <input type="number" inputMode="numeric" min={0} value={form.fee_pkr} onChange={(e) => setForm((f) => ({ ...f, fee_pkr: e.target.value }))} className={`${input} w-full`} />
            {errors.fee_pkr && <p role="alert" className="text-xs text-red-600 mt-1.5">{errors.fee_pkr}</p>}
          </label>
          <label className="block sm:col-span-2">
            <span className="block text-xs font-bold text-gray-700 uppercase tracking-wide mb-2">Zoom or Google Meet link</span>
            <input type="url" value={form.video_link} onChange={(e) => setForm((f) => ({ ...f, video_link: e.target.value }))} placeholder="https://zoom.us/j/…" className={`${input} w-full`} />
            <span className="block text-xs text-gray-500 mt-1.5">Patients see it only on confirmed sessions.</span>
            {errors.video_link && <p role="alert" className="text-xs text-red-600 mt-1.5">{errors.video_link}</p>}
          </label>
        </div>
        <div className="flex justify-end mt-4">
          <button type="button" onClick={saveBasics} disabled={busy === 'basics'} className="bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 disabled:opacity-50">
            {busy === 'basics' ? 'Saving…' : 'Save'}
          </button>
        </div>
      </section>

      <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6" aria-labelledby="hours-title">
        <h2 id="hours-title" className="font-bold text-gray-900">Weekly hours</h2>
        <p className="text-xs text-gray-500 mb-4">In your time zone ({timezone}). Sessions start inside these hours, with a 10-minute gap between them.</p>
        {windows.length === 0 && <p className="text-sm text-gray-500 mb-3">No hours yet.</p>}
        <ul className="space-y-2">
          {windows.map((w, i) => (
            <li key={i} className="flex flex-wrap items-center gap-2">
              <select aria-label="Day" value={w.weekday} onChange={(e) => setWindow(i, { weekday: Number(e.target.value) })} className={input}>
                {WEEKDAYS.map((d, n) => (
                  <option key={d} value={n}>{d}</option>
                ))}
              </select>
              <input aria-label="From" type="time" value={w.start_time.slice(0, 5)} onChange={(e) => setWindow(i, { start_time: e.target.value })} className={input} />
              <span className="text-sm text-gray-500">to</span>
              <input aria-label="Until" type="time" value={w.end_time.slice(0, 5)} onChange={(e) => setWindow(i, { end_time: e.target.value })} className={input} />
              <button type="button" onClick={() => setWindows((x) => x!.filter((_, j) => j !== i))} aria-label="Remove these hours" className="p-2 rounded-lg text-gray-400 hover:text-red-600">
                <Trash2 size={15} />
              </button>
            </li>
          ))}
        </ul>
        {errors.windows && <p role="alert" className="text-xs text-red-600 mt-2">{errors.windows}</p>}
        <div className="flex justify-between mt-4">
          <button type="button" onClick={() => setWindows((x) => [...x!, { weekday: 0, start_time: '09:00', end_time: '13:00' }])} className="inline-flex items-center gap-1.5 border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400">
            <Plus size={14} aria-hidden="true" /> Add hours
          </button>
          <button type="button" onClick={saveWindows} disabled={busy === 'hours'} className="bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 disabled:opacity-50">
            {busy === 'hours' ? 'Saving…' : 'Save hours'}
          </button>
        </div>
      </section>

      <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6" aria-labelledby="daysoff-title">
        <h2 id="daysoff-title" className="font-bold text-gray-900 mb-4">Days off</h2>
        <ul className="space-y-2 mb-4">
          {daysOff.length === 0 && <li className="text-sm text-gray-500">No days off coming up.</li>}
          {daysOff.map((d) => (
            <li key={d.id} className="flex items-center justify-between border border-gray-100 rounded-xl px-4 py-2.5">
              <span className="text-sm text-gray-800">{formatDate(d.date)}</span>
              <button type="button" onClick={() => deleteDay(d)} disabled={busy === `day-${d.id}`} aria-label={`Remove ${formatDate(d.date)}`} className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 disabled:opacity-50">
                <Trash2 size={14} />
              </button>
            </li>
          ))}
        </ul>
        <div className="flex flex-wrap gap-2">
          <input aria-label="Day off" type="date" value={newDay} onChange={(e) => setNewDay(e.target.value)} className={input} />
          <button type="button" onClick={addDay} disabled={!newDay || busy === 'day'} className="inline-flex items-center gap-1.5 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 disabled:opacity-40">
            <Plus size={14} aria-hidden="true" /> Add day off
          </button>
        </div>
        {errors.date && <p role="alert" className="text-xs text-red-600 mt-2">{errors.date}</p>}
      </section>
    </div>
  );
};

// ——— Page ———

type Tab = SessionView | 'settings';
const TABS: { id: Tab; label: string }[] = [
  { id: 'requests', label: 'Requests' },
  { id: 'upcoming', label: 'Upcoming' },
  { id: 'past', label: 'Past' },
  { id: 'settings', label: 'Booking settings' },
];

const TherapistSchedulePage: React.FC = () => {
  const [tab, setTab] = useState<Tab>('requests');
  const [banner, setBanner] = useState<{ tone: 'ok' | 'err'; text: string } | null>(null);

  return (
    <TherapistLayout breadcrumb={['Practice', 'Schedule']}>
      <h1 className="text-5xl font-black text-gray-900 mb-2">
        Your <span className="italic font-serif font-normal">schedule.</span>
      </h1>
      <p className="text-gray-500 mb-6 max-w-2xl">Session requests from your patients, your upcoming and past sessions, and when patients can book you.</p>

      {banner && <Banner tone={banner.tone} text={banner.text} onClose={() => setBanner(null)} />}

      <div className="flex flex-wrap gap-2 mb-6" role="tablist" aria-label="Schedule">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => { setTab(t.id); setBanner(null); }}
            className={`text-sm font-semibold px-4 py-2 rounded-full transition-colors ${
              tab === t.id ? 'bg-gray-900 text-white' : 'bg-white border border-gray-200 text-gray-700 hover:border-gray-400'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'settings' ? (
        <SettingsTab onSaved={(text) => setBanner({ tone: 'ok', text })} />
      ) : (
        <SessionsTab key={tab} view={tab} onChanged={(text) => setBanner({ tone: 'ok', text })} onError={(text) => setBanner({ tone: 'err', text })} />
      )}
    </TherapistLayout>
  );
};

export default TherapistSchedulePage;
