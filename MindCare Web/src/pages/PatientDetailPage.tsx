// ============================================================
// MindCare — Therapist Console: Patient Detail
// ============================================================

import React, { useState } from 'react';
import { useParams, Navigate } from 'react-router-dom';
import { AreaChart, Area, ResponsiveContainer, YAxis } from 'recharts';
import { Video, MessageSquare, Plus, X, Zap, Code } from 'lucide-react';
import TherapistLayout from '../components/therapist/TherapistLayout';
import Sparkline from '../components/therapist/Sparkline';
import Avatar from '../components/common/Avatar';
import {
  CONSOLE_PATIENTS,
  LAYLA_DETAIL,
  PATIENT_DETAIL_TABS,
  CONSOLE_ROUTES,
} from '../constants/therapistConsole';

type Tab = (typeof PATIENT_DETAIL_TABS)[number];

const PatientDetailPage: React.FC = () => {
  const { patientId } = useParams<{ patientId: string }>();
  const [activeTab, setActiveTab] = useState<Tab>('Overview');
  const [moodRange, setMoodRange] = useState<'30d' | '90d' | '1y'>('30d');

  const patient = CONSOLE_PATIENTS.find((p) => p.id === patientId);
  if (!patient) {
    return <Navigate to={CONSOLE_ROUTES.PATIENTS} replace />;
  }

  // Full clinical mock content (notes, sensors, Aida) is only fully
  // authored for the Layla example patient; other patients reuse it
  // here as illustrative dummy content for reviewing the UI/data flow.
  const detail = { ...LAYLA_DETAIL, patient };
  const isDemoContent = patient.id !== 'p-layla';

  const chartData = detail.moodChart.map((value, i) => ({ i, value }));

  return (
    <TherapistLayout
      breadcrumb={['Practice', 'Patients', patient.name]}
      headerAction={
        <div className="flex gap-2 shrink-0">
          <button
            type="button"
            className="inline-flex items-center gap-2 border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 transition-colors"
          >
            <MessageSquare size={15} aria-hidden="true" /> Message
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 transition-colors"
          >
            <Video size={15} aria-hidden="true" /> Start session
          </button>
        </div>
      }
    >
      {isDemoContent && (
        <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-6">
          Demo note: clinical notes, sensors, and Aida panels below show illustrative sample data for
          reviewing the UI, not data specific to {patient.name.split(' ')[0]}.
        </p>
      )}

      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6 mb-8">
        <div className="flex items-start gap-5">
          <Avatar initials={patient.initials} color={patient.avatarColor} size="lg" />
          <div>
            <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-1">
              Patient · {detail.patientCode}
            </p>
            <h1 className="text-4xl font-black text-gray-900 mb-2">{patient.name}</h1>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-gray-500 mb-3">
              <span>
                {patient.age} · {patient.city === 'Islamabad' || patient.city === 'Lahore' ? 'Woman' : ''}
              </span>
              <span>{patient.city}, PK</span>
              <span>Joined {detail.joined}</span>
              <span>{detail.billing}</span>
              <span>{detail.medication}</span>
              <span>{detail.languages}</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {patient.focus.map((f, i) => (
                <span
                  key={f}
                  className={`text-xs font-semibold px-3 py-1 rounded-full ${
                    ['bg-rose-100 text-rose-700', 'bg-violet-100 text-violet-700', 'bg-emerald-100 text-emerald-700'][i % 3]
                  }`}
                >
                  {f}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="flex gap-4 shrink-0">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 px-5 py-4 text-center min-w-[100px]">
            <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-1">Streak</p>
            <p className="text-2xl font-black text-gray-900">{patient.streakDays}d</p>
            <p className="text-xs text-gray-500">check-ins</p>
          </div>
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 px-5 py-4 text-center min-w-[100px]">
            <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-1">Sessions</p>
            <p className="text-2xl font-black text-gray-900">{detail.totalSessions}</p>
            <p className="text-xs text-gray-500">
              {detail.sessionsThisMonth} of {detail.sessionsMonthlyTarget} this month
            </p>
          </div>
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 px-5 py-4 text-center min-w-[100px]">
            <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-1">Avg mood</p>
            <p className="text-2xl font-black text-emerald-700">
              {patient.mood30d.toFixed(1)} <span className="text-sm font-semibold">{detail.avgMoodDelta}</span>
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-6 border-b border-gray-200 mb-8 overflow-x-auto">
        {PATIENT_DETAIL_TABS.map((tab) => (
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

      {activeTab !== 'Overview' ? (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center text-gray-400">
          {getTabPlaceholder(activeTab)}
        </div>
      ) : (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Mood chart + notes */}
          <div className="xl:col-span-2 space-y-6">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase">Mood · {moodRange}</p>
                <div className="flex gap-1">
                  {(['30d', '90d', '1y'] as const).map((range) => (
                    <button
                      key={range}
                      type="button"
                      onClick={() => setMoodRange(range)}
                      className={`text-xs font-semibold px-3 py-1.5 rounded-full ${
                        moodRange === range ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {range}
                    </button>
                  ))}
                </div>
              </div>
              <h2 className="text-xl font-bold text-gray-900 mb-4">{detail.moodChartLabel}</h2>

              <div style={{ height: 180 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ top: 4, right: 4, bottom: 4, left: 4 }}>
                    <defs>
                      <linearGradient id="moodGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#166534" stopOpacity={0.25} />
                        <stop offset="100%" stopColor="#166534" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <YAxis hide domain={['dataMin - 0.5', 'dataMax + 0.5']} />
                    <Area type="monotone" dataKey="value" stroke="#166534" strokeWidth={2} fill="url(#moodGradient)" isAnimationActive={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>{detail.moodChartDates[0]}</span>
                <span>{detail.moodChartDates[1]}</span>
                <span>{detail.moodChartDates[2]}</span>
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-4">
                <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase">Session notes</p>
                <button
                  type="button"
                  className="inline-flex items-center gap-1.5 bg-gray-900 text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-gray-800"
                >
                  <Plus size={13} aria-hidden="true" /> New note
                </button>
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-4">Latest entries</h3>
              <ul className="divide-y divide-gray-100">
                {detail.sessionNotes.map((note) => (
                  <li key={note.id} className="py-4">
                    <p className="text-sm font-bold text-gray-900">{note.date}</p>
                    <p className="text-xs text-gray-500 mb-2">{note.meta}</p>
                    <p className="text-sm text-gray-700 leading-relaxed">{note.content}</p>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Right column: MindBand + Aida */}
          <div className="space-y-6">
            <div className="bg-gray-950 rounded-2xl p-6 text-white">
              <p className="text-xs font-semibold tracking-widest text-orange-400 uppercase mb-1">MindBand · Live</p>
              <h3 className="text-lg font-bold mb-5">Body, this week</h3>
              <div className="grid grid-cols-2 gap-5">
                {detail.bodyMetrics.map((metric) => (
                  <div key={metric.label}>
                    <p className="text-[11px] font-semibold tracking-widest text-gray-400 uppercase mb-1">
                      {metric.label}
                    </p>
                    <p className="text-2xl font-black mb-1">
                      {metric.value} <span className="text-sm font-medium text-gray-400">{metric.unit}</span>
                    </p>
                    <Sparkline data={metric.trend} color={metric.color} height={24} />
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-1">
                <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase flex items-center gap-1.5">
                  <Code size={13} aria-hidden="true" /> Aida · Recommendations
                </p>
                <span className="text-xs font-semibold bg-emerald-100 text-emerald-700 px-2.5 py-1 rounded-full">
                  {detail.aidaPendingCount} pending
                </span>
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-4">Generate · review · amend</h3>

              <div className="border border-gray-200 rounded-xl p-4 mb-3">
                <p className="text-sm font-semibold text-gray-900 mb-1 flex items-center gap-1.5">
                  <Code size={13} aria-hidden="true" /> Ask Aida for {patient.name.split(' ')[0]}
                </p>
                <span className="inline-block text-[11px] text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full mb-3">
                  uses 30d sensor + journal
                </span>
                <div className="flex flex-wrap gap-2 mb-3">
                  {['Sleep', 'Anxiety', 'Diet', 'Reflect', 'Movement'].map((tag, i) => (
                    <span
                      key={tag}
                      className={`text-xs font-semibold px-3 py-1.5 rounded-full ${
                        i === 0 ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
                <div className="flex items-center justify-between gap-3 bg-gray-50 rounded-lg px-3 py-2.5">
                  <p className="text-xs text-gray-600 leading-snug">
                    e.g. Suggest a calmer pre-sleep routine that works around her Tue review meetings
                  </p>
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 bg-gray-900 text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-gray-800 shrink-0"
                  >
                    <Zap size={12} aria-hidden="true" /> Generate · 3
                  </button>
                </div>
              </div>

              {detail.aidaRecommendations.map((rec) => (
                <div key={rec.id} className="border border-orange-200 bg-orange-50/60 rounded-xl p-4 relative">
                  <button
                    type="button"
                    aria-label="Dismiss recommendation"
                    className="absolute top-3 right-3 text-gray-400 hover:text-gray-700"
                  >
                    <X size={14} />
                  </button>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-[11px] font-semibold text-orange-700 bg-orange-100 px-2 py-0.5 rounded-full">
                      {rec.status === 'editing' ? 'Editing' : 'Pending'}
                    </span>
                    <span className="text-xs text-gray-500">{rec.category}</span>
                  </div>
                  <p className="text-sm font-semibold text-gray-900 pr-6">{rec.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </TherapistLayout>
  );
};

function getTabPlaceholder(tab: Tab): string {
  return `${tab} — coming soon in this demo.`;
}

export default PatientDetailPage;