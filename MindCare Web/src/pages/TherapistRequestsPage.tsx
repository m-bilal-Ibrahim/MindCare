// ============================================================
// MindCare — Therapist Console: Session Requests
// ============================================================

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Check } from 'lucide-react';
import TherapistLayout from '../components/therapist/TherapistLayout';
import Avatar from '../components/common/Avatar';
import { SESSION_REQUESTS, REQUESTS_SUMMARY, buildPatientDetailRoute } from '../constants/therapistConsole';
import type { RequestStatus } from '../types/therapistConsole';

const TAG_STYLES: Record<string, string> = {
  default: 'bg-emerald-100 text-emerald-700',
  warning: 'bg-amber-100 text-amber-700',
  info: 'bg-violet-100 text-violet-700',
};

const TherapistRequestsPage: React.FC = () => {
  const [tab, setTab] = useState<RequestStatus>('inbox');
  const [resolvedIds, setResolvedIds] = useState<Set<string>>(new Set());

  const visible = SESSION_REQUESTS.filter((r) => r.status === 'inbox' && !resolvedIds.has(r.id));

  const handleConfirm = (id: string) => {
    // TODO: call real API to confirm the session and generate the Meet link.
    setResolvedIds((prev) => new Set(prev).add(id));
  };

  const handleDecline = (id: string) => {
    // TODO: call real API to decline and notify the patient.
    setResolvedIds((prev) => new Set(prev).add(id));
  };

  return (
    <TherapistLayout breadcrumb={['Practice', 'Requests']}>
      <h1 className="text-5xl font-black text-gray-900 mb-2">
        Session <span className="italic font-serif font-normal">requests.</span>
      </h1>
      <p className="text-gray-500 mb-6 max-w-2xl">
        Confirm, amend, or decline. A Meet link is generated automatically once both sides agree.
      </p>

      <div className="flex flex-wrap gap-2 mb-6">
        <button
          type="button"
          onClick={() => setTab('inbox')}
          className={`text-sm font-semibold px-4 py-2 rounded-full transition-colors ${
            tab === 'inbox' ? 'bg-gray-900 text-white' : 'bg-white border border-gray-200 text-gray-700 hover:border-gray-400'
          }`}
        >
          Inbox · {REQUESTS_SUMMARY.inbox}
        </button>
        <button
          type="button"
          onClick={() => setTab('awaiting')}
          className={`text-sm font-semibold px-4 py-2 rounded-full transition-colors ${
            tab === 'awaiting' ? 'bg-gray-900 text-white' : 'bg-white border border-gray-200 text-gray-700 hover:border-gray-400'
          }`}
        >
          Awaiting them · {REQUESTS_SUMMARY.awaitingThem}
        </button>
        <button
          type="button"
          onClick={() => setTab('resolved')}
          className={`text-sm font-semibold px-4 py-2 rounded-full transition-colors ${
            tab === 'resolved' ? 'bg-gray-900 text-white' : 'bg-white border border-gray-200 text-gray-700 hover:border-gray-400'
          }`}
        >
          Past 30d · {REQUESTS_SUMMARY.past30d}
        </button>
      </div>

      {tab !== 'inbox' ? (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center text-gray-400">
          Nothing to show here in this demo yet.
        </div>
      ) : visible.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center">
          <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-4">
            <Check size={18} className="text-emerald-700" />
          </div>
          <p className="text-gray-900 font-semibold">Inbox clear.</p>
          <p className="text-sm text-gray-500">No pending requests right now.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {visible.map((req) => (
            <div key={req.id} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-start justify-between gap-4 mb-3">
                <div className="flex items-start gap-4">
                  <Avatar initials={req.patientInitials} color={req.avatarColor} />
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-bold text-gray-900">{req.patientName}</p>
                      <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${TAG_STYLES[req.tagTone]}`}>
                        {req.tag}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 mt-0.5">
                      {req.date} · {req.time} · {req.durationMin} min
                    </p>
                  </div>
                </div>
                <span className="text-xs text-gray-400 shrink-0">{req.requestedAgo}</span>
              </div>

              {req.note && (
                <div className="bg-[#F5F0E8] rounded-xl px-4 py-3 mb-4">
                  <span className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mr-2">
                    Note
                  </span>
                  <span className="text-sm text-gray-700">{req.note}</span>
                </div>
              )}

              <div className="flex flex-wrap items-center gap-3">
                {req.patientId ? (
                  <Link
                    to={buildPatientDetailRoute(req.patientId)}
                    className="border border-gray-200 text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 transition-colors"
                  >
                    View patient
                  </Link>
                ) : (
                  <button
                    type="button"
                    disabled
                    title="New lead — not yet in your patient roster"
                    className="border border-gray-200 text-gray-400 text-sm font-semibold px-4 py-2.5 rounded-xl cursor-not-allowed"
                  >
                    View patient
                  </button>
                )}
                <button
                  type="button"
                  className="border border-gray-200 text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 transition-colors"
                >
                  Propose new time
                </button>
                <button
                  type="button"
                  onClick={() => handleDecline(req.id)}
                  className="bg-red-50 border border-red-200 text-red-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-red-100 transition-colors"
                >
                  Decline
                </button>
                <button
                  type="button"
                  onClick={() => handleConfirm(req.id)}
                  className="ml-auto inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 transition-colors"
                >
                  <Check size={14} aria-hidden="true" /> Confirm
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </TherapistLayout>
  );
};

export default TherapistRequestsPage;