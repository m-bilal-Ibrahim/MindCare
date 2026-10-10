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
  } | null;
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
