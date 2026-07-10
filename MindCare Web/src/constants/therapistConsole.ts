// ============================================================
// MindCare — Therapist Console Mock Data
//
// All data below is fictional dummy data for reviewing the UI
// flow end-to-end. Nothing here represents real patients.
// ============================================================

import type {
  TherapistNavItem,
  ConsolePatient,
  TherapistSessionEntry,
  SensorFlagEntry,
  AiSuggestionEntry,
  ConsoleStat,
  PatientDetailData,
} from '../types/therapistConsole';

// ——— Console routes ———
export const CONSOLE_ROUTES = {
  TODAY: '/therapist/today',
  PATIENTS: '/therapist/patients',
  PATIENT_DETAIL: '/therapist/patients/:patientId',
} as const;

export const buildPatientDetailRoute = (patientId: string) => `/therapist/patients/${patientId}`;

// ——— Sidebar navigation ———
export const THERAPIST_NAV_PRACTICE: TherapistNavItem[] = [
  { id: 'today', label: 'Today', route: CONSOLE_ROUTES.TODAY, icon: 'home' },
  { id: 'patients', label: 'Patients', route: CONSOLE_ROUTES.PATIENTS, icon: 'users' },
  { id: 'schedule', label: 'Schedule', route: '#', icon: 'calendar', badge: 3 },
  { id: 'requests', label: 'Requests', route: '#', icon: 'inbox', badge: 5 },
  { id: 'messages', label: 'Messages', route: '#', icon: 'message', badge: 2 },
];

export const THERAPIST_NAV_CARE: TherapistNavItem[] = [
  { id: 'care-plans', label: 'Care plans', route: '#', icon: 'clipboard' },
  { id: 'circles', label: 'Circles', route: '#', icon: 'circle-users' },
  { id: 'reports', label: 'Reports', route: '#', icon: 'file' },
];

export const THERAPIST_NAV_ACCOUNT: TherapistNavItem[] = [
  { id: 'profile', label: 'Profile & availability', route: '#', icon: 'sun' },
];

// ——— Patients (mock roster) ———
export const CONSOLE_PATIENTS: ConsolePatient[] = [
  {
    id: 'p-layla',
    initials: 'LS',
    avatarColor: 'bg-amber-600',
    name: 'Layla Siddiqui',
    age: 28,
    city: 'Islamabad',
    focus: ['Anxiety', 'Burnout'],
    plan: 'Monthly',
    status: 'Active',
    mood30d: 3.4,
    moodTrend: [2.6, 2.8, 2.7, 3.0, 3.1, 3.0, 3.3, 3.2, 3.4, 3.5, 3.4],
    streakDays: 14,
    lastSeen: 'Today',
  },
  {
    id: 'p-ammar',
    initials: 'AS',
    avatarColor: 'bg-orange-600',
    name: 'Ammar Sheikh',
    age: 34,
    city: 'Islamabad',
    focus: ['Sober walk', 'Stress'],
    plan: 'Yearly',
    status: 'Active',
    mood30d: 4.1,
    moodTrend: [3.2, 3.4, 3.5, 3.6, 3.8, 3.7, 3.9, 4.0, 4.0, 4.1, 4.1],
    streakDays: 32,
    lastSeen: '2d ago',
    flag: '↑ sleep',
    flagTone: 'info',
  },
  {
    id: 'p-hira',
    initials: 'HK',
    avatarColor: 'bg-emerald-700',
    name: 'Hira Khan',
    age: 26,
    city: 'Lahore',
    focus: ['Grief', 'Family'],
    plan: 'Monthly',
    status: 'Trial',
    mood30d: 2.7,
    moodTrend: [3.4, 3.1, 2.9, 3.0, 2.7, 2.5, 2.8, 2.6, 2.7, 2.6, 2.7],
    streakDays: 5,
    lastSeen: 'Yesterday',
    flag: 'low mood',
    flagTone: 'warning',
  },
  {
    id: 'p-zoya',
    initials: 'ZI',
    avatarColor: 'bg-blue-900',
    name: 'Zoya Iqbal',
    age: 23,
    city: 'Lahore',
    focus: ['Identity', 'Sleep'],
    plan: 'Monthly',
    status: 'Active',
    mood30d: 3.8,
    moodTrend: [3.0, 3.1, 3.3, 3.4, 3.5, 3.6, 3.6, 3.7, 3.8, 3.8, 3.8],
    streakDays: 21,
    lastSeen: '3d ago',
  },
  {
    id: 'p-omar',
    initials: 'OR',
    avatarColor: 'bg-rose-500',
    name: 'Omar Raza',
    age: 41,
    city: 'Islamabad',
    focus: ['Work', 'Burnout'],
    plan: 'Yearly',
    status: 'Active',
    mood30d: 3.2,
    moodTrend: [3.6, 3.4, 3.1, 3.3, 3.0, 2.9, 3.1, 3.0, 3.1, 3.2, 3.2],
    streakDays: 9,
    lastSeen: 'Today',
  },
  {
    id: 'p-sana',
    initials: 'SY',
    avatarColor: 'bg-emerald-800',
    name: 'Sana Yousaf',
    age: 31,
    city: 'Lahore',
    focus: ['Trauma', 'Stress'],
    plan: 'Monthly',
    status: 'Paused',
    mood30d: 3.0,
    moodTrend: [3.5, 3.2, 2.9, 3.1, 2.8, 3.0, 2.7, 2.9, 3.0, 2.9, 3.0],
    streakDays: 0,
    lastSeen: '14d ago',
    flag: 'inactive',
    flagTone: 'warning',
  },
  {
    id: 'p-fatima',
    initials: 'FA',
    avatarColor: 'bg-amber-700',
    name: 'Fatima Aslam',
    age: 29,
    city: 'Lahore',
    focus: ['Couples'],
    plan: 'Monthly',
    status: 'Active',
    mood30d: 4.0,
    moodTrend: [3.2, 3.4, 3.5, 3.6, 3.7, 3.8, 3.8, 3.9, 3.9, 4.0, 4.0],
    streakDays: 18,
    lastSeen: '4d ago',
  },
  {
    id: 'p-bilal',
    initials: 'BR',
    avatarColor: 'bg-blue-950',
    name: 'Bilal Rauf',
    age: 36,
    city: 'Islamabad',
    focus: ['Addiction', 'Recovery'],
    plan: 'Yearly',
    status: 'Active',
    mood30d: 3.6,
    moodTrend: [2.9, 3.0, 3.2, 3.3, 3.4, 3.5, 3.5, 3.6, 3.6, 3.7, 3.6],
    streakDays: 27,
    lastSeen: 'Today',
    flag: '↑ HR',
    flagTone: 'warning',
  },
];

export const CONSOLE_PATIENT_SUMMARY = { active: 32, trials: 6, paused: 2, total: 40 };
export const CONSOLE_FOCUS_FILTERS = ['Anxiety', 'Burnout', 'Couples', 'Grief', 'Trauma', 'Identity', 'Addiction'];

// ——— Today page ———
export const TODAY_SESSIONS: TherapistSessionEntry[] = [
  {
    id: 's-1',
    time: '10:00 AM',
    durationMin: 50,
    patientId: 'p-layla',
    patientName: 'Layla Siddiqui',
    patientInitials: 'LS',
    avatarColor: 'bg-amber-600',
    label: 'Session 7 of monthly',
    status: 'next',
    statusMeta: 'in 22 min',
  },
  {
    id: 's-2',
    time: '12:30 PM',
    durationMin: 50,
    patientId: 'p-omar',
    patientName: 'Omar Raza',
    patientInitials: 'OR',
    avatarColor: 'bg-rose-500',
    label: 'Trial · day 4',
    status: 'confirmed',
  },
  {
    id: 's-3',
    time: '3:30 PM',
    durationMin: 50,
    patientId: 'p-hira',
    patientName: 'Hira Khan',
    patientInitials: 'HK',
    avatarColor: 'bg-emerald-700',
    label: 'Couples · with partner',
    status: 'pending',
  },
  {
    id: 's-4',
    time: '5:00 PM',
    durationMin: 30,
    patientId: 'p-bilal',
    patientName: 'Bilal Rauf',
    patientInitials: 'BR',
    avatarColor: 'bg-blue-950',
    label: 'Check-in (short)',
    status: 'confirmed',
  },
];

export const TODAY_SENSOR_FLAGS: SensorFlagEntry[] = [
  {
    id: 'flag-1',
    patientId: 'p-bilal',
    patientName: 'Bilal Rauf',
    patientInitials: 'BR',
    avatarColor: 'bg-blue-950',
    summary: 'Resting HR up 14 bpm overnight · 3 nights running',
  },
];

export const TODAY_AI_SUGGESTIONS: AiSuggestionEntry[] = [
  { id: 'ai-1', patientName: 'Layla S.', suggestion: 'Add 4-7-8 breath before sleep' },
  { id: 'ai-2', patientName: 'Zoya I.', suggestion: 'Swap evening journal → morning' },
  { id: 'ai-3', patientName: 'Fatima A.', suggestion: 'Trim cognitive reframe to 2×/wk' },
];

export const TODAY_AI_SUGGESTIONS_TOTAL = 9;

export const TODAY_STATS: ConsoleStat[] = [
  { label: 'Active patients', value: '32', delta: '+4 this month', trend: [20, 22, 24, 26, 28, 30, 32], trendColor: 'green' },
  { label: 'On trial', value: '6', delta: '3 ending this week', trend: [2, 4, 3, 5, 4, 6, 6], trendColor: 'red' },
  { label: 'Sessions · 7d', value: '24', delta: '+12% · 22 confirmed · 2 rescheduled', trend: [15, 18, 16, 20, 19, 22, 24], trendColor: 'neutral' },
  { label: 'Avg mood · cohort', value: '3.4', delta: '+0.2 of 5 · trending up', trend: [3.0, 3.1, 3.1, 3.2, 3.3, 3.3, 3.4], trendColor: 'green' },
];

// ——— Patient detail (Layla Siddiqui, matches T03) ———
export const LAYLA_DETAIL: PatientDetailData = {
  patient: CONSOLE_PATIENTS[0],
  patientCode: '#MC-2026-0412',
  joined: 'Feb 2026',
  billing: 'Monthly plan · Rs 18,000',
  medication: 'No medication',
  languages: 'English · Urdu',
  sessionsThisMonth: 3,
  sessionsMonthlyTarget: 4,
  totalSessions: 8,
  avgMoodDelta: '+0.6',
  moodChart: [2.6, 2.5, 2.8, 2.7, 2.9, 3.0, 2.9, 3.1, 3.2, 3.1, 3.3, 3.2, 3.4, 3.3, 3.5, 3.4],
  moodChartLabel: 'Quietly improving',
  moodChartDates: ['Apr 21', 'May 6', 'May 21'],
  bodyMetrics: [
    { label: 'Heart rate', value: '68', unit: 'bpm', trend: [72, 71, 70, 69, 70, 68, 68], color: '#f97316' },
    { label: 'Breathing', value: '13', unit: '/min', trend: [15, 14, 14, 13, 14, 13, 13], color: '#60a5fa' },
    { label: 'Sweat · EDA', value: '2.1', unit: 'µS', trend: [2.6, 2.5, 2.3, 2.4, 2.2, 2.1, 2.1], color: '#a3a3a3' },
    { label: 'Sleep', value: '6h 40', unit: '', trend: [5.5, 5.8, 6.0, 6.1, 6.3, 6.5, 6.67], color: '#93c5fd' },
  ],
  sessionNotes: [
    {
      id: 'note-1',
      date: 'Fri · May 16',
      meta: 'Session 7 · 50 min',
      content:
        'Work pressure peaked after Tue review. Practiced 4-7-8 in-session, reported "instant easier shoulders." Agreed to journal trigger thoughts on Mon/Wed.',
    },
    {
      id: 'note-2',
      date: 'Wed · May 14',
      meta: 'Quick check-in',
      content: 'Slept 6h 40 (best week). Skipped Tuesday journal — flagged not as failure, but as data.',
    },
    {
      id: 'note-3',
      date: 'Fri · May 9',
      meta: 'Session 6 · 50 min',
      content: "First mention of grandmother's health. Held space, did not push.",
    },
  ],
  aidaRecommendations: [
    {
      id: 'rec-1',
      status: 'editing',
      category: 'Permanent',
      description: 'Add 4-7-8 breath before sleep (8 min)',
    },
  ],
  aidaPendingCount: 3,
};

export const PATIENT_DETAIL_TABS = ['Overview', 'Sensors', 'Care plan', 'Notes', 'Sessions', 'Reports', 'Billing'] as const;