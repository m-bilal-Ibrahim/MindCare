// ============================================================
// MindCare — App-wide Constants (swap URLs for real API later)
// ============================================================

import type {
  NavItem,
  Feature,
  HowItWorksStep,
  Partner,
  Stat,
  MoodEntry,
  StoryEntry,
  NGOPartnerEntry,
  TherapistFeature,
} from '../types';

export const APP_NAME = 'MindCare';
export const APP_TAGLINE = 'A quieter mind is the work of a year, not a download.';

// ——— Navigation ———
export const NAV_ITEMS: NavItem[] = [
  { label: 'How it works', href: '#how-it-works' },
  { label: 'For therapists', href: '/for-therapists' },
  { label: 'For NGOs', href: '/for-ngos' },
  { label: 'Stories', href: '/stories' },
  { label: 'Pricing', href: '#pricing' },
  { label: 'About us', href: '#about' },
  { label: 'Help', href: '#help' },
];

// ——— Landing page stats ———
export const HERO_STATS: Stat[] = [
  { value: '12,400+', label: 'People in care' },
  { value: '184', label: 'Verified therapists' },
  { value: '14', label: 'Cities' },
];

// ——— Partners ———
export const PARTNERS: Partner[] = [
  { name: 'Umang' },
  { name: 'Rozan' },
  { name: 'Karwan-e-Hayat' },
  { name: 'Dawn' },
  { name: 'Geo' },
  { name: 'Aurora' },
];

// ——— How It Works steps ———
export const HOW_IT_WORKS: HowItWorksStep[] = [
  {
    number: '01',
    title: 'Tell us where you are',
    description: '15-minute intake. No labels, no diagnosis — just where it hurts and what you need.',
  },
  {
    number: '02',
    title: 'Match with a therapist',
    description: 'Verified, PMDC-listed clinicians. Aida proposes 3 — you pick. Switch any time.',
  },
  {
    number: '03',
    title: 'Weekly sessions, real ones',
    description: '50-minute video. Notes auto-prepared. Your therapist shapes your plan, not a bot.',
  },
  {
    number: '04',
    title: 'The days between matter',
    description: 'Body data, journaling, peer circles, dua, breath. Tiny exercises, all reviewed by your therapist.',
  },
];

// ——— What You Get features ———
export const FEATURES: Feature[] = [
  {
    id: 'therapist',
    icon: '🧑‍⚕️',
    title: 'A real therapist',
    description: 'Weekly 50-minute video sessions. Switch any time, no questions asked.',
    color: 'bg-emerald-100 text-emerald-700',
  },
  {
    id: 'aida',
    icon: '🤖',
    title: 'Aida, your co-pilot',
    description: 'AI between sessions — your therapist shapes what it can say and recommend.',
    color: 'bg-purple-100 text-purple-700',
  },
  {
    id: 'mindband',
    icon: '📡',
    title: 'MindBand sensors',
    description: 'Optional wearable. Heart, breath, sleep — picked up so you don\'t have to log.',
    color: 'bg-orange-100 text-orange-700',
  },
  {
    id: 'journal',
    icon: '📓',
    title: 'Journaling that breathes',
    description: 'Prompts, freewrite, voice. Auto-summarised for your next session.',
    color: 'bg-yellow-100 text-yellow-700',
  },
  {
    id: 'circles',
    icon: '❤️',
    title: 'Quiet peer circles',
    description: 'Anonymous, moderated. Anxiety, sober walks, grief, new parents.',
    color: 'bg-rose-100 text-rose-700',
  },
  {
    id: 'sos',
    icon: '🆘',
    title: 'SOS, held by humans',
    description: 'One tap. Trained listener within 4 minutes, NGO escalation if needed.',
    color: 'bg-red-100 text-red-700',
  },
];

// ——— Dummy mood data (replace with API call) ———
export const DUMMY_MOOD_DATA: MoodEntry[] = [
  { day: 'Mon', value: 3 },
  { day: 'Tue', value: 4 },
  { day: 'Wed', value: 3 },
  { day: 'Thu', value: 5 },
  { day: 'Fri', value: 4 },
  { day: 'Sat', value: 6 },
  { day: 'Sun', value: 5 },
];

// ——— Client benefits (onboarding) ———
export const CLIENT_BENEFITS = [
  'Weekly therapy with a verified clinician',
  'Aida co-pilot between sessions',
  'Body, journal, circles, SOS — one app',
];

// ——— Clinician benefits (onboarding) ———
export const CLINICIAN_BENEFITS = [
  'Verified profile · matched patients',
  'Session video, notes, billing in one place',
  'Aida assists, you stay in charge',
];

// ——— Routes ———
export const ROUTES = {
  HOME: '/',
  ONBOARDING: '/get-started',
  CLIENT_APP: '/get-started/client',
  CLINICIAN_APP: '/get-started/clinician',
  SIGN_IN: '/sign-in',
  SIGN_UP: '/sign-up',
  STORIES: '/stories',
  FOR_NGOS: '/for-ngos',
  FOR_THERAPISTS: '/for-therapists',
  THERAPIST_LOGIN: '/therapist/sign-in',
  THERAPIST_REGISTER: '/therapist/apply',
} as const;

// ——— Stories page ———
export const STORIES: StoryEntry[] = [
  {
    id: 'story-1',
    quote: 'Day 90. The walks really do help.',
    name: 'Ammar',
    age: 34,
    location: 'Karachi',
    tag: 'sober walk',
    avatarInitials: 'A3',
    avatarColor: 'bg-emerald-700',
  },
  {
    id: 'story-2',
    quote: "First time I've felt heard without being fixed.",
    name: 'Hira',
    age: 26,
    location: 'Lahore',
    tag: 'grief',
    avatarInitials: 'H2',
    avatarColor: 'bg-rose-400',
  },
  {
    id: 'story-3',
    quote: 'My therapist saw my sleep break before I did.',
    name: 'Bilal',
    age: 36,
    location: 'Multan',
    tag: 'burnout',
    avatarInitials: 'B3',
    avatarColor: 'bg-amber-600',
  },
  {
    id: 'story-4',
    quote: 'Going through divorce. The couples circle saved me from doing it alone.',
    name: 'Fatima',
    age: 29,
    location: 'Islamabad',
    tag: 'divorce',
    avatarInitials: 'F2',
    avatarColor: 'bg-violet-500',
  },
];

export const STORIES_TOTAL_COUNT = 42;

// ——— For NGOs page ———
export const NGO_PARTNERS: NGOPartnerEntry[] = [
  {
    id: 'ngo-1',
    initials: 'UH',
    color: 'bg-orange-500',
    name: 'Umang Helpline',
    description: '24/7 helpline · nationwide',
    routedCount: 1240,
  },
  {
    id: 'ngo-2',
    initials: 'R',
    color: 'bg-emerald-700',
    name: 'Rozan',
    description: 'Counselling · referral · ISB/RWP',
    routedCount: 412,
  },
  {
    id: 'ngo-3',
    initials: 'K',
    color: 'bg-violet-500',
    name: 'Karwan-e-Hayat',
    description: 'Hospital partner · Karachi',
    routedCount: 86,
  },
  {
    id: 'ngo-4',
    initials: 'T',
    color: 'bg-amber-600',
    name: 'Taskeen',
    description: 'Helpline · 12h · LHR/FSD',
    routedCount: 268,
  },
];

export const NGO_STATS: Stat[] = [
  { value: '2,054', label: 'Cases routed YTD' },
  { value: '100%', label: 'Closed loop' },
  { value: 'Rs 220k', label: 'Monthly partner share' },
];

export const NGO_COVERAGE_TYPES = ['Helpline · 24/7', 'Counselling · referral', 'Hospital partner', 'Shelter / crisis care'];

// ——— For Therapists page ———
export const THERAPIST_FEATURES: TherapistFeature[] = [
  {
    id: 'aida-voice',
    icon: 'code',
    title: 'Aida, in your voice',
    description: 'AI assistant suggests · you approve. Every nudge to your patient passes through your hand first.',
    color: 'bg-violet-500',
  },
  {
    id: 'booking',
    icon: 'calendar',
    title: 'Booking that respects you',
    description: 'Patients request. You confirm. No auto-bookings, no late-night surprises.',
    color: 'bg-emerald-700',
  },
  {
    id: 'notes',
    icon: 'file-text',
    title: 'Notes that write themselves',
    description: 'In-session voice → structured SOAP. You edit instead of typing.',
    color: 'bg-orange-500',
  },
  {
    id: 'care',
    icon: 'heart',
    title: 'Care that follows the week',
    description: 'Body, journal, exercises — all in one chart, with your name on it.',
    color: 'bg-rose-400',
  },
  {
    id: 'crisis',
    icon: 'shield',
    title: 'Crisis support, not on you',
    description: "SOS routes to trained listeners and NGO partners. You're notified, not on the hook.",
    color: 'bg-amber-600',
  },
];

export const THERAPIST_STATS: Stat[] = [
  { value: '72%', label: 'Take-home split' },
  { value: 'Rs 164k', label: 'Avg monthly · active therapists' },
  { value: '2–3 days', label: 'Verification turnaround' },
];

export const THERAPIST_TESTIMONIAL = {
  quote: 'I have my Sundays back. The notes thing alone was worth the switch.',
  name: 'Dr. Sana',
  meta: '2 yrs on MindCare',
  initials: 'SY',
};

// ——— Therapist login page ———
export const THERAPIST_LOGIN_TESTIMONIAL = {
  label: 'YOUR PEOPLE, MAY 27',
  quote: 'He listens like nobody is in a hurry. The panic loops have actually slowed down.',
  attribution: '— Layla S., in care with Dr. Tariq for 3 months',
};

export const THERAPIST_WAITING_ITEMS = [
  { id: 'w1', color: 'bg-rose-400', title: 'Session notes', meta: 'Layla S. · last Friday' },
  { id: 'w2', color: 'bg-emerald-700', title: 'Care plan amendment', meta: 'Aida proposed for Bilal R.' },
  { id: 'w3', color: 'bg-amber-600', title: '5 new patient requests', meta: 'inbox' },
];

// ——— Therapist registration ———
export const THERAPIST_ONBOARDING_STEPS: { id: string; label: string }[] = [
  { id: 'identity', label: 'Identity' },
  { id: 'credentials', label: 'Credentials' },
  { id: 'practice', label: 'Practice' },
  { id: 'review', label: 'Review' },
];

export const THERAPIST_WHAT_HAPPENS_NEXT = [
  { id: 'n1', title: 'You finish all 4 steps', meta: '~10 minutes' },
  { id: 'n2', title: 'Auto-checks run', meta: 'PMDC, HEC, Verisys — usually overnight' },
  { id: 'n3', title: 'A senior reviews flagged items', meta: '~24 hours' },
  { id: 'n4', title: 'You get a welcome email', meta: 'Onboarding call · then patients' },
];

export const THERAPIST_SPECIALTIES = [
  'Clinical psychologist',
  'Psychiatrist',
  'Counselling psychologist',
  'Marriage & family therapist',
];

export const THERAPIST_FOCUS_AREAS = [
  'Anxiety',
  'Burnout',
  'Trauma',
  'EMDR',
  'CBT',
  'Couples',
  'Family',
  'Grief',
  'Addiction',
  'Adolescent',
  'Sleep',
  'Identity',
  'Post-partum',
  'OCD',
];

// ——— API base URL (swap to real endpoint) ———
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL ?? 'https://api.mindcare.pk/v1';