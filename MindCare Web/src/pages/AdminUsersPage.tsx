// ============================================================
// MindCare — Admin Console: Users (live)
// Every non-admin account from GET /accounts/admin/users/, with
// search, role/status filters, CSV export, account details and
// deactivate / reactivate. Private patients appear by pseudonym only;
// opening one reveals them, and the backend records that reveal.
// ============================================================

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Download, SlidersHorizontal, MoreHorizontal, ChevronLeft, ChevronRight, X } from 'lucide-react';
import AdminLayout from '../components/admin/AdminLayout';
import Avatar from '../components/common/Avatar';
import Sheet from '../components/common/Sheet';
import ConfirmSheet from '../components/therapist/ConfirmSheet';
import { ErrorPanel, LoadingPanel, formatDate, relativeTime } from '../components/therapist/ApiStates';
import {
  ADMIN_API_MISSING,
  DEACTIVATE_REASONS,
  deactivateUser,
  getAdminOverview,
  getAdminUser,
  listAdminUsers,
  listAllAdminUsers,
  reactivateUser,
  type AccountRole,
  type AccountStatus,
  type AdminOverview,
  type AdminUserDetail,
  type AdminUserRow,
  type DeactivateReason,
  type Page,
} from '../services/admin.service';

const PAGE_SIZE = 20;

const ROLE_LABELS: Record<AccountRole, string> = { patient: 'Patient', psychologist: 'Psychologist', ngo: 'NGO' };
const ROLE_FILTERS: { value: AccountRole | ''; label: string }[] = [
  { value: '', label: 'All roles' },
  { value: 'patient', label: 'Patients' },
  { value: 'psychologist', label: 'Psychologists' },
  { value: 'ngo', label: 'NGOs' },
];
const STATUS_TABS: { value: AccountStatus | ''; label: string }[] = [
  { value: '', label: 'All' },
  { value: 'active', label: 'Active' },
  { value: 'pending', label: 'Pending' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'deactivated', label: 'Deactivated' },
];

const STATUS_STYLES: Record<AccountStatus, string> = {
  active: 'bg-emerald-100 text-emerald-700',
  pending: 'bg-amber-100 text-amber-700',
  rejected: 'bg-red-100 text-red-700',
  deactivated: 'bg-gray-200 text-gray-600',
};
const AVATAR_COLORS: Record<AccountRole, string> = { patient: 'bg-violet-600', psychologist: 'bg-blue-950', ngo: 'bg-emerald-700' };

/** Same order as the backend's status filters: deactivated wins over approval state. */
function statusOf(u: { is_active: boolean; approval_status: string }): AccountStatus {
  if (!u.is_active) return 'deactivated';
  if (u.approval_status === 'pending') return 'pending';
  if (u.approval_status === 'rejected') return 'rejected';
  return 'active';
}

const initialsOf = (name: string) =>
  name
    .replace(/^dr\.?\s+/i, '')
    .split(/[\s-]+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('') || '?';

/** Overview counts for the chips, for one role or all roles. */
function countsFor(overview: AdminOverview | null, role: AccountRole | '') {
  if (!overview) return null;
  const roles: AccountRole[] = role ? [role] : ['patient', 'psychologist', 'ngo'];
  const sum = (k: 'total' | 'active' | 'pending' | 'rejected' | 'deactivated') =>
    roles.reduce((n, r) => n + (overview.users[r]?.[k] ?? 0), 0);
  return { '': sum('total'), active: sum('active'), pending: sum('pending'), rejected: sum('rejected'), deactivated: sum('deactivated') };
}

// ——— CSV export (cells starting with = + - @ are prefixed so spreadsheets don't run them) ———
function csvCell(v: string) {
  const safe = /^[=+\-@\t\r]/.test(v) ? `'${v}` : v;
  return `"${safe.replace(/"/g, '""')}"`;
}
function downloadCsv(rows: AdminUserRow[]) {
  const header = ['Name', 'Shown as', 'Email', 'Role', 'Status', 'Joined', 'Last sign-in'];
  const lines = rows.map((u) =>
    [
      u.display_name,
      u.is_real_name ? 'Real name' : 'Pseudonym (private patient)',
      u.email ?? '',
      ROLE_LABELS[u.role],
      statusOf(u),
      u.created_at ? new Date(u.created_at).toISOString().slice(0, 10) : '',
      u.last_login ? new Date(u.last_login).toISOString().slice(0, 10) : '',
    ]
      .map(csvCell)
      .join(',')
  );
  const blob = new Blob(['﻿' + [header.map(csvCell).join(','), ...lines].join('\r\n')], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `mindcare-users-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

type Pending = { kind: 'deactivate' | 'reactivate'; user: AdminUserRow } | null;

const AdminUsersPage: React.FC = () => {
  const [params, setParams] = useSearchParams();
  const role = (params.get('role') ?? '') as AccountRole | '';
  const status = (params.get('status') ?? '') as AccountStatus | '';
  const search = params.get('search') ?? '';
  const page = Math.max(1, Number(params.get('page')) || 1);

  const [data, setData] = useState<Page<AdminUserRow> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [showFilters, setShowFilters] = useState(!!role);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const [menuFor, setMenuFor] = useState<number | null>(null);
  const [pending, setPending] = useState<Pending>(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [revealFor, setRevealFor] = useState<AdminUserRow | null>(null);
  const [detail, setDetail] = useState<{ row: AdminUserRow; data: AdminUserDetail | null; error: string | null } | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  /** Change one or more URL filters; any filter change goes back to page 1. */
  const update = (next: Partial<Record<'role' | 'status' | 'search' | 'page', string>>) => {
    const p = new URLSearchParams(params);
    for (const [k, v] of Object.entries(next)) {
      if (v) p.set(k, v);
      else p.delete(k);
    }
    if (!('page' in next)) p.delete('page');
    setParams(p);
  };

  const load = useCallback(async () => {
    setError(null);
    setData(null);
    const res = await listAdminUsers({ role: role || undefined, status: status || undefined, search, page, pageSize: PAGE_SIZE });
    if (res.data) setData(res.data);
    else setError(res.error ?? 'Couldn’t load users.');
  }, [role, status, search, page]);

  const loadOverview = useCallback(async () => {
    const res = await getAdminOverview();
    if (res.data) setOverview(res.data);
  }, []);

  useEffect(() => {
    load();
  }, [load]);
  useEffect(() => {
    loadOverview();
  }, [loadOverview]);

  // Close the row menu on outside click / Escape.
  useEffect(() => {
    if (menuFor === null) return;
    const onDown = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuFor(null);
    };
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setMenuFor(null);
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [menuFor]);

  const counts = countsFor(overview, role);
  const allCounts = countsFor(overview, '');

  const handleExport = async () => {
    setExporting(true);
    setExportError(null);
    const res = await listAllAdminUsers({ role: role || undefined, status: status || undefined, search });
    setExporting(false);
    if (res.data) downloadCsv(res.data);
    else setExportError(res.error ?? 'Export failed. Please try again.');
  };

  const openDetail = async (row: AdminUserRow) => {
    setRevealFor(null);
    setDetail({ row, data: null, error: null });
    const res = await getAdminUser(row.id);
    setDetail({ row, data: res.data, error: res.data ? null : res.error ?? 'Couldn’t load this account.' });
  };

  const handleView = (row: AdminUserRow) => {
    setMenuFor(null);
    // A private patient is listed by pseudonym; opening them reveals who they are.
    if (row.role === 'patient' && !row.is_real_name) setRevealFor(row);
    else openDetail(row);
  };

  const handleConfirm = async (reason: string | null) => {
    if (!pending) return;
    setBusy(true);
    setActionError(null);
    const { kind, user } = pending;
    const res = kind === 'deactivate' ? await deactivateUser(user.id, reason as DeactivateReason | null) : await reactivateUser(user.id);
    setBusy(false);
    if (!res.data) {
      setActionError(res.error ?? 'That didn’t work. Please try again.');
      return;
    }
    const result = res.data;
    setData((prev) =>
      prev ? { ...prev, results: prev.results.map((u) => (u.id === user.id ? { ...u, is_active: result.is_active, approval_status: result.approval_status as AdminUserRow['approval_status'] } : u)) } : prev
    );
    setNotice(kind === 'deactivate' ? `${user.display_name} has been deactivated.` : `${user.display_name} has been reactivated.`);
    setPending(null);
    loadOverview();
  };

  const total = data?.count ?? 0;
  const from = total ? (page - 1) * PAGE_SIZE + 1 : 0;
  const to = Math.min(page * PAGE_SIZE, total);
  const notReady = error === ADMIN_API_MISSING;

  return (
    <AdminLayout
      breadcrumb={['Operations', 'Users']}
      headerAction={
        <div className="flex gap-2 shrink-0">
          <button
            type="button"
            onClick={handleExport}
            disabled={exporting || !data || total === 0}
            title={total === 0 ? 'Nothing to export' : 'Download the users matching these filters as a CSV file'}
            className="inline-flex items-center gap-2 border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download size={15} aria-hidden="true" /> {exporting ? 'Exporting…' : 'Export'}
          </button>
          <button
            type="button"
            onClick={() => setShowFilters((s) => !s)}
            aria-expanded={showFilters}
            aria-controls="user-filters"
            className={`inline-flex items-center gap-2 border text-sm font-semibold px-4 py-2.5 rounded-xl transition-colors ${
              showFilters || role ? 'bg-gray-900 border-gray-900 text-white' : 'bg-white border-gray-200 text-gray-700 hover:border-gray-400'
            }`}
          >
            <SlidersHorizontal size={15} aria-hidden="true" /> Filters{role ? ' · 1' : ''}
          </button>
        </div>
      }
    >
      <h1 className="text-5xl font-black text-gray-900 mb-2">
        Users <span className="italic font-serif font-normal">on the platform.</span>
      </h1>
      <p className="text-gray-500 mb-6">
        {allCounts
          ? `${allCounts.active.toLocaleString()} active · ${allCounts.pending.toLocaleString()} pending approval · ${allCounts.deactivated.toLocaleString()} deactivated`
          : 'Patients, psychologists and NGOs. Private patients are shown by pseudonym only.'}
      </p>

      {exportError && (
        <p role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl px-4 py-3 mb-4">
          {exportError}
        </p>
      )}
      {notice && (
        <div role="status" className="flex items-start justify-between gap-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm rounded-xl px-4 py-3 mb-6">
          <span>{notice}</span>
          <button type="button" onClick={() => setNotice(null)} aria-label="Dismiss" className="shrink-0">
            <X size={14} />
          </button>
        </div>
      )}

      {showFilters && (
        <div id="user-filters" className="bg-white border border-gray-200 rounded-2xl p-4 mb-6 flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold tracking-widest text-gray-500 uppercase mr-2">Role</span>
          {ROLE_FILTERS.map((r) => (
            <button
              key={r.value || 'all'}
              type="button"
              onClick={() => update({ role: r.value })}
              aria-pressed={role === r.value}
              className={`text-sm font-semibold px-4 py-2 rounded-full transition-colors ${
                role === r.value ? 'bg-gray-900 text-white' : 'bg-white border border-gray-200 text-gray-700 hover:border-gray-400'
              }`}
            >
              {r.label}
            </button>
          ))}
          {(role || status || search) && (
            <button type="button" onClick={() => setParams(new URLSearchParams())} className="ml-auto text-sm font-semibold text-gray-500 hover:text-gray-900">
              Clear all filters
            </button>
          )}
        </div>
      )}

      {search && (
        <div className="flex items-center gap-2 mb-4 text-sm text-gray-600">
          Searching for <span className="font-semibold text-gray-900">“{search}”</span>
          <button type="button" onClick={() => update({ search: '' })} className="inline-flex items-center gap-1 text-gray-500 hover:text-gray-900">
            <X size={13} aria-hidden="true" /> clear
          </button>
          <span className="text-gray-400">· patients are found by pseudonym only</span>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2 mb-6" role="tablist" aria-label="Account status">
        {STATUS_TABS.map((t) => (
          <button
            key={t.value || 'all'}
            type="button"
            role="tab"
            aria-selected={status === t.value}
            onClick={() => update({ status: t.value })}
            className={`text-sm font-semibold px-4 py-2 rounded-full transition-colors ${
              status === t.value ? 'bg-gray-900 text-white' : 'bg-white border border-gray-200 text-gray-700 hover:border-gray-400'
            }`}
          >
            {t.label}
            {counts ? ` · ${counts[t.value].toLocaleString()}` : ''}
          </button>
        ))}
      </div>

      {error ? (
        <ErrorPanel message={error} title={notReady ? 'Not available yet' : undefined} onRetry={notReady ? undefined : load} />
      ) : !data ? (
        <LoadingPanel label="Loading users…" />
      ) : data.results.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center">
          <p className="text-gray-900 font-semibold">No users match.</p>
          <p className="text-sm text-gray-500">Try another status, role or search.</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[11px] font-semibold tracking-widest text-gray-500 uppercase border-b border-gray-100">
                  <th className="px-6 py-4">User</th>
                  <th className="px-6 py-4">Role</th>
                  <th className="px-6 py-4">Joined</th>
                  <th className="px-6 py-4">Last sign-in</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.results.map((u) => {
                  const st = statusOf(u);
                  return (
                    <tr key={u.id} className="border-b border-gray-50 last:border-0">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <Avatar initials={initialsOf(u.display_name)} color={AVATAR_COLORS[u.role]} size="sm" />
                          <div className="min-w-0">
                            <p className="font-semibold text-gray-900 truncate">{u.display_name}</p>
                            <p className="text-xs text-gray-500 truncate">
                              {u.email ?? 'Private patient · pseudonym only'}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-gray-700">{ROLE_LABELS[u.role]}</td>
                      <td className="px-6 py-4 text-gray-700">{formatDate(u.created_at)}</td>
                      <td className="px-6 py-4 text-gray-500">{u.last_login ? relativeTime(u.last_login) : 'Never'}</td>
                      <td className="px-6 py-4">
                        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full capitalize ${STATUS_STYLES[st]}`}>{st}</span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="relative inline-block" ref={menuFor === u.id ? menuRef : undefined}>
                          <button
                            type="button"
                            onClick={() => setMenuFor(menuFor === u.id ? null : u.id)}
                            aria-label={`Actions for ${u.display_name}`}
                            aria-expanded={menuFor === u.id}
                            aria-haspopup="menu"
                            className="w-9 h-9 rounded-lg border border-gray-200 flex items-center justify-center text-gray-500 hover:border-gray-400"
                          >
                            <MoreHorizontal size={16} />
                          </button>
                          {menuFor === u.id && (
                            <div role="menu" className="absolute right-0 mt-1 w-44 bg-white border border-gray-200 rounded-xl shadow-lg z-20 py-1 text-left">
                              <button type="button" role="menuitem" onClick={() => handleView(u)} className="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50">
                                View details
                              </button>
                              {u.is_active ? (
                                <button
                                  type="button"
                                  role="menuitem"
                                  onClick={() => {
                                    setMenuFor(null);
                                    setActionError(null);
                                    setPending({ kind: 'deactivate', user: u });
                                  }}
                                  className="w-full text-left px-4 py-2.5 text-sm text-red-700 hover:bg-red-50"
                                >
                                  Deactivate
                                </button>
                              ) : (
                                <button
                                  type="button"
                                  role="menuitem"
                                  onClick={() => {
                                    setMenuFor(null);
                                    setActionError(null);
                                    setPending({ kind: 'reactivate', user: u });
                                  }}
                                  className="w-full text-left px-4 py-2.5 text-sm text-emerald-700 hover:bg-emerald-50"
                                >
                                  Reactivate
                                </button>
                              )}
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between gap-3 px-6 py-4 border-t border-gray-100 text-sm text-gray-500">
            <span>
              Showing {from.toLocaleString()}–{to.toLocaleString()} of {total.toLocaleString()}
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => update({ page: String(page - 1) })}
                disabled={!data.previous}
                className="inline-flex items-center gap-1 border border-gray-200 bg-white text-gray-700 font-semibold px-3 py-2 rounded-xl hover:border-gray-400 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <ChevronLeft size={14} aria-hidden="true" /> Previous
              </button>
              <button
                type="button"
                onClick={() => update({ page: String(page + 1) })}
                disabled={!data.next}
                className="inline-flex items-center gap-1 border border-gray-200 bg-white text-gray-700 font-semibold px-3 py-2 rounded-xl hover:border-gray-400 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Next <ChevronRight size={14} aria-hidden="true" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Private patient: confirm before revealing their identity (the backend logs it). */}
      <ConfirmSheet
        open={!!revealFor}
        title="Open a private patient?"
        body={
          <>
            <span className="font-semibold">{revealFor?.display_name}</span> keeps their profile private. Opening their account
            shows their real name and email, and this is recorded in the access log.
          </>
        }
        confirmLabel="Open account"
        onConfirm={() => revealFor && openDetail(revealFor)}
        onClose={() => setRevealFor(null)}
      />

      <ConfirmSheet
        open={pending?.kind === 'deactivate'}
        title={`Deactivate ${pending?.user.display_name ?? ''}?`}
        body="They won’t be able to sign in, and any care relationships they have end now. You can reactivate them later, but ended relationships stay ended."
        confirmLabel="Deactivate account"
        tone="danger"
        reasons={DEACTIVATE_REASONS}
        busy={busy}
        error={actionError}
        onConfirm={handleConfirm}
        onClose={() => !busy && setPending(null)}
      />
      <ConfirmSheet
        open={pending?.kind === 'reactivate'}
        title={`Reactivate ${pending?.user.display_name ?? ''}?`}
        body="They’ll be able to sign in again. Care relationships that ended stay ended."
        confirmLabel="Reactivate account"
        busy={busy}
        error={actionError}
        onConfirm={handleConfirm}
        onClose={() => !busy && setPending(null)}
      />

      <UserDetailSheet detail={detail} onClose={() => setDetail(null)} />
    </AdminLayout>
  );
};

// ——— Account details ———

const Row: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => (
  <div className="grid grid-cols-[140px_minmax(0,1fr)] gap-3 py-2.5 border-b border-gray-100 last:border-0">
    <dt className="text-xs font-semibold tracking-widest text-gray-500 uppercase pt-0.5">{label}</dt>
    <dd className="text-sm text-gray-900 break-words">{children || '—'}</dd>
  </div>
);

/** Plain text for any NGO profile field the backend sends (strings, numbers, {name}, lists). */
function show(v: unknown): string {
  if (v == null || v === '') return '';
  if (Array.isArray(v)) return v.map(show).filter(Boolean).join(', ');
  if (typeof v === 'object') {
    const o = v as Record<string, unknown>;
    return show(o.name ?? o.city ?? o.label ?? o.code ?? '');
  }
  return String(v);
}

const UserDetailSheet: React.FC<{
  detail: { row: AdminUserRow; data: AdminUserDetail | null; error: string | null } | null;
  onClose: () => void;
}> = ({ detail, onClose }) => {
  const d = detail?.data;
  const p = d?.psychologist_profile;
  return (
    <Sheet open={!!detail} onClose={onClose} labelledBy="user-detail-title">
      <div className="p-6 sm:p-8">
        <h2 id="user-detail-title" className="text-2xl font-black text-gray-900 mb-1 pr-8">
          {d?.identity.display_name ?? detail?.row.display_name}
        </h2>
        {detail && <p className="text-sm text-gray-500 mb-5">{ROLE_LABELS[detail.row.role]}</p>}

        {detail?.error ? (
          <p role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
            {detail.error}
          </p>
        ) : !d ? (
          <p className="text-sm text-gray-500" aria-live="polite">
            Loading…
          </p>
        ) : (
          <dl>
            <Row label="Email">{d.email}</Row>
            <Row label="Status">
              <span className="capitalize">{statusOf(d)}</span>
            </Row>
            <Row label="Joined">{formatDate(d.created_at)}</Row>
            <Row label="Last sign-in">{d.last_login ? formatDate(d.last_login) : 'Never'}</Row>
            {d.patient && (
              <>
                <Row label="Pseudonym">{d.patient.pseudonym}</Row>
                <Row label="Profile">{d.patient.is_profile_public ? 'Public' : 'Private'}</Row>
                <Row label="Country">{d.patient.country}</Row>
              </>
            )}
            {p && (
              <>
                <Row label="License">{[p.license_number, p.license_issuing_country?.name].filter(Boolean).join(' · ')}</Row>
                <Row label="Authority">{p.license_issuing_authority}</Row>
                <Row label="Qualifications">{p.qualifications}</Row>
                <Row label="Experience">{p.years_of_experience != null ? `${p.years_of_experience} years` : ''}</Row>
                <Row label="Specializations">{p.specializations.map((s) => s.name).join(', ')}</Row>
                <Row label="Languages">{p.languages.map((l) => l.name).join(', ')}</Row>
                <Row label="Location">{[p.city?.name, p.country?.name].filter(Boolean).join(', ')}</Row>
              </>
            )}
            {d.ngo_profile &&
              Object.entries(d.ngo_profile)
                .filter(([k, v]) => !['created_at', 'updated_at'].includes(k) && show(v))
                .map(([k, v]) => (
                  <Row key={k} label={k.replace(/_/g, ' ')}>
                    {show(v)}
                  </Row>
                ))}
          </dl>
        )}
      </div>
    </Sheet>
  );
};

export default AdminUsersPage;
