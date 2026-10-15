// ============================================================
// MindCare — Admin Console: Verifications (live)
// Pending psychologist and NGO applications: review what they
// registered, then approve or reject. The backend re-checks the
// admin role and audit-logs every decision.
// ============================================================

import React, { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Check, ExternalLink, ShieldCheck, X } from 'lucide-react';
import AdminLayout from '../components/admin/AdminLayout';
import Avatar from '../components/common/Avatar';
import ConfirmSheet from '../components/therapist/ConfirmSheet';
import { ErrorPanel, LoadingPanel, formatDate, relativeTime } from '../components/therapist/ApiStates';
import { FileText } from 'lucide-react'; // documents list
import {
  APPROVAL_API_MISSING,
  DJANGO_ADMIN_PENDING_NGO_URL,
  DJANGO_ADMIN_PENDING_URL,
  NGO_REJECT_REASONS,
  REJECT_REASONS,
  approveAccount,
  getPendingNgos,
  getPendingPsychologists,
  openCredentialDocument,
  rejectAccount,
  type CredentialDocument,
  type PendingNgo,
  type PendingPsychologist,
  type RejectReason,
} from '../services/admin.service';
import type { ApiResponse } from '../types';

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

const SectionTitle: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <h2 className="text-xs font-semibold tracking-widest text-gray-500 uppercase mt-6 mb-1">{children}</h2>
);

// ——— Credential documents (psychologists) ———

const DOC_KIND_LABELS: Record<CredentialDocument['kind'], string> = {
  license: 'License document',
  degree: 'Degree certificate',
  other: 'Other document',
};

const fileSize = (bytes: number) =>
  bytes >= 1024 * 1024 ? `${(bytes / (1024 * 1024)).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;

/** Lists the uploaded files; "Open" fetches a short-lived signed link (the backend logs each opening). */
const DocumentsSection: React.FC<{ documents: CredentialDocument[] }> = ({ documents }) => {
  const [openingId, setOpeningId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  const open = async (doc: CredentialDocument) => {
    setError(null);
    setOpeningId(doc.id);
    // Open the tab now (inside the click) so pop-up blockers allow it, then point it at the file.
    const tab = window.open('', '_blank');
    const res = await openCredentialDocument(doc.id);
    setOpeningId(null);
    if (res.data?.url) {
      if (tab) {
        tab.opener = null;
        tab.location.href = res.data.url;
      } else {
        window.location.assign(res.data.url);
      }
    } else {
      tab?.close();
      setError(res.error ?? 'Couldn’t open this document.');
    }
  };

  if (!documents.length) {
    return <p className="text-sm text-gray-500 py-3">No documents uploaded with this application.</p>;
  }
  return (
    <>
      <ul className="divide-y divide-gray-100">
        {documents.map((doc) => (
          <li key={doc.id} className="flex items-center gap-3 py-3">
            <FileText size={16} className="text-gray-500 shrink-0" aria-hidden="true" />
            <span className="min-w-0 flex-1">
              <span className="block text-sm text-gray-900">{DOC_KIND_LABELS[doc.kind] ?? 'Document'}</span>
              <span className="block text-xs text-gray-500">
                {doc.file_type.toUpperCase()} · {fileSize(doc.size)} · uploaded {formatDate(doc.uploaded_at)}
              </span>
            </span>
            <button
              type="button"
              onClick={() => open(doc)}
              disabled={openingId === doc.id}
              className="inline-flex items-center gap-1.5 border border-gray-200 bg-white text-gray-700 text-xs font-semibold px-3 py-2 rounded-lg hover:border-gray-400 disabled:opacity-50"
            >
              <ExternalLink size={12} aria-hidden="true" /> {openingId === doc.id ? 'Opening…' : 'Open'}
            </button>
          </li>
        ))}
      </ul>
      {error && (
        <p role="alert" className="text-xs text-red-600 mt-1">
          {error}
        </p>
      )}
      <p className="text-xs text-gray-400 mt-2">Each opening is recorded in the access log.</p>
    </>
  );
};

// ——— What differs between the two queues ———

interface QueueItem {
  id: number;
  email: string;
  full_name: string;
  created_at: string;
}

interface QueueConfig<T extends QueueItem> {
  load: () => Promise<ApiResponse<T[]>>;
  /** Name shown in the list, the detail header and the dialogs. */
  nameOf: (item: T) => string;
  /** Second line under the name in the detail header. */
  subtitleOf: (item: T) => string;
  avatarColor: string;
  emptyHint: string;
  djangoUrl: string;
  rejectReasons: readonly { value: string; label: string }[];
  approveLabel: string;
  approveBody: string;
  approvedNotice: (name: string) => string;
  renderDetail: (item: T) => React.ReactNode;
}

const PSYCHOLOGISTS: QueueConfig<PendingPsychologist> = {
  load: getPendingPsychologists,
  nameOf: (p) => p.full_name,
  subtitleOf: (p) => p.email,
  avatarColor: 'bg-blue-950',
  emptyHint: 'New psychologist sign-ups appear here.',
  djangoUrl: DJANGO_ADMIN_PENDING_URL,
  rejectReasons: REJECT_REASONS,
  approveLabel: 'Approve psychologist',
  approveBody:
    'They can sign in straight away, appear in the app’s psychologist directory and receive patient requests. Only approve after checking their license.',
  approvedNotice: (name) => `${name} is approved and can now sign in to the therapist console.`,
  renderDetail: (active) => {
    const profile = active.psychologist_profile;
    return (
      <>
        <SectionTitle>License</SectionTitle>
        <dl>
          <Row label="License number">{profile?.license_number}</Row>
          <Row label="Issuing country">{profile?.license_issuing_country?.name}</Row>
          <Row label="Issuing authority">{profile?.license_issuing_authority}</Row>
        </dl>

        <SectionTitle>Documents</SectionTitle>
        <DocumentsSection key={active.id} documents={profile?.documents ?? []} />

        <SectionTitle>Practice</SectionTitle>
        <dl>
          <Row label="Qualifications">{profile?.qualifications}</Row>
          <Row label="Experience">{profile?.years_of_experience != null ? `${profile.years_of_experience} years` : null}</Row>
          <Row label="Specializations">{profile?.specializations.map((s) => s.name).join(', ')}</Row>
          <Row label="Languages">{profile?.languages.map((l) => l.name).join(', ')}</Row>
          <Row label="Location">{[profile?.city?.name, profile?.country?.name].filter(Boolean).join(', ')}</Row>
          <Row label="Time zone">{profile?.timezone}</Row>
          <Row label="Gender">{capitalize(profile?.gender)}</Row>
          <Row label="Bio">{profile?.bio}</Row>
          <Row label="Applied">{formatDate(active.created_at)}</Row>
        </dl>
      </>
    );
  },
};

const NGOS: QueueConfig<PendingNgo> = {
  load: getPendingNgos,
  nameOf: (n) => n.ngo_profile?.organization_name || n.full_name,
  subtitleOf: (n) => n.email,
  avatarColor: 'bg-emerald-700',
  emptyHint: 'New NGO sign-ups appear here.',
  djangoUrl: DJANGO_ADMIN_PENDING_NGO_URL,
  rejectReasons: NGO_REJECT_REASONS,
  approveLabel: 'Approve NGO',
  approveBody: 'Their NGO account becomes active. Only approve after checking their registration with the registering authority.',
  approvedNotice: (name) => `${name} is approved.`,
  renderDetail: (active) => {
    const ngo = active.ngo_profile;
    const website = ngo?.website?.trim();
    return (
      <>
        <SectionTitle>Registration</SectionTitle>
        <dl>
          <Row label="Registration number">{ngo?.registration_number}</Row>
          <Row label="Registration country">{ngo?.registration_country?.name}</Row>
          <Row label="Registering authority">{ngo?.registering_authority}</Row>
        </dl>

        <SectionTitle>Organisation</SectionTitle>
        <dl>
          <Row label="Representative">{ngo?.representative_name || active.full_name}</Row>
          <Row label="Location">{[ngo?.city?.name, ngo?.country?.name].filter(Boolean).join(', ')}</Row>
          <Row label="Time zone">{ngo?.timezone}</Row>
          <Row label="Official phone">{ngo?.official_phone}</Row>
          <Row label="Official email">{ngo?.official_email}</Row>
          <Row label="Website">
            {website && /^https:\/\//i.test(website) ? (
              <a href={website} target="_blank" rel="noopener noreferrer" className="underline hover:text-gray-600">
                {website}
              </a>
            ) : (
              website
            )}
          </Row>
          <Row label="Service areas">
            {ngo?.service_areas
              ?.map((a) => (a.city?.name ? `${a.city.name}, ${a.country?.name ?? ''}` : `${a.country?.name ?? ''} (whole country)`))
              .join(' · ')}
          </Row>
          <Row label="Description">{ngo?.description}</Row>
          <Row label="Applied">{formatDate(active.created_at)}</Row>
        </dl>
      </>
    );
  },
};

// ——— One queue (list + detail + approve / reject) ———

function VerificationQueue<T extends QueueItem>({ config }: { config: QueueConfig<T> }) {
  const [items, setItems] = useState<T[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [pending, setPending] = useState<{ kind: 'approve' | 'reject'; item: T } | null>(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    setItems(null);
    const res = await config.load();
    if (res.data) {
      const rows = res.data;
      setItems(rows);
      setActiveId((prev) => (rows.some((p) => p.id === prev) ? prev : rows[0]?.id ?? null));
    } else {
      setError(res.error ?? 'Couldn’t load applications.');
    }
  }, [config]);

  useEffect(() => {
    load();
  }, [load]);

  const active = items?.find((p) => p.id === activeId) ?? null;
  const pendingName = pending ? config.nameOf(pending.item) : '';

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
    const name = config.nameOf(item);
    setNotice(kind === 'approve' ? config.approvedNotice(name) : `${name}’s application was rejected.`);
    setPending(null);
  };

  return (
    <>
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
                href={config.djangoUrl}
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
          <p className="text-sm text-gray-500">{config.emptyHint}</p>
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
                    <Avatar initials={initialsOf(config.nameOf(p))} color={config.avatarColor} size="sm" />
                    <span className="min-w-0">
                      <span className="block font-semibold text-gray-900 truncate">{config.nameOf(p)}</span>
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
                  <Avatar initials={initialsOf(config.nameOf(active))} color={config.avatarColor} size="lg" />
                  <div>
                    <p className="text-2xl font-black text-gray-900">{config.nameOf(active)}</p>
                    <p className="text-sm text-gray-500">{config.subtitleOf(active)}</p>
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

              {config.renderDetail(active)}
            </div>
          )}
        </div>
      )}

      <ConfirmSheet
        open={pending?.kind === 'approve'}
        title={`Approve ${pendingName}?`}
        body={config.approveBody}
        confirmLabel={config.approveLabel}
        busy={busy}
        error={actionError}
        onConfirm={handleConfirm}
        onClose={() => !busy && setPending(null)}
      />
      <ConfirmSheet
        open={pending?.kind === 'reject'}
        title={`Reject ${pendingName}?`}
        body="They won’t be able to sign in. When they try, they’re told their application wasn’t approved."
        confirmLabel="Reject application"
        tone="danger"
        reasons={config.rejectReasons}
        busy={busy}
        error={actionError}
        onConfirm={handleConfirm}
        onClose={() => !busy && setPending(null)}
      />
    </>
  );
}

// ——— Page ———

type Tab = 'psychologist' | 'ngo';

const TABS: { id: Tab; label: string; title: string; intro: string }[] = [
  {
    id: 'psychologist',
    label: 'Psychologists',
    title: 'Psychologist',
    intro: 'New psychologists can’t sign in until an admin approves them. Check the license with the issuing authority before approving.',
  },
  {
    id: 'ngo',
    label: 'NGOs',
    title: 'NGO',
    intro: 'New NGOs can’t sign in until an admin approves them. Check the registration with the registering authority before approving.',
  },
];

const AdminVerificationsPage: React.FC = () => {
  // ?type=ngo opens the NGO tab (used by "Continue review" on NGO partners).
  const [params] = useSearchParams();
  const [tab, setTab] = useState<Tab>(params.get('type') === 'ngo' ? 'ngo' : 'psychologist');
  const current = TABS.find((t) => t.id === tab)!;

  return (
    <AdminLayout breadcrumb={['Operations', 'Verifications']}>
      <h1 className="text-5xl font-black text-gray-900 mb-2">
        {current.title} <span className="italic font-serif font-normal">verifications.</span>
      </h1>
      <p className="text-gray-500 mb-6 max-w-2xl">{current.intro}</p>

      <div className="flex flex-wrap gap-2 mb-6" role="tablist" aria-label="Application type">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={`text-sm font-semibold px-4 py-2 rounded-full transition-colors ${
              tab === t.id ? 'bg-gray-900 text-white' : 'bg-white border border-gray-200 text-gray-700 hover:border-gray-400'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* key: switching tabs starts that queue fresh */}
      {tab === 'psychologist' ? (
        <VerificationQueue key="psychologist" config={PSYCHOLOGISTS} />
      ) : (
        <VerificationQueue key="ngo" config={NGOS} />
      )}
    </AdminLayout>
  );
};

export default AdminVerificationsPage;
