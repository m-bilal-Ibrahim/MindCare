// ============================================================
// MindCare — Therapist Console: Profile & Availability
// ============================================================

import React, { useState } from 'react';
import { Eye, Pencil, Download, Star, ArrowRight } from 'lucide-react';
import TherapistLayout from '../components/therapist/TherapistLayout';
import Avatar from '../components/common/Avatar';
import {
  THERAPIST_PROFILE,
  THERAPIST_AVAILABILITY,
  AVAILABILITY_HOURS,
  PROFILE_TABS,
} from '../constants/therapistConsole';
import type { AvailabilitySlot, AvailabilityStatus } from '../types/therapistConsole';

const DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];

const STATUS_CYCLE: AvailabilityStatus[] = ['open', 'tentative', 'blocked', 'closed'];

const STATUS_STYLES: Record<AvailabilityStatus, string> = {
  open: 'bg-emerald-50 text-emerald-700 border border-emerald-100',
  tentative: 'bg-amber-100 text-amber-800 border border-amber-200 font-bold',
  blocked: 'bg-gray-900 text-white',
  closed: 'bg-transparent',
};

type ProfileTab = (typeof PROFILE_TABS)[number];

const ProfilePage: React.FC = () => {
  const profile = THERAPIST_PROFILE;
  const [activeTab, setActiveTab] = useState<ProfileTab>('Availability');
  const [slots, setSlots] = useState<Map<string, AvailabilitySlot>>(
    () => new Map(THERAPIST_AVAILABILITY.map((s) => [`${s.day}-${s.hour}`, s]))
  );

  const handleCellClick = (day: number, hour: number) => {
    const key = `${day}-${hour}`;
    const current = slots.get(key)?.status ?? 'closed';
    const nextIndex = (STATUS_CYCLE.indexOf(current) + 1) % STATUS_CYCLE.length;
    const next = STATUS_CYCLE[nextIndex];
    setSlots((prev) => new Map(prev).set(key, { day, hour, status: next }));
  };

  const renderCell = (day: number, hour: number) => {
    const slot = slots.get(`${day}-${hour}`);
    const status = slot?.status ?? 'closed';

    return (
      <button
        key={`${day}-${hour}`}
        type="button"
        onClick={() => handleCellClick(day, hour)}
        className={`h-11 rounded-lg text-[11px] font-semibold flex items-center justify-center transition-colors hover:opacity-80 ${STATUS_STYLES[status]}`}
        aria-label={`${DAYS[day]} ${hour}:00 — ${status}`}
      >
        {status === 'open' && 'OPEN'}
        {status === 'tentative' && 'TENT'}
        {status === 'blocked' && '•'}
      </button>
    );
  };

  return (
    <TherapistLayout breadcrumb={['Account', 'Profile & availability']}>
      <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6 mb-8">
        <div className="flex items-start gap-5">
          <div className="relative shrink-0">
            <Avatar initials="TM" color="bg-blue-950" size="lg" />
            <span className="absolute -bottom-1 -right-1 w-7 h-7 rounded-full bg-gray-900 border-2 border-[#F5F0E8] flex items-center justify-center text-white">
              <Eye size={12} />
            </span>
          </div>
          <div>
            <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-1">
              {profile.title} · Verified {profile.verifiedDate}
            </p>
            <h1 className="text-4xl font-black text-gray-900 mb-2">{profile.name}</h1>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-gray-500 mb-3">
              <span>
                {profile.yearsExperience} years · {profile.license}
              </span>
              <span>{profile.city}</span>
              <span>{profile.timezone}</span>
              <span>
                {profile.languages.join(' · ')} · <Star size={12} className="inline -mt-0.5 fill-amber-400 text-amber-400" />{' '}
                {profile.rating.toFixed(1)} · {profile.reviewCount} reviews
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="text-xs font-semibold px-3 py-1 rounded-full bg-rose-100 text-rose-700">
                {profile.specialtyTags[0]}
              </span>
              <span className="text-xs font-semibold px-3 py-1 rounded-full bg-violet-100 text-violet-700">
                {profile.specialtyTags[1]}
              </span>
              <span className="text-xs font-semibold px-3 py-1 rounded-full bg-emerald-100 text-emerald-700">
                {profile.approachTags.join(' · ')}
              </span>
              {profile.acceptsTrials && (
                <span className="text-xs font-semibold px-3 py-1 rounded-full border border-gray-200 text-gray-700">
                  Accepts trials
                </span>
              )}
              <span className="text-xs font-semibold px-3 py-1 rounded-full border border-gray-200 text-gray-700">
                {profile.inNetworkNote}
              </span>
            </div>
          </div>
        </div>

        <div className="flex gap-2 shrink-0">
          <button
            type="button"
            className="inline-flex items-center gap-2 border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 transition-colors"
          >
            <Eye size={15} aria-hidden="true" /> View public profile
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 transition-colors"
          >
            <Pencil size={15} aria-hidden="true" /> Edit profile
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-6 border-b border-gray-200 mb-8 overflow-x-auto">
        {PROFILE_TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            className={`pb-3 text-sm font-semibold whitespace-nowrap border-b-2 transition-colors ${
              activeTab === tab ? 'text-gray-900 border-gray-900' : 'text-gray-400 border-transparent hover:text-gray-600'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab !== 'Availability' && activeTab !== 'Reviews' && activeTab !== 'Earnings & wallet' ? (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center text-gray-400">
          {activeTab} — coming soon in this demo.
        </div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Main column */}
          <div className="xl:col-span-2 space-y-6">
            {activeTab === 'Availability' && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-center justify-between mb-1">
                  <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase">
                    Your week · Standard availability
                  </p>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      className="border border-gray-200 text-gray-700 text-sm font-semibold px-3 py-2 rounded-xl hover:border-gray-400"
                    >
                      Apply for 4 weeks
                    </button>
                    <button
                      type="button"
                      className="bg-gray-900 text-white text-sm font-semibold px-3 py-2 rounded-xl hover:bg-gray-800"
                    >
                      Save changes
                    </button>
                  </div>
                </div>
                <h2 className="text-2xl font-black text-gray-900 mb-6">When patients can request you</h2>

                <div className="grid" style={{ gridTemplateColumns: '48px repeat(7, 1fr)' }}>
                  <div />
                  {DAYS.map((d) => (
                    <p key={d} className="text-xs font-semibold tracking-widest text-gray-400 text-center pb-2">
                      {d}
                    </p>
                  ))}

                  {AVAILABILITY_HOURS.map((hour) => (
                    <React.Fragment key={hour}>
                      <p className="text-xs text-gray-400 flex items-center pr-2">{hour}:00</p>
                      {DAYS.map((_, dayIndex) => (
                        <div key={`${dayIndex}-${hour}`} className="p-0.5">
                          {renderCell(dayIndex, hour)}
                        </div>
                      ))}
                    </React.Fragment>
                  ))}
                </div>

                <p className="text-xs text-gray-400 mt-4">
                  Click a cell to cycle Open → Tentative → Blocked → Closed. Patients only see Open slots as
                  requestable.
                </p>
              </div>
            )}

            {activeTab === 'Reviews' && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-4">
                  Ratings · 12 months
                </p>
                <div className="flex items-center gap-8 mb-6">
                  <div>
                    <p className="text-5xl font-black text-gray-900">{profile.rating.toFixed(1)}</p>
                    <p className="text-sm text-gray-500">of 5 · {profile.reviewCount} reviews</p>
                  </div>
                  <div className="flex-1 space-y-1.5">
                    {profile.ratingBreakdown.map((r) => (
                      <div key={r.stars} className="flex items-center gap-2 text-xs text-gray-500">
                        <span className="w-3">{r.stars}</span>
                        <Star size={11} className="fill-amber-400 text-amber-400" />
                        <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-emerald-600 rounded-full"
                            style={{ width: `${(r.count / profile.reviewCount) * 100}%` }}
                          />
                        </div>
                        <span className="w-8 text-right">{r.count}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-4">
                  What your people say
                </p>
                <ul className="divide-y divide-gray-100">
                  {profile.recentReviews.map((r) => (
                    <li key={r.id} className="py-4 flex items-start gap-3">
                      <Avatar initials={r.initials} color={r.color} size="sm" />
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap mb-1">
                          <p className="font-bold text-gray-900 text-sm">{r.handle}</p>
                          <span className="flex items-center gap-0.5">
                            {Array.from({ length: r.rating }).map((_, i) => (
                              <Star key={i} size={11} className="fill-amber-400 text-amber-400" />
                            ))}
                          </span>
                          <span className="text-xs text-gray-400">{r.timeAgo}</span>
                        </div>
                        <p className="text-sm text-gray-600 leading-relaxed">{r.content}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {activeTab === 'Earnings & wallet' && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <p className="text-sm text-gray-500 leading-relaxed">
                  Detailed payout history and tax documents are available via the wallet panel on the right.
                </p>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <aside className="space-y-6">
            <div className="bg-gray-950 rounded-2xl p-6 text-white">
              <p className="text-xs font-semibold tracking-widest text-orange-400 uppercase mb-1">
                Wallet · May
              </p>
              <p className="text-4xl font-black mb-1">
                {profile.walletBalance} <span className="text-sm font-semibold text-emerald-400">{profile.walletDeltaVsLastMonth}</span>
              </p>
              <p className="text-sm text-gray-400 mb-5">
                {profile.sessionsBilled} sessions billed · payout on {profile.payoutDate} to {profile.payoutAccount}
              </p>
              <div className="flex flex-wrap gap-2 mb-5">
                <button
                  type="button"
                  className="inline-flex items-center gap-1.5 bg-white text-gray-900 text-xs font-semibold px-3 py-2 rounded-lg hover:bg-gray-100"
                >
                  <Download size={12} aria-hidden="true" /> Withdraw
                </button>
                <button
                  type="button"
                  className="border border-white/20 text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-white/10"
                >
                  History
                </button>
                <button
                  type="button"
                  className="border border-white/20 text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-white/10"
                >
                  Tax docs
                </button>
              </div>
              <div style={{ height: 40 }} className="opacity-70">
                <svg viewBox="0 0 200 40" className="w-full h-full" preserveAspectRatio="none">
                  <polyline
                    points="0,35 30,32 60,28 90,25 120,20 150,12 200,4"
                    fill="none"
                    stroke="white"
                    strokeWidth="1.5"
                  />
                </svg>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setActiveTab('Reviews')}
              className="w-full bg-white rounded-2xl shadow-sm border border-gray-100 p-6 text-left hover:border-gray-300 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-3xl font-black text-gray-900">{profile.rating.toFixed(1)}</p>
                  <p className="text-sm text-gray-500">
                    {profile.reviewCount} reviews · See all <ArrowRight size={11} className="inline" aria-hidden="true" />
                  </p>
                </div>
                <span className="flex items-center gap-0.5">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Star key={i} size={16} className="fill-amber-400 text-amber-400" />
                  ))}
                </span>
              </div>
            </button>
          </aside>
        </div>
      )}
    </TherapistLayout>
  );
};

export default ProfilePage;