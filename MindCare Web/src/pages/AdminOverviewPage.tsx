// ============================================================
// MindCare — Admin Console: Overview
// ============================================================

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { AreaChart, Area, Line, ComposedChart, ResponsiveContainer, XAxis, Tooltip } from 'recharts';
import { Download, Bell as BellIcon, ArrowRight } from 'lucide-react';
import AdminLayout from '../components/admin/AdminLayout';
import Avatar from '../components/common/Avatar';
import {
  PLATFORM_STATS,
  GROWTH_CHART_DATA,
  RETENTION_WEEK4,
  VERIFICATION_QUEUE_PREVIEW,
  VERIFICATION_QUEUE_SUMMARY,
  SAFETY_LAST_24H,
  MODERATION_QUEUE_OPEN,
  COMMUNITY_TOP_CIRCLES,
  ADMIN_ROUTES,
} from '../constants/adminConsole';

const STATUS_TONE_STYLES: Record<string, string> = {
  default: 'bg-gray-100 text-gray-700',
  new: 'bg-amber-100 text-amber-700',
  flag: 'bg-red-100 text-red-700',
  wait: 'bg-gray-100 text-gray-500',
};

type GrowthRange = '90d' | '1y' | 'All';

const AdminOverviewPage: React.FC = () => {
  const [range, setRange] = useState<GrowthRange>('90d');
  const totalWaiting =
    VERIFICATION_QUEUE_SUMMARY.therapists + VERIFICATION_QUEUE_SUMMARY.ngoPartners + VERIFICATION_QUEUE_SUMMARY.hospitalPartners;

  const today = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });

  return (
    <AdminLayout
      breadcrumb={['Operations', 'Overview']}
      headerAction={
        <div className="flex gap-2 shrink-0">
          <button
            type="button"
            className="inline-flex items-center gap-2 border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 transition-colors"
          >
            <Download size={15} aria-hidden="true" /> Weekly report
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 transition-colors"
          >
            <BellIcon size={15} aria-hidden="true" /> View all alerts
          </button>
        </div>
      }
    >
      <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-2">{today}</p>
      <h1 className="text-4xl font-black text-gray-900 mb-2">
        Platform <span className="italic font-serif font-normal">today.</span>
      </h1>
      <p className="text-gray-600 mb-8">
        All systems nominal. {VERIFICATION_QUEUE_SUMMARY.therapists} therapist credentials waiting ·{' '}
        {MODERATION_QUEUE_OPEN} moderation items · 0 active SOS.
      </p>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4 mb-6">
        {PLATFORM_STATS.map((stat) => {
          const chartData = stat.trend.map((v, i) => ({ i, v }));
          const strokeColor =
            stat.trendColor === 'green' ? '#15803d' : stat.trendColor === 'red' ? '#dc2626' : stat.trendColor === 'gold' ? '#b45309' : '#1a1a1a';
          return (
            <div key={stat.label} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
              <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-2">{stat.label}</p>
              <p className="text-2xl font-black text-gray-900 mb-0.5">
                {stat.value} {stat.delta && <span className="text-sm font-semibold text-gray-400">{stat.delta}</span>}
              </p>
              <p className="text-xs text-gray-500 mb-2">{stat.meta}</p>
              <div style={{ height: 32 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ top: 2, right: 0, bottom: 0, left: 0 }}>
                    <defs>
                      <linearGradient id={`grad-${stat.label}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={strokeColor} stopOpacity={0.2} />
                        <stop offset="100%" stopColor={strokeColor} stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <Area type="monotone" dataKey="v" stroke={strokeColor} strokeWidth={1.5} fill={`url(#grad-${stat.label})`} isAnimationActive={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-6">
        {/* Growth chart */}
        <div className="xl:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase">Growth · 90 days</p>
            <div className="flex gap-1">
              {(['90d', '1y', 'All'] as GrowthRange[]).map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => setRange(r)}
                  className={`text-xs font-semibold px-3 py-1.5 rounded-full transition-colors ${
                    range === r ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-4">Users, sessions, retention</h2>

          <div style={{ height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={GROWTH_CHART_DATA} margin={{ top: 4, right: 4, bottom: 0, left: 4 }}>
                <defs>
                  <linearGradient id="growthGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#166534" stopOpacity={0.15} />
                    <stop offset="100%" stopColor="#166534" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#9ca3af' }} interval={5} />
                <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid #e5e7eb', fontSize: 12 }} />
                <Area type="monotone" dataKey="activeUsers" stroke="#166534" strokeWidth={2} fill="url(#growthGradient)" isAnimationActive={false} name="Active users (k)" />
                <Line type="monotone" dataKey="sessions" stroke="#f97316" strokeWidth={2} strokeDasharray="4 3" dot={false} isAnimationActive={false} name="Sessions (×100)" />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          <div className="flex items-center justify-between mt-3">
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-0.5 bg-emerald-700" /> Active users (k)
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-0.5 bg-orange-500" style={{ borderTop: '1.5px dashed' }} /> Sessions (×100)
              </span>
            </div>
            <p className="text-sm text-gray-700">
              Retention W4: <span className="font-bold text-gray-900">{RETENTION_WEEK4}</span>
            </p>
          </div>
        </div>

        {/* Needs you */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs font-semibold tracking-widest text-orange-600 uppercase">Needs you</p>
            <span className="text-xs font-semibold text-orange-700 bg-orange-100 px-2.5 py-1 rounded-full">
              {totalWaiting} waiting
            </span>
          </div>
          <h3 className="text-lg font-bold text-gray-900 mb-4">Verification queue</h3>

          <ul className="divide-y divide-gray-100">
            {VERIFICATION_QUEUE_PREVIEW.map((item) => (
              <li key={item.id} className="py-3 flex items-center gap-3">
                <Avatar initials={item.initials} color={item.avatarColor} size="sm" />
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-gray-900 text-sm truncate">{item.name}</p>
                  <p className="text-xs text-gray-500 truncate">{item.meta}</p>
                </div>
                <div className="text-right shrink-0">
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${STATUS_TONE_STYLES[item.statusTone]}`}>
                    {item.statusTag}
                  </span>
                  <p className="text-[11px] text-gray-400 mt-1">{item.timeAgo}</p>
                </div>
              </li>
            ))}
          </ul>

          <Link
            to={ADMIN_ROUTES.VERIFICATIONS}
            className="text-sm text-gray-500 hover:text-gray-900 mt-4 flex items-center gap-1"
          >
            Open queue <ArrowRight size={13} aria-hidden="true" />
          </Link>
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-1">Safety · Live</p>
          <h3 className="text-lg font-bold text-gray-900 mb-3">Last 24h</h3>
          <p className="text-sm text-gray-600">
            {SAFETY_LAST_24H.resolved} SOS resolved · avg {SAFETY_LAST_24H.avgResponseMin} min response
          </p>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-1">Moderation queue</p>
          <h3 className="text-lg font-bold text-gray-900 mb-3">{MODERATION_QUEUE_OPEN} items open</h3>
          <p className="text-sm text-gray-600">Community posts flagged for medical-advice risk or abuse.</p>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-1">Community · Top circles</p>
          <h3 className="text-lg font-bold text-gray-900 mb-3">What&apos;s alive this week</h3>
          <div className="flex flex-wrap gap-2">
            {COMMUNITY_TOP_CIRCLES.map((c) => (
              <span key={c} className="text-xs font-semibold px-2.5 py-1 rounded-full bg-gray-100 text-gray-600">
                {c}
              </span>
            ))}
          </div>
        </div>
      </div>
    </AdminLayout>
  );
};

export default AdminOverviewPage;