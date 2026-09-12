// ============================================================
// MindCare — Admin Console Types (Settings, A09)
// ============================================================

export type SettingsTabKey =
  | 'general'
  | 'brand'
  | 'roles'
  | 'integrations'
  | 'pricing'
  | 'privacy'
  | 'notifications'
  | 'flags'
  | 'danger';

export interface SettingsTabItem {
  key: SettingsTabKey;
  label: string;
}

export interface GeneralSettings {
  platformName: string;
  supportEmail: string;
  defaultRegion: string;
  defaultLanguage: string;
  currency: string;
  taxId: string;
}

export interface BrandColorSwatch {
  name: string;
  hex: string;
}

export interface MicrocopyEntry {
  label: string;
  tag: string;
  text: string;
}

export interface RoleRow {
  role: string;
  users: number;
  verify: string;
  refund: string;
  moderate: string;
  unmaskPii: string;
  settingsAccess: string;
  audit: string;
}

export interface AdminUserRow {
  name: string;
  email: string;
  initials: string;
  avatarColor: string;
  role: string;
  lastSignIn: string;
  twoFA: boolean;
  active: boolean;
}

export interface IntegrationService {
  id: string;
  initial: string;
  color: string;
  name: string;
  connected: boolean;
  description: string;
  meta: string;
}

export interface PricingPlanCard {
  key: string;
  label: string;
  price: string;
  meta: string;
  visible: boolean;
}

export interface DiscountCode {
  code: string;
  discount: string;
  cohort: string;
  used: number;
  total: number | null;
  expires: string;
  status: 'Live' | 'Sunset';
}

export interface PrivacyToggle {
  label: string;
  meta: string;
  locked: boolean;
  value: boolean;
}

export interface DataRegionShare {
  region: string;
  percent: number;
}

export interface ErasureQueueSummary {
  activeCount: number;
  closedYtd: number;
}

export interface NotificationRow {
  event: string;
  audience: string;
  inApp: boolean;
  email: boolean;
  sms: boolean;
  push: boolean;
  slack: boolean;
}

export interface NotificationTemplate {
  title: string;
  body: string;
}

export type FeatureFlagStatus = 'Live' | 'Ramping' | 'Beta' | 'Canary';

export interface FeatureFlag {
  key: string;
  description: string;
  cohort: string;
  rolloutPercent: number;
  owner: string;
  status: FeatureFlagStatus;
  since: string;
}

export interface DangerAction {
  title: string;
  description: string;
  buttonLabel: string;
  tone: 'warning' | 'critical';
}