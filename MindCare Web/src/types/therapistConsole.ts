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

// ——— Schedule (T04) ———
export type ScheduleEventType = 'confirmed' | 'pending' | 'trial' | 'block';

export interface ScheduleEvent {
  id: string;
  day: number; // 0 = Mon .. 6 = Sun
  startHour: number; // 24h, .5 = half hour
  durationMin: number;
  patientName?: string;
  patientId?: string;
  label: string;
  type: ScheduleEventType;
}

// ——— Requests (T05) ———
export type RequestStatus = 'inbox' | 'awaiting' | 'resolved';

export interface SessionRequestEntry {
  id: string;
  patientId: string | null;
  patientName: string;
  patientInitials: string;
  avatarColor: string;
  tag: string;
  tagTone: 'default' | 'warning' | 'info';
  date: string;
  time: string;
  durationMin: number;
  note?: string;
  requestedAgo: string;
  status: RequestStatus;
}

// ——— In-session (T06) ———
export interface LiveSensorReading {
  label: string;
  value: string;
  trend: number[];
  color: string;
}

export interface LiveNoteEntry {
  id: string;
  type: 'auto' | 'marked';
  time?: string;
  content: string;
}

export interface InSessionData {
  patientId: string;
  patientName: string;
  patientInitials: string;
  avatarColor: string;
  sessionLabel: string;
  elapsedLabel: string;
  totalLabel: string;
  speakingCaption: string;
  aiPromptSuggestion: string;
  liveSensors: LiveSensorReading[];
  liveCue: string;
  liveNotes: LiveNoteEntry[];
}

// ——— Care plan editor (T09) ———
export type CarePlanCategory = 'Breath' | 'Body' | 'Thinking' | 'Reflect' | 'Diet' | 'Sleep' | 'Motivation';

export interface CarePlanBlock {
  id: string;
  category: CarePlanCategory;
  title: string;
  cadence: string;
  addedBy: string;
  addedDate: string;
  doneCount: number;
  totalCount: number;
  pending?: boolean;
  lowCompliance?: boolean;
}

export interface ExerciseLibraryItem {
  id: string;
  category: CarePlanCategory;
  title: string;
  meta: string;
}

export interface CarePlanData {
  patientId: string;
  patientName: string;
  patientInitials: string;
  avatarColor: string;
  weekLabel: string;
  nextReview: string;
  version: string;
  completedCount: number;
  totalCount: number;
  compliancePercent: number;
  lastUpdated: string;
  pendingFromAida: number;
  blocks: CarePlanBlock[];
  quickReliefNote: string;
}

// ——— Messages (T08) ———
export interface ChatMessage {
  id: string;
  sender: 'therapist' | 'patient';
  content: string;
  time: string;
  dateGroup: string;
}

export interface MessageThread {
  id: string;
  patientId: string;
  patientName: string;
  patientInitials: string;
  avatarColor: string;
  preview: string;
  timeAgo: string;
  unreadCount: number;
  online: boolean;
  lastSessionMeta: string;
  messages: ChatMessage[];
  aidaDraftReply?: string;
}

// ——— Weekly report (T07) ———
export interface ReportStat {
  label: string;
  value: string;
  delta?: string;
  meta: string;
  deltaPositive?: boolean;
}

export interface MoodDailyPoint {
  day: string;
  value: number;
}

export interface SensorPattern {
  label: string;
  value: string;
  meta: string;
  trend: number[];
  color: string;
}

export interface KeyInsight {
  id: string;
  tone: 'positive' | 'warning' | 'negative';
  title: string;
  description: string;
}

export interface WeeklyReportData {
  patientId: string;
  patientName: string;
  weekRange: string;
  weekLabel: string;
  generatedDate: string;
  stats: ReportStat[];
  summaryTitle: string;
  summaryText: string;
  moodDaily: MoodDailyPoint[];
  sensorPatterns: SensorPattern[];
  keyInsights: KeyInsight[];
  noteToPatient: string;
}

// ——— Profile & availability (T10) ———
export type AvailabilityStatus = 'open' | 'tentative' | 'booked' | 'blocked' | 'closed';

export interface AvailabilitySlot {
  day: number; // 0 = Mon .. 6 = Sun
  hour: number;
  status: AvailabilityStatus;
}

export interface RatingBreakdown {
  stars: number;
  count: number;
}

export interface ReviewEntry {
  id: string;
  initials: string;
  color: string;
  handle: string;
  rating: number;
  timeAgo: string;
  content: string;
}

export interface TherapistProfileData {
  name: string;
  title: string;
  verifiedDate: string;
  license: string;
  yearsExperience: number;
  city: string;
  timezone: string;
  specialtyTags: string[];
  approachTags: string[];
  acceptsTrials: boolean;
  inNetworkNote: string;
  languages: string[];
  rating: number;
  reviewCount: number;
  walletBalance: string;
  walletDeltaVsLastMonth: string;
  sessionsBilled: number;
  payoutDate: string;
  payoutAccount: string;
  ratingBreakdown: RatingBreakdown[];
  recentReviews: ReviewEntry[];
}

// ——— Circles / community (T11) ———
export type CircleRole = 'Verified voice' | 'Member' | 'Host';

export interface CircleSummary {
  id: string;
  name: string;
  memberCount: number;
  role: CircleRole;
  color: string;
  unreadCount?: number;
}

export interface CircleTherapistReply {
  content: string;
  timeAgo: string;
  moderationClear: boolean;
}

export interface CirclePost {
  id: string;
  authorHandle: string;
  circleName: string;
  timeAgo: string;
  content: string;
  likes: number;
  commentCount: number;
  repostCount: number;
  isAskingTherapist: boolean;
  authorInitial: string;
  authorColor: string;
  therapistReply?: CircleTherapistReply;
}

export interface CircleQuestionWaiting {
  id: string;
  tag: string;
  timeAgo: string;
  question: string;
}

export interface CircleStats {
  month: string;
  answers: number;
  peopleHelped: number;
  helpfulRatePercent: number;
  trialReferrals: number;
}