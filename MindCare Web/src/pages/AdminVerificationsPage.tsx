// ============================================================
// MindCare — Admin Console: Verifications (live)
// Pending psychologist applications: review the registered
// credentials, then approve or reject. The backend re-checks the
// admin role and audit-logs every decision.
// ============================================================

import React, { useCallback, useEffect, useState } from 'react';
import { Check, ExternalLink, ShieldCheck, X } from 'lucide-react';
import AdminLayout from '../components/admin/AdminLayout';
import Avatar from '../components/common/Avatar';
import ConfirmSheet from '../components/therapist/ConfirmSheet';
import { ErrorPanel, LoadingPanel, formatDate, relativeTime } from '../components/therapist/ApiStates';
import {
  APPROVAL_API_MISSING,
  DJANGO_ADMIN_PENDING_URL,
  REJECT_REASONS,
  approveAccount,
  getPendingPsychologists,
  rejectAccount,
  type PendingPsychologist,
  type RejectReason,
} from '../services/admin.service';

const initialsOf = (name: string) =>
  name
    .replace(/^dr\.?\s+/i, '')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('') || '?';

const capitalize = (s: string | null | undefined) => (s ? s[0].toUpperCase() + s.slice(1).replace(/_/g, ' ') : '—');

const Row: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => (
  <div className="grid grid-cols-1 sm:grid-cols-[180px_minmax(0,1fr)] gap-1 sm:gap-4 py-3 border-b border-gray-100 last:border-0">
    <dt className="text-xs font-semibold tracking-widest text-gray-500 uppercase sm:pt-0.5">{label}</dt>
    <dd className="text-sm text-gray-900 break-words">{children || '—'}</dd>
  </div>
);

type Pending = { kind: 'approve' | 'reject'; item: PendingPsychologist } | null;

const AdminVerificationsPage: React.FC = () => {
  const [items, setItems] = useState<PendingPsychologist[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [pending, setPending] = useState<Pending>(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    setItems(null);
    const res = await getPendingPsychologists();
    if (res.data) {
      setItems(res.data);
      setActiveId((prev) => (res.data!.some((p) => p.id === prev) ? prev : res.data![0]?.id ?? null));
    } else {
      setError(res.error ?? 'Couldn’t load applications.');
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const active = items?.find((p) => p.id === activeId) ?? null;

  const handleConfirm = async (reason: string | null) => {
    if (!pending) return;
    setBusy(true);
    setActionError(null);
    const { kind, item } = pending;
    const res = kind === 'approve' ? await approveAccount(item.id) : await rejectAccount(item.id, reason as RejectReason | null);
    setBusy(false);
    if (!res.data) {
      setActionError(res.error ?? 'That didn’t work. Please try again.');
      return;
    }
    const rest = items?.filter((p) => p.id !== item.id) ?? [];
    setItems(rest);
    setActiveId(rest[0]?.id ?? null);
    setNotice(
      kind === 'approve'
        ? `${item.full_name} is approved and can now sign in to the therapist console.`
        : `${item.full_name}’s application was rejected.`
    );
    setPending(null);
  };

  const profile = active?.psychologist_profile;

  return (
    <AdminLayout breadcrumb={['Operations', 'Verifications']}>
      <h1 className="text-5xl font-black text-gray-900 mb-2">
        Psychologist <span className="italic font-serif font-normal">verifications.</span>
      </h1>
      <p className="text-gray-500 mb-6 max-w-2xl">
        New psychologists can’t sign in until an admin approves them. Check the license with the issuing authority before
        approving.
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
        <div className="space-y-4">
          <ErrorPanel
            message={error}
            title={error === APPROVAL_API_MISSING ? 'Not available yet' : undefined}
            onRetry={error === APPROVAL_API_MISSING ? undefined : load}
          />
          {error === APPROVAL_API_MISSING && (
            <div className="text-center">
              <a
                href={DJANGO_ADMIN_PENDING_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-5 py-3 rounded-xl hover:bg-gray-800"
              >
                Open Django admin <ExternalLink size={14} aria-hidden="true" />
              </a>
            </div>
          )}
        </div>
      ) : !items ? (
        <LoadingPanel label="Loading applications…" />
      ) : items.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center">
          <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-4">
            <ShieldCheck size={18} className="text-emerald-700" />
          </div>
          <p className="text-gray-900 font-semibold">No applications waiting.</p>
          <p className="text-sm text-gray-500">New psychologist sign-ups appear here.</p>
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[320px_minmax(0,1fr)] items-start">
          {/* Queue */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <p className="px-5 py-3 text-xs font-semibold tracking-widest text-gray-500 uppercase border-b border-gray-100">
              Waiting · {items.length}
            </p>
            <ul>
              {items.map((p) => (
                <li key={p.id}>
                  <button
                    type="button"
                    onClick={() => setActiveId(p.id)}
                    aria-current={p.id === activeId}
                    className={`w-full text-left flex items-center gap-3 px-5 py-4 border-b border-gray-50 last:border-0 transition-colors ${
                      p.id === activeId ? 'bg-[#F5F0E8]' : 'hover:bg-gray-50'
                    }`}
                  >
                    <Avatar initials={initialsOf(p.full_name)} color="bg-blue-950" size="sm" />
                    <span className="min-w-0">
                      <span className="block font-semibold text-gray-900 truncate">{p.full_name}</span>
                      <span className="block text-xs text-gray-500">Applied {relativeTime(p.created_at)}</span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Detail */}
          {active && (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
                <div className="flex items-start gap-4">
                  <Avatar initials={initialsOf(active.full_name)} color="bg-blue-950" size="lg" />
                  <div>
                    <p className="text-2xl font-black text-gray-900">{active.full_name}</p>
                    <p className="text-sm text-gray-500">{active.email}</p>
                    <span className="inline-block mt-2 text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-100 text-amber-700">
                      Pending review
                    </span>
                  </div>
                </div>
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      setActionError(null);
                      setPending({ kind: 'reject', item: active });
                    }}
                    className="bg-red-50 border border-red-200 text-red-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-red-100"
                  >
                    Reject
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setActionError(null);
                      setPending({ kind: 'approve', item: active });
                    }}
                    className="inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800"
                  >
                    <Check size={14} aria-hidden="true" /> Approve
                  </button>
                </div>
              </div>

              <h2 className="text-xs font-semibold tracking-widest text-gray-500 uppercase mt-6 mb-1">License</h2>
              <dl>
                <Row label="License number">{profile?.license_number}</Row>
                <Row label="Issuing country">{profile?.license_issuing_country?.name}</Row>
                <Row label="Issuing authority">{profile?.license_issuing_authority}</Row>
              </dl>

              <h2 className="text-xs font-semibold tracking-widest text-gray-500 uppercase mt-6 mb-1">Practice</h2>
              <dl>
                <Row label="Qualifications">{profile?.qualifications}</Row>
                <Row label="Experience">
                  {profile?.years_of_experience != null ? `${profile.years_of_experience} years` : null}
                </Row>
                <Row label="Specializations">{profile?.specializations.map((s) => s.name).join(', ')}</Row>
                <Row label="Languages">{profile?.languages.map((l) => l.name).join(', ')}</Row>
                <Row label="Location">{[profile?.city?.name, profile?.country?.name].filter(Boolean).join(', ')}</Row>
                <Row label="Time zone">{profile?.timezone}</Row>
                <Row label="Gender">{capitalize(profile?.gender)}</Row>
                <Row label="Bio">{profile?.bio}</Row>
                <Row label="Applied">{formatDate(active.created_at)}</Row>
              </dl>
            </div>
          )}
        </div>
      )}

      <ConfirmSheet
        open={pending?.kind === 'approve'}
        title={`Approve ${pending?.item.full_name ?? ''}?`}
        body="They can sign in straight away, appear in the app’s psychologist directory and receive patient requests. Only approve after checking their license."
        confirmLabel="Approve psychologist"
        busy={busy}
        error={actionError}
        onConfirm={handleConfirm}
        onClose={() => !busy && setPending(null)}
      />
      <ConfirmSheet
        open={pending?.kind === 'reject'}
        title={`Reject ${pending?.item.full_name ?? ''}?`}
        body="They won’t be able to sign in. When they try, they’re told their application wasn’t approved."
        confirmLabel="Reject application"
        tone="danger"
        reasons={REJECT_REASONS}
        busy={busy}
        error={actionError}
        onConfirm={handleConfirm}
        onClose={() => !busy && setPending(null)}
      />
    </AdminLayout>
  );
};

export default AdminVerificationsPage;
