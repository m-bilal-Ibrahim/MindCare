// ============================================================
// MindCare — Therapist Console: Today ("Good morning, Tariq.")
// ============================================================

import React from 'react';
import { Link } from 'react-router-dom';
import { Video, FileText, Check, Pencil, ArrowRight, Plus } from 'lucide-react';
import TherapistLayout from '../components/therapist/TherapistLayout';
import Sparkline from '../components/therapist/Sparkline';
import Avatar from '../components/common/Avatar';
import { useTherapistAuth } from '../utils/authGuard';
import {
  TODAY_SESSIONS,
  TODAY_SENSOR_FLAGS,
  TODAY_AI_SUGGESTIONS,
  TODAY_AI_SUGGESTIONS_TOTAL,
  TODAY_STATS,
  buildPatientDetailRoute,
} from '../constants/therapistConsole';

const STATUS_STYLES: Record<string, string> = {
  next: 'bg-emerald-100 text-emerald-700',
  confirmed: 'bg-gray-100 text-gray-700',
  pending: 'bg-amber-100 text-amber-700',
};

const TREND_COLORS: Record<string, string> = {
  green: '#15803d',
  red: '#dc2626',
  neutral: '#1a1a1a',
};

const TherapistTodayPage: React.FC = () => {
  const { therapist } = useTherapistAuth();
  const firstName = therapist?.name.replace('Dr. ', '').split(' ')[0] ?? 'there';

  const today = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });

  return (
    <TherapistLayout
      breadcrumb={['Practice', 'Today']}
      headerAction={
        <button
          type="button"
          className="inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 transition-colors shrink-0"
        >
          <Plus size={15} aria-hidden="true" /> New note
        </button>
      }
    >
      <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-2">{today}</p>
      <h1 className="text-4xl font-black text-gray-900 mb-2">
        Good morning, <span className="italic font-serif font-normal">{firstName}.</span>
      </h1>
      <p className="text-gray-600 mb-8">
        {TODAY_SESSIONS.length} sessions today · {TODAY_SENSOR_FLAGS.length + 4} pending requests · 1 sensor flag
        worth a look.
      </p>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-8">
        {/* Sessions list */}
        <div className="xl:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase">Today · Sessions</p>
            <button type="button" className="text-sm text-gray-500 hover:text-gray-900 flex items-center gap-1">
              Open schedule <ArrowRight size={13} aria-hidden="true" />
            </button>
          </div>
          <h2 className="text-lg font-bold text-gray-900 mb-4">Your day at a glance</h2>

          <ul className="divide-y divide-gray-100">
            {TODAY_SESSIONS.map((session) => (
              <li key={session.id} className="py-4 flex items-center gap-4">
                <div className="w-20 shrink-0">
                  <p className="font-bold text-gray-900 text-sm">{session.time}</p>
                  <p className="text-xs text-gray-400">{session.durationMin} min</p>
                </div>
                <Avatar initials={session.patientInitials} color={session.avatarColor} size="sm" />
                <div className="flex-1 min-w-0">
                  <Link
                    to={buildPatientDetailRoute(session.patientId)}
                    className="font-semibold text-gray-900 hover:underline truncate block"
                  >
                    {session.patientName}
                  </Link>
                  <p className="text-xs text-gray-500 truncate">{session.label}</p>
                </div>
                <span
                  className={`text-xs font-semibold px-2.5 py-1 rounded-full shrink-0 ${STATUS_STYLES[session.status]}`}
                >
                  {session.status === 'next' && '● '}
                  {session.status === 'next' ? `Next · ${session.statusMeta}` : session.status === 'confirmed' ? 'Confirmed' : 'Pending'}
                </span>
                <button
                  type="button"
                  className="inline-flex items-center gap-1.5 border border-gray-200 text-gray-700 text-xs font-semibold px-3 py-2 rounded-lg hover:border-gray-400 shrink-0"
                >
                  <Video size={13} aria-hidden="true" /> Meet
                </button>
                <Link
                  to={buildPatientDetailRoute(session.patientId)}
                  className="inline-flex items-center gap-1.5 bg-gray-900 text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-gray-800 shrink-0"
                >
                  <FileText size={13} aria-hidden="true" /> Open notes
                </Link>
              </li>
            ))}
          </ul>
        </div>

        {/* Right column: needs review + AI suggestions */}
        <div className="space-y-6">
          {TODAY_SENSOR_FLAGS.length > 0 && (
            <div className="bg-orange-50 border border-orange-200 rounded-2xl p-6">
              <p className="text-xs font-semibold tracking-widest text-orange-600 uppercase mb-4">Needs review</p>
              {TODAY_SENSOR_FLAGS.map((flag) => (
                <div key={flag.id} className="flex items-start gap-3 mb-4">
                  <Avatar initials={flag.patientInitials} color={flag.avatarColor} />
                  <div className="min-w-0">
                    <p className="font-bold text-gray-900 text-sm truncate">{flag.patientName} · sensor flag</p>
                    <p className="text-sm text-gray-600 leading-snug">{flag.summary}</p>
                  </div>
                </div>
              ))}
              <div className="flex gap-2">
                <Link
                  to={buildPatientDetailRoute(TODAY_SENSOR_FLAGS[0].patientId)}
                  className="bg-gray-900 text-white text-xs font-semibold px-4 py-2 rounded-lg hover:bg-gray-800"
                >
                  Open file
                </Link>
                <button type="button" className="bg-white border border-gray-200 text-gray-700 text-xs font-semibold px-4 py-2 rounded-lg hover:border-gray-400">
                  Dismiss
                </button>
              </div>
            </div>
          )}

          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-1">AI suggestions</p>
            <h3 className="text-sm font-bold text-gray-900 mb-4">To review</h3>
            <ul className="space-y-4">
              {TODAY_AI_SUGGESTIONS.map((s) => (
                <li key={s.id} className="flex items-start justify-between gap-3">
                  <p className="text-sm text-gray-800 leading-snug">
                    <span className="font-semibold">{s.patientName}</span> · {s.suggestion}
                  </p>
                  <div className="flex gap-1.5 shrink-0">
                    <button
                      type="button"
                      aria-label={`Approve suggestion for ${s.patientName}`}
                      className="w-7 h-7 rounded-lg border border-gray-200 flex items-center justify-center text-gray-500 hover:border-emerald-400 hover:text-emerald-600"
                    >
                      <Check size={13} />
                    </button>
                    <button
                      type="button"
                      aria-label={`Edit suggestion for ${s.patientName}`}
                      className="w-7 h-7 rounded-lg border border-gray-200 flex items-center justify-center text-gray-500 hover:border-gray-400"
                    >
                      <Pencil size={13} />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
            <button type="button" className="text-sm text-gray-500 hover:text-gray-900 mt-4 flex items-center gap-1">
              Review all {TODAY_AI_SUGGESTIONS_TOTAL} <ArrowRight size={13} aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {TODAY_STATS.map((stat) => (
          <div key={stat.label} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-3">{stat.label}</p>
            <div className="flex items-end justify-between">
              <div>
                <p className="text-3xl font-black text-gray-900">{stat.value}</p>
                {stat.delta && <p className="text-xs text-gray-500 mt-1">{stat.delta}</p>}
              </div>
              <Sparkline data={stat.trend} color={TREND_COLORS[stat.trendColor]} />
            </div>
          </div>
        ))}
      </div>
    </TherapistLayout>
  );
};

export default TherapistTodayPage;