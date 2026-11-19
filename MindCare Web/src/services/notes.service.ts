// ============================================================
// MindCare — Therapy notes (psychologist, current patients only)
// Backend PR #88, MindCare Backend/docs/handoff/therapy-notes.md.
// Base /clinical-notes/patients/{rel}/ where rel = relationship id.
// No DELETE. Errors (400/403/404/429) are shown as the backend sends them.
// ============================================================

import { apiFetch } from './api.service';
import type { Page } from './admin.service';
import type { AssignedPatient } from './psychologist.service';

export type RiskLevel = 'low' | 'medium' | 'high';

export interface Addendum {
  id: number;
  text: string;
  created_at: string;
}

export interface TherapyNote {
  id: number;
  session_id: number | null;
  session_starts_at: string | null;
  observations: string;
  interventions: string;
  plan: string;
  progress_rating: number | null;
  risk_level: RiskLevel | null;
  version: number;
  created_at: string;
  updated_at: string;
  locked_at: string;
  is_locked: boolean;
  addenda: Addendum[];
}

/** Body for create / edit. `session` only on create. */
export interface NoteInput {
  session?: number | null;
  observations?: string;
  interventions?: string;
  plan?: string;
  progress_rating?: number | null;
  risk_level?: RiskLevel | null;
}

export interface ProgressPoint {
  note_id: number;
  date: string;
  session_id: number | null;
  session_starts_at: string | null;
  progress_rating: number | null;
  risk_level: RiskLevel | null;
}

export interface PatientSummary {
  text: string | null;
  updated_at: string | null;
}

/** A session from /appointments/psychologist/sessions/ (only what the note form needs). */
export interface PsychologistSession {
  id: number;
  status: string;
  starts_at: string;
  relationship_id: number;
}

const base = (rel: number) => `/clinical-notes/patients/${rel}`;
const asList = <T,>(d: T[] | Page<T> | null): T[] | null => (d == null ? null : Array.isArray(d) ? d : d.results);

/** GET /relationships/patients/{rel}/ — the patient this page is about (404 = not your current patient). */
export const getPatient = (rel: number) => apiFetch<AssignedPatient>(`/relationships/patients/${rel}/`);

/** GET notes/ — newest first. shortcut: first page only (20), add paging when a patient has more. */
export async function listNotes(rel: number) {
  const res = await apiFetch<TherapyNote[] | Page<TherapyNote>>(`${base(rel)}/notes/`);
  return { ...res, data: asList(res.data) };
}

export const createNote = (rel: number, body: NoteInput) =>
  apiFetch<TherapyNote>(`${base(rel)}/notes/`, { method: 'POST', body: JSON.stringify(body) });

/** PATCH — only while the note isn't locked (24 h after it was written). */
export const updateNote = (rel: number, id: number, body: NoteInput) =>
  apiFetch<TherapyNote>(`${base(rel)}/notes/${id}/`, { method: 'PATCH', body: JSON.stringify(body) });

export const addAddendum = (rel: number, id: number, text: string) =>
  apiFetch<Addendum>(`${base(rel)}/notes/${id}/addenda/`, { method: 'POST', body: JSON.stringify({ text }) });

/** GET progress/ — rated notes, oldest first. */
export async function getProgress(rel: number) {
  const res = await apiFetch<ProgressPoint[] | Page<ProgressPoint>>(`${base(rel)}/progress/`);
  return { ...res, data: asList(res.data) };
}

/** The summary the patient reads word for word in the app. */
export const getSummary = (rel: number) => apiFetch<PatientSummary>(`${base(rel)}/summary/`);
export const saveSummary = (rel: number, text: string) =>
  apiFetch<PatientSummary>(`${base(rel)}/summary/`, { method: 'PUT', body: JSON.stringify({ text }) });

const NOTE_SESSION_STATUSES = ['confirmed', 'completed', 'no_show'];

/** This patient's confirmed / past sessions, for the optional "link to a session" choice. */
export async function getNoteSessions(rel: number): Promise<PsychologistSession[]> {
  const views = await Promise.all(
    ['past', 'upcoming'].map((v) =>
      apiFetch<PsychologistSession[] | Page<PsychologistSession>>(`/appointments/psychologist/sessions/?view=${v}`)
    )
  );
  return views
    .flatMap((r) => asList(r.data) ?? [])
    .filter((s) => s.relationship_id === rel && NOTE_SESSION_STATUSES.includes(s.status))
    .sort((a, b) => b.starts_at.localeCompare(a.starts_at));
}
