// ============================================================
// MindCare — Admin Console: Settings (A09)
// ============================================================

import React, { useState } from 'react';
import { Plus } from 'lucide-react';
import AdminLayout from '../components/admin/AdminLayout';
import Avatar from '../components/common/Avatar';
import {
  SETTINGS_TABS,
  SETTINGS_LAST_CHANGE,
  GENERAL_SETTINGS,
  BRAND_COLORS,
  BRAND_MICROCOPY,
  ROLE_ROWS,
  ROLES_SUMMARY,
  ADMIN_USER_ROWS,
  INTEGRATION_SERVICES,
  INTEGRATIONS_SUMMARY,
  PRICING_PLANS,
  DISCOUNT_CODES,
  PRIVACY_TOGGLES,
  SENSOR_DATA_RETENTION_DAYS,
  ERASURE_QUEUE_SUMMARY,
  NOTIFICATION_ROWS,
  NOTIFICATION_RATE_LIMIT_MAX_PUSH_PER_DAY,
  NOTIFICATION_TEMPLATE,
  FEATURE_FLAGS,
  DANGER_ACTIONS,
} from '../constants/adminSettings';
import { sanitizeText, MAX_LENGTHS } from '../utils/validation';
import type { SettingsTabKey, FeatureFlagStatus } from '../types/adminSettings';

const FLAG_STATUS_STYLES: Record<FeatureFlagStatus, string> = {
  Live: 'bg-emerald-100 text-emerald-700',
  Ramping: 'bg-amber-100 text-amber-700',
  Beta: 'bg-violet-100 text-violet-700',
  Canary: 'bg-orange-100 text-orange-700',
};

const Toggle: React.FC<{ checked: boolean; disabled?: boolean; onChange?: () => void }> = ({ checked, disabled, onChange }) => (
  <button
    type="button"
    role="switch"
    aria-checked={checked}
    disabled={disabled}
    onClick={onChange}
    className={`relative w-11 h-6 rounded-full transition-colors shrink-0 ${
      checked ? 'bg-emerald-600' : 'bg-gray-200'
    } ${disabled ? 'opacity-70 cursor-not-allowed' : 'cursor-pointer'}`}
  >
    <span
      className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${
        checked ? 'translate-x-[22px]' : 'translate-x-0.5'
      }`}
    />
  </button>
);

const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<SettingsTabKey>('general');
  const [general, setGeneral] = useState(GENERAL_SETTINGS);
  const [privacyToggles, setPrivacyToggles] = useState(PRIVACY_TOGGLES);
  const [flagFilter, setFlagFilter] = useState('');
  const [maintenanceOn, setMaintenanceOn] = useState(false);
  const [signupsPaused, setSignupsPaused] = useState(false);
  const [confirmAction, setConfirmAction] = useState<string | null>(null);

  const handleGeneralChange = (field: keyof typeof general, value: string) => {
    setGeneral((prev) => ({ ...prev, [field]: sanitizeText(value).slice(0, MAX_LENGTHS.shortText) }));
  };

  const togglePrivacy = (index: number) => {
    setPrivacyToggles((prev) => {
      const item = prev[index];
      if (item.locked) return prev;
      const next = [...prev];
      next[index] = { ...item, value: !item.value };
      return next;
    });
  };

  const handleDangerClick = (title: string, tone: 'warning' | 'critical') => {
    if (tone === 'critical') {
      // TODO: real API call. Destructive admin ops require 2-eyes
      // approval server-side, written justification, and are always
      // audit-logged — never fire from a single client click alone.
      setConfirmAction(title);
      return;
    }
    if (title.includes('maintenance')) setMaintenanceOn((v) => !v);
    if (title.includes('signups')) setSignupsPaused((v) => !v);
  };

  const filteredFlags = FEATURE_FLAGS.filter((f) => {
    const q = sanitizeText(flagFilter).toLowerCase();
    if (!q) return true;
    return f.key.toLowerCase().includes(q) || f.description.toLowerCase().includes(q);
  });

  return (
    <AdminLayout
      breadcrumb={['Platform', 'Settings', SETTINGS_TABS.find((t) => t.key === activeTab)?.label ?? '']}
      headerAction={
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-gray-500 border border-gray-200 bg-white px-3 py-2 rounded-xl">
            {SETTINGS_LAST_CHANGE}
          </span>
          <button
            type="button"
            className="border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 transition-colors"
          >
            Audit log
          </button>
        </div>
      }
    >
      <h1 className="text-5xl font-black text-gray-900 mb-2">
        Platform <span className="italic font-serif font-normal">settings.</span>
      </h1>
      <p className="text-gray-500 mb-8 max-w-2xl">
        The knobs that affect every user, every therapist, every session. Change carefully · all edits log to audit.
      </p>

      <div className="grid grid-cols-1 xl:grid-cols-[240px_1fr] gap-6">
        {/* Tab rail */}
        <nav className="space-y-1">
          {SETTINGS_TABS.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveTab(tab.key)}
              className={`w-full text-left px-4 py-3 rounded-xl text-sm font-semibold transition-colors ${
                activeTab === tab.key ? 'bg-white shadow-sm border border-gray-100 text-gray-900' : 'text-gray-500 hover:text-gray-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Panel */}
        <div className="space-y-6">
          {/* ——— General ——— */}
          {activeTab === 'general' && (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase">General</p>
                <button type="button" className="bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800">
                  Save changes
                </button>
              </div>
              <h2 className="text-2xl font-black text-gray-900 mb-6">The basics</h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-xs font-semibold tracking-widest text-gray-500 uppercase mb-2">Platform name</label>
                  <input
                    value={general.platformName}
                    onChange={(e) => handleGeneralChange('platformName', e.target.value)}
                    maxLength={MAX_LENGTHS.shortText}
                    className="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold tracking-widest text-gray-500 uppercase mb-2">Support email</label>
                  <input
                    type="email"
                    value={general.supportEmail}
                    onChange={(e) => handleGeneralChange('supportEmail', e.target.value)}
                    maxLength={MAX_LENGTHS.email}
                    className="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold tracking-widest text-gray-500 uppercase mb-2">Default region</label>
                  <input
                    value={general.defaultRegion}
                    onChange={(e) => handleGeneralChange('defaultRegion', e.target.value)}
                    maxLength={MAX_LENGTHS.shortText}
                    className="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold tracking-widest text-gray-500 uppercase mb-2">Default language</label>
                  <input
                    value={general.defaultLanguage}
                    onChange={(e) => handleGeneralChange('defaultLanguage', e.target.value)}
                    maxLength={MAX_LENGTHS.shortText}
                    className="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold tracking-widest text-gray-500 uppercase mb-2">Currency</label>
                  <input
                    value={general.currency}
                    onChange={(e) => handleGeneralChange('currency', e.target.value)}
                    maxLength={10}
                    className="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold tracking-widest text-gray-500 uppercase mb-2">Tax ID</label>
                  <input
                    value={general.taxId}
                    onChange={(e) => handleGeneralChange('taxId', e.target.value)}
                    maxLength={MAX_LENGTHS.shortText}
                    className="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white"
                  />
                </div>
              </div>
            </div>
          )}

          {/* ——— Brand & content ——— */}
          {activeTab === 'brand' && (
            <>
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase">Brand identity</p>
                  <button type="button" className="bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800">
                    Save changes
                  </button>
                </div>
                <h2 className="text-2xl font-black text-gray-900 mb-6">The visible bits</h2>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                  <div className="space-y-4">
                    <div>
                      <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-2">Wordmark</p>
                      <div className="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center">
                        <p className="text-3xl font-black text-gray-900 mb-3">
                          MindCare<span className="text-orange-500">.</span>
                        </p>
                        <button type="button" className="border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2 rounded-xl hover:border-gray-400">
                          Replace
                        </button>
                      </div>
                    </div>
                    <div>
                      <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-2">App icon</p>
                      <div className="border border-gray-200 rounded-xl p-4 flex items-center gap-4">
                        <span className="w-14 h-14 rounded-2xl bg-gray-900 text-white flex items-center justify-center text-xl font-black shrink-0">
                          M.
                        </span>
                        <div className="flex-1 text-sm">
                          <p className="text-gray-900">mindcare-icon-1024.png</p>
                          <p className="text-gray-500 text-xs">1024×1024 · last edited Feb 2026</p>
                        </div>
                        <button type="button" className="border border-gray-200 bg-white text-gray-700 text-xs font-semibold px-3 py-2 rounded-lg hover:border-gray-400 shrink-0">
                          Replace
                        </button>
                      </div>
                    </div>
                  </div>

                  <div>
                    <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-2">Palette · locked to design system</p>
                    <div className="grid grid-cols-2 gap-2 mb-4">
                      {BRAND_COLORS.map((c) => (
                        <div key={c.name} className="rounded-xl p-4" style={{ backgroundColor: c.hex, color: c.name === 'CREAM' || c.name === 'GOLD' ? '#1a1a1a' : '#fff' }}>
                          <p className="text-xs font-bold tracking-widest">{c.name}</p>
                          <p className="text-xs opacity-80">{c.hex}</p>
                        </div>
                      ))}
                    </div>
                    <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-2">Typography</p>
                    <div className="border border-gray-200 rounded-xl p-4">
                      <p className="text-2xl font-serif italic text-gray-900">Fraunces Italic</p>
                      <p className="text-xs text-gray-500">Inter · body and UI</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-1">Voice & microcopy</p>
                <h3 className="text-xl font-black text-gray-900 mb-4">What MindCare sounds like</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {BRAND_MICROCOPY.map((m) => (
                    <div key={m.label} className="border border-gray-100 rounded-xl p-4">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase">{m.label}</p>
                        <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{m.tag}</span>
                      </div>
                      <p className="text-sm text-gray-700 bg-[#F5F0E8] rounded-lg px-3 py-2.5">{m.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* ——— Roles & permissions ——— */}
          {activeTab === 'roles' && (
            <>
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase">Roles</p>
                  <button type="button" className="inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800">
                    <Plus size={14} aria-hidden="true" /> New role
                  </button>
                </div>
                <h2 className="text-2xl font-black text-gray-900 mb-5">Who can do what</h2>

                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs font-semibold tracking-widest text-gray-500 uppercase border-b border-gray-100">
                      <th className="py-3">Role</th>
                      <th className="py-3">Users</th>
                      <th className="py-3">Verify</th>
                      <th className="py-3">Refund</th>
                      <th className="py-3">Moderate</th>
                      <th className="py-3">Unmask PII</th>
                      <th className="py-3">Settings</th>
                      <th className="py-3">Audit</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {ROLE_ROWS.map((r) => (
                      <tr key={r.role}>
                        <td className="py-3.5 font-bold text-gray-900">{r.role}</td>
                        <td className="py-3.5 text-gray-700">{r.users}</td>
                        <td className="py-3.5">
                          <span className={r.verify === '—' ? 'text-gray-300' : 'text-xs font-semibold bg-emerald-100 text-emerald-700 px-2 py-1 rounded-full'}>
                            {r.verify}
                          </span>
                        </td>
                        <td className="py-3.5 text-gray-700">{r.refund}</td>
                        <td className="py-3.5">
                          <span className={r.moderate === '—' ? 'text-gray-300' : 'text-xs font-semibold bg-emerald-100 text-emerald-700 px-2 py-1 rounded-full'}>
                            {r.moderate}
                          </span>
                        </td>
                        <td className="py-3.5">
                          {r.unmaskPii === '—' ? (
                            <span className="text-gray-300">—</span>
                          ) : (
                            <span className="text-xs font-semibold bg-amber-100 text-amber-700 px-2 py-1 rounded-full">{r.unmaskPii}</span>
                          )}
                        </td>
                        <td className="py-3.5 text-gray-700">{r.settingsAccess}</td>
                        <td className="py-3.5 text-gray-700">{r.audit}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase">Admin users</p>
                  <button type="button" className="bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800">
                    Invite admin
                  </button>
                </div>
                <h3 className="text-xl font-black text-gray-900 mb-5">
                  {ROLES_SUMMARY.totalAdmins} admins · {ROLES_SUMMARY.activeNow} active right now
                </h3>

                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs font-semibold tracking-widest text-gray-500 uppercase border-b border-gray-100">
                      <th className="py-3">Name</th>
                      <th className="py-3">Role</th>
                      <th className="py-3">Last sign-in</th>
                      <th className="py-3">2FA</th>
                      <th className="py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {ADMIN_USER_ROWS.map((a) => (
                      <tr key={a.email}>
                        <td className="py-3.5">
                          <div className="flex items-center gap-3">
                            <Avatar initials={a.initials} color={a.avatarColor} size="sm" />
                            <div>
                              <p className="font-bold text-gray-900">{a.name}</p>
                              <p className="text-xs text-gray-500">{a.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="py-3.5">
                          <span className="text-xs font-semibold border border-gray-200 px-2.5 py-1 rounded-full text-gray-700">{a.role}</span>
                        </td>
                        <td className="py-3.5 text-gray-700">{a.lastSignIn}</td>
                        <td className="py-3.5">
                          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${a.twoFA ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-500'}`}>
                            {a.twoFA ? 'On' : 'Off'}
                          </span>
                        </td>
                        <td className="py-3.5">
                          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${a.active ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-500'}`}>
                            ● {a.active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {/* ——— Integrations ——— */}
          {activeTab === 'integrations' && (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase">Connected services</p>
                <div className="flex gap-1">
                  <span className="text-xs font-semibold px-3 py-1.5 rounded-full bg-gray-900 text-white">All · {INTEGRATIONS_SUMMARY.total}</span>
                  <span className="text-xs font-semibold px-3 py-1.5 rounded-full bg-gray-100 text-gray-600">
                    Connected · {INTEGRATIONS_SUMMARY.connected}
                  </span>
                  <span className="text-xs font-semibold px-3 py-1.5 rounded-full bg-gray-100 text-gray-600">
                    Not connected · {INTEGRATIONS_SUMMARY.notConnected}
                  </span>
                </div>
              </div>
              <h2 className="text-2xl font-black text-gray-900 mb-6">The other systems we plug into</h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {INTEGRATION_SERVICES.map((s) => (
                  <div key={s.id} className="border border-gray-100 rounded-xl p-5 flex items-start gap-4">
                    <span className={`w-11 h-11 rounded-xl flex items-center justify-center font-black shrink-0 ${s.color}`}>{s.initial}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-bold text-gray-900">{s.name}</p>
                        <span
                          className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                            s.connected ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                          }`}
                        >
                          {s.connected ? '● Connected' : 'Not connected'}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">{s.description}</p>
                      <p className="text-xs text-gray-400 mt-1">{s.meta}</p>
                    </div>
                    <button
                      type="button"
                      className={`text-sm font-semibold px-3 py-2 rounded-xl shrink-0 ${
                        s.connected ? 'border border-gray-200 bg-white text-gray-700 hover:border-gray-400' : 'bg-gray-900 text-white hover:bg-gray-800'
                      }`}
                    >
                      {s.connected ? 'Manage' : 'Connect'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ——— Pricing & plans ——— */}
          {activeTab === 'pricing' && (
            <>
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase">Client plans</p>
                  <button type="button" className="bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800">
                    Save & publish
                  </button>
                </div>
                <h2 className="text-2xl font-black text-gray-900 mb-6">What people pay</h2>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {PRICING_PLANS.map((p) => (
                    <div key={p.key} className="border border-gray-100 rounded-xl p-5">
                      <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-3">{p.label.toUpperCase()}</p>
                      <div className="border border-gray-200 rounded-lg px-3 py-3 mb-2">
                        <p className="text-2xl font-black text-gray-900">{p.price}</p>
                      </div>
                      <p className="text-xs text-gray-500 mb-4">{p.meta}</p>
                      <div className="flex items-center justify-between">
                        <span className="flex items-center gap-2 text-sm text-gray-700">
                          <Toggle checked={p.visible} /> Visible
                        </span>
                        <button type="button" className="border border-gray-200 bg-white text-gray-700 text-xs font-semibold px-3 py-2 rounded-lg hover:border-gray-400">
                          Edit features
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase">Discounts & scholarships</p>
                  <button type="button" className="inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800">
                    <Plus size={14} aria-hidden="true" /> New code
                  </button>
                </div>
                <h3 className="text-xl font-black text-gray-900 mb-5">Code-based and NGO-funded</h3>

                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs font-semibold tracking-widest text-gray-500 uppercase border-b border-gray-100">
                      <th className="py-3">Code</th>
                      <th className="py-3">Discount</th>
                      <th className="py-3">Cohort</th>
                      <th className="py-3">Used</th>
                      <th className="py-3">Expires</th>
                      <th className="py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {DISCOUNT_CODES.map((d) => (
                      <tr key={d.code}>
                        <td className="py-3.5 font-mono font-bold text-gray-900">{d.code}</td>
                        <td className="py-3.5 text-gray-700">{d.discount}</td>
                        <td className="py-3.5 text-gray-700">{d.cohort}</td>
                        <td className="py-3.5 text-gray-700">
                          {d.used} / {d.total ?? 'open'}
                        </td>
                        <td className="py-3.5 text-gray-700">{d.expires}</td>
                        <td className="py-3.5">
                          <span
                            className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                              d.status === 'Live' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                            }`}
                          >
                            {d.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {/* ——— Privacy & data ——— */}
          {activeTab === 'privacy' && (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase">Defaults · what every new user gets</p>
                <button type="button" className="bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800">
                  Save changes
                </button>
              </div>
              <h2 className="text-2xl font-black text-gray-900 mb-6">Privacy by default, not by opt-in</h2>

              <ul className="divide-y divide-gray-100 mb-6">
                {privacyToggles.map((t, i) => (
                  <li key={t.label} className="py-4 flex items-center justify-between gap-4">
                    <div>
                      <p className="font-bold text-gray-900">
                        {t.label} {t.locked && <span className="text-xs font-normal text-gray-400">· locked by policy</span>}
                      </p>
                      <p className="text-sm text-gray-500">{t.meta}</p>
                    </div>
                    <Toggle checked={t.value} disabled={t.locked} onChange={() => togglePrivacy(i)} />
                  </li>
                ))}
                <li className="py-4 flex items-center justify-between gap-4">
                  <div>
                    <p className="font-bold text-gray-900">Sensor data retention</p>
                    <p className="text-sm text-gray-500">Rolling {SENSOR_DATA_RETENTION_DAYS} days · anonymised after</p>
                  </div>
                  <input readOnly value={`${SENSOR_DATA_RETENTION_DAYS} d`} className="w-24 px-3 py-2 text-sm border border-gray-200 rounded-lg text-center" />
                </li>
              </ul>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="border border-gray-100 rounded-xl p-5">
                  <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-3">Data storage · regions</p>
                  <p className="font-bold text-gray-900 mb-1">Where the data sits</p>
                  <p className="text-sm text-gray-600">All production data stored in-region (Pakistan) · no cross-border replication.</p>
                </div>
                <div className="border border-gray-100 rounded-xl p-5">
                  <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-3">Right-to-erase queue</p>
                  <p className="font-bold text-gray-900 mb-1">
                    {ERASURE_QUEUE_SUMMARY.activeCount} active · {ERASURE_QUEUE_SUMMARY.closedYtd} closed YTD
                  </p>
                  <p className="text-sm text-gray-600">GDPR/PDPA-style erasure requests awaiting processing.</p>
                </div>
              </div>
            </div>
          )}

          {/* ——— Notifications ——— */}
          {activeTab === 'notifications' && (
            <>
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-1">Notification matrix</p>
                <h2 className="text-2xl font-black text-gray-900 mb-5">Who hears what, where</h2>

                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs font-semibold tracking-widest text-gray-500 uppercase border-b border-gray-100">
                      <th className="py-3">Event</th>
                      <th className="py-3">Audience</th>
                      <th className="py-3 text-center">In-app</th>
                      <th className="py-3 text-center">Email</th>
                      <th className="py-3 text-center">SMS</th>
                      <th className="py-3 text-center">Push</th>
                      <th className="py-3 text-center">Slack</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {NOTIFICATION_ROWS.map((n) => (
                      <tr key={n.event}>
                        <td className="py-3.5 font-bold text-gray-900">{n.event}</td>
                        <td className="py-3.5 text-gray-600">{n.audience}</td>
                        <td className="py-3.5 text-center"><Toggle checked={n.inApp} /></td>
                        <td className="py-3.5 text-center"><Toggle checked={n.email} /></td>
                        <td className="py-3.5 text-center"><Toggle checked={n.sms} /></td>
                        <td className="py-3.5 text-center"><Toggle checked={n.push} /></td>
                        <td className="py-3.5 text-center"><Toggle checked={n.slack} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                  <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-4">Rate limits · anti-fatigue</p>
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-gray-700">Max push per client per day</p>
                    <input readOnly value={NOTIFICATION_RATE_LIMIT_MAX_PUSH_PER_DAY} className="w-16 px-3 py-2 text-sm border border-gray-200 rounded-lg text-center" />
                  </div>
                </div>
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                  <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-2">Templates</p>
                  <p className="text-xs font-semibold text-gray-500 uppercase mb-2">{NOTIFICATION_TEMPLATE.title}</p>
                  <p className="text-sm italic text-gray-700">&ldquo;{NOTIFICATION_TEMPLATE.body}&rdquo;</p>
                </div>
              </div>
            </>
          )}

          {/* ——— Feature flags ——— */}
          {activeTab === 'flags' && (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase">Active flags</p>
                <div className="flex items-center gap-2">
                  <input
                    value={flagFilter}
                    onChange={(e) => setFlagFilter(e.target.value.slice(0, MAX_LENGTHS.shortText))}
                    maxLength={MAX_LENGTHS.shortText}
                    placeholder="Filter flags…"
                    className="px-3 py-2 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900"
                  />
                  <button type="button" className="inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800">
                    <Plus size={14} aria-hidden="true" /> New flag
                  </button>
                </div>
              </div>
              <h2 className="text-2xl font-black text-gray-900 mb-5">Roll things out, slowly</h2>

              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs font-semibold tracking-widest text-gray-500 uppercase border-b border-gray-100">
                    <th className="py-3">Flag</th>
                    <th className="py-3">Description</th>
                    <th className="py-3">Cohort</th>
                    <th className="py-3">Rollout</th>
                    <th className="py-3">Owner</th>
                    <th className="py-3">Status</th>
                    <th className="py-3">Since</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredFlags.map((f) => (
                    <tr key={f.key}>
                      <td className="py-4 font-mono text-gray-900">{f.key}</td>
                      <td className="py-4 text-gray-600 max-w-[220px]">{f.description}</td>
                      <td className="py-4 text-gray-600">{f.cohort}</td>
                      <td className="py-4">
                        <div className="flex items-center gap-2 w-32">
                          <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${f.rolloutPercent === 100 ? 'bg-emerald-600' : f.rolloutPercent >= 30 ? 'bg-amber-500' : 'bg-violet-500'}`}
                              style={{ width: `${f.rolloutPercent}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-500 w-9 text-right">{f.rolloutPercent}%</span>
                        </div>
                      </td>
                      <td className="py-4 text-gray-700">{f.owner}</td>
                      <td className="py-4">
                        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${FLAG_STATUS_STYLES[f.status]}`}>{f.status}</span>
                      </td>
                      <td className="py-4 text-gray-500">{f.since}</td>
                    </tr>
                  ))}
                  {filteredFlags.length === 0 && (
                    <tr>
                      <td colSpan={7} className="py-6 text-center text-gray-400">
                        No flags match &ldquo;{flagFilter}&rdquo;.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          {/* ——— Danger zone ——— */}
          {activeTab === 'danger' && (
            <div className="space-y-4">
              <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6">
                <p className="font-black text-gray-900 text-lg mb-1">⚠ Operations that <span className="italic text-orange-700">cannot</span> be undone.</p>
                <p className="text-sm text-gray-600">
                  Every action here writes to the audit log and pages the owner. Two-eyes required on all destructive
                  operations.
                </p>
              </div>

              {confirmAction && (
                <div className="bg-red-50 border border-red-200 rounded-2xl p-5 flex items-center justify-between gap-4">
                  <p className="text-sm text-red-800">
                    <strong>{confirmAction}</strong> requires a second admin&apos;s approval and cannot be reversed.
                    This demo does not execute it.
                  </p>
                  <button
                    type="button"
                    onClick={() => setConfirmAction(null)}
                    className="text-sm font-semibold text-red-700 hover:text-red-900 shrink-0"
                  >
                    Dismiss
                  </button>
                </div>
              )}

              {DANGER_ACTIONS.map((action) => {
                const isMaintenance = action.title.includes('maintenance');
                const isSignups = action.title.includes('signups');
                const isActive = (isMaintenance && maintenanceOn) || (isSignups && signupsPaused);
                return (
                  <div
                    key={action.title}
                    className={`bg-white rounded-2xl shadow-sm border p-6 flex items-center justify-between gap-4 ${
                      action.tone === 'critical' ? 'border-red-200' : 'border-gray-100'
                    }`}
                  >
                    <div>
                      <p className="font-bold text-gray-900 mb-1">{action.title}</p>
                      <p className="text-sm text-gray-500">{action.description}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => handleDangerClick(action.title, action.tone)}
                      className={`text-sm font-semibold px-4 py-2.5 rounded-xl shrink-0 transition-colors ${
                        action.tone === 'critical'
                          ? 'bg-red-600 text-white hover:bg-red-700'
                          : isActive
                          ? 'bg-amber-600 text-white hover:bg-amber-700'
                          : 'border border-amber-300 text-amber-700 hover:bg-amber-50'
                      }`}
                    >
                      {isActive && isMaintenance ? 'Disable maintenance' : isActive && isSignups ? 'Resume signups' : action.buttonLabel}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </AdminLayout>
  );
};

export default SettingsPage;