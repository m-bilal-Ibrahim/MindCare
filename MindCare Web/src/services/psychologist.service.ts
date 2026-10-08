// ============================================================
// MindCare — Psychologist console API (live backend)
// Inbox / accept / decline, assigned patients, end relationship,
// "accepting new patients" switch, and the AI anxiety-risk form.
//
// Every endpoint here needs an APPROVED psychologist: the backend
// answers 403 otherwise, which callers show as NOT_APPROVED_MESSAGE.
// ============================================================

import { apiFetch } from './api.service';
import type { ApiResponse } from '../types';

export const NOT_APPROVED_MESSAGE =
  'Your account is still waiting for admin approval. Patient tools unlock once it’s approved.';
export const AI_WAKING_MESSAGE = 'AI is waking up, try again in a minute.';

/** Replace the generic 403 text with the approval explanation. */
function explain<T>(res: ApiResponse<T>): ApiResponse<T> {
  if (res.status === 403) return { ...res, error: NOT_APPROVED_MESSAGE };
  return res;
}

// ——— Shared shapes ———

export interface CodeName {
  code: string;
  name: string;
}

export interface InboxItem {
  id: number;
  requested_at: string;
  expires_at: string;
  requester: {
    pseudonym: string;
    preferred_language: CodeName | null;
    timezone: string;
    country: CodeName | null;
    gender: string | null;
    age: number | null;
  };
}

export interface AssignedPatient {
  relationship_id: number;
  accepted_at: string | null;
  full_name: string;
  pseudonym: string;
  age: number | null;
  gender: string | null;
  phone_number: string | null;
  country: CodeName | null;
  city: { id?: number; name: string } | null;
  preferred_language: CodeName | null;
  timezone: string;
}

export interface HistoryItem {
  relationship_id: number;
  pseudonym: string;
  accepted_at: string | null;
  ended_at: string | null;
  ended_by: string;
  end_reason: string;
}

// Reason choices mirror the backend's TextChoices.
export const DECLINE_REASONS = [
  { value: 'outside_specializations', label: 'Outside my specializations' },
  { value: 'language_or_timezone_mismatch', label: 'Language or time-zone mismatch' },
  { value: 'case_type_not_taken', label: 'Not taking this type of case' },
  { value: 'other', label: 'Other' },
] as const;

export const END_REASONS = [
  { value: 'treatment_completed', label: 'Treatment completed' },
  { value: 'referred_elsewhere', label: 'Referred to another professional' },
  { value: 'other', label: 'Other' },
] as const;

export const NOT_ACCEPTING_REASONS = [
  { value: 'fully_booked', label: 'Fully booked' },
  { value: 'away', label: 'Away / on leave' },
  { value: 'other', label: 'Other' },
] as const;

export type DeclineReason = (typeof DECLINE_REASONS)[number]['value'];
export type EndReason = (typeof END_REASONS)[number]['value'];
export type NotAcceptingReason = (typeof NOT_ACCEPTING_REASONS)[number]['value'];

// ——— Requests inbox ———

/** GET /relationships/inbox/ — pending, unexpired requests (pseudonym only, no name). */
export async function getInbox() {
  return explain(await apiFetch<InboxItem[]>('/relationships/inbox/'));
}

/** POST /relationships/requests/{id}/accept/ */
export async function acceptRequest(id: number) {
  return explain(
    await apiFetch<{ id: number; status: string }>(`/relationships/requests/${id}/accept/`, { method: 'POST' })
  );
}

/** POST /relationships/requests/{id}/decline/ — reason is optional. */
export async function declineRequest(id: number, reason: DeclineReason | null) {
  return explain(
    await apiFetch<{ id: number; status: string }>(`/relationships/requests/${id}/decline/`, {
      method: 'POST',
      body: JSON.stringify(reason ? { reason } : {}),
    })
  );
}

// ——— Patients ———

/** GET /relationships/patients/ — accepted patients, with real identity. */
export async function getPatients() {
  return explain(await apiFetch<AssignedPatient[]>('/relationships/patients/'));
}

/** POST /relationships/patients/{id}/end/ — a reason is required. */
export async function endRelationship(relationshipId: number, reason: EndReason) {
  return explain(
    await apiFetch<HistoryItem>(`/relationships/patients/${relationshipId}/end/`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    })
  );
}

/** GET /relationships/history/ — ended relationships (pseudonym only). */
export async function getHistory() {
  return explain(await apiFetch<HistoryItem[]>('/relationships/history/'));
}

// ——— Availability ———

export interface Availability {
  accepting: boolean;
  reason: NotAcceptingReason | null;
}

/** GET /psychologists/me/availability/ */
export async function getAvailability() {
  return explain(await apiFetch<Availability>('/psychologists/me/availability/'));
}

/** PUT /psychologists/me/availability/ — a reason is required when accepting is false. */
export async function setAvailability(value: Availability) {
  return explain(
    await apiFetch<Availability>('/psychologists/me/availability/', {
      method: 'PUT',
      body: JSON.stringify(value.accepting ? { accepting: true } : value),
    })
  );
}

// ——— AI anxiety-risk prediction (decision support) ———

export const AI_OCCUPATIONS = [
  'Artist',
  'Athlete',
  'Chef',
  'Doctor',
  'Engineer',
  'Freelancer',
  'Lawyer',
  'Musician',
  'Nurse',
  'Other',
  'Scientist',
  'Student',
  'Teacher',
] as const;

/** Keys are the AI service's exact column names (with spaces). */
export interface AnxietyPredictionInput {
  Age: number;
  'Sleep Hours': number;
  'Physical Activity (hrs/week)': number;
  cups_of_coffee: number;
  cups_of_tea: number;
  energy_drinks: number;
  cans_of_soda: number;
  pss_uncontrollable: number;
  pss_confident: number;
  pss_going_your_way: number;
  pss_difficulties_piling_up: number;
  'Heart Rate (bpm)': number;
  'Breathing Rate (breaths/min)': number;
  'Therapy Sessions (per month)': number;
  'Diet Quality (1-10)': number;
  Occupation: (typeof AI_OCCUPATIONS)[number];
  'Family History of Anxiety': 'Yes' | 'No';
}

export type RiskClass = 'Low' | 'Medium' | 'High';

export interface AnxietyPrediction {
  predicted_class: RiskClass;
  probabilities: Record<RiskClass, number>;
  uncertainty_flag: boolean;
  warnings: string[];
  estimated_caffeine_mg: number;
  estimated_stress_level: number;
  confidence: number;
  confidence_label: 'confident' | 'borderline';
  borderline_reasons: string[];
  borderline_between: string[] | null;
}

/** POST /ai/anxiety-prediction/ — 503 means the AI service is asleep. */
export async function predictAnxiety(input: AnxietyPredictionInput) {
  const res = explain(
    await apiFetch<AnxietyPrediction>('/ai/anxiety-prediction/', {
      method: 'POST',
      body: JSON.stringify(input),
    })
  );
  if (res.status === 503) return { ...res, error: AI_WAKING_MESSAGE };
  return res;
}

// ——— Own profile ———

export interface MyPsychologistProfile {
  full_name: string;
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
}

/** GET /psychologists/me/ — works for pending psychologists too. */
export function getMyProfile() {
  return apiFetch<MyPsychologistProfile>('/psychologists/me/');
}
