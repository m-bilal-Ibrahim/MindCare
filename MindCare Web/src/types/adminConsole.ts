// ============================================================
// MindCare — Admin Console Types
// ============================================================

export interface AdminNavItem {
  id: string;
  label: string;
  route: string;
  icon: 'home' | 'shield' | 'code' | 'users' | 'flag' | 'alert-triangle' | 'heart' | 'file' | 'sun';
  badge?: number;
}

// ——— Overview (A01) ———
export interface PlatformStat {
  label: string;
  value: string;
  delta: string;
  meta: string;
  trend: number[];
  trendColor: 'green' | 'red' | 'neutral' | 'gold';
}

export interface GrowthPoint {
  label: string;
  activeUsers: number;
  sessions: number;
}

export interface QueuePreviewItem {
  id: string;
  name: string;
  initials: string;
  avatarColor: string;
  meta: string;
  statusTag: string;
  statusTone: 'default' | 'new' | 'flag' | 'wait';
  timeAgo: string;
}

// ——— Verifications (A02 / A02b) ———
export type VerificationType = 'therapist' | 'ngo' | 'hospital';
export type VerificationCheckStatus = 'verified' | 'needs-review' | 'pending';

export interface VerificationQueueItem {
  id: string;
  type: VerificationType;
  name: string;
  initials: string;
  avatarColor: string;
  submittedAgo: string;
  statusTag: string;
  statusTone: 'default' | 'new' | 'flag' | 'wait';
}

export interface CredentialCheck {
  id: string;
  label: string;
  meta: string;
  status: VerificationCheckStatus;
}

export interface VerificationTimelineEntry {
  time: string;
  label: string;
}

export interface TherapistVerificationDetail {
  applicationId: string;
  queueItemId: string;
  name: string;
  initials: string;
  avatarColor: string;
  submittedDate: string;
  waitingDays: number;
  specialtyTags: string[];
  languages: string;
  city: string;
  phoneMasked: string;
  emailMasked: string;
  credentialSummary: string;
  riskScore: number;
  riskLabel: string;
  riskDescription: string;
  identityMatchSources: string;
  sanctionsStatus: string;
  publicReviewsNote: string;
  imageAuthenticityNote: string;
  checksComplete: number;
  checksTotal: number;
  checks: CredentialCheck[];
  timeline: VerificationTimelineEntry[];
}

export interface SlaCommitment {
  pickupTimeBusiness: string;
  pickupTimeAfterHours: string;
  closedLoopReport: string;
  closedLoopReportWeekend: string;
  reroutingWindow: string;
  annualDrill: string;
}

export interface NgoVerificationDetail {
  applicationId: string;
  queueItemId: string;
  name: string;
  initials: string;
  avatarColor: string;
  submittedDate: string;
  waitingDays: number;
  summary: string;
  address: string;
  phoneMasked: string;
  emailMasked: string;
  ntn: string;
  tags: string[];
  languages: string;
  slaCommitment: SlaCommitment;
  checksComplete: number;
  checksTotal: number;
  checks: CredentialCheck[];
}

// ——— Users (A03) ———
export type PlatformUserStatus = 'Active' | 'Trial' | 'Paused' | 'Onboarding';

export interface PlatformUser {
  id: string;
  initials: string;
  avatarColor: string;
  name: string;
  emailMasked: string;
  city: string;
  plan: 'Monthly' | 'Yearly' | 'Trial' | null;
  therapistName: string | null;
  joined: string;
  status: PlatformUserStatus;
  flag?: string;
}

export interface UsersSummary {
  active: number;
  trialsThisMonth: number;
  pausedOrRefund: number;
  activeCount: number;
  trialCount: number;
  pausedCount: number;
  hasFlagsCount: number;
  refundPendingCount: number;
  wearableIssuesCount: number;
}