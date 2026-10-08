// ============================================================
// MindCare — Therapist Console: Care requests (live)
// Pending requests from patients, shown by pseudonym only — the
// real name is revealed once the psychologist accepts.
// ============================================================

import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Check, Clock, Globe, Languages, X } from 'lucide-react';
import TherapistLayout from '../components/therapist/TherapistLayout';
import Avatar from '../components/common/Avatar';
import ConfirmSheet from '../components/therapist/ConfirmSheet';
import { ErrorPanel, LoadingPanel, relativeTime } from '../components/therapist/ApiStates';
import { CONSOLE_ROUTES } from '../constants/therapistConsole';
import {
  DECLINE_REASONS,
  acceptRequest,
  declineRequest,
  getInbox,
  type DeclineReason,
  type InboxItem,
} from '../services/psychologist.service';

const initialsOf = (name: string) =>
  name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('') || '?';

type Pending = { kind: 'accept' | 'decline'; item: InboxItem } | null;

const TherapistRequestsPage: React.FC = () => {
  const [items, setItems] = useState<InboxItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<Pending>(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    setItems(null);
    const res = await getInbox();
    if (res.data) setItems(res.data);
    else setError(res.error ?? 'Couldn’t load requests.');
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const close = () => {
    if (busy) return;
    setPending(null);
    setActionError(null);
  };

  const handleConfirm = async (reason: string | null) => {
    if (!pending) return;
    setBusy(true);
    setActionError(null);
    const { kind, item } = pending;
    const res =
      kind === 'accept' ? await acceptRequest(item.id) : await declineRequest(item.id, reason as DeclineReason | null);
    setBusy(false);
    if (!res.data) {
      setActionError(res.error ?? 'That didn’t work. Please try again.');
      return;
    }
    setItems((prev) => prev?.filter((r) => r.id !== item.id) ?? prev);
    setNotice(
      kind === 'accept'
        ? `${item.requester.pseudonym} is now your patient. Their details are on the Patients page.`
        : `Request from ${item.requester.pseudonym} declined.`
    );
    setPending(null);
  };

  return (
    <TherapistLayout breadcrumb={['Practice', 'Requests']}>
      <h1 className="text-5xl font-black text-gray-900 mb-2">
        Care <span className="italic font-serif font-normal">requests.</span>
      </h1>
      <p className="text-gray-500 mb-6 max-w-2xl">
        Patients who asked you to be their psychologist. You see a pseudonym until you accept; requests expire after 3
        days.
      </p>

      {notice && (
        <div
          role="status"
          className="flex items-start justify-between gap-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm rounded-xl px-4 py-3 mb-6"
        >
          <span>
            {notice}{' '}
            {notice.includes('Patients page') && (
              <Link to={CONSOLE_ROUTES.PATIENTS} className="font-semibold underline">
                Open patients
              </Link>
            )}
          </span>
          <button type="button" onClick={() => setNotice(null)} aria-label="Dismiss" className="shrink-0">
            <X size={14} />
          </button>
        </div>
      )}

      {error ? (
        <ErrorPanel message={error} onRetry={load} />
      ) : !items ? (
        <LoadingPanel label="Loading requests…" />
      ) : items.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center">
          <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-4">
            <Check size={18} className="text-emerald-700" />
          </div>
          <p className="text-gray-900 font-semibold">Inbox clear.</p>
          <p className="text-sm text-gray-500">No pending requests right now.</p>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-sm font-semibold text-gray-700">
            {items.length} pending {items.length === 1 ? 'request' : 'requests'}
          </p>
          {items.map((req) => {
            const r = req.requester;
            const facts = [r.age != null ? `${r.age} yrs` : null, r.gender ? r.gender[0].toUpperCase() + r.gender.slice(1) : null]
              .filter(Boolean)
              .join(' · ');
            return (
              <div key={req.id} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-start justify-between gap-4 mb-4">
                  <div className="flex items-start gap-4">
                    <Avatar initials={initialsOf(r.pseudonym)} color="bg-violet-600" />
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <p className="font-bold text-gray-900">{r.pseudonym}</p>
                        <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-violet-100 text-violet-700">
                          Pseudonym
                        </span>
                      </div>
                      {facts && <p className="text-sm text-gray-500 mt-0.5">{facts}</p>}
                    </div>
                  </div>
                  <span className="text-xs text-gray-400 shrink-0">Requested {relativeTime(req.requested_at)}</span>
                </div>

                <div className="flex flex-wrap gap-x-5 gap-y-2 text-sm text-gray-600 mb-5">
                  {r.country && (
                    <span className="inline-flex items-center gap-1.5">
                      <Globe size={14} aria-hidden="true" /> {r.country.name}
                    </span>
                  )}
                  {r.preferred_language && (
                    <span className="inline-flex items-center gap-1.5">
                      <Languages size={14} aria-hidden="true" /> {r.preferred_language.name}
                    </span>
                  )}
                  {r.timezone && <span className="text-gray-500">{r.timezone}</span>}
                  <span className="inline-flex items-center gap-1.5 text-amber-700">
                    <Clock size={14} aria-hidden="true" /> Expires {relativeTime(req.expires_at)}
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  <button
                    type="button"
                    onClick={() => setPending({ kind: 'decline', item: req })}
                    className="bg-red-50 border border-red-200 text-red-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-red-100 transition-colors"
                  >
                    Decline
                  </button>
                  <button
                    type="button"
                    onClick={() => setPending({ kind: 'accept', item: req })}
                    className="ml-auto inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 transition-colors"
                  >
                    <Check size={14} aria-hidden="true" /> Accept
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <ConfirmSheet
        open={pending?.kind === 'accept'}
        title={`Accept ${pending?.item.requester.pseudonym ?? ''}?`}
        body="They become your patient and you’ll see their full name and contact details on the Patients page."
        confirmLabel="Accept request"
        busy={busy}
        error={actionError}
        onConfirm={handleConfirm}
        onClose={close}
      />
      <ConfirmSheet
        open={pending?.kind === 'decline'}
        title={`Decline ${pending?.item.requester.pseudonym ?? ''}?`}
        body="The patient is told the request was declined and can choose another psychologist. They can’t request you again for 30 days."
        confirmLabel="Decline request"
        tone="danger"
        reasons={DECLINE_REASONS}
        busy={busy}
        error={actionError}
        onConfirm={handleConfirm}
        onClose={close}
      />
    </TherapistLayout>
  );
};

export default TherapistRequestsPage;
