// ============================================================
// MindCare — Admin Console: Admins (super-admins only)
// docs/handoff/admin-panel-2.md §2 (backend PR #67).
// List admins; add one (the one-time temporary password is shown
// once and never stored); promote; deactivate / reactivate ordinary
// admins; step down yourself. The backend enforces every rule (last
// super-admin, no self-deactivation, …) and its messages are shown.
// ============================================================

import React, { useCallback, useEffect, useState } from 'react';
import { Check, Copy, Plus, ShieldCheck, X } from 'lucide-react';
import AdminLayout from '../components/admin/AdminLayout';
import Avatar from '../components/common/Avatar';
import Sheet, { sheetInputClass } from '../components/common/Sheet';
import ConfirmSheet from '../components/therapist/ConfirmSheet';
import { ErrorPanel, LoadingPanel, formatDate, relativeTime } from '../components/therapist/ApiStates';
import { flattenFieldErrors } from '../services/api.service';
import {
  NOT_SUPER_ADMIN,
  createAdmin,
  deactivateAdmin,
  demoteSelf,
  listAdmins,
  promoteAdmin,
  reactivateAdmin,
  resetSuperAdminCheck,
  type AdminAccount,
} from '../services/admin.service';
import { useAuth } from '../utils/auth';
import { normalizeSingleLine, validateEmail, validatePersonName } from '../utils/validation';

const initialsOf = (name: string) =>
  name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('') || '?';

type Action = 'promote' | 'deactivate' | 'reactivate' | 'demote';
type Pending = { action: Action; admin: AdminAccount } | null;

const ACTION_COPY: Record<Action, { title: (n: string) => string; body: string; confirm: string; danger?: boolean }> = {
  promote: {
    title: (n) => `Make ${n} a super-admin?`,
    body: 'Super-admins can add admins, promote them and deactivate them. Only you can step down from your own super-admin role later.',
    confirm: 'Make super-admin',
  },
  deactivate: {
    title: (n) => `Deactivate ${n}?`,
    body: 'They’re signed out everywhere and can’t sign in until an admin reactivates them.',
    confirm: 'Deactivate admin',
    danger: true,
  },
  reactivate: {
    title: (n) => `Reactivate ${n}?`,
    body: 'They’ll be able to sign in to the admin console again.',
    confirm: 'Reactivate admin',
  },
  demote: {
    title: () => 'Step down as super-admin?',
    body: 'You stay an admin but can no longer manage other admins. The platform must keep at least one super-admin.',
    confirm: 'Step down',
    danger: true,
  },
};

const AdminAdminsPage: React.FC = () => {
  const { session } = useAuth();
  const myId = Number(session?.userId);
  const [admins, setAdmins] = useState<AdminAccount[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [pending, setPending] = useState<Pending>(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    setAdmins(null);
    const res = await listAdmins();
    if (res.data) setAdmins(res.data);
    else setError(res.status === 403 ? NOT_SUPER_ADMIN : res.error ?? 'Couldn’t load admins.');
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const replaceRow = (row: AdminAccount) => setAdmins((prev) => prev?.map((a) => (a.id === row.id ? row : a)) ?? prev);

  const handleConfirm = async () => {
    if (!pending) return;
    setBusy(true);
    setActionError(null);
    const { action, admin } = pending;
    const res =
      action === 'promote'
        ? await promoteAdmin(admin.id)
        : action === 'deactivate'
        ? await deactivateAdmin(admin.id)
        : action === 'reactivate'
        ? await reactivateAdmin(admin.id)
        : await demoteSelf();
    setBusy(false);
    if (!res.data) {
      // The backend's rule message, e.g. "You're the only super-admin. Promote another admin first."
      const fe = res.errorBody ? flattenFieldErrors(res.errorBody) : {};
      setActionError(Object.values(fe)[0] ?? res.error ?? 'That didn’t work. Please try again.');
      return;
    }
    replaceRow(res.data);
    setPending(null);
    const name = res.data.full_name;
    setNotice(
      action === 'promote'
        ? `${name} is now a super-admin.`
        : action === 'deactivate'
        ? `${name} has been deactivated.`
        : action === 'reactivate'
        ? `${name} has been reactivated.`
        : 'You’ve stepped down. You’re no longer a super-admin.'
    );
    if (action === 'demote') {
      // This page is for super-admins only; after stepping down, refresh so the sidebar updates.
      resetSuperAdminCheck();
      window.setTimeout(() => window.location.assign('/admin/overview'), 1500);
    }
  };

  const open = (action: Action, admin: AdminAccount) => {
    setActionError(null);
    setPending({ action, admin });
  };

  const copy = pending ? ACTION_COPY[pending.action] : null;

  return (
    <AdminLayout
      breadcrumb={['Platform', 'Admins']}
      headerAction={
        admins ? (
          <button
            type="button"
            onClick={() => setAdding(true)}
            className="inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 shrink-0"
          >
            <Plus size={15} aria-hidden="true" /> Add admin
          </button>
        ) : undefined
      }
    >
      <h1 className="text-5xl font-black text-gray-900 mb-2">
        Admin <span className="italic font-serif font-normal">accounts.</span>
      </h1>
      <p className="text-gray-500 mb-6 max-w-2xl">
        Who can sign in to this console. Only super-admins see this page.
      </p>

      {notice && (
        <div role="status" className="flex items-start justify-between gap-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm rounded-xl px-4 py-3 mb-6">
          <span>{notice}</span>
          <button type="button" onClick={() => setNotice(null)} aria-label="Dismiss" className="shrink-0">
            <X size={14} />
          </button>
        </div>
      )}

      {error ? (
        <ErrorPanel message={error} title={error === NOT_SUPER_ADMIN ? 'Super-admins only' : undefined} onRetry={error === NOT_SUPER_ADMIN ? undefined : load} />
      ) : !admins ? (
        <LoadingPanel label="Loading admins…" />
      ) : (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] font-semibold tracking-widest text-gray-500 uppercase border-b border-gray-100">
                <th className="px-6 py-4">Admin</th>
                <th className="px-6 py-4">Role</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Last sign-in</th>
                <th className="px-6 py-4">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {admins.map((a) => {
                const me = a.id === myId;
                return (
                  <tr key={a.id} className="border-b border-gray-50 last:border-0 align-middle">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <Avatar initials={initialsOf(a.full_name)} color={a.is_super_admin ? 'bg-orange-600' : 'bg-gray-700'} size="sm" />
                        <div className="min-w-0">
                          <p className="font-semibold text-gray-900 truncate">
                            {a.full_name}
                            {me && <span className="ml-2 text-xs font-medium text-gray-400">(you)</span>}
                          </p>
                          <p className="text-xs text-gray-500 truncate">{a.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {a.is_super_admin ? (
                        <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full bg-orange-100 text-orange-700">
                          <ShieldCheck size={12} aria-hidden="true" /> Super-admin
                        </span>
                      ) : (
                        <span className="text-gray-700">Admin</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1.5">
                        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${a.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-200 text-gray-600'}`}>
                          {a.is_active ? 'Active' : 'Deactivated'}
                        </span>
                        {a.must_change_password && (
                          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-100 text-amber-700">Must change password</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-500" title={a.last_login ? formatDate(a.last_login) : undefined}>
                      {a.last_login ? relativeTime(a.last_login) : 'Never'}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap justify-end gap-2">
                        {me && a.is_super_admin && (
                          <RowButton danger onClick={() => open('demote', a)}>
                            Step down
                          </RowButton>
                        )}
                        {!a.is_super_admin && a.is_active && <RowButton onClick={() => open('promote', a)}>Promote</RowButton>}
                        {a.is_active ? (
                          <RowButton
                            danger
                            disabled={me || a.is_super_admin}
                            title={me ? 'You can’t deactivate your own account.' : a.is_super_admin ? 'A super-admin must step down before they can be deactivated.' : undefined}
                            onClick={() => open('deactivate', a)}
                          >
                            Deactivate
                          </RowButton>
                        ) : (
                          <RowButton onClick={() => open('reactivate', a)}>Reactivate</RowButton>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {copy && pending && (
        <ConfirmSheet
          open
          title={copy.title(pending.admin.full_name)}
          body={copy.body}
          confirmLabel={copy.confirm}
          tone={copy.danger ? 'danger' : 'default'}
          busy={busy}
          error={actionError}
          onConfirm={handleConfirm}
          onClose={() => !busy && setPending(null)}
        />
      )}

      <AddAdminSheet
        open={adding}
        onClose={() => setAdding(false)}
        onCreated={(row) => setAdmins((prev) => (prev ? [...prev, row] : [row]))}
      />
    </AdminLayout>
  );
};

const RowButton: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement> & { danger?: boolean }> = ({ danger, className, ...rest }) => (
  <button
    type="button"
    {...rest}
    className={`text-xs font-semibold px-3 py-2 rounded-lg border transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${
      danger ? 'border-red-200 text-red-700 bg-red-50 hover:bg-red-100' : 'border-gray-200 text-gray-700 bg-white hover:border-gray-400'
    } ${className ?? ''}`}
  />
);

// ——— Add admin: form, then the one-time temporary password ———

const AddAdminSheet: React.FC<{ open: boolean; onClose: () => void; onCreated: (row: AdminAccount) => void }> = ({
  open,
  onClose,
  onCreated,
}) => {
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [errors, setErrors] = useState<Record<string, string | undefined>>({});
  const [busy, setBusy] = useState(false);
  const [created, setCreated] = useState<{ name: string; email: string; password: string } | null>(null);
  const [copied, setCopied] = useState(false);

  // Forget everything (especially the temporary password) when the sheet closes.
  const close = () => {
    if (busy) return;
    setEmail('');
    setFullName('');
    setErrors({});
    setCreated(null);
    setCopied(false);
    onClose();
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const found = {
      email: validateEmail(email) ?? undefined,
      full_name: validatePersonName(fullName, 'Full name') ?? undefined,
    };
    setErrors(found);
    if (found.email || found.full_name) return;
    setBusy(true);
    const res = await createAdmin(email.trim().toLowerCase(), normalizeSingleLine(fullName));
    setBusy(false);
    if (res.data) {
      const { temporary_password, ...row } = res.data;
      onCreated(row);
      setCreated({ name: row.full_name, email: row.email, password: temporary_password });
      return;
    }
    if (res.status === 400 && res.errorBody) {
      const fe = flattenFieldErrors(res.errorBody);
      setErrors({ email: fe.email, full_name: fe.full_name, _: fe._ ?? (fe.email || fe.full_name ? undefined : res.error ?? undefined) });
      return;
    }
    setErrors({ _: res.status === 403 ? NOT_SUPER_ADMIN : res.error ?? 'Couldn’t add the admin. Please try again.' });
  };

  const copyPassword = async () => {
    if (!created) return;
    try {
      await navigator.clipboard.writeText(created.password);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };

  return (
    <Sheet open={open} onClose={close} labelledBy="add-admin-title">
      <div className="p-6 sm:p-8">
        {created ? (
          <>
            <h2 id="add-admin-title" className="text-2xl font-black text-gray-900 mb-2 pr-8">
              {created.name} is an admin.
            </h2>
            <p className="text-sm text-gray-600 mb-5">
              Give this password to the new admin privately. They must change it when they first sign in. You won’t see it
              again.
            </p>
            <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-1.5">Temporary password for {created.email}</p>
            <div className="flex items-center gap-2 mb-6">
              <code className="flex-1 min-w-0 break-all rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm font-mono text-gray-900">
                {created.password}
              </code>
              <button
                type="button"
                onClick={copyPassword}
                className="inline-flex items-center gap-1.5 border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-3 py-3 rounded-xl hover:border-gray-400 shrink-0"
              >
                {copied ? <Check size={14} aria-hidden="true" /> : <Copy size={14} aria-hidden="true" />}
                {copied ? 'Copied' : 'Copy'}
              </button>
            </div>
            <button type="button" onClick={close} className="w-full bg-gray-900 text-white text-sm font-semibold py-3 rounded-xl hover:bg-gray-800">
              Done
            </button>
          </>
        ) : (
          <form onSubmit={submit} noValidate>
            <h2 id="add-admin-title" className="text-2xl font-black text-gray-900 mb-2 pr-8">
              Add an admin
            </h2>
            <p className="text-sm text-gray-600 mb-6">They get a temporary password, which you’ll see once on the next screen.</p>

            <label htmlFor="new-admin-name" className="block text-xs font-bold text-gray-700 uppercase tracking-wide mb-2">
              Full name *
            </label>
            <input
              id="new-admin-name"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              maxLength={100}
              autoComplete="off"
              aria-invalid={!!errors.full_name}
              className={sheetInputClass}
            />
            {errors.full_name && (
              <p role="alert" className="text-xs text-red-600 mt-1.5">
                {errors.full_name}
              </p>
            )}

            <label htmlFor="new-admin-email" className="block text-xs font-bold text-gray-700 uppercase tracking-wide mb-2 mt-5">
              Email *
            </label>
            <input
              id="new-admin-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              maxLength={254}
              autoComplete="off"
              aria-invalid={!!errors.email}
              className={sheetInputClass}
            />
            {errors.email && (
              <p role="alert" className="text-xs text-red-600 mt-1.5">
                {errors.email}
              </p>
            )}

            {errors._ && (
              <p role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl px-4 py-3 mt-5">
                {errors._}
              </p>
            )}

            <div className="flex flex-col-reverse sm:flex-row gap-3 sm:justify-end mt-6">
              <button
                type="button"
                onClick={close}
                disabled={busy}
                className="border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-5 py-3 rounded-xl hover:border-gray-400 disabled:opacity-50"
              >
                Cancel
              </button>
              <button type="submit" disabled={busy} className="bg-gray-900 text-white text-sm font-semibold px-5 py-3 rounded-xl hover:bg-gray-800 disabled:opacity-50">
                {busy ? 'Adding…' : 'Add admin'}
              </button>
            </div>
          </form>
        )}
      </div>
    </Sheet>
  );
};

export default AdminAdminsPage;
