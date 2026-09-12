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
  ScheduleEvent,
  SessionRequestEntry,
  InSessionData,
  CarePlanData,
  CarePlanCategory,
  ExerciseLibraryItem,
  MessageThread,
  WeeklyReportData,
  TherapistProfileData,
  AvailabilitySlot,
  CircleSummary,
  CirclePost,
  CircleQuestionWaiting,
  CircleStats,
} from '../types/therapistConsole';

// ——— Console routes ———
export const CONSOLE_ROUTES = {
  TODAY: '/therapist/today',
  PATIENTS: '/therapist/patients',
  PATIENT_DETAIL: '/therapist/patients/:patientId',
  SCHEDULE: '/therapist/schedule',
  REQUESTS: '/therapist/requests',
  IN_SESSION: '/therapist/session',
  CARE_PLAN: '/therapist/care-plans/:patientId',
  MESSAGES: '/therapist/messages',
  WEEKLY_REPORT: '/therapist/reports/:patientId',
  CIRCLES: '/therapist/circles',
  PROFILE: '/therapist/profile',
} as const;

export const buildPatientDetailRoute = (patientId: string) => `/therapist/patients/${patientId}`;
export const buildCarePlanRoute = (patientId: string) => `/therapist/care-plans/${patientId}`;
export const buildWeeklyReportRoute = (patientId: string) => `/therapist/reports/${patientId}`;

// ——— Sidebar navigation ———
export const THERAPIST_NAV_PRACTICE: TherapistNavItem[] = [
  { id: 'today', label: 'Today', route: CONSOLE_ROUTES.TODAY, icon: 'home' },
  { id: 'patients', label: 'Patients', route: CONSOLE_ROUTES.PATIENTS, icon: 'users' },
  { id: 'schedule', label: 'Schedule', route: CONSOLE_ROUTES.SCHEDULE, icon: 'calendar', badge: 3 },
  { id: 'requests', label: 'Requests', route: CONSOLE_ROUTES.REQUESTS, icon: 'inbox', badge: 5 },
  { id: 'messages', label: 'Messages', route: CONSOLE_ROUTES.MESSAGES, icon: 'message', badge: 2 },
];

export const THERAPIST_NAV_CARE: TherapistNavItem[] = [
  { id: 'care-plans', label: 'Care plans', route: buildCarePlanRoute('p-layla'), icon: 'clipboard' },
  { id: 'circles', label: 'Circles', route: CONSOLE_ROUTES.CIRCLES, icon: 'circle-users' },
  { id: 'reports', label: 'Reports', route: buildWeeklyReportRoute('p-layla'), icon: 'file' },
];

export const THERAPIST_NAV_ACCOUNT: TherapistNavItem[] = [
  { id: 'profile', label: 'Profile & availability', route: CONSOLE_ROUTES.PROFILE, icon: 'sun' },
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

// ——— Schedule (T04) ———
export const SCHEDULE_WEEK_DAYS = [
  { label: 'MON', date: 19 },
  { label: 'TUE', date: 20 },
  { label: 'WED', date: 21 },
  { label: 'THU', date: 22 },
  { label: 'FRI', date: 23 },
  { label: 'SAT', date: 24 },
  { label: 'SUN', date: 25 },
];

export const SCHEDULE_HOURS = [9, 10, 11, 12, 13, 14, 15, 16, 17, 18];
export const SCHEDULE_SUMMARY = { confirmed: 11, awaiting: 3, free: 4 };

export const SCHEDULE_EVENTS: ScheduleEvent[] = [
  { id: 'e1', day: 0, startHour: 9.5, durationMin: 50, patientName: 'Hira K.', patientId: 'p-hira', label: '9:30 AM', type: 'confirmed' },
  { id: 'e2', day: 0, startHour: 12, durationMin: 30, label: 'Aida sync', type: 'block' },
  { id: 'e3', day: 1, startHour: 10.5, durationMin: 50, patientName: 'Ammar S.', patientId: 'p-ammar', label: '10:30', type: 'confirmed' },
  { id: 'e4', day: 1, startHour: 14, durationMin: 50, patientName: 'Sana Y.', patientId: 'p-sana', label: '2:00 · pending', type: 'pending' },
  { id: 'e5', day: 2, startHour: 10, durationMin: 50, patientName: 'Layla S.', patientId: 'p-layla', label: '10:00', type: 'confirmed' },
  { id: 'e6', day: 2, startHour: 12.5, durationMin: 50, patientName: 'Omar R.', patientId: 'p-omar', label: '12:30 · trial', type: 'trial' },
  { id: 'e7', day: 2, startHour: 15.5, durationMin: 50, patientName: 'Hira K.', patientId: 'p-hira', label: '3:30 · pending', type: 'pending' },
  { id: 'e8', day: 2, startHour: 17, durationMin: 50, patientName: 'Bilal R.', patientId: 'p-bilal', label: '5:00', type: 'confirmed' },
  { id: 'e9', day: 3, startHour: 9, durationMin: 50, patientName: 'Fatima A.', patientId: 'p-fatima', label: '9:00', type: 'confirmed' },
  { id: 'e10', day: 3, startHour: 16, durationMin: 50, patientName: 'Zoya I.', patientId: 'p-zoya', label: '4:00', type: 'confirmed' },
  { id: 'e11', day: 4, startHour: 10.5, durationMin: 50, patientName: 'Layla S.', patientId: 'p-layla', label: '10:30', type: 'confirmed' },
  { id: 'e12', day: 4, startHour: 13, durationMin: 60, label: 'Block · admin', type: 'block' },
  { id: 'e13', day: 4, startHour: 16, durationMin: 50, patientName: 'Omar R.', patientId: 'p-omar', label: '4:00 · trial', type: 'trial' },
];

// ——— Requests (T05) ———
export const SESSION_REQUESTS: SessionRequestEntry[] = [
  {
    id: 'r1',
    patientId: 'p-hira',
    patientName: 'Hira Khan',
    patientInitials: 'HK',
    avatarColor: 'bg-emerald-700',
    tag: 'Couples',
    tagTone: 'default',
    date: 'Tue · May 27',
    time: '3:30 PM',
    durationMin: 50,
    note: 'Want to bring partner first time. Will introduce gently.',
    requestedAgo: '2h ago',
    status: 'inbox',
  },
  {
    id: 'r2',
    patientId: 'p-sana',
    patientName: 'Sana Yousaf',
    patientInitials: 'SY',
    avatarColor: 'bg-emerald-800',
    tag: 'Reschedule',
    tagTone: 'warning',
    date: 'Fri · May 23',
    time: '11:00 AM',
    durationMin: 50,
    note: 'Out sick — can we push to Saturday morning?',
    requestedAgo: '5h ago',
    status: 'inbox',
  },
  {
    id: 'r3',
    patientId: 'p-omar',
    patientName: 'Omar Raza',
    patientInitials: 'OR',
    avatarColor: 'bg-rose-500',
    tag: 'Check-in',
    tagTone: 'default',
    date: 'Wed · May 28',
    time: '12:30 PM',
    durationMin: 30,
    requestedAgo: 'yesterday',
    status: 'inbox',
  },
  {
    id: 'r4',
    patientId: null,
    patientName: 'Ahmed Bhatti',
    patientInitials: 'AB',
    avatarColor: 'bg-violet-600',
    tag: 'New patient · trial',
    tagTone: 'info',
    date: 'Thu · May 29',
    time: '5:00 PM',
    durationMin: 50,
    note: 'First session — referred by Rozan helpline.',
    requestedAgo: 'yesterday',
    status: 'inbox',
  },
  {
    id: 'r5',
    patientId: 'p-zoya',
    patientName: 'Zoya Iqbal',
    patientInitials: 'ZI',
    avatarColor: 'bg-blue-900',
    tag: 'Check-in',
    tagTone: 'default',
    date: 'Mon · Jun 2',
    time: '4:00 PM',
    durationMin: 30,
    requestedAgo: '2d ago',
    status: 'inbox',
  },
];

export const REQUESTS_SUMMARY = { inbox: 5, awaitingThem: 3, past30d: 42 };

// ——— In-session (T06) ———
export const IN_SESSION_DATA: InSessionData = {
  patientId: 'p-layla',
  patientName: 'Layla Siddiqui',
  patientInitials: 'LS',
  avatarColor: 'bg-amber-600',
  sessionLabel: 'session 7',
  elapsedLabel: '12:34',
  totalLabel: '50:00',
  speakingCaption: '"Work stuff, again. My head won\'t switch off."',
  aiPromptSuggestion: '"Let\'s stay with that for a moment — what does it sound like inside your head?"',
  liveSensors: [
    { label: 'HR', value: '74', trend: [68, 70, 71, 73, 74, 74, 74], color: '#f97316' },
    { label: 'Breath', value: '16', trend: [14, 14, 15, 15, 16, 16, 16], color: '#60a5fa' },
    { label: 'EDA', value: '3.2', trend: [2.1, 2.3, 2.6, 2.9, 3.0, 3.1, 3.2], color: '#eab308' },
  ],
  liveCue: 'EDA climbing as Layla mentions "review meeting" — consider grounding before next prompt.',
  liveNotes: [
    {
      id: 'n1',
      type: 'auto',
      content: 'Opened on "work won\'t switch off." Mentions Tue review specifically — different from last week\'s vagueness.',
    },
    { id: 'n2', type: 'marked', time: '12:18', content: 'Layla: "I keep rehearsing it." → rumination loop.' },
    {
      id: 'n3',
      type: 'auto',
      content: 'Tried 4-7-8 — visible shoulder drop on cam at 04:50. Will prescribe permanent pre-sleep.',
    },
  ],
};
// ——— Care plan editor (T09) ———
export const LAYLA_CARE_PLAN: CarePlanData = {
  patientId: 'p-layla',
  patientName: 'Layla Siddiqui',
  patientInitials: 'LS',
  avatarColor: 'bg-amber-600',
  weekLabel: 'Week 21 of May',
  nextReview: 'Fri',
  version: 'v 0.8',
  completedCount: 10,
  totalCount: 19,
  compliancePercent: 58,
  lastUpdated: '3 days ago',
  pendingFromAida: 1,
  blocks: [
    {
      id: 'b1',
      category: 'Breath',
      title: 'Box breathing',
      cadence: 'Daily · 5 min · pre-sleep',
      addedBy: 'You',
      addedDate: 'Mar 12',
      doneCount: 5,
      totalCount: 7,
    },
    {
      id: 'b2',
      category: 'Body',
      title: '10-min body scan',
      cadence: 'Mon · Wed · Fri',
      addedBy: 'You',
      addedDate: 'Mar 12',
      doneCount: 1,
      totalCount: 3,
    },
    {
      id: 'b3',
      category: 'Thinking',
      title: 'Cognitive reframe',
      cadence: 'Tue · Thu · 12 min',
      addedBy: 'You',
      addedDate: 'Apr 4',
      doneCount: 0,
      totalCount: 2,
      lowCompliance: true,
    },
    {
      id: 'b4',
      category: 'Reflect',
      title: 'Evening journal',
      cadence: 'Daily · 3 min',
      addedBy: 'You',
      addedDate: 'Feb 26',
      doneCount: 4,
      totalCount: 7,
    },
    {
      id: 'b5',
      category: 'Breath',
      title: '4-7-8 pre-sleep',
      cadence: 'Daily · 8 min · proposed',
      addedBy: 'Aida',
      addedDate: 'pending',
      doneCount: 0,
      totalCount: 0,
      pending: true,
    },
  ],
  quickReliefNote:
    "Aida can suggest one-off exercises in chat when Layla flags she's struggling. These don't enter the weekly program unless you approve them.",
};

export const EXERCISE_LIBRARY: ExerciseLibraryItem[] = [
  { id: 'ex1', category: 'Breath', title: 'Coherent breath', meta: '6 breaths/min · 5 min' },
  { id: 'ex2', category: 'Breath', title: 'Alternate nostril', meta: '8 cycles · 4 min' },
  { id: 'ex3', category: 'Body', title: 'Progressive relax', meta: '12 min · audio' },
  { id: 'ex4', category: 'Body', title: 'Walking meditation', meta: '15 min · outside' },
  { id: 'ex5', category: 'Thinking', title: 'Worry window', meta: 'Daily · 10 min' },
  { id: 'ex6', category: 'Thinking', title: 'Thought record', meta: 'When triggered' },
  { id: 'ex7', category: 'Reflect', title: 'Gratitude prompt', meta: '3 lines · morning' },
];

export const CARE_PLAN_CATEGORY_STYLES: Record<CarePlanCategory, { bg: string; text: string }> = {
  Breath: { bg: 'bg-emerald-100', text: 'text-emerald-700' },
  Body: { bg: 'bg-rose-100', text: 'text-rose-700' },
  Thinking: { bg: 'bg-violet-100', text: 'text-violet-700' },
  Reflect: { bg: 'bg-amber-100', text: 'text-amber-700' },
  Diet: { bg: 'bg-orange-100', text: 'text-orange-700' },
  Sleep: { bg: 'bg-blue-100', text: 'text-blue-700' },
  Motivation: { bg: 'bg-pink-100', text: 'text-pink-700' },
};

// ——— Messages (T08) ———
export const MESSAGE_THREADS: MessageThread[] = [
  {
    id: 'th-layla',
    patientId: 'p-layla',
    patientName: 'Layla Siddiqui',
    patientInitials: 'LS',
    avatarColor: 'bg-amber-600',
    preview: 'Done — added a 4 PM nudge.',
    timeAgo: '2h',
    unreadCount: 0,
    online: true,
    lastSessionMeta: 'last session Fri · 5:00 PM',
    messages: [
      {
        id: 'm1',
        sender: 'patient',
        content: 'Hi Dr. Tariq — quick one. I kept forgetting the evening journal. Is it okay if I move it to mornings?',
        time: '7:42 AM',
        dateGroup: 'Tuesday · May 20',
      },
      {
        id: 'm2',
        sender: 'therapist',
        content: 'Try it for a week and we\'ll see what the data says. No "right" time — just the one you actually do.',
        time: '8:11 AM · seen',
        dateGroup: 'Tuesday · May 20',
      },
      {
        id: 'm3',
        sender: 'patient',
        content: "Three mornings done. It's stickier — I think because I'm not as tired.",
        time: '7:31 AM',
        dateGroup: 'Today',
      },
    ],
    aidaDraftReply: "Good — let's lock morning as the slot. I'll move it in your care plan.",
  },
  {
    id: 'th-bilal',
    patientId: 'p-bilal',
    patientName: 'Bilal Rauf',
    patientInitials: 'BR',
    avatarColor: 'bg-blue-950',
    preview: 'Doc, can we talk? Rough night.',
    timeAgo: '5h',
    unreadCount: 2,
    online: true,
    lastSessionMeta: 'last session Today · 5:00 PM',
    messages: [
      {
        id: 'm1',
        sender: 'patient',
        content: 'Doc, can we talk? Rough night.',
        time: '11:20 PM',
        dateGroup: 'Yesterday',
      },
    ],
  },
  {
    id: 'th-ammar',
    patientId: 'p-ammar',
    patientName: 'Ammar Sheikh',
    patientInitials: 'AS',
    avatarColor: 'bg-orange-600',
    preview: 'Walk did it. Sleeping at 11 tonight.',
    timeAgo: 'yest',
    unreadCount: 0,
    online: false,
    lastSessionMeta: 'last session 2d ago',
    messages: [
      { id: 'm1', sender: 'patient', content: 'Walk did it. Sleeping at 11 tonight.', time: 'Yesterday', dateGroup: 'Yesterday' },
    ],
  },
  {
    id: 'th-hira',
    patientId: 'p-hira',
    patientName: 'Hira Khan',
    patientInitials: 'HK',
    avatarColor: 'bg-emerald-700',
    preview: "Sharing partner's availability →",
    timeAgo: 'yest',
    unreadCount: 1,
    online: false,
    lastSessionMeta: 'last session 5d ago',
    messages: [
      { id: 'm1', sender: 'patient', content: "Sharing partner's availability for Tuesday's session.", time: 'Yesterday', dateGroup: 'Yesterday' },
    ],
  },
  {
    id: 'th-zoya',
    patientId: 'p-zoya',
    patientName: 'Zoya Iqbal',
    patientInitials: 'ZI',
    avatarColor: 'bg-blue-900',
    preview: 'Will try the morning journal swap',
    timeAgo: '2d',
    unreadCount: 0,
    online: false,
    lastSessionMeta: 'last session 3d ago',
    messages: [{ id: 'm1', sender: 'patient', content: 'Will try the morning journal swap.', time: '2d ago', dateGroup: '2 days ago' }],
  },
  {
    id: 'th-omar',
    patientId: 'p-omar',
    patientName: 'Omar Raza',
    patientInitials: 'OR',
    avatarColor: 'bg-rose-500',
    preview: 'Trial day 4 ✦ feeling lighter',
    timeAgo: '3d',
    unreadCount: 0,
    online: false,
    lastSessionMeta: 'last session 9d ago',
    messages: [{ id: 'm1', sender: 'patient', content: 'Trial day 4 — feeling lighter honestly.', time: '3d ago', dateGroup: '3 days ago' }],
  },
  {
    id: 'th-fatima',
    patientId: 'p-fatima',
    patientName: 'Fatima Aslam',
    patientInitials: 'FA',
    avatarColor: 'bg-amber-700',
    preview: 'Couples session brief attached',
    timeAgo: '5d',
    unreadCount: 0,
    online: false,
    lastSessionMeta: 'last session 4d ago',
    messages: [{ id: 'm1', sender: 'patient', content: 'Attached our couples session brief for Thursday.', time: '5d ago', dateGroup: '5 days ago' }],
  },
];

// ——— Weekly report (T07) ———
export const LAYLA_WEEKLY_REPORT: WeeklyReportData = {
  patientId: 'p-layla',
  patientName: 'Layla Siddiqui',
  weekRange: 'May 15 – May 21',
  weekLabel: 'Week 21',
  generatedDate: 'May 22',
  stats: [
    { label: 'Mood avg', value: '3.4 / 5', delta: '+0.6', meta: 'vs last week', deltaPositive: true },
    { label: 'Check-ins', value: '6 / 7', meta: 'missed Tuesday' },
    { label: 'Exercises', value: '11 / 19', meta: '58% of plan' },
    { label: 'Resting HR', value: '68 bpm', delta: '-4', meta: 'overnight median', deltaPositive: true },
  ],
  summaryTitle: 'A quieter week than last',
  summaryText:
    'Mood lifted on three of four days when Layla journaled in the evening. Sleep is the bright spot — six nights at or above 6h 30, the best stretch since onboarding.',
  moodDaily: [
    { day: 'Thu', value: 2.8 },
    { day: 'Fri', value: 3.2 },
    { day: 'Sat', value: 3.0 },
    { day: 'Sun', value: 3.6 },
    { day: 'Mon', value: 3.5 },
    { day: 'Tue', value: 2.9 },
    { day: 'Wed', value: 3.8 },
  ],
  sensorPatterns: [
    { label: 'Resting HR overnight', value: '64–72', meta: 'Trending down — good sign', trend: [72, 71, 70, 69, 68, 65, 64], color: '#f97316' },
    { label: 'Sleep duration', value: '6h 12 – 7h 04', meta: '+38 min on average', trend: [5.8, 6.0, 6.2, 6.4, 6.6, 6.9, 7.0], color: '#166534' },
    { label: 'EDA evening peaks', value: '2.1 µS avg', meta: 'Spikes Tue eve only', trend: [2.4, 2.3, 2.2, 2.1, 2.6, 2.0, 2.0], color: '#eab308' },
  ],
  keyInsights: [
    {
      id: 'ki1',
      tone: 'positive',
      title: 'Sunday journaling lifts Monday mood',
      description: 'Avg +0.6 the day after Sunday entries — keep it.',
    },
    {
      id: 'ki2',
      tone: 'warning',
      title: 'Tuesday review days are spike days',
      description: '3 of last 4 Tue eves show EDA peaks before sleep.',
    },
    {
      id: 'ki3',
      tone: 'negative',
      title: 'Skipped exercises cluster mid-week',
      description: 'Wed/Thu compliance 2/7 — possibly too dense.',
    },
  ],
  noteToPatient:
    "You showed up six days this week — and the body data is showing it. Let's leave Wed/Thu lighter and protect Sunday journaling. That's the lever right now.",
};

// ——— Profile & availability (T10) ———
const buildStandardAvailability = (): AvailabilitySlot[] => {
  const slots: AvailabilitySlot[] = [];
  const openDays = [0, 1, 2, 3, 4, 5, 6]; // Mon..Sun
  const tentHours = [10, 17];
  const openHours = [11, 12, 13, 14, 15];
  const blockedHour = 16;

  for (const day of openDays) {
    const isWeekend = day >= 5;
    if (!isWeekend) {
      tentHours.forEach((hour) => slots.push({ day, hour, status: 'tentative' }));
      openHours.forEach((hour) => slots.push({ day, hour, status: 'open' }));
      slots.push({ day, hour: blockedHour, status: 'blocked' });
      slots.push({ day, hour: 18, status: 'open' });
    } else {
      slots.push({ day, hour: 10, status: 'open' });
      slots.push({ day, hour: 18, status: 'open' });
    }
    slots.push({ day, hour: 9, status: 'closed' });
  }
  return slots;
};

export const THERAPIST_AVAILABILITY: AvailabilitySlot[] = buildStandardAvailability();
export const AVAILABILITY_HOURS = [9, 10, 11, 12, 13, 14, 15, 16, 17, 18];
export const PROFILE_TABS = ['Availability', 'Reviews', 'Earnings & wallet', 'Session logs', 'Credentials', 'Settings'] as const;

export const THERAPIST_PROFILE: TherapistProfileData = {
  name: 'Dr. Tariq Mahmood',
  title: 'Clinical psychologist',
  verifiedDate: 'May 26',
  license: 'PMDC #44-CP-3392',
  yearsExperience: 12,
  city: 'Lahore, PK',
  timezone: 'GMT+5',
  specialtyTags: ['Anxiety', 'Burnout'],
  approachTags: ['CBT', 'ACT'],
  acceptsTrials: true,
  inNetworkNote: 'In-network · all NGOs',
  languages: ['Urdu', 'English'],
  rating: 4.9,
  reviewCount: 218,
  walletBalance: 'Rs 184,500',
  walletDeltaVsLastMonth: '+12% vs Apr',
  sessionsBilled: 32,
  payoutDate: 'May 31',
  payoutAccount: 'HBL •••• 3412',
  ratingBreakdown: [
    { stars: 5, count: 186 },
    { stars: 4, count: 24 },
    { stars: 3, count: 6 },
    { stars: 2, count: 1 },
    { stars: 1, count: 1 },
  ],
  recentReviews: [
    {
      id: 'rev-1',
      initials: 'XW',
      color: 'bg-violet-600',
      handle: '@warm-thistle',
      rating: 5,
      timeAgo: '2d ago',
      content: "He listens like nobody is in a hurry. The panic loops have actually slowed down.",
    },
    {
      id: 'rev-2',
      initials: 'BR',
      color: 'bg-blue-950',
      handle: '@bilal.r',
      rating: 5,
      timeAgo: '6d ago',
      content: 'Practical, never preachy. Gave me something to try every single session.',
    },
    {
      id: 'rev-3',
      initials: 'FA',
      color: 'bg-amber-700',
      handle: '@fatima.a',
      rating: 4,
      timeAgo: '9d ago',
      content: 'Great with couples work. Wish sessions were a bit longer some weeks.',
    },
  ],
};

// ——— Circles / community (T11) ———
export const THERAPIST_CIRCLES: CircleSummary[] = [
  { id: 'c-anxiety', name: 'Anxiety', memberCount: 1247, role: 'Verified voice', color: 'bg-rose-400', unreadCount: 12 },
  { id: 'c-sober', name: 'Sober walk', memberCount: 231, role: 'Member', color: 'bg-emerald-600' },
  { id: 'c-parents', name: 'New parents', memberCount: 480, role: 'Host', color: 'bg-amber-500', unreadCount: 4 },
  { id: 'c-loss', name: 'After loss', memberCount: 189, role: 'Verified voice', color: 'bg-violet-500', unreadCount: 2 },
];

export const CIRCLES_TOTAL_AVAILABLE = 14;

export const CIRCLE_POSTS: CirclePost[] = [
  {
    id: 'post-1',
    authorHandle: '@warm-thistle',
    circleName: 'Anxiety',
    timeAgo: '2h ago',
    content:
      "Why does my chest tighten the moment my alarm goes off? It's like the day starts already disappointed in me. Is this anxiety or something else?",
    likes: 47,
    commentCount: 22,
    repostCount: 8,
    isAskingTherapist: true,
    authorInitial: 'W',
    authorColor: 'bg-violet-500',
    therapistReply: {
      content:
        "That morning tightness is really common — it's your body running tomorrow's worry on yesterday's fuel. One thing to try this week: before you reach for the phone, take three slow breaths and name one thing you're looking forward to today.",
      timeAgo: 'now',
      moderationClear: true,
    },
  },
];

export const CIRCLE_QUESTIONS_WAITING: CircleQuestionWaiting[] = [
  { id: 'q1', tag: 'Anxiety', timeAgo: '2h ago', question: 'Is racing thoughts at 4 AM a sleep problem or anxiety?' },
  { id: 'q2', tag: 'After loss', timeAgo: '5h ago', question: 'How long until grief stops feeling like fog?' },
  {
    id: 'q3',
    tag: 'Anxiety',
    timeAgo: '6h ago',
    question: 'Beta-blockers vs therapy for public speaking — what do you actually see work?',
  },
];

export const CIRCLE_STATS: CircleStats = {
  month: 'May',
  answers: 23,
  peopleHelped: 1400,
  helpfulRatePercent: 92,
  trialReferrals: 3,
};