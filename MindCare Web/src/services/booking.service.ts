// ============================================================
// MindCare — Booking (psychologist side). Backend Phase 2 module 4,
// MindCare Backend/docs/handoff/booking-fees.md. Base /appointments/psychologist/.
// Times are UTC ISO from the API; slots are sent back exactly as received.
// ============================================================

import { apiFetch } from './api.service';
import type { Page } from './admin.service';

export type SessionStatus = 'requested' | 'proposed' | 'confirmed' | 'cancelled' | 'expired' | 'completed' | 'no_show';
export type SessionView = 'requests' | 'upcoming' | 'past';

export interface BookingSession {
  id: number;
  status: SessionStatus;
  starts_at: string;
  ends_at: string;
  duration_minutes: number;
  fee_pkr: number | null;
  requested_starts_at: string | null;
  confirmed_at: string | null;
  cancelled_at: string | null;
  cancelled_by: 'patient' | 'psychologist' | 'system' | null;
  is_late_cancellation: boolean;
  created_at: string;
  relationship_id: number;
  patient: { display_name: string; is_real_name: boolean };
  outcome_marked_at: string | null;
}

export interface BookingSettings {
  session_minutes: 30 | 50 | 60;
  fee_pkr: number | null;
  video_link: string;
  is_bookable: boolean;
  not_bookable_reason: 'no_fee' | 'no_video_link' | 'no_working_hours' | null;
}

export interface HoursWindow {
  weekday: number; // Monday = 0
  start_time: string; // "09:00"
  end_time: string;
}

export interface DayOff {
  id: number;
  date: string;
}

const P = '/appointments/psychologist';
const json = (method: string, body?: unknown) => ({ method, body: body === undefined ? undefined : JSON.stringify(body) });

export const getSettings = () => apiFetch<BookingSettings>(`${P}/settings/`);
export const saveSettings = (body: Partial<Pick<BookingSettings, 'session_minutes' | 'fee_pkr' | 'video_link'>>) =>
  apiFetch<BookingSettings>(`${P}/settings/`, json('PATCH', body));

export const getHours = () => apiFetch<{ windows: HoursWindow[]; timezone: string }>(`${P}/working-hours/`);
/** Replaces all windows. */
export const saveHours = (windows: HoursWindow[]) =>
  apiFetch<{ windows: HoursWindow[]; timezone: string }>(`${P}/working-hours/`, json('PUT', { windows }));

export async function getDaysOff() {
  const res = await apiFetch<DayOff[] | Page<DayOff>>(`${P}/days-off/`);
  return { ...res, data: res.data == null ? null : Array.isArray(res.data) ? res.data : res.data.results };
}
export const addDayOff = (date: string) => apiFetch<DayOff>(`${P}/days-off/`, json('POST', { date }));
export const removeDayOff = (id: number) => apiFetch<null>(`${P}/days-off/${id}/`, json('DELETE'));

/** Your free slots 12 h to 30 days ahead (for proposing another time). */
export const getSlots = () => apiFetch<{ slots: string[] }>(`${P}/slots/`);

/** shortcut: first page only (20), add paging if a view ever has more. */
export async function listSessions(view: SessionView) {
  const res = await apiFetch<BookingSession[] | Page<BookingSession>>(`${P}/sessions/?view=${view}`);
  return { ...res, data: res.data == null ? null : Array.isArray(res.data) ? res.data : res.data.results };
}

export const confirmSession = (id: number) => apiFetch<BookingSession>(`${P}/sessions/${id}/confirm/`, json('POST'));
export const proposeSession = (id: number, startsAt: string) =>
  apiFetch<BookingSession>(`${P}/sessions/${id}/propose/`, json('POST', { starts_at: startsAt }));
export const cancelSession = (id: number) => apiFetch<BookingSession>(`${P}/sessions/${id}/cancel/`, json('POST'));
export const markOutcome = (id: number, outcome: 'completed' | 'no_show') =>
  apiFetch<BookingSession>(`${P}/sessions/${id}/outcome/`, json('POST', { outcome }));
