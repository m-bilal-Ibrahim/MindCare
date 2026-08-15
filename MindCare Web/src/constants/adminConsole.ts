// ============================================================
// MindCare — Admin Console Mock Data
//
// All data below is fictional dummy data for reviewing the UI
// flow end-to-end. Nothing here represents real people or orgs.
// ============================================================

import type {
  AdminNavItem,
  PlatformStat,
  GrowthPoint,
  QueuePreviewItem,
  VerificationQueueItem,
  TherapistVerificationDetail,
  NgoVerificationDetail,
  PlatformUser,
  UsersSummary,
  ModerationCaseSummary,
  ModerationCaseDetail,
  ModerationSummary,
  SosEventSummary,
  SosCaseDetail,
  SafetyStats,
  TherapistDirectoryEntry,
  TherapistDirectorySummary,
  NgoPartnerCard,
  NgoPartnersSummary,
  SosRoutingStep,
  PartnerOnboardingSummary,
  BillingStats,
  RevenueMonthPoint,
  PaymentMethodShare,
  TransactionEntry,
  RefundQueueItem,
} from '../types/adminConsole';

// ——— Routes ———
export const ADMIN_ROUTES = {
  SIGN_IN: '/admin/sign-in',
  OVERVIEW: '/admin/overview',
  VERIFICATIONS: '/admin/verifications',
  THERAPISTS: '/admin/therapists',
  USERS: '/admin/users',
  MODERATION: '/admin/moderation',
  SAFETY: '/admin/safety',
  NGO_PARTNERS: '/admin/ngo-partners',
  BILLING: '/admin/billing',
  SETTINGS: '/admin/settings',
} as const;

// ——— Sidebar navigation ———
export const ADMIN_NAV_OPERATIONS: AdminNavItem[] = [
  { id: 'overview', label: 'Overview', route: ADMIN_ROUTES.OVERVIEW, icon: 'home' },
  { id: 'verifications', label: 'Verifications', route: ADMIN_ROUTES.VERIFICATIONS, icon: 'shield', badge: 7 },
  { id: 'therapists', label: 'Therapists', route: ADMIN_ROUTES.THERAPISTS, icon: 'code' },
  { id: 'users', label: 'Users', route: ADMIN_ROUTES.USERS, icon: 'users' },
];

export const ADMIN_NAV_TRUST_SAFETY: AdminNavItem[] = [
  { id: 'moderation', label: 'Moderation', route: ADMIN_ROUTES.MODERATION, icon: 'flag', badge: 12 },
  { id: 'safety-sos', label: 'Safety / SOS', route: ADMIN_ROUTES.SAFETY, icon: 'alert-triangle' },
  { id: 'ngo-partners', label: 'NGO partners', route: ADMIN_ROUTES.NGO_PARTNERS, icon: 'heart' },
];

export const ADMIN_NAV_PLATFORM: AdminNavItem[] = [
  { id: 'billing', label: 'Billing', route: ADMIN_ROUTES.BILLING, icon: 'file' },
  { id: 'settings', label: 'Settings', route: ADMIN_ROUTES.SETTINGS, icon: 'sun' },
];

// ——— Overview (A01) ———
export const PLATFORM_STATS: PlatformStat[] = [
  { label: 'Active users', value: '12,408', delta: '+3.2%', meta: 'weekly active', trend: [9800, 10200, 10900, 11400, 11900, 12100, 12408], trendColor: 'green' },
  { label: 'Therapists', value: '184', delta: '+6', meta: '9 verifying', trend: [150, 158, 164, 170, 176, 180, 184], trendColor: 'neutral' },
  { label: 'Sessions · 7d', value: '2,876', delta: '+11%', meta: '92% completed', trend: [2100, 2300, 2450, 2550, 2700, 2800, 2876], trendColor: 'red' },
  { label: 'MRR', value: 'Rs 9.4M', delta: '+4.6%', meta: 'of Rs 10M target', trend: [7.8, 8.1, 8.4, 8.7, 9.0, 9.2, 9.4], trendColor: 'gold' },
  { label: 'SOS · 30d', value: '14', delta: '', meta: 'all resolved · avg 4.2 min', trend: [3, 1, 4, 2, 1, 3, 0], trendColor: 'red' },
];

export const GROWTH_CHART_DATA: GrowthPoint[] = [
  { label: 'Feb 21', activeUsers: 7.8, sessions: 14 },
  { label: 'Feb 28', activeUsers: 8.1, sessions: 15 },
  { label: 'Mar 7', activeUsers: 8.4, sessions: 16.5 },
  { label: 'Mar 14', activeUsers: 8.7, sessions: 17.5 },
  { label: 'Mar 21', activeUsers: 9.0, sessions: 18.5 },
  { label: 'Mar 28', activeUsers: 9.3, sessions: 19.5 },
  { label: 'Apr 6', activeUsers: 9.7, sessions: 20.5 },
  { label: 'Apr 13', activeUsers: 10.1, sessions: 21.8 },
  { label: 'Apr 20', activeUsers: 10.5, sessions: 22.8 },
  { label: 'Apr 27', activeUsers: 10.9, sessions: 24.0 },
  { label: 'May 4', activeUsers: 11.3, sessions: 25.2 },
  { label: 'May 11', activeUsers: 11.8, sessions: 26.5 },
  { label: 'May 21', activeUsers: 12.4, sessions: 28.76 },
];

export const RETENTION_WEEK4 = '71%';

export const VERIFICATION_QUEUE_PREVIEW: QueuePreviewItem[] = [
  { id: 'q-saima', name: 'Dr. Saima Hashmi', initials: 'DS', avatarColor: 'bg-blue-950', meta: 'PMDC verified · awaiting cert review', statusTag: 'Review', statusTone: 'default', timeAgo: '12 min ago' },
  { id: 'q-faisal', name: 'Dr. Faisal Mehmood', initials: 'DF', avatarColor: 'bg-emerald-700', meta: 'Documents uploaded', statusTag: 'New', statusTone: 'new', timeAgo: '1h ago' },
  { id: 'q-nida', name: 'Dr. Nida Tariq', initials: 'DN', avatarColor: 'bg-amber-600', meta: 'License expired — flagged', statusTag: 'Flag', statusTone: 'flag', timeAgo: '3h ago' },
  { id: 'q-hamza', name: 'Dr. Hamza Sheikh', initials: 'DH', avatarColor: 'bg-blue-900', meta: 'Background check pending', statusTag: 'Wait', statusTone: 'wait', timeAgo: '5h ago' },
];

export const SAFETY_LAST_24H = { resolved: 3, avgResponseMin: 4.2 };
export const MODERATION_QUEUE_OPEN = 12;
export const COMMUNITY_TOP_CIRCLES = ['Anxiety', 'Sober walk', 'New parents'];

// ——— Verifications (A02 / A02b) ———
export const VERIFICATION_QUEUE_SUMMARY = { therapists: 7, ngoPartners: 2, hospitalPartners: 1 };

export const THERAPIST_VERIFICATION_QUEUE: VerificationQueueItem[] = [
  { id: 'q-saima', type: 'therapist', name: 'Dr. Saima Hashmi', initials: 'SH', avatarColor: 'bg-blue-900', submittedAgo: '2 days waiting', statusTag: 'Review', statusTone: 'default' },
  { id: 'q-faisal', type: 'therapist', name: 'Dr. Faisal Mehmood', initials: 'FM', avatarColor: 'bg-emerald-700', submittedAgo: '1h ago', statusTag: 'New', statusTone: 'new' },
  { id: 'q-nida', type: 'therapist', name: 'Dr. Nida Tariq', initials: 'NT', avatarColor: 'bg-amber-600', submittedAgo: '3h ago', statusTag: 'Flag', statusTone: 'flag' },
  { id: 'q-hamza', type: 'therapist', name: 'Dr. Hamza Sheikh', initials: 'HS', avatarColor: 'bg-blue-950', submittedAgo: '5h ago', statusTag: 'Wait', statusTone: 'wait' },
  { id: 'q-ayaan', type: 'therapist', name: 'Dr. Ayaan Qureshi', initials: 'AQ', avatarColor: 'bg-rose-500', submittedAgo: '1 day waiting', statusTag: 'New', statusTone: 'new' },
  { id: 'q-zainab', type: 'therapist', name: 'Dr. Zainab Chaudhry', initials: 'ZC', avatarColor: 'bg-violet-500', submittedAgo: '2 days waiting', statusTag: 'Wait', statusTone: 'wait' },
  { id: 'q-imran', type: 'therapist', name: 'Dr. Imran Baig', initials: 'IB', avatarColor: 'bg-amber-700', submittedAgo: '4 days waiting', statusTag: 'Review', statusTone: 'default' },
];

export const NGO_VERIFICATION_QUEUE: VerificationQueueItem[] = [
  { id: 'q-therapyworks', type: 'ngo', name: 'Therapy Works', initials: 'TW', avatarColor: 'bg-rose-500', submittedAgo: '6 days waiting', statusTag: 'Review', statusTone: 'default' },
  { id: 'q-sukoon', type: 'ngo', name: 'Sukoon Foundation', initials: 'SF', avatarColor: 'bg-emerald-700', submittedAgo: '2 days waiting', statusTag: 'New', statusTone: 'new' },
];

export const HOSPITAL_VERIFICATION_QUEUE: VerificationQueueItem[] = [
  { id: 'q-shifa', type: 'hospital', name: 'Shifa Wellness Wing', initials: 'SW', avatarColor: 'bg-blue-900', submittedAgo: '3 days waiting', statusTag: 'Wait', statusTone: 'wait' },
];

export const THERAPIST_VERIFICATION_DETAILS: Record<string, TherapistVerificationDetail> = {
  'q-saima': {
    applicationId: '#MC-T-0931',
    queueItemId: 'q-saima',
    name: 'Dr. Saima Hashmi',
    initials: 'SH',
    avatarColor: 'bg-blue-900',
    submittedDate: 'May 19',
    waitingDays: 2,
    specialtyTags: ['Trauma · EMDR', 'Anxiety', 'Couples'],
    languages: 'Urdu · English',
    city: 'Lahore, PK',
    phoneMasked: '+92 333 ••• ••••',
    emailMasked: 's.hashmi@gmail.com',
    credentialSummary: 'Clinical psychologist · MS Clinical Psychology, FJWU · 11 yrs practice',
    riskScore: 9.2,
    riskLabel: 'Low risk profile.',
    riskDescription: 'Documents authentic, no public flags, identity matches across sources.',
    identityMatchSources: '4/4 sources',
    sanctionsStatus: 'OFAC/PEP clean',
    publicReviewsNote: 'Avg 4.7 across 2 sources',
    imageAuthenticityNote: '1 cert needs human eye',
    checksComplete: 4,
    checksTotal: 4,
    checks: [
      { id: 'c1', label: 'PMDC license', meta: '102-CP-44871 · Verified · valid through Aug 2027', status: 'verified' },
      { id: 'c2', label: 'MS Clinical Psychology', meta: 'FJWU · 2014 · Degree verified via HEC API', status: 'verified' },
      { id: 'c3', label: 'CBT certification', meta: 'Beck Institute · Auto-verified', status: 'verified' },
      { id: 'c4', label: 'EMDR training', meta: 'EMDR Asia · 2019 · Cert image uploaded · needs eye', status: 'needs-review' },
      { id: 'c5', label: 'Background check', meta: 'Cleared by Verisys · May 21 · No flags', status: 'verified' },
    ],
    timeline: [
      { time: 'May 19, 14:02', label: 'Application submitted' },
      { time: 'May 19, 14:08', label: 'Auto-checks queued (Verisys + HEC + PMDC)' },
      { time: 'May 20, 09:15', label: 'Auto-checks complete — 4 of 4 passed' },
      { time: 'May 21, 10:30', label: 'Flagged for human review — 1 cert needs eye check' },
    ],
  },
  'q-faisal': {
    applicationId: '#MC-T-0932',
    queueItemId: 'q-faisal',
    name: 'Dr. Faisal Mehmood',
    initials: 'FM',
    avatarColor: 'bg-emerald-700',
    submittedDate: 'May 20',
    waitingDays: 1,
    specialtyTags: ['Addiction', 'Recovery'],
    languages: 'Urdu · English',
    city: 'Karachi, PK',
    phoneMasked: '+92 321 ••• ••••',
    emailMasked: 'f.mehmood@outlook.com',
    credentialSummary: 'Psychiatrist · MBBS, MD Psychiatry · 8 yrs practice',
    riskScore: 8.6,
    riskLabel: 'Low risk profile.',
    riskDescription: 'Documents uploaded, auto-checks still running.',
    identityMatchSources: '3/4 sources',
    sanctionsStatus: 'OFAC/PEP clean',
    publicReviewsNote: 'No public reviews yet',
    imageAuthenticityNote: 'Pending review',
    checksComplete: 2,
    checksTotal: 4,
    checks: [
      { id: 'c1', label: 'PMDC license', meta: '210-PSY-88231 · Verifying with PMDC.gov.pk', status: 'pending' },
      { id: 'c2', label: 'MD Psychiatry', meta: 'Dow University · 2016 · Degree verified via HEC API', status: 'verified' },
      { id: 'c3', label: 'Addiction medicine certificate', meta: 'Uploaded · awaiting review', status: 'needs-review' },
      { id: 'c4', label: 'Background check', meta: 'Queued with Verisys', status: 'pending' },
    ],
    timeline: [
      { time: 'May 20, 11:20', label: 'Application submitted' },
      { time: 'May 20, 11:25', label: 'Auto-checks queued' },
    ],
  },
  'q-nida': {
    applicationId: '#MC-T-0928',
    queueItemId: 'q-nida',
    name: 'Dr. Nida Tariq',
    initials: 'NT',
    avatarColor: 'bg-amber-600',
    submittedDate: 'May 17',
    waitingDays: 4,
    specialtyTags: ['Family', 'Grief'],
    languages: 'Urdu · English',
    city: 'Islamabad, PK',
    phoneMasked: '+92 300 ••• ••••',
    emailMasked: 'n.tariq@yahoo.com',
    credentialSummary: 'Counselling psychologist · MS Counselling · 6 yrs practice',
    riskScore: 4.1,
    riskLabel: 'Needs review.',
    riskDescription: 'PMDC license shows as expired against the registry — requires clarification before approval.',
    identityMatchSources: '4/4 sources',
    sanctionsStatus: 'OFAC/PEP clean',
    publicReviewsNote: 'Avg 4.5 across 1 source',
    imageAuthenticityNote: 'Clear',
    checksComplete: 2,
    checksTotal: 4,
    checks: [
      { id: 'c1', label: 'PMDC license', meta: '188-CP-33021 · Expired Jan 2026 — flagged', status: 'needs-review' },
      { id: 'c2', label: 'MS Counselling Psychology', meta: 'Punjab University · 2018 · Verified via HEC API', status: 'verified' },
      { id: 'c3', label: 'Grief counselling certificate', meta: 'Auto-verified', status: 'verified' },
      { id: 'c4', label: 'Background check', meta: 'Cleared by Verisys · No flags', status: 'verified' },
    ],
    timeline: [
      { time: 'May 17, 09:40', label: 'Application submitted' },
      { time: 'May 17, 16:00', label: 'Auto-checks complete' },
      { time: 'May 18, 08:00', label: 'PMDC license flagged as expired' },
    ],
  },
  'q-hamza': {
    applicationId: '#MC-T-0935',
    queueItemId: 'q-hamza',
    name: 'Dr. Hamza Sheikh',
    initials: 'HS',
    avatarColor: 'bg-blue-950',
    submittedDate: 'May 21',
    waitingDays: 0,
    specialtyTags: ['Anxiety', 'Sleep'],
    languages: 'Urdu · English',
    city: 'Multan, PK',
    phoneMasked: '+92 345 ••• ••••',
    emailMasked: 'h.sheikh@gmail.com',
    credentialSummary: 'Clinical psychologist · MS Clinical Psychology · 5 yrs practice',
    riskScore: 7.8,
    riskLabel: 'Low risk profile.',
    riskDescription: 'Documents authentic, background check still in progress.',
    identityMatchSources: '4/4 sources',
    sanctionsStatus: 'Pending',
    publicReviewsNote: 'Avg 4.8 across 1 source',
    imageAuthenticityNote: 'Clear',
    checksComplete: 3,
    checksTotal: 4,
    checks: [
      { id: 'c1', label: 'PMDC license', meta: '244-CP-51092 · Verified · valid through 2028', status: 'verified' },
      { id: 'c2', label: 'MS Clinical Psychology', meta: 'Bahauddin Zakariya University · 2019 · Verified', status: 'verified' },
      { id: 'c3', label: 'Sleep medicine module', meta: 'Auto-verified', status: 'verified' },
      { id: 'c4', label: 'Background check', meta: 'Submitted to Verisys · pending', status: 'pending' },
    ],
    timeline: [
      { time: 'May 21, 08:00', label: 'Application submitted' },
      { time: 'May 21, 08:10', label: 'Auto-checks queued' },
    ],
  },
};

export const NGO_VERIFICATION_DETAILS: Record<string, NgoVerificationDetail> = {
  'q-therapyworks': {
    applicationId: '#MC-N-0118',
    queueItemId: 'q-therapyworks',
    name: 'Therapy Works',
    initials: 'TW',
    avatarColor: 'bg-rose-500',
    submittedDate: 'May 14',
    waitingDays: 6,
    summary: 'Sliding-scale community clinic · Karachi · est. 2014 · 11 in-house therapists',
    address: 'F-7/3, Block 4 · Clifton',
    phoneMasked: '+92 21 3589 ••••',
    emailMasked: 'partners@therapyworks.com.pk',
    ntn: '4001294-7',
    tags: ['Sliding-scale clinic', 'Karachi', 'Walk-in + appointment'],
    languages: 'Urdu · English',
    slaCommitment: {
      pickupTimeBusiness: '< 3 min · business hours',
      pickupTimeAfterHours: '< 15 min · after hours',
      closedLoopReport: 'within 24h',
      closedLoopReportWeekend: 'within 48h on weekends',
      reroutingWindow: '90s if no pick-up',
      annualDrill: '1 mock case per quarter',
    },
    checksComplete: 5,
    checksTotal: 7,
    checks: [
      { id: 'c1', label: 'Legal registration', meta: 'SECP · NPO #41-K · Verified · NPO valid through 2028', status: 'verified' },
      { id: 'c2', label: 'NTN / tax exemption', meta: '4001294-7 · FBR verified · Section 2(36) tax-exempt', status: 'verified' },
      { id: 'c3', label: 'MOU signed', meta: 'v3 · May 18, 2026 · Both signatures on file · 36-month term', status: 'verified' },
      { id: 'c4', label: 'Liability insurance', meta: 'EFU Life · Rs 5M · Cover valid through 2027', status: 'verified' },
      { id: 'c5', label: 'Helpline staff list', meta: 'Awaiting CNICs for Hina & Ayaan', status: 'needs-review' },
      { id: 'c6', label: 'Crisis protocol review', meta: 'Submitted · pending admin sign-off', status: 'pending' },
      { id: 'c7', label: 'Annual drill scheduling', meta: 'Drill date not yet confirmed', status: 'pending' },
    ],
  },
  'q-sukoon': {
    applicationId: '#MC-N-0121',
    queueItemId: 'q-sukoon',
    name: 'Sukoon Foundation',
    initials: 'SF',
    avatarColor: 'bg-emerald-700',
    submittedDate: 'May 19',
    waitingDays: 2,
    summary: 'Free helpline & referral network · Lahore · est. 2019 · volunteer-run',
    address: 'Gulberg III, Block C',
    phoneMasked: '+92 42 3571 ••••',
    emailMasked: 'contact@sukoonfoundation.org',
    ntn: '3987211-2',
    tags: ['Helpline · 24/7', 'Lahore', 'Volunteer network'],
    languages: 'Urdu · English · Punjabi',
    slaCommitment: {
      pickupTimeBusiness: '< 2 min · all hours',
      pickupTimeAfterHours: '< 2 min · all hours',
      closedLoopReport: 'within 24h',
      closedLoopReportWeekend: 'within 24h',
      reroutingWindow: '60s if no pick-up',
      annualDrill: 'Not yet scheduled',
    },
    checksComplete: 3,
    checksTotal: 7,
    checks: [
      { id: 'c1', label: 'Legal registration', meta: 'SECP · NPO #52-L · Verified', status: 'verified' },
      { id: 'c2', label: 'NTN / tax exemption', meta: '3987211-2 · FBR verification in progress', status: 'pending' },
      { id: 'c3', label: 'MOU signed', meta: 'Draft sent · awaiting signature', status: 'needs-review' },
      { id: 'c4', label: 'Liability insurance', meta: 'Not yet submitted', status: 'pending' },
      { id: 'c5', label: 'Helpline staff list', meta: 'Submitted · CNICs verified', status: 'verified' },
      { id: 'c6', label: 'Crisis protocol review', meta: 'Approved', status: 'verified' },
      { id: 'c7', label: 'Annual drill scheduling', meta: 'Not yet scheduled', status: 'pending' },
    ],
  },
};

// ——— Users (A03) ———
export const USERS_SUMMARY: UsersSummary = {
  active: 12408,
  trialsThisMonth: 1204,
  pausedOrRefund: 84,
  activeCount: 11120,
  trialCount: 1204,
  pausedCount: 84,
  hasFlagsCount: 38,
  refundPendingCount: 7,
  wearableIssuesCount: 12,
};

export const PLATFORM_USERS: PlatformUser[] = [
  { id: 'u-layla', initials: 'LS', avatarColor: 'bg-amber-600', name: 'Layla Siddiqui', emailMasked: 'l.siddiqui@•••.com', city: 'Islamabad', plan: 'Monthly', therapistName: 'Dr. Tariq', joined: 'Feb 26', status: 'Active' },
  { id: 'u-ammar', initials: 'AS', avatarColor: 'bg-orange-600', name: 'Ammar Sheikh', emailMasked: 'ammar.s@gmail.com', city: 'Karachi', plan: 'Yearly', therapistName: 'Dr. Tariq', joined: 'Jan 26', status: 'Active' },
  { id: 'u-hira', initials: 'HK', avatarColor: 'bg-emerald-700', name: 'Hira Khan', emailMasked: 'hk@protonmail.com', city: 'Lahore', plan: 'Monthly', therapistName: 'Dr. Tariq', joined: 'May 26', status: 'Trial' },
  { id: 'u-zoya', initials: 'ZI', avatarColor: 'bg-blue-900', name: 'Zoya Iqbal', emailMasked: 'z.iqbal@me.com', city: 'Islamabad', plan: 'Monthly', therapistName: 'Dr. Tariq', joined: 'Mar 26', status: 'Active', flag: 'support' },
  { id: 'u-omar', initials: 'OR', avatarColor: 'bg-rose-500', name: 'Omar Raza', emailMasked: 'o.raza@gmail.com', city: 'Lahore', plan: 'Yearly', therapistName: 'Dr. Tariq', joined: 'Apr 26', status: 'Active' },
  { id: 'u-sana', initials: 'SY', avatarColor: 'bg-emerald-800', name: 'Sana Yousaf', emailMasked: 's.yousaf@hotmail', city: 'Karachi', plan: 'Monthly', therapistName: null, joined: 'Feb 26', status: 'Paused', flag: 'refund' },
  { id: 'u-bilal', initials: 'BR', avatarColor: 'bg-blue-950', name: 'Bilal Rauf', emailMasked: 'b.rauf@gmail.com', city: 'Multan', plan: 'Yearly', therapistName: 'Dr. Tariq', joined: 'Dec 25', status: 'Active', flag: 'sensor' },
  { id: 'u-fatima', initials: 'FA', avatarColor: 'bg-amber-700', name: 'Fatima Aslam', emailMasked: 'fa.couples@gmail', city: 'Islamabad', plan: 'Monthly', therapistName: 'Dr. Sana', joined: 'Mar 26', status: 'Active' },
  { id: 'u-ahmed', initials: 'AW', avatarColor: 'bg-violet-500', name: 'Ahmed Wali', emailMasked: 'a.wali@gmail.com', city: 'Faisalabad', plan: 'Trial', therapistName: null, joined: 'May 25', status: 'Onboarding' },
];

// ——— Moderation (A04) ———
export const MODERATION_SUMMARY: ModerationSummary = { open: 12, highSeverity: 4, closedThisWeek: 38, autoFlagPercent: 73 };

export const MODERATION_QUEUE: ModerationCaseSummary[] = [
  { id: 'mod-1', severity: 'high', category: 'Post', context: 'Anxiety', title: 'Medical advice · reported ×3', preview: 'I take 200mg twice a day, you should too. Doctors …' },
  { id: 'mod-2', severity: 'high', category: 'User', context: '—', title: 'Repeated flags across 3 circles', preview: 'Account flagged 4× in 14 days. Multiple users repo…' },
  { id: 'mod-3', severity: 'med', category: 'Photo', context: 'New parents', title: 'Auto-flag · likely face / PII', preview: 'Photo upload contains a recognizable face — circl…' },
  { id: 'mod-4', severity: 'med', category: 'Listener', context: 'Peer talk', title: 'Listener went off-script', preview: 'Have you tried God? My pastor helped me a lot, yo…' },
  { id: 'mod-5', severity: 'high', category: 'Post', context: 'After loss', title: 'Self-harm mention · auto-flag', preview: 'Some days I think it would be easier to just stop.' },
  { id: 'mod-6', severity: 'low', category: 'Post', context: 'Couples', title: 'Off-topic spam', preview: 'Selling unused therapy sessions DM me' },
];

export const MODERATION_CASE_DETAIL: ModerationCaseDetail = {
  id: 'mod-1',
  severity: 'high',
  category: 'Post',
  context: 'Anxiety circle',
  title: 'Medical advice in a peer post',
  reportedContent: "I take 200mg twice a day, you should too. Doctors don't know, this is what works.",
  replies: 47,
  likes: 22,
  postedAgo: '2h ago',
  authorHandle: '@warm-thistle',
  authorInitial: 'W',
  authorColor: 'bg-violet-500',
  authorMemberSince: '4 months',
  authorPostCount: 88,
  authorPriorWarns: 1,
  reportedByCount: 3,
  reporters: [
    { handle: '@quiet-river', initials: 'XQ', avatarColor: 'bg-orange-500', reason: 'Dangerous medical advice', timeAgo: '12m ago' },
    { handle: '@late-march', initials: 'XL', avatarColor: 'bg-blue-900', reason: 'Could trigger self-harm', timeAgo: '38m ago' },
    { handle: '@open-window', initials: 'XO', avatarColor: 'bg-orange-500', reason: 'Not a doctor', timeAgo: '1h ago' },
  ],
  authorHistory: [{ date: 'Mar 12', label: 'soft-warn · off-topic in Sober walk. Otherwise positive contributor.' }],
  messageTemplate:
    "Hi — we removed a post because medical dosing advice from peers isn't allowed here. The community is for stories and support, not prescriptions. Read the guideline →",
};

// ——— Safety / SOS (A05) ———
export const SAFETY_STATS: SafetyStats = {
  sosCount30d: 14,
  delta30d: -3,
  avgResponse: '4:12',
  hospitalEscalations: 1,
  hospitalEscalationMeta: 'May 18 · Lahore',
  falsePositives: 2,
  falsePositivesPercent: 14,
};

export const SOS_EVENTS: SosEventSummary[] = [
  { id: 'sos-1', caseCode: 'MC-SOS-0231', anonId: 'anon-71f8', realNameHint: 'Layla S.', city: 'Islamabad', timeLabel: 'Today · 14:22', triggerType: 'user-initiated', triggerLabel: 'User-initiated · SOS button (Pulse screen)', durationLabel: '4 min 12s', status: 'resolved' },
  { id: 'sos-2', caseCode: 'MC-SOS-0230', anonId: 'anon-2a3c', city: 'Lahore', timeLabel: 'Today · 03:08', triggerType: 'aida-detected', triggerLabel: 'Aida detection · keyword + EDA spike', durationLabel: '6 min 41s', status: 'resolved' },
  { id: 'sos-3', caseCode: 'MC-SOS-0229', anonId: 'anon-9012', city: 'Karachi', timeLabel: 'Yest · 21:14', triggerType: 'sensor-flag', triggerLabel: 'Sensor flag · resolved by check-in', durationLabel: '3 min 02s', status: 'resolved-false-positive' },
  { id: 'sos-4', caseCode: 'MC-SOS-0228', anonId: 'anon-44e1', city: 'Multan', timeLabel: 'May 19 · 11:50', triggerType: 'user-initiated', triggerLabel: 'User-initiated', durationLabel: '5 min 37s', status: 'resolved' },
];

export const SOS_CASE_DETAIL: SosCaseDetail = {
  caseCode: 'MC-SOS-0231',
  openedLabel: 'Today · 14:22',
  resolvedInLabel: '4:12',
  description:
    'User pressed SOS from the Pulse screen during work hours. EDA had been climbing for 30 min. Aida went into crisis mode within 3 seconds.',
  region: 'Islamabad',
  triggerLabel: 'User · button',
  responder: 'Umang helpline',
  handoffTo: 'Dr. Tariq',
  timeline: [
    { time: '14:22:08', label: 'SOS triggered' },
    { time: '14:22:11', label: 'Aida crisis mode engaged · grounding script' },
    { time: '14:23:40', label: 'Umang helpline auto-dialed' },
    { time: '14:24:01', label: 'Therapist Dr. Tariq notified' },
    { time: '14:24:18', label: 'Helpline answered · user transferred' },
    { time: '14:26:20', label: 'Resolved · user safe at home' },
  ],
};

// ——— Therapists directory (A06) ———
export const THERAPIST_DIRECTORY_SUMMARY: TherapistDirectorySummary = {
  totalCount: 196,
  activeCount: 184,
  onboardingCount: 7,
  pausedCount: 3,
  flaggedCount: 2,
  activeCountDelta: '+6 this month',
  avgPatientsPerTx: 17,
  avgPatientsDelta: '+1',
  avgRating: 4.8,
  avgCompliance: 86,
};

export const THERAPIST_DIRECTORY: TherapistDirectoryEntry[] = [
  { id: 'dir-1', initials: 'DT', avatarColor: 'bg-orange-600', name: 'Dr. Tariq Mahmood', specialty: 'Anxiety · Burnout · CBT', city: 'Lahore', patients: 32, mrrContrib: 'Rs 184k', rating: 4.9, compliance: 92, status: 'Active' },
  { id: 'dir-2', initials: 'DS', avatarColor: 'bg-violet-600', name: 'Dr. Sana Yousaf', specialty: 'Depression · Grief', city: 'Karachi', patients: 28, mrrContrib: 'Rs 162k', rating: 4.8, compliance: 89, status: 'Active' },
  { id: 'dir-3', initials: 'HK', avatarColor: 'bg-emerald-700', name: 'Hira Khan, MSc', specialty: 'Couples · Family', city: 'Lahore', patients: 18, mrrContrib: 'Rs 96k', rating: 4.7, compliance: 95, status: 'Active' },
  { id: 'dir-4', initials: 'DO', avatarColor: 'bg-emerald-800', name: 'Dr. Omar Raza', specialty: 'Addiction · Recovery', city: 'Islamabad', patients: 22, mrrContrib: 'Rs 138k', rating: 4.8, compliance: 88, status: 'Active' },
  { id: 'dir-5', initials: 'DS2', avatarColor: 'bg-blue-900', name: 'Dr. Saima Hashmi', specialty: 'Trauma · EMDR', city: 'Lahore', patients: null, mrrContrib: null, rating: null, compliance: null, status: 'Onboarding' },
  { id: 'dir-6', initials: 'DN', avatarColor: 'bg-amber-600', name: 'Dr. Nida Tariq', specialty: 'Anxiety · Sleep', city: 'Karachi', patients: 14, mrrContrib: 'Rs 72k', rating: 4.6, compliance: 78, status: 'Flagged', warning: 'License expired' },
  { id: 'dir-7', initials: 'DF', avatarColor: 'bg-rose-500', name: 'Dr. Faisal Mehmood', specialty: 'Adolescent · ADHD', city: 'Multan', patients: null, mrrContrib: null, rating: null, compliance: null, status: 'Pending verify' },
];

// ——— NGO partners (A07) ———
export const NGO_PARTNERS_SUMMARY: NgoPartnersSummary = { activePartners: 5, ytdRouted: 2054, closedLoopPercent: 100 };

export const NGO_PARTNER_CARDS: NgoPartnerCard[] = [
  { id: 'p-umang', initials: 'UH', avatarColor: 'bg-orange-500', name: 'Umang Helpline', status: 'Active', typeLine: 'Helpline · 24/7 · Nationwide · Urdu/English', pickupSla: '< 90s', ytdRouted: 1240, slaHitPercent: 94, email: 'helpline@umang.com.pk', phone: '0311-7786264' },
  { id: 'p-rozan', initials: 'R', avatarColor: 'bg-emerald-700', name: 'Rozan', status: 'Active', typeLine: 'Counselling · referral · Islamabad, Rawalpindi', pickupSla: '< 5 min', ytdRouted: 412, slaHitPercent: 88, email: 'info@rozan.org', phone: '051-2890505' },
  { id: 'p-karwan', initials: 'K', avatarColor: 'bg-violet-500', name: 'Karwan-e-Hayat', status: 'Active', typeLine: 'Hospital partner · Karachi', pickupSla: '< 15 min', ytdRouted: 86, slaHitPercent: 91, email: 'admin@kehayat.org', phone: '021-3637-3737' },
  { id: 'p-taskeen', initials: 'T', avatarColor: 'bg-amber-600', name: 'Taskeen', status: 'Active', typeLine: 'Helpline · 12h · Lahore, Faisalabad', pickupSla: '< 3 min', ytdRouted: 268, slaHitPercent: 82, email: 'reach@taskeen.org', phone: '0316-8275336' },
];

export const SOS_ROUTING_TREE: SosRoutingStep[] = [
  { id: 'r1', label: 'SOS triggered (user or Aida)', tone: 'critical', indent: 0 },
  { id: 'r2', label: 'Aida crisis-mode engaged · grounding script · 8s', tone: 'neutral', indent: 1 },
  { id: 'r3', label: 'Identify region from device + profile', tone: 'neutral', indent: 1 },
  { id: 'r4', label: 'If suicidal language → call Umang directly (24/7)', tone: 'critical', indent: 2 },
  { id: 'r5', label: 'Else → primary NGO for that region', tone: 'neutral', indent: 2 },
];

export const NGO_PARTNER_ONBOARDING: PartnerOnboardingSummary = {
  name: 'Therapy Works',
  meta: 'Submitted May 14 · sliding-scale clinic · Karachi',
  checklist: [
    { label: 'MOU signed', meta: 'May 18', done: true },
    { label: 'Insurance cover', meta: 'Rs 5M cover · expires 2027', done: true },
    { label: 'Helpline staff list', meta: '4 listed · 2 verified', done: true },
  ],
};

// ——— Billing (A08) ———
export const BILLING_STATS: BillingStats = {
  grossMrr: 'Rs 9.4M',
  grossMrrDelta: '+4.6%',
  grossMrrPrevMonth: 'Rs 8.98M',
  therapistPayout: 'Rs 6.8M',
  revSharePercent: 72,
  refunds: 'Rs 184k',
  refundsDelta: '+12%',
  refundsPercentOfGross: 1.9,
  churn: 3.8,
  churnDelta: -0.4,
  trialToPaidPercent: 41,
};

export const REVENUE_MONTHS: RevenueMonthPoint[] = [
  { label: 'J', mrr: 6.1, payouts: 4.2, refunds: 0.08 },
  { label: 'J', mrr: 6.5, payouts: 4.5, refunds: 0.09 },
  { label: 'A', mrr: 6.9, payouts: 4.8, refunds: 0.1 },
  { label: 'S', mrr: 7.2, payouts: 5.0, refunds: 0.11 },
  { label: 'O', mrr: 7.1, payouts: 4.9, refunds: 0.12 },
  { label: 'N', mrr: 7.5, payouts: 5.2, refunds: 0.11 },
  { label: 'D', mrr: 7.7, payouts: 5.4, refunds: 0.13 },
  { label: 'J', mrr: 8.0, payouts: 5.6, refunds: 0.14 },
  { label: 'F', mrr: 8.3, payouts: 5.9, refunds: 0.13 },
  { label: 'M', mrr: 8.6, payouts: 6.1, refunds: 0.15 },
  { label: 'A', mrr: 8.98, payouts: 6.4, refunds: 0.16 },
  { label: 'M', mrr: 9.4, payouts: 6.8, refunds: 0.184 },
];

export const PAYMENT_METHOD_SHARE: PaymentMethodShare[] = [
  { label: 'Mastercard', percent: 52, color: '#1a1a1a' },
  { label: 'Easypaisa', percent: 28, color: '#166534' },
  { label: 'JazzCash', percent: 12, color: '#f97316' },
  { label: 'Bank transfer', percent: 8, color: '#d4a94a' },
];

export const RECENT_TRANSACTIONS: TransactionEntry[] = [
  { id: 't1', whenLabel: '2h ago', who: 'Layla Siddiqui', type: 'Charge', method: 'Mastercard', amount: 'Rs 18,000', status: 'Success' },
  { id: 't2', whenLabel: '3h ago', who: 'Dr. Tariq Mahmood', type: 'Payout', method: 'HBL •••• 3412', amount: 'Rs 184,500', status: 'Success' },
  { id: 't3', whenLabel: '5h ago', who: 'Sana Yousaf', type: 'Refund', method: 'Easypaisa', amount: 'Rs 18,000', status: 'Pending' },
  { id: 't4', whenLabel: '8h ago', who: 'Ammar Sheikh', type: 'Charge', method: 'JazzCash', amount: 'Rs 24,000', status: 'Success' },
  { id: 't5', whenLabel: '11h ago', who: 'Bilal Rauf', type: 'Charge', method: 'Mastercard', amount: 'Rs 24,000', status: 'Failed' },
];

export const REFUND_QUEUE: RefundQueueItem[] = [
  { id: 'r1', initials: 'SY', avatarColor: 'bg-emerald-800', name: 'Sana Y.', amount: 'Rs 18,000', reason: 'Therapist mismatch · session 1' },
];