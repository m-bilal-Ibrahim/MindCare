// ============================================================
// MindCare — Admin Console: Safety / SOS
// ============================================================

import React, { useState } from 'react';
import { Download, ShieldAlert } from 'lucide-react';
import AdminLayout from '../components/admin/AdminLayout';
import { SAFETY_STATS, SOS_EVENTS, SOS_CASE_DETAIL } from '../constants/adminConsole';

type EventFilter = 'all' | 'user-initiated' | 'aida-detected';

const SafetyPage: React.FC = () => {
  const [filter, setFilter] = useState<EventFilter>('all');
  const [activeEventId, setActiveEventId] = useState(SOS_EVENTS[0].id);

  const filteredEvents = SOS_EVENTS.filter((e) => {
    if (filter === 'all') return true;
    if (filter === 'user-initiated') return e.triggerType === 'user-initiated';
    if (filter === 'aida-detected') return e.triggerType === 'aida-detected';
    return true;
  });

  const activeEvent = SOS_EVENTS.find((e) => e.id === activeEventId);
  const showFullDetail = activeEvent?.caseCode === SOS_CASE_DETAIL.caseCode;

  return (
    <AdminLayout
      breadcrumb={['Trust & safety', 'Safety / SOS']}
      headerAction={
        <div className="flex gap-2 shrink-0">
          <button
            type="button"
            className="inline-flex items-center gap-2 border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 transition-colors"
          >
            <Download size={15} aria-hidden="true" /> HIPAA log
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 transition-colors"
          >
            <ShieldAlert size={15} aria-hidden="true" /> Drill mode
          </button>
        </div>
      }
    >
      <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-2">
        Last 30 days · {SOS_EVENTS.length + 10} events · 100% resolved
      </p>
      <h1 className="text-5xl font-black text-gray-900 mb-2">
        Safety, <span className="italic font-serif font-normal">logged &amp; responded.</span>
      </h1>
      <p className="text-gray-500 mb-8 max-w-2xl">
        All SOS events are anonymized to admin view by default. PII unlocked only with case lead consent.
      </p>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-2">SOS · 30D</p>
          <p className="text-3xl font-black text-orange-600">
            {SAFETY_STATS.sosCount30d} <span className="text-base font-semibold text-gray-400">{SAFETY_STATS.delta30d}</span>
          </p>
          <p className="text-xs text-gray-500 mt-1">vs prior 30d</p>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-2">Avg response</p>
          <p className="text-3xl font-black text-emerald-700">{SAFETY_STATS.avgResponse}</p>
          <p className="text-xs text-gray-500 mt-1">trained listener picks up</p>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-2">Hospital escal.</p>
          <p className="text-3xl font-black text-gray-900">{SAFETY_STATS.hospitalEscalations}</p>
          <p className="text-xs text-gray-500 mt-1">{SAFETY_STATS.hospitalEscalationMeta}</p>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-2">False positives</p>
          <p className="text-3xl font-black text-gray-900">{SAFETY_STATS.falsePositives}</p>
          <p className="text-xs text-gray-500 mt-1">{SAFETY_STATS.falsePositivesPercent}% of triggers</p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_420px] gap-6">
        {/* Events list */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-1">
            <h2 className="text-2xl font-black text-gray-900">Events</h2>
            <div className="flex gap-1">
              {(
                [
                  { key: 'all', label: 'All' },
                  { key: 'user-initiated', label: 'User-initiated' },
                  { key: 'aida-detected', label: 'Aida-detected' },
                ] as { key: EventFilter; label: string }[]
              ).map(({ key, label }) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setFilter(key)}
                  className={`text-xs font-semibold px-3 py-1.5 rounded-full transition-colors ${
                    filter === key ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <ul className="divide-y divide-gray-100 mt-4">
            {filteredEvents.map((event) => {
              const isActive = event.id === activeEventId;
              return (
                <li key={event.id}>
                  <button
                    type="button"
                    onClick={() => setActiveEventId(event.id)}
                    className={`w-full text-left py-4 px-2 rounded-xl transition-colors ${isActive ? 'bg-[#F5F0E8]' : 'hover:bg-gray-50'}`}
                  >
                    <div className="flex items-center justify-between gap-3 mb-1">
                      <p className="text-xs text-gray-400">
                        {event.caseCode} · {event.timeLabel}
                      </p>
                      <p className="text-xs text-gray-400">{event.durationLabel}</p>
                    </div>
                    <p className="font-bold text-gray-900">
                      {event.anonId}
                      {event.realNameHint && <span className="font-normal text-gray-500"> ({event.realNameHint})</span>} ·{' '}
                      {event.city}
                    </p>
                    <p className="text-sm text-gray-500 mb-2">{event.triggerLabel}</p>
                    <span
                      className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                        event.status === 'resolved' ? 'bg-emerald-100 text-emerald-700' : 'bg-emerald-50 text-emerald-600'
                      }`}
                    >
                      {event.status === 'resolved' ? 'Resolved' : 'Resolved · false positive'}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>

        {/* Case detail */}
        {showFullDetail ? (
          <div className="space-y-6">
            <div className="bg-gray-950 rounded-2xl p-6 text-white">
              <p className="text-xs font-semibold tracking-widest text-orange-400 uppercase mb-1">
                Case open · {SOS_CASE_DETAIL.caseCode}
              </p>
              <h3 className="text-2xl font-black mb-3">
                {SOS_CASE_DETAIL.openedLabel} — resolved in {SOS_CASE_DETAIL.resolvedInLabel}
              </h3>
              <p className="text-sm text-gray-300 leading-relaxed mb-5">{SOS_CASE_DETAIL.description}</p>
              <div className="grid grid-cols-2 gap-4 text-sm border-t border-white/10 pt-4">
                <div>
                  <p className="text-gray-500 text-xs">Region</p>
                  <p className="font-bold">{SOS_CASE_DETAIL.region}</p>
                </div>
                <div>
                  <p className="text-gray-500 text-xs">Trigger</p>
                  <p className="font-bold">{SOS_CASE_DETAIL.triggerLabel}</p>
                </div>
                <div>
                  <p className="text-gray-500 text-xs">Responder</p>
                  <p className="font-bold">{SOS_CASE_DETAIL.responder}</p>
                </div>
                <div>
                  <p className="text-gray-500 text-xs">Handoff</p>
                  <p className="font-bold">{SOS_CASE_DETAIL.handoffTo}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-4">
                Response timeline
              </p>
              <ul className="space-y-4">
                {SOS_CASE_DETAIL.timeline.map((entry, i) => (
                  <li key={i} className="flex gap-3">
                    <span
                      className={`w-2.5 h-2.5 rounded-full mt-1.5 shrink-0 ${
                        i === 0 ? 'bg-red-500' : i === SOS_CASE_DETAIL.timeline.length - 1 ? 'bg-emerald-600' : 'bg-gray-400'
                      }`}
                    />
                    <div>
                      <p className="text-sm text-gray-800">{entry.label}</p>
                      <p className="text-xs text-gray-400">({entry.time})</p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-3">Actions</p>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  className="border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 transition-colors"
                >
                  Unlock PII (case lead)
                </button>
                <button
                  type="button"
                  className="border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 transition-colors"
                >
                  Add note
                </button>
                <button
                  type="button"
                  className="border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 transition-colors"
                >
                  Mark false positive
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center text-gray-400">
            Full detail template is only built for the first demo case — select it from the events list to review.
          </div>
        )}
      </div>
    </AdminLayout>
  );
};

export default SafetyPage;