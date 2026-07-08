// ============================================================
// MindCare — Domain Types / Entities
// ============================================================

export type UserRole = 'client' | 'clinician';

export interface NavItem {
  label: string;
  href: string;
}

export interface Stat {
  value: string;
  label: string;
}

export interface Feature {
  id: string;
  icon: string;
  title: string;
  description: string;
  color: string;
}

export interface HowItWorksStep {
  number: string;
  title: string;
  description: string;
}

export interface Partner {
  name: string;
}

export interface Therapist {
  id: string;
  name: string;
  specialty: string;
  nextSession: string;
}

export interface MoodEntry {
  day: string;
  value: number;
}

export interface OnboardingChoice {
  role: UserRole;
  selectedAt: string;
}

export interface AppDownloadInfo {
  platform: 'ios' | 'android';
  url: string;
}

// ——— Form / Auth types (ready for backend integration) ———

export interface SignInPayload {
  email: string;
  password: string;
}

export interface SignUpPayload {
  name: string;
  email: string;
  password: string;
  role: UserRole;
}

export interface ApiResponse<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
}

// ——— Stories page ———
export interface StoryEntry {
  id: string;
  quote: string;
  name: string;
  age: number;
  location: string;
  tag: string;
  avatarInitials: string;
  avatarColor: string;
}

// ——— For NGOs page ———
export interface NGOPartnerEntry {
  id: string;
  initials: string;
  color: string;
  name: string;
  description: string;
  routedCount: number;
}

export interface NGORegisterPayload {
  organisationName: string;
  coverageType: string;
  coverage: string;
  contactEmail: string;
  description: string;
}

// ——— For Therapists page ———
export interface TherapistFeature {
  id: string;
  icon: 'code' | 'calendar' | 'file-text' | 'heart' | 'shield';
  title: string;
  description: string;
  color: string;
}

// ——— Therapist onboarding / auth ———
export interface TherapistLoginPayload {
  identifier: string;
  password: string;
  keepSignedIn: boolean;
}

export type TherapistRegisterStep = 'identity' | 'credentials' | 'practice' | 'review';

export interface TherapistCredentials {
  pmdcLicenseNumber: string;
  pmdcVerified: boolean;
  specialty: string;
  degree: string;
  university: string;
  graduationYear: string;
  focusAreas: string[];
  consentBackgroundCheck: boolean;
}