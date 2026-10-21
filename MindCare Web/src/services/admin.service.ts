// ============================================================
// MindCare — Admin console API: psychologist approvals
// Contract: MindCare Web/docs/admin-approvals-api-contract.md
// (backend Phase 2.5). Until those endpoints are deployed the list
// call answers 404, which the page shows as APPROVAL_API_MISSING.
// ============================================================

import { API_BASE_URL } from '../constants';
import { apiFetch } from './api.service';
import type { ApiResponse } from '../types';
import type { CodeName } from './psychologist.service';

export const APPROVAL_API_MISSING =
  'The approval endpoints aren’t on the backend yet. Until they are deployed, approve accounts in Django admin.';
export const NOT_ADMIN_MESSAGE = 'This account doesn’t have permission to review applications.';

/** Django admin, pre-filtered to pending psychologists — the interim approval path. */
export const DJANGO_ADMIN_PENDING_URL = `${API_BASE_URL.replace(/\/api\/v1\/?$/, '')}/admin/accounts/user/?approval_status__exact=pending&role__exact=psychologist`;

export interface PendingPsychologist {
  id: number;
  email: string;
  full_name: string;
  role: 'psychologist';
  approval_status: 'pending';
  created_at: string;
  psychologist_profile: {
    license_number: string;
    license_issuing_country: CodeName | null;
    license_issuing_authority: string;
    qualifications: string;
    specializations: { slug: string; name: string }[];
    years_of_experience: number | null;
    languages: CodeName[];
    country: CodeName | null;
    city: { id?: number; name: string } | null;
    timezone: string;
    gender: string | null;
    bio: string;
    /** Credential files uploaded at registration (metadata only; open with openCredentialDocument). */
    documents?: CredentialDocument[];
  } | null;
}

export interface CredentialDocument {
  id: number;
  kind: 'license' | 'degree' | 'other';
  file_type: string;
  size: number;
  uploaded_at: string;
}

/**
 * GET /accounts/admin/documents/{id}/ — a signed link to one credential file,
 * valid for a few minutes. The backend records every opening in the audit trail.
 */
export async function openCredentialDocument(documentId: number) {
  const res = await apiFetch<{ id: number; kind: string; file_type: string; url: string; expires_in: number }>(
    `/accounts/admin/documents/${documentId}/`
  );
  if (res.status === 404) return { ...res, data: null, error: 'This document wasn’t found.' };
  if (res.status === 403) return { ...res, error: NOT_ADMIN_MESSAGE };
  return res;
}

export const REJECT_REASONS = [
  { value: 'license_unverified', label: 'License couldn’t be verified' },
  { value: 'incomplete_details', label: 'Details incomplete or incorrect' },
  { value: 'not_eligible', label: 'Not eligible (not a licensed psychologist)' },
  { value: 'other', label: 'Other' },
] as const;

export type RejectReason = (typeof REJECT_REASONS)[number]['value'];

function explain<T>(res: ApiResponse<T>): ApiResponse<T> {
  if (res.status === 403) return { ...res, error: NOT_ADMIN_MESSAGE };
  return res;
}

/** GET /accounts/admin/pending/?role=psychologist — oldest first. Accepts a plain or paginated list. */
export async function getPendingPsychologists(): Promise<ApiResponse<PendingPsychologist[]>> {
  const res = explain(
    await apiFetch<PendingPsychologist[] | { results: PendingPsychologist[] }>('/accounts/admin/pending/?role=psychologist')
  );
  if (res.status === 404) return { ...res, data: null, error: APPROVAL_API_MISSING };
  if (!res.data) return { ...res, data: null };
  return { ...res, data: Array.isArray(res.data) ? res.data : res.data.results ?? [] };
}

// ——— NGO applications (same approve / reject endpoints as psychologists) ———

/** Django admin, pre-filtered to pending NGOs. */
export const DJANGO_ADMIN_PENDING_NGO_URL = DJANGO_ADMIN_PENDING_URL.replace('role__exact=psychologist', 'role__exact=ngo');

export interface PendingNgo {
  id: number;
  email: string;
  full_name: string;
  role: 'ngo';
  approval_status: 'pending';
  created_at: string;
  /** NGOProfileOwnerSerializer */
  ngo_profile: {
    representative_name: string;
    organization_name: string;
    registration_number: string;
    registration_country: CodeName | null;
    registering_authority: string;
    country: CodeName | null;
    city: { id?: number; name: string } | null;
    timezone: string;
    official_phone: string;
    official_email: string;
    website: string | null;
    description: string;
    service_areas: { country: CodeName | null; city: { id?: number; name: string } | null }[];
  } | null;
}

/** Same reason codes as psychologists; NGO wording. */
export const NGO_REJECT_REASONS = [
  { value: 'license_unverified', label: 'Registration couldn’t be verified' },
  { value: 'incomplete_details', label: 'Details incomplete or incorrect' },
  { value: 'not_eligible', label: 'Not eligible' },
  { value: 'other', label: 'Other' },
] as const;

/** GET /accounts/admin/pending/?role=ngo — oldest first. */
export async function getPendingNgos(): Promise<ApiResponse<PendingNgo[]>> {
  const res = explain(await apiFetch<PendingNgo[] | { results: PendingNgo[] }>('/accounts/admin/pending/?role=ngo'));
  if (res.status === 404) return { ...res, data: null, error: APPROVAL_API_MISSING };
  if (!res.data) return { ...res, data: null };
  return { ...res, data: Array.isArray(res.data) ? res.data : res.data.results ?? [] };
}

/** POST /accounts/admin/{id}/approve/ */
export async function approveAccount(userId: number) {
  return explain(
    await apiFetch<{ id: number; approval_status: string }>(`/accounts/admin/${userId}/approve/`, { method: 'POST' })
  );
}

/** POST /accounts/admin/{id}/reject/ — reason optional. */
export async function rejectAccount(userId: number, reason: RejectReason | null) {
  return explain(
    await apiFetch<{ id: number; approval_status: string }>(`/accounts/admin/${userId}/reject/`, {
      method: 'POST',
      body: JSON.stringify(reason ? { reason } : {}),
    })
  );
}

// ============================================================
// Overview + Users (backend PR #42, `apps/accounts/api/admin_*`).
// Until those endpoints are deployed they answer 404, shown as
// ADMIN_API_MISSING.
// ============================================================

export const ADMIN_API_MISSING =
  'This part of the admin console isn’t on the backend yet. It will show real data as soon as the backend update is deployed.';

const ACCOUNT_NOT_FOUND = 'This account wasn’t found. It may have been removed — refresh the list.';

export type AccountRole = 'patient' | 'psychologist' | 'ngo';
export type AccountStatus = 'active' | 'pending' | 'rejected' | 'deactivated';

interface RoleCounts {
  total: number;
  active: number;
  pending: number;
  rejected: number;
  deactivated: number;
}

export interface AdminOverview {
  users: Record<AccountRole, RoleCounts>;
  pending_approvals: { psychologist: number; ngo: number };
  relationships: Record<string, number>;
  open_reports: number;
  weekly_signups: { week_start: string; patient: number; psychologist: number; ngo: number }[];
}

export interface AdminUserRow {
  id: number;
  role: AccountRole;
  display_name: string;
  /** false for a private patient: display_name is their pseudonym */
  is_real_name: boolean;
  /** null for a private patient */
  email: string | null;
  approval_status: 'approved' | 'pending' | 'rejected';
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

export interface AdminUserDetail {
  id: number;
  role: AccountRole;
  identity: { id: number; role: string; display_name: string; is_real_name: boolean };
  email: string;
  approval_status: 'approved' | 'pending' | 'rejected';
  is_active: boolean;
  created_at: string;
  last_login: string | null;
  patient: { pseudonym: string; is_profile_public: boolean; country: string | null } | null;
  psychologist_profile: PendingPsychologist['psychologist_profile'];
  ngo_profile: Record<string, unknown> | null;
}

export interface Page<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface AdminUsersQuery {
  role?: AccountRole;
  status?: AccountStatus;
  search?: string;
  page?: number;
  pageSize?: number;
}

export const DEACTIVATE_REASONS = [
  { value: 'policy_violation', label: 'Broke platform policies' },
  { value: 'report_upheld', label: 'A report against them was upheld' },
  { value: 'user_request', label: 'The user asked for it' },
  { value: 'other', label: 'Other' },
] as const;

export type DeactivateReason = (typeof DEACTIVATE_REASONS)[number]['value'];

function adminExplain<T>(res: ApiResponse<T>, notFound: string = ADMIN_API_MISSING): ApiResponse<T> {
  if (res.status === 404) return { ...res, data: null, error: notFound };
  if (res.status === 403) return { ...res, error: 'This account doesn’t have admin access.' };
  return res;
}

/** GET /accounts/admin/overview/ — counts only, no names or health data. */
export async function getAdminOverview() {
  return adminExplain(await apiFetch<AdminOverview>('/accounts/admin/overview/'));
}

function usersParams(q: AdminUsersQuery) {
  const p = new URLSearchParams();
  if (q.role) p.set('role', q.role);
  if (q.status) p.set('status', q.status);
  if (q.search?.trim()) p.set('search', q.search.trim());
  if (q.page && q.page > 1) p.set('page', String(q.page));
  if (q.pageSize) p.set('page_size', String(q.pageSize));
  const s = p.toString();
  return s ? `?${s}` : '';
}

/** GET /accounts/admin/users/ — newest first, 20 per page. Patients are found by pseudonym only. */
export async function listAdminUsers(q: AdminUsersQuery) {
  return adminExplain(await apiFetch<Page<AdminUserRow>>(`/accounts/admin/users/${usersParams(q)}`));
}

/** Every row matching the filters (50 per request), for Export. */
export async function listAllAdminUsers(q: Omit<AdminUsersQuery, 'page' | 'pageSize'>): Promise<ApiResponse<AdminUserRow[]>> {
  const rows: AdminUserRow[] = [];
  for (let page = 1; page <= 200; page++) {
    const res = await listAdminUsers({ ...q, page, pageSize: 50 });
    if (!res.data) return { ...res, data: null };
    rows.push(...res.data.results);
    if (!res.data.next) break;
  }
  return { data: rows, error: null, status: 200, loading: false };
}

/** GET /accounts/admin/users/{id}/ — opening a private patient reveals them; the backend audits it. */
export async function getAdminUser(userId: number) {
  return adminExplain(await apiFetch<AdminUserDetail>(`/accounts/admin/users/${userId}/`), ACCOUNT_NOT_FOUND);
}

/** POST /accounts/admin/users/{id}/deactivate/ — ends their care relationships. */
export async function deactivateUser(userId: number, reason: DeactivateReason | null) {
  return adminExplain(
    await apiFetch<{ id: number; approval_status: string; is_active: boolean }>(`/accounts/admin/users/${userId}/deactivate/`, {
      method: 'POST',
      body: JSON.stringify(reason ? { reason } : {}),
    }),
    ACCOUNT_NOT_FOUND
  );
}

/** POST /accounts/admin/users/{id}/reactivate/ — care relationships that ended stay ended. */
export async function reactivateUser(userId: number) {
  return adminExplain(
    await apiFetch<{ id: number; approval_status: string; is_active: boolean }>(`/accounts/admin/users/${userId}/reactivate/`, {
      method: 'POST',
    }),
    ACCOUNT_NOT_FOUND
  );
}

// ============================================================
// Managing admins (super-admins only) — backend PR #67,
// docs/handoff/admin-panel-2.md §2. Ordinary admins get 403
// "Only a super-admin can do this." on every call.
// ============================================================

export interface AdminAccount {
  id: number;
  email: string;
  full_name: string;
  is_super_admin: boolean;
  is_active: boolean;
  must_change_password: boolean;
  created_at: string;
  last_login: string | null;
}

export const NOT_SUPER_ADMIN = 'Only a super-admin can do this.';

function superExplain<T>(res: ApiResponse<T>): ApiResponse<T> {
  if (res.status === 404) return { ...res, data: null, error: 'No admin with that id.' };
  return res;
}

/** GET /accounts/admin/admins/ — oldest first. 403 = the caller isn't a super-admin. */
export async function listAdmins() {
  return apiFetch<AdminAccount[]>('/accounts/admin/admins/');
}

let superAdminCheck: Promise<boolean> | null = null;
/** True if the signed-in admin is a super-admin (one call per page load, as the handoff suggests). */
export function isSuperAdmin(): Promise<boolean> {
  superAdminCheck ??= listAdmins().then((r) => {
    if (r.status === 0 || (r.status ?? 0) >= 500) superAdminCheck = null; // retry later on network errors
    return !!r.data;
  });
  return superAdminCheck;
}
export function resetSuperAdminCheck() {
  superAdminCheck = null;
}

/** POST /accounts/admin/admins/ — 201 with temporary_password, shown only in this response. */
export async function createAdmin(email: string, fullName: string) {
  return apiFetch<AdminAccount & { temporary_password: string }>('/accounts/admin/admins/', {
    method: 'POST',
    body: JSON.stringify({ email, full_name: fullName }),
  });
}

const adminAction = async (path: string) =>
  superExplain(await apiFetch<AdminAccount>(path, { method: 'POST' }));

/** POST /accounts/admin/admins/{id}/promote/ */
export const promoteAdmin = (id: number) => adminAction(`/accounts/admin/admins/${id}/promote/`);
/** POST /accounts/admin/admins/me/demote/ — step down yourself (not the last super-admin). */
export const demoteSelf = () => adminAction('/accounts/admin/admins/me/demote/');
/** POST /accounts/admin/admins/{id}/deactivate/ — ordinary admins only; signs them out. */
export const deactivateAdmin = (id: number) => adminAction(`/accounts/admin/admins/${id}/deactivate/`);
/** POST /accounts/admin/admins/{id}/reactivate/ */
export const reactivateAdmin = (id: number) => adminAction(`/accounts/admin/admins/${id}/reactivate/`);
