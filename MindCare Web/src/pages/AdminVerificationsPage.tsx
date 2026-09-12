// ============================================================
// MindCare — Admin Console: Verifications
// ============================================================

import React, { useState } from 'react';
import { Check, Eye, AlertCircle, Clock } from 'lucide-react';
import AdminLayout from '../components/admin/AdminLayout';
import Avatar from '../components/common/Avatar';
import {
  VERIFICATION_QUEUE_SUMMARY,
  THERAPIST_VERIFICATION_QUEUE,
  NGO_VERIFICATION_QUEUE,
  HOSPITAL_VERIFICATION_QUEUE,
  THERAPIST_VERIFICATION_DETAILS,
  NGO_VERIFICATION_DETAILS,
} from '../constants/adminConsole';
import { sanitizeText, MAX_LENGTHS } from '../utils/validation';
import type { VerificationType, VerificationCheckStatus } from '../types/adminConsole';

const STATUS_TONE_STYLES: Record<string, string> = {
  default: 'bg-gray-100 text-gray-700',
  new: 'bg-amber-100 text-amber-700',
  flag: 'bg-red-100 text-red-700',
  wait: 'bg-gray-100 text-gray-500',
};

const CHECK_STATUS_ICON: Record<VerificationCheckStatus, React.ReactNode> = {
  verified: <Check size={13} className="text-white" />,
  'needs-review': <Eye size={13} className="text-white" />,
  pending: <Clock size={12} className="text-white" />,
};

const CHECK_STATUS_BG: Record<VerificationCheckStatus, string> = {
  verified: 'bg-emerald-600',
  'needs-review': 'bg-amber-500',
  pending: 'bg-gray-300',
};

const AdminVerificationsPage: React.FC = () => {
  const [activeType, setActiveType] = useState<VerificationType>('therapist');
  const [activeItemId, setActiveItemId] = useState(THERAPIST_VERIFICATION_QUEUE[0].id);
  const [reviewNote, setReviewNote] = useState('');
  const [blockUntilDrill, setBlockUntilDrill] = useState(false);
  const [decision, setDecision] = useState<'pending' | 'approved' | 'rejected'>('pending');

  const queue =
    activeType === 'therapist' ? THERAPIST_VERIFICATION_QUEUE : activeType === 'ngo' ? NGO_VERIFICATION_QUEUE : HOSPITAL_VERIFICATION_QUEUE;

  const handleSwitchType = (type: VerificationType) => {
    setActiveType(type);
    const firstId =
      type === 'therapist' ? THERAPIST_VERIFICATION_QUEUE[0]?.id : type === 'ngo' ? NGO_VERIFICATION_QUEUE[0]?.id : HOSPITAL_VERIFICATION_QUEUE[0]?.id;
    setActiveItemId(firstId ?? '');
    setDecision('pending');
    setReviewNote('');
  };

  const handleSelectItem = (id: string) => {
    setActiveItemId(id);
    setDecision('pending');
    setReviewNote('');
  };

  const handleApprove = () => {
    // TODO: real API call. The backend MUST independently re-verify this
    // admin has approval permission (RBAC) and audit-log who approved
    // which application, when, and with what note attached.
    setDecision('approved');
  };

  const handleReject = () => {
    // TODO: same audit-logging requirement as approve.
    setDecision('rejected');
  };

  const handleAskForMore = () => {
    const clean = sanitizeText(reviewNote);
    // TODO: real API call to notify the applicant and log the request.
    console.info('[MindCare] Asked for more info:', { itemId: activeItemId, note: clean });
  };

  const handleSaveNote = () => {
    const clean = sanitizeText(reviewNote);
    if (!clean) return;
    // TODO: real API call. Internal notes must never be visible to the
    // applicant and must be scoped to admins with review permission.
    console.info('[MindCare] Internal review note saved:', { itemId: activeItemId, note: clean });
  };

  const therapistDetail = activeType === 'therapist' ? THERAPIST_VERIFICATION_DETAILS[activeItemId] : null;
  const ngoDetail = activeType === 'ngo' ? NGO_VERIFICATION_DETAILS[activeItemId] : null;

  return (
    <AdminLayout breadcrumb={['Operations', 'Verifications', therapistDetail?.name ?? ngoDetail?.name ?? 'Hospital partners']}>
      {decision !== 'pending' ? (
        <div
          className={`rounded-2xl p-6 mb-6 border ${
            decision === 'approved' ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'
          }`}
        >
          <p className={`font-bold ${decision === 'approved' ? 'text-emerald-800' : 'text-red-800'}`}>
            {decision === 'approved' ? '✓ Approved and onboarded.' : '✗ Rejected.'} This is a demo action — no real
            account was changed.
          </p>
        </div>
      ) : null}

      {therapistDetail && (
        <>
          <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-1">
            Therapist · Application {therapistDetail.applicationId}
          </p>
          <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4 mb-2">
            <h1 className="text-5xl font-black text-gray-900">
              Verify <span className="italic font-serif font-normal">{therapistDetail.name}.</span>
            </h1>
            <div className="flex gap-2 shrink-0">
              <button
                type="button"
                onClick={handleReject}
                className="bg-red-600 text-white text-sm font-semibold px-5 py-2.5 rounded-xl hover:bg-red-700 transition-colors"
              >
                Reject
              </button>
              <button
                type="button"
                onClick={handleAskForMore}
                className="border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 transition-colors"
              >
                Ask for more
              </button>
              <button
                type="button"
                onClick={handleApprove}
                className="inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 transition-colors"
              >
                <Check size={15} aria-hidden="true" /> Approve &amp; onboard
              </button>
            </div>
          </div>
          <p className="text-gray-500 mb-8">
            Submitted {therapistDetail.submittedDate} · {therapistDetail.waitingDays} days waiting ·{' '}
            {therapistDetail.checksComplete === therapistDetail.checksTotal
              ? 'auto-checks all green.'
              : `${therapistDetail.checksComplete} of ${therapistDetail.checksTotal} auto-checks passed.`}{' '}
            Your call.
          </p>
        </>
      )}

      {ngoDetail && (
        <>
          <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-1">
            NGO Partner · Application {ngoDetail.applicationId}
          </p>
          <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4 mb-2">
            <h1 className="text-5xl font-black text-gray-900">
              Verify <span className="italic font-serif font-normal">{ngoDetail.name}.</span>
            </h1>
            <div className="flex gap-2 shrink-0">
              <button
                type="button"
                onClick={handleReject}
                className="bg-red-600 text-white text-sm font-semibold px-5 py-2.5 rounded-xl hover:bg-red-700 transition-colors"
              >
                Reject
              </button>
              <button
                type="button"
                onClick={handleAskForMore}
                className="border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 transition-colors"
              >
                Ask for more
              </button>
              <button
                type="button"
                onClick={handleApprove}
                className="inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 transition-colors"
              >
                <Check size={15} aria-hidden="true" /> Approve · go live
              </button>
            </div>
          </div>
          <p className="text-gray-500 mb-8">
            Submitted {ngoDetail.submittedDate} · {ngoDetail.waitingDays} days waiting · MOU signed, drill scheduled.
            Your call to flip them live.
          </p>
        </>
      )}

      {activeType === 'hospital' && !ngoDetail && !therapistDetail && (
        <>
          <h1 className="text-5xl font-black text-gray-900 mb-2">
            Hospital <span className="italic font-serif font-normal">partners.</span>
          </h1>
          <p className="text-gray-500 mb-8">Detailed review template for hospital partners is coming soon in this demo.</p>
        </>
      )}

      {/* Type tabs */}
      <div className="flex gap-8 border-b border-gray-200 mb-6">
        <button
          type="button"
          onClick={() => handleSwitchType('therapist')}
          className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeType === 'therapist' ? 'text-gray-900 border-gray-900' : 'text-gray-400 border-transparent hover:text-gray-600'
          }`}
        >
          Therapists{' '}
          <span className="w-6 h-6 rounded-full bg-gray-100 text-gray-600 text-xs flex items-center justify-center">
            {VERIFICATION_QUEUE_SUMMARY.therapists}
          </span>
        </button>
        <button
          type="button"
          onClick={() => handleSwitchType('ngo')}
          className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeType === 'ngo' ? 'text-gray-900 border-gray-900' : 'text-gray-400 border-transparent hover:text-gray-600'
          }`}
        >
          NGO partners{' '}
          <span className="w-6 h-6 rounded-full bg-gray-100 text-gray-600 text-xs flex items-center justify-center">
            {VERIFICATION_QUEUE_SUMMARY.ngoPartners}
          </span>
        </button>
        <button
          type="button"
          onClick={() => handleSwitchType('hospital')}
          className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${
            activeType === 'hospital' ? 'text-gray-900 border-gray-900' : 'text-gray-400 border-transparent hover:text-gray-600'
          }`}
        >
          Hospital partners{' '}
          <span className="w-6 h-6 rounded-full bg-gray-100 text-gray-600 text-xs flex items-center justify-center">
            {VERIFICATION_QUEUE_SUMMARY.hospitalPartners}
          </span>
        </button>
      </div>

      {/* Queue selector */}
      {queue.length > 1 && (
        <div className="flex flex-wrap gap-2 mb-6">
          {queue.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => handleSelectItem(item.id)}
              className={`inline-flex items-center gap-2 pl-1.5 pr-3 py-1.5 rounded-full border text-sm font-semibold transition-colors ${
                item.id === activeItemId ? 'bg-gray-900 border-gray-900 text-white' : 'bg-white border-gray-200 text-gray-700 hover:border-gray-400'
              }`}
            >
              <Avatar initials={item.initials} color={item.avatarColor} size="sm" />
              {item.name}
              <span
                className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                  item.id === activeItemId ? 'bg-white/20 text-white' : STATUS_TONE_STYLES[item.statusTone]
                }`}
              >
                {item.statusTag}
              </span>
            </button>
          ))}
        </div>
      )}

      {/* Therapist detail layout */}
      {therapistDetail && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div className="xl:col-span-2 space-y-6">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-start gap-4">
                <Avatar initials={therapistDetail.initials} color={therapistDetail.avatarColor} size="lg" />
                <div>
                  <h2 className="text-2xl font-black text-gray-900 mb-1">{therapistDetail.name}</h2>
                  <p className="text-sm text-gray-500 mb-3">{therapistDetail.credentialSummary}</p>
                  <div className="flex flex-wrap gap-2 mb-3">
                    {therapistDetail.specialtyTags.map((tag, i) => (
                      <span
                        key={tag}
                        className={`text-xs font-semibold px-3 py-1 rounded-full ${
                          ['bg-violet-100 text-violet-700', 'bg-rose-100 text-rose-700', 'bg-emerald-100 text-emerald-700'][i % 3]
                        }`}
                      >
                        {tag}
                      </span>
                    ))}
                    <span className="text-xs font-semibold px-3 py-1 rounded-full border border-gray-200 text-gray-700">
                      {therapistDetail.languages}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500">
                    {therapistDetail.city} · {therapistDetail.phoneMasked} · {therapistDetail.emailMasked}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-4">
                <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase">Credentials &amp; checks</p>
                <span className="text-xs text-gray-500">
                  {therapistDetail.checksComplete} of {therapistDetail.checksTotal} auto-checks passed
                </span>
              </div>
              <ul className="divide-y divide-gray-100">
                {therapistDetail.checks.map((check) => (
                  <li key={check.id} className="py-4 flex items-center gap-4">
                    <span className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${CHECK_STATUS_BG[check.status]}`}>
                      {CHECK_STATUS_ICON[check.status]}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="font-bold text-gray-900">{check.label}</p>
                      <p className="text-sm text-gray-500">{check.meta}</p>
                    </div>
                    <button
                      type="button"
                      className="inline-flex items-center gap-1.5 border border-gray-200 text-gray-700 text-sm font-semibold px-3 py-1.5 rounded-xl hover:border-gray-400 shrink-0"
                    >
                      <Eye size={13} aria-hidden="true" /> View
                    </button>
                  </li>
                ))}
              </ul>
            </div>

            {therapistDetail.timeline.length > 0 && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-4">Timeline</p>
                <ul className="space-y-3">
                  {therapistDetail.timeline.map((entry, i) => (
                    <li key={i} className="flex gap-4 text-sm">
                      <span className="text-gray-400 shrink-0 w-32">{entry.time}</span>
                      <span className="text-gray-700">{entry.label}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <aside className="space-y-6">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-4">Auto risk score</p>
              <div className="flex items-center gap-4 mb-4">
                <div className="relative w-16 h-16 shrink-0">
                  <svg viewBox="0 0 36 36" className="w-16 h-16 -rotate-90">
                    <circle cx="18" cy="18" r="16" fill="none" stroke="#e5e7eb" strokeWidth="3" />
                    <circle
                      cx="18"
                      cy="18"
                      r="16"
                      fill="none"
                      stroke={therapistDetail.riskScore >= 7 ? '#15803d' : '#d97706'}
                      strokeWidth="3"
                      strokeDasharray={`${(therapistDetail.riskScore / 10) * 100.5} 100.5`}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-sm font-black text-gray-900">{therapistDetail.riskScore}</span>
                    <span className="text-[9px] text-gray-400">of 10</span>
                  </div>
                </div>
                <div>
                  <p className="font-bold text-gray-900">{therapistDetail.riskLabel}</p>
                  <p className="text-sm text-gray-500">{therapistDetail.riskDescription}</p>
                </div>
              </div>
              <ul className="space-y-3 text-sm border-t border-gray-100 pt-4">
                <li className="flex items-center justify-between">
                  <span className="text-gray-600">Identity match</span>
                  <span className="text-xs font-semibold bg-emerald-100 text-emerald-700 px-2.5 py-1 rounded-full">
                    {therapistDetail.identityMatchSources}
                  </span>
                </li>
                <li className="flex items-center justify-between">
                  <span className="text-gray-600">Sanctions list</span>
                  <span className="text-xs font-semibold bg-emerald-100 text-emerald-700 px-2.5 py-1 rounded-full">
                    {therapistDetail.sanctionsStatus}
                  </span>
                </li>
                <li className="flex items-center justify-between">
                  <span className="text-gray-600">Public reviews</span>
                  <span className="text-xs font-semibold bg-emerald-100 text-emerald-700 px-2.5 py-1 rounded-full">
                    {therapistDetail.publicReviewsNote}
                  </span>
                </li>
                <li className="flex items-center justify-between">
                  <span className="text-gray-600">Image authenticity</span>
                  <span className="text-xs font-semibold bg-amber-100 text-amber-700 px-2.5 py-1 rounded-full">
                    {therapistDetail.imageAuthenticityNote}
                  </span>
                </li>
              </ul>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-3">Your review</p>
              <textarea
                value={reviewNote}
                onChange={(e) => setReviewNote(e.target.value.slice(0, MAX_LENGTHS.longText))}
                maxLength={MAX_LENGTHS.longText}
                rows={4}
                placeholder={`Notes here are visible to other admins only. ${therapistDetail.name.split(' ').pop()} won't see them.`}
                className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-gray-50 resize-none mb-3"
              />
              <div className="flex items-center justify-between">
                <p className="text-xs text-gray-500">
                  Reviewer: <span className="font-semibold text-gray-700">Ayesha S.</span>
                </p>
                <button
                  type="button"
                  onClick={handleSaveNote}
                  className="bg-gray-900 text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-gray-800"
                >
                  Save note
                </button>
              </div>
            </div>
          </aside>
        </div>
      )}

      {/* NGO detail layout */}
      {ngoDetail && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div className="xl:col-span-2 space-y-6">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-start gap-4">
                <span className={`w-16 h-16 rounded-2xl flex items-center justify-center text-white text-xl font-black shrink-0 ${ngoDetail.avatarColor}`}>
                  {ngoDetail.initials}
                </span>
                <div className="flex-1">
                  <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-3">
                    <div>
                      <h2 className="text-2xl font-black text-gray-900 mb-1">{ngoDetail.name}</h2>
                      <p className="text-sm text-gray-500 mb-3">{ngoDetail.summary}</p>
                    </div>
                    <div className="text-sm text-gray-500 shrink-0">
                      <p>{ngoDetail.address}</p>
                      <p>{ngoDetail.phoneMasked}</p>
                      <p>{ngoDetail.emailMasked}</p>
                      <p>NTN · {ngoDetail.ntn}</p>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {ngoDetail.tags.map((tag, i) => (
                      <span
                        key={tag}
                        className={`text-xs font-semibold px-3 py-1 rounded-full ${
                          ['bg-violet-100 text-violet-700', 'bg-emerald-100 text-emerald-700', 'border border-gray-200 text-gray-700'][i % 3]
                        }`}
                      >
                        {tag}
                      </span>
                    ))}
                    <span className="text-xs font-semibold px-3 py-1 rounded-full border border-gray-200 text-gray-700">
                      {ngoDetail.languages}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-4">
                <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase">Partner verification</p>
                <span className="text-xs text-gray-500">
                  {ngoDetail.checksComplete} of {ngoDetail.checksTotal} checks complete
                </span>
              </div>
              <ul className="divide-y divide-gray-100">
                {ngoDetail.checks.map((check) => (
                  <li key={check.id} className="py-4 flex items-center gap-4">
                    <span className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${CHECK_STATUS_BG[check.status]}`}>
                      {CHECK_STATUS_ICON[check.status]}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="font-bold text-gray-900">{check.label}</p>
                      <p className="text-sm text-gray-500">{check.meta}</p>
                    </div>
                    <button
                      type="button"
                      className="inline-flex items-center gap-1.5 border border-gray-200 text-gray-700 text-sm font-semibold px-3 py-1.5 rounded-xl hover:border-gray-400 shrink-0"
                    >
                      <Eye size={13} aria-hidden="true" /> View
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <aside className="space-y-6">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-4">SLA commitment</p>
              <h3 className="text-lg font-bold text-gray-900 mb-4">What they&apos;re promising</h3>
              <div className="space-y-3 text-sm">
                <div>
                  <p className="text-gray-500">Pick-up time</p>
                  <p className="text-gray-900 font-semibold">{ngoDetail.slaCommitment.pickupTimeBusiness}</p>
                  <p className="text-gray-900 font-semibold">{ngoDetail.slaCommitment.pickupTimeAfterHours}</p>
                </div>
                <div className="border-t border-gray-100 pt-3">
                  <p className="text-gray-500">Closed-loop case report</p>
                  <p className="text-gray-900 font-semibold">{ngoDetail.slaCommitment.closedLoopReport}</p>
                  <p className="text-gray-900 font-semibold">{ngoDetail.slaCommitment.closedLoopReportWeekend}</p>
                </div>
                <div className="border-t border-gray-100 pt-3">
                  <p className="text-gray-500">Re-routing window</p>
                  <p className="text-gray-900 font-semibold">{ngoDetail.slaCommitment.reroutingWindow}</p>
                </div>
                <div className="border-t border-gray-100 pt-3">
                  <p className="text-gray-500">Annual drill</p>
                  <p className="text-gray-900 font-semibold">{ngoDetail.slaCommitment.annualDrill}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-3">Your review</p>
              <textarea
                value={reviewNote}
                onChange={(e) => setReviewNote(e.target.value.slice(0, MAX_LENGTHS.longText))}
                maxLength={MAX_LENGTHS.longText}
                rows={4}
                placeholder={`Internal notes · visible to other admins only. ${ngoDetail.name} will not see them.`}
                className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-gray-50 resize-none mb-3"
              />
              <label className="flex items-center gap-2 text-sm text-gray-600 mb-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={blockUntilDrill}
                  onChange={(e) => setBlockUntilDrill(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300 accent-gray-900"
                />
                Block live status until drill passes
              </label>
              <div className="flex items-center justify-between">
                <p className="text-xs text-gray-500">
                  Reviewer: <span className="font-semibold text-gray-700">Ayesha S.</span>
                </p>
                <button
                  type="button"
                  onClick={handleSaveNote}
                  className="bg-gray-900 text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-gray-800"
                >
                  Save note
                </button>
              </div>
            </div>
          </aside>
        </div>
      )}

      {activeType === 'hospital' && (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center text-gray-400">
          <AlertCircle size={24} className="mx-auto mb-3 text-gray-300" />
          Detailed hospital partner review is not yet built in this demo — {HOSPITAL_VERIFICATION_QUEUE[0]?.name} is
          waiting in the queue above.
        </div>
      )}
    </AdminLayout>
  );
};

export default AdminVerificationsPage;