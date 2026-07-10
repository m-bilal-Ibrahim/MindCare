// ============================================================
// MindCare — Therapist Console Types
// ============================================================

export interface TherapistNavItem {
  id: string;
  label: string;
  route: string;
  icon: 'home' | 'users' | 'calendar' | 'inbox' | 'message' | 'clipboard' | 'circle-users' | 'file' | 'sun';
  badge?: number;
}

export type PatientStatus = 'Active' | 'Trial' | 'Paused';

export interface ConsolePatient {
  id: string;
  initials: string;
  avatarColor: string;
  name: string;
  age: number;
  city: string;
  focus: string[];
  plan: 'Monthly' | 'Yearly';
  status: PatientStatus;
  mood30d: number;
  moodTrend: number[];
  streakDays: number;
  lastSeen: string;
  flag?: string;
  flagTone?: 'warning' | 'info';
}

export interface TherapistSessionEntry {
  id: string;
  time: string;
  durationMin: number;
  patientId: string;
  patientName: string;
  patientInitials: string;
  avatarColor: string;
  label: string;
  status: 'confirmed' | 'pending' | 'next';
  statusMeta?: string;
}

export interface SensorFlagEntry {
  id: string;
  patientId: string;
  patientName: string;
  patientInitials: string;
  avatarColor: string;
  summary: string;
}

export interface AiSuggestionEntry {
  id: string;
  patientName: string;
  suggestion: string;
}

export interface ConsoleStat {
  label: string;
  value: string;
  delta?: string;
  trend: number[];
  trendColor: 'green' | 'red' | 'neutral';
}

export interface SessionNoteEntry {
  id: string;
  date: string;
  meta: string;
  content: string;
}

export interface BodyMetric {
  label: string;
  value: string;
  unit: string;
  trend: number[];
  color: string;
}

export interface AidaRecommendation {
  id: string;
  status: 'editing' | 'pending';
  category: 'Permanent' | 'Temporary';
  description: string;
}

export interface PatientDetailData {
  patient: ConsolePatient;
  patientCode: string;
  joined: string;
  billing: string;
  medication: string;
  languages: string;
  sessionsThisMonth: number;
  sessionsMonthlyTarget: number;
  totalSessions: number;
  avgMoodDelta: string;
  moodChart: number[];
  moodChartLabel: string;
  moodChartDates: [string, string, string];
  bodyMetrics: BodyMetric[];
  sessionNotes: SessionNoteEntry[];
  aidaRecommendations: AidaRecommendation[];
  aidaPendingCount: number;
}