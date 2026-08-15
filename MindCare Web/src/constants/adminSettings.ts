// ============================================================
// MindCare — Admin Console Mock Data (Settings, A09)
// ============================================================

import type {
  SettingsTabItem,
  GeneralSettings,
  BrandColorSwatch,
  MicrocopyEntry,
  RoleRow,
  AdminUserRow,
  IntegrationService,
  PricingPlanCard,
  DiscountCode,
  PrivacyToggle,
  DataRegionShare,
  ErasureQueueSummary,
  NotificationRow,
  NotificationTemplate,
  FeatureFlag,
  DangerAction,
} from '../types/adminSettings';

export const SETTINGS_TABS: SettingsTabItem[] = [
  { key: 'general', label: 'General' },
  { key: 'brand', label: 'Brand & content' },
  { key: 'roles', label: 'Roles & permissions' },
  { key: 'integrations', label: 'Integrations' },
  { key: 'pricing', label: 'Pricing & plans' },
  { key: 'privacy', label: 'Privacy & data' },
  { key: 'notifications', label: 'Notifications' },
  { key: 'flags', label: 'Feature flags' },
  { key: 'danger', label: 'Danger zone' },
];

export const SETTINGS_LAST_CHANGE = 'Last change · May 19 by Ayesha S.';

export const GENERAL_SETTINGS: GeneralSettings = {
  platformName: 'MindCare',
  supportEmail: 'help@mindcare.pk',
  defaultRegion: 'PK · GMT+5',
  defaultLanguage: 'Urdu + English',
  currency: 'PKR',
  taxId: '1234567-8',
};

export const BRAND_COLORS: BrandColorSwatch[] = [
  { name: 'CREAM', hex: '#f5f2ec' },
  { name: 'INK', hex: '#1d1a17' },
  { name: 'CORAL', hex: '#d97757' },
  { name: 'SAGE', hex: '#7a9b7e' },
  { name: 'ROSE', hex: '#c1857e' },
  { name: 'GOLD', hex: '#c9a661' },
  { name: 'PLUM', hex: '#8a7ba0' },
  { name: 'NAVY', hex: '#3b4a66' },
];

export const BRAND_MICROCOPY: MicrocopyEntry[] = [
  { label: 'Empty inbox', tag: 'warm', text: 'A quiet moment. Nothing pending — enjoy it.' },
  { label: 'Welcome (client)', tag: 'soft', text: "Hello. We're glad you came." },
  { label: 'SOS confirm', tag: 'firm', text: 'Help is on the way. Stay where you are — we\'re here.' },
  { label: 'Subscription end', tag: 'soft', text: 'No pressure. You can come back any time.' },
];

export const ROLE_ROWS: RoleRow[] = [
  { role: 'Owner', users: 2, verify: 'all', refund: 'all', moderate: 'all', unmaskPii: '2-eyes', settingsAccess: 'all', audit: 'all' },
  { role: 'Lead admin', users: 4, verify: 'all', refund: 'all', moderate: 'all', unmaskPii: '2-eyes', settingsAccess: 'most', audit: 'read' },
  { role: 'T&S officer', users: 6, verify: '—', refund: '—', moderate: 'all', unmaskPii: 'request', settingsAccess: '—', audit: 'read' },
  { role: 'Support agent', users: 18, verify: '—', refund: 'up to Rs 25k', moderate: '—', unmaskPii: '—', settingsAccess: '—', audit: '—' },
  { role: 'Finance', users: 3, verify: '—', refund: 'all', moderate: '—', unmaskPii: '—', settingsAccess: '—', audit: 'read' },
  { role: 'Read-only', users: 9, verify: '—', refund: '—', moderate: '—', unmaskPii: '—', settingsAccess: '—', audit: 'read' },
];

export const ROLES_SUMMARY = { totalAdmins: 42, activeNow: 4 };

export const ADMIN_USER_ROWS: AdminUserRow[] = [
  { name: 'Ayesha Sultan', email: 'ayesha.sultan@mindcare.pk', initials: 'AS', avatarColor: 'bg-emerald-800', role: 'Lead admin', lastSignIn: 'now', twoFA: true, active: true },
  { name: 'Maryam Ali', email: 'maryam.ali@mindcare.pk', initials: 'MA', avatarColor: 'bg-gray-700', role: 'Owner', lastSignIn: '12 min ago', twoFA: true, active: true },
];

export const INTEGRATION_SERVICES: IntegrationService[] = [
  { id: 'zoom', initial: 'Z', color: 'bg-blue-100 text-blue-700', name: 'Zoom', connected: true, description: 'Auto-generate Meet links for confirmed sessions', meta: 'Webhook · v3 · last sync 2 min ago' },
  { id: 'gmeet', initial: 'G', color: 'bg-emerald-100 text-emerald-700', name: 'Google Meet', connected: true, description: 'Fallback when Zoom is down', meta: 'OAuth refreshed Mar 14' },
  { id: 'stripe', initial: 'S', color: 'bg-violet-100 text-violet-700', name: 'Stripe', connected: true, description: 'Cards · subscriptions · payouts', meta: 'Live mode · 41 webhooks · 0 failed today' },
  { id: 'easypaisa', initial: 'E', color: 'bg-emerald-50 text-emerald-700', name: 'Easypaisa', connected: true, description: 'Local mobile wallet payments', meta: 'Merchant ID 88-12-EP-441' },
  { id: 'jazzcash', initial: 'J', color: 'bg-rose-100 text-rose-700', name: 'JazzCash', connected: true, description: 'Local mobile wallet payments', meta: 'Merchant ID JC-2206-LHR' },
  { id: 'openai', initial: 'O', color: 'bg-teal-100 text-teal-700', name: 'OpenAI · GPT', connected: true, description: 'Powers Aida chat + recommendations', meta: 'gpt-4o-mini-aida · 12k req today · org-mc-prod' },
  { id: 'verisys', initial: 'V', color: 'bg-gray-200 text-gray-700', name: 'Verisys', connected: true, description: 'Therapist background checks', meta: 'Bulk API · 184 checks YTD' },
  { id: 'pmdc', initial: 'P', color: 'bg-emerald-100 text-emerald-700', name: 'PMDC.gov.pk', connected: true, description: 'License auto-verification', meta: 'Daily nightly pull · cached' },
  { id: 'twilio', initial: 'T', color: 'bg-rose-100 text-rose-700', name: 'Twilio', connected: true, description: 'SMS · OTP + reminders', meta: 'PK long-code · 4.1k msgs today' },
  { id: 'slack', initial: 'S', color: 'bg-violet-100 text-violet-700', name: 'Slack', connected: false, description: 'On-call alerts for SOS & infra', meta: 'Bot token expired Mar 2' },
];

export const INTEGRATIONS_SUMMARY = { total: 12, connected: 9, notConnected: 3 };

export const PRICING_PLANS: PricingPlanCard[] = [
  { key: 'trial', label: 'Trial', price: 'Free', meta: '7 days · 1 session', visible: true },
  { key: 'monthly', label: 'Monthly', price: 'Rs 18,000', meta: '/month · everything', visible: true },
  { key: 'yearly', label: 'Yearly', price: 'Rs 180,000', meta: '/year · save 2 mo', visible: true },
];

export const DISCOUNT_CODES: DiscountCode[] = [
  { code: 'WELCOME50', discount: '50% off month 1', cohort: 'Trial → paid', used: 412, total: 1000, expires: 'Jun 30', status: 'Live' },
  { code: 'ROZAN-FREE', discount: '80% off · NGO seat', cohort: 'Rozan-referred', used: 54, total: 200, expires: 'no end', status: 'Live' },
  { code: 'UMANG-FREE', discount: '100% off · 3 mo', cohort: 'Umang post-crisis', used: 37, total: 100, expires: 'no end', status: 'Live' },
  { code: 'STUDENT30', discount: '30% off · monthly', cohort: 'Student email', used: 218, total: null, expires: 'Aug 31', status: 'Live' },
  { code: 'LAUNCH26', discount: '40% off · yearly', cohort: 'All', used: 1902, total: 2000, expires: 'Jul 1', status: 'Sunset' },
];

export const PRIVACY_TOGGLES: PrivacyToggle[] = [
  { label: 'HIPAA-aligned voice masking in peer talk', meta: 'Always on — required for community calls', locked: true, value: true },
  { label: 'End-to-end encrypted DMs', meta: 'Symmetric · key escrow off by default', locked: true, value: true },
  { label: 'Journal entries retention', meta: 'Forever, unless user requests delete', locked: false, value: true },
  { label: 'Default profile visibility', meta: 'New users see only therapist + their circles', locked: false, value: true },
  { label: 'AI training on user data', meta: 'Off by default · users opt in per-modality', locked: false, value: false },
  { label: 'Admin PII unmask requires 2-eyes', meta: 'Two admins must approve every PII unlock', locked: false, value: true },
  { label: 'Cross-border data transfer', meta: 'Disabled · all data stays in-region', locked: true, value: false },
];

export const SENSOR_DATA_RETENTION_DAYS = 365;

export const DATA_REGIONS: DataRegionShare[] = [{ region: 'Pakistan (primary)', percent: 100 }];

export const ERASURE_QUEUE_SUMMARY: ErasureQueueSummary = { activeCount: 3, closedYtd: 14 };

export const NOTIFICATION_ROWS: NotificationRow[] = [
  { event: 'Session booked', audience: 'Client + Therapist', inApp: true, email: true, sms: false, push: true, slack: false },
  { event: 'Session reminder · 1h', audience: 'Client + Therapist', inApp: true, email: false, sms: true, push: true, slack: false },
  { event: 'No-show recorded', audience: 'Both + Support', inApp: true, email: true, sms: false, push: true, slack: true },
  { event: 'Refund issued', audience: 'Client', inApp: true, email: true, sms: false, push: false, slack: false },
  { event: 'Therapist verified', audience: 'Therapist + Admin', inApp: true, email: true, sms: false, push: false, slack: true },
  { event: 'SOS triggered', audience: 'Therapist + T&S', inApp: true, email: true, sms: true, push: true, slack: true },
  { event: 'Moderation flag · high', audience: 'T&S officers', inApp: true, email: false, sms: false, push: false, slack: true },
  { event: 'Weekly report ready', audience: 'Client + Therapist', inApp: true, email: true, sms: false, push: true, slack: false },
  { event: 'Subscription renewing', audience: 'Client', inApp: true, email: true, sms: false, push: false, slack: false },
];

export const NOTIFICATION_RATE_LIMIT_MAX_PUSH_PER_DAY = 5;

export const NOTIFICATION_TEMPLATE: NotificationTemplate = {
  title: 'SESSION REMINDER · 1H',
  body: 'Hello {firstName}, gentle reminder — your session with {therapist} is in an hour.',
};

export const FEATURE_FLAGS: FeatureFlag[] = [
  { key: 'aida_crisis_v3', description: 'New escalation tree · keyword + EDA', cohort: 'All users', rolloutPercent: 100, owner: 'Hassan', status: 'Live', since: 'Feb 3' },
  { key: 'couples_intake_v2', description: 'Joint intake form for partner pairs', cohort: 'New trials', rolloutPercent: 40, owner: 'Sana', status: 'Ramping', since: 'May 14' },
  { key: 'reward_streaks_v2', description: 'Visible streak counter on Today screen', cohort: 'iOS only', rolloutPercent: 15, owner: 'Ali', status: 'Beta', since: 'May 18' },
  { key: 'therapist_match_v4', description: 'New match algorithm using journal embeds', cohort: 'Aida-recommended', rolloutPercent: 5, owner: 'Hassan', status: 'Canary', since: 'May 21' },
  { key: 'voice_journal_v2', description: 'Whisper · diarisation + emotion labels', cohort: 'Power users', rolloutPercent: 25, owner: 'Faisal', status: 'Ramping', since: 'May 9' },
  { key: 'darkmode', description: 'Therapist console dark theme', cohort: 'All', rolloutPercent: 100, owner: 'Ali', status: 'Live', since: 'Mar 1' },
];

export const DANGER_ACTIONS: DangerAction[] = [
  { title: 'Put platform in maintenance mode', description: 'Disables new sessions, locks billing, shows a banner to all users. Reversible.', buttonLabel: 'Enable maintenance', tone: 'warning' },
  { title: 'Pause new signups', description: 'Existing users unaffected. Useful when scaling support.', buttonLabel: 'Pause signups', tone: 'warning' },
  { title: 'Force-rotate all admin sessions', description: 'Signs out every admin · re-prompts 2FA. Use after a suspected breach.', buttonLabel: 'Rotate now', tone: 'warning' },
  { title: 'Export full audit log', description: 'Generates a signed archive of every admin action, ever. Large file.', buttonLabel: 'Generate export', tone: 'warning' },
  { title: 'Delete a user · GDPR right-to-erase', description: 'Removes all PII while keeping anonymised clinical aggregates. Cannot be reversed.', buttonLabel: 'Open delete tool', tone: 'critical' },
  { title: 'Decommission entire instance', description: 'Wipes production. Requires written approval from 3 owners and the board.', buttonLabel: 'Begin decommission', tone: 'critical' },
];