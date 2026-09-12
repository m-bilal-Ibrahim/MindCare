// ============================================================
// MindCare — Admin Console: Moderation
// ============================================================

import React, { useState } from 'react';
import { ArrowRight, Trash2, ShieldAlert } from 'lucide-react';
import AdminLayout from '../components/admin/AdminLayout';
import Avatar from '../components/common/Avatar';
import { MODERATION_SUMMARY, MODERATION_QUEUE, MODERATION_CASE_DETAIL } from '../constants/adminConsole';
import { sanitizeText, MAX_LENGTHS } from '../utils/validation';
import type { ModerationSeverity } from '../types/adminConsole';

type FilterKey = 'all' | 'high' | 'posts' | 'users' | 'photos' | 'listeners';

const SEVERITY_STYLES: Record<ModerationSeverity, string> = {
  high: 'bg-red-100 text-red-700',
  med: 'bg-amber-100 text-amber-700',
  low: 'bg-gray-100 text-gray-600',
};

const ModerationPage: React.FC = () => {
  const [filter, setFilter] = useState<FilterKey>('all');
  const [activeCaseId, setActiveCaseId] = useState(MODERATION_QUEUE[0].id);
  const [messageDraft, setMessageDraft] = useState(MODERATION_CASE_DETAIL.messageTemplate);
  const [actionTaken, setActionTaken] = useState<string | null>(null);

  const filteredQueue = MODERATION_QUEUE.filter((item) => {
    if (filter === 'all') return true;
    if (filter === 'high') return item.severity === 'high';
    if (filter === 'posts') return item.category === 'Post';
    if (filter === 'users') return item.category === 'User';
    if (filter === 'photos') return item.category === 'Photo';
    if (filter === 'listeners') return item.category === 'Listener';
    return true;
  });

  const activeCase = activeCaseId === MODERATION_CASE_DETAIL.id ? MODERATION_CASE_DETAIL : null;

  const handleAction = (action: string) => {
    // TODO: real API call. Every moderation action MUST be audit-logged
    // server-side (who, what, when, on which content), and destructive
    // actions (remove/mute) must be independently re-authorized by RBAC.
    setActionTaken(action);
  };

  const handleSendMessage = () => {
    const clean = sanitizeText(messageDraft);
    if (!clean) return;
    console.info('[MindCare] Moderation message sent to author:', clean);
  };

  return (
    <AdminLayout breadcrumb={['Trust & safety', 'Moderation']}>
      <h1 className="text-5xl font-black text-gray-900 mb-2">
        Keeping the <span className="italic font-serif font-normal">circles</span> safe.
      </h1>
      <p className="text-gray-500 mb-6 max-w-2xl">
        {MODERATION_SUMMARY.open} open · {MODERATION_SUMMARY.highSeverity} high severity ·{' '}
        {MODERATION_SUMMARY.closedThisWeek} closed this week. Auto-flag picks up ≈{MODERATION_SUMMARY.autoFlagPercent}%
        before human report.
      </p>

      <div className="flex flex-wrap items-center gap-2 mb-6">
        {(
          [
            { key: 'all', label: `All open · ${MODERATION_QUEUE.length}` },
            { key: 'high', label: `High · ${MODERATION_QUEUE.filter((i) => i.severity === 'high').length}` },
            { key: 'posts', label: `Posts · ${MODERATION_QUEUE.filter((i) => i.category === 'Post').length}` },
            { key: 'users', label: `Users · ${MODERATION_QUEUE.filter((i) => i.category === 'User').length}` },
            { key: 'photos', label: `Photos · ${MODERATION_QUEUE.filter((i) => i.category === 'Photo').length}` },
            { key: 'listeners', label: `Listeners · ${MODERATION_QUEUE.filter((i) => i.category === 'Listener').length}` },
          ] as { key: FilterKey; label: string }[]
        ).map(({ key, label }) => (
          <button
            key={key}
            type="button"
            onClick={() => setFilter(key)}
            className={`text-sm font-semibold px-4 py-2 rounded-full transition-colors ${
              filter === key ? 'bg-gray-900 text-white' : 'bg-white border border-gray-200 text-gray-700 hover:border-gray-400'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[400px_1fr] gap-6">
        {/* Queue list */}
        <div className="space-y-3">
          {filteredQueue.map((item) => {
            const isActive = item.id === activeCaseId;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setActiveCaseId(item.id)}
                className={`w-full text-left bg-white rounded-2xl shadow-sm border p-5 transition-colors ${
                  isActive ? 'border-gray-900' : 'border-gray-100 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center justify-between gap-3 mb-2">
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${SEVERITY_STYLES[item.severity]}`}>
                    {item.severity}
                  </span>
                  <span className="text-xs text-gray-400">
                    {item.category} · {item.context}
                  </span>
                </div>
                <p className="font-bold text-gray-900 mb-1">{item.title}</p>
                <p className="text-sm text-gray-500 truncate">{item.preview}</p>
              </button>
            );
          })}
          {filteredQueue.length === 0 && (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center text-gray-400">
              No cases match this filter.
            </div>
          )}
        </div>

        {/* Case detail */}
        {activeCase ? (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            {actionTaken && (
              <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 mb-5">
                <p className="text-emerald-800 font-semibold text-sm">
                  ✓ Action recorded: {actionTaken}. This is a demo action — no real content was changed.
                </p>
              </div>
            )}

            <div className="flex items-center gap-2 mb-3">
              <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${SEVERITY_STYLES[activeCase.severity]}`}>
                {activeCase.severity === 'high' ? 'High' : activeCase.severity === 'med' ? 'Med' : 'Low'}
              </span>
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-gray-100 text-gray-600">
                {activeCase.category} · {activeCase.context}
              </span>
              <span className="text-xs text-gray-400 ml-auto">
                Case #{activeCase.id.toUpperCase()} · {activeCase.postedAgo} open
              </span>
            </div>

            <h2 className="text-2xl font-black text-gray-900 mb-1">{activeCase.title}</h2>
            <p className="text-sm text-gray-500 mb-4">
              By {activeCase.authorHandle} · reported by {activeCase.reportedByCount} members
            </p>

            <div className="bg-[#F5F0E8] rounded-xl p-5 mb-5">
              <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-2">
                Reported content
              </p>
              <p className="text-lg italic text-gray-800 mb-3">&ldquo;{activeCase.reportedContent}&rdquo;</p>
              <p className="text-sm text-gray-500">
                {activeCase.replies} replies · {activeCase.likes} ♥ · posted {activeCase.postedAgo}
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
              <div>
                <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-3">
                  Who reported
                </p>
                <ul className="space-y-3">
                  {activeCase.reporters.map((r) => (
                    <li key={r.handle} className="flex items-center gap-3">
                      <Avatar initials={r.initials} color={r.avatarColor} size="sm" />
                      <div className="min-w-0 flex-1">
                        <p className="font-bold text-gray-900 text-sm truncate">{r.handle}</p>
                        <p className="text-xs text-gray-500 truncate">{r.reason}</p>
                      </div>
                      <span className="text-xs text-gray-400 shrink-0">{r.timeAgo}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-3">
                  Author history
                </p>
                <div className="flex items-center gap-3 mb-2">
                  <Avatar initials={activeCase.authorInitial} color={activeCase.authorColor} size="sm" />
                  <div className="min-w-0">
                    <p className="font-bold text-gray-900 text-sm">{activeCase.authorHandle}</p>
                    <p className="text-xs text-gray-500">
                      Member {activeCase.authorMemberSince} · {activeCase.authorPostCount} posts ·{' '}
                      {activeCase.authorPriorWarns} prior warn
                    </p>
                  </div>
                </div>
                {activeCase.authorHistory.map((h, i) => (
                  <p key={i} className="text-xs text-gray-500 leading-relaxed">
                    {h.date} · {h.label}
                  </p>
                ))}
              </div>
            </div>

            <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-3">Action</p>
            <div className="flex flex-wrap gap-2 mb-4">
              <button
                type="button"
                onClick={() => handleAction('Keep · dismiss flags')}
                className="border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 transition-colors"
              >
                Keep · dismiss flags
              </button>
              <button
                type="button"
                onClick={() => handleAction('Soft-warn author')}
                className="border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 transition-colors"
              >
                Soft-warn author
              </button>
              <button
                type="button"
                onClick={() => handleAction('Hide post · notify author')}
                className="border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 transition-colors"
              >
                Hide post · notify author
              </button>
            </div>
            <div className="flex flex-wrap gap-2 mb-5">
              <button
                type="button"
                onClick={() => handleAction('Remove · 30-day mute')}
                className="inline-flex items-center gap-2 bg-red-600 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-red-700 transition-colors"
              >
                <Trash2 size={14} aria-hidden="true" /> Remove · 30-day mute
              </button>
              <button
                type="button"
                onClick={() => handleAction('Escalated to safety')}
                className="inline-flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-red-100 transition-colors"
              >
                <ShieldAlert size={14} aria-hidden="true" /> Escalate to safety
              </button>
            </div>

            <textarea
              value={messageDraft}
              onChange={(e) => setMessageDraft(e.target.value.slice(0, MAX_LENGTHS.longText))}
              maxLength={MAX_LENGTHS.longText}
              rows={4}
              placeholder="Optional message to author (template)"
              className="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-gray-50 resize-none mb-3"
            />
            <button
              type="button"
              onClick={handleSendMessage}
              className="text-sm font-semibold text-gray-700 hover:text-gray-900 flex items-center gap-1"
            >
              Send message <ArrowRight size={13} aria-hidden="true" />
            </button>
          </div>
        ) : (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center text-gray-400">
            Full detail template is only built for the first demo case — select it from the queue to review.
          </div>
        )}
      </div>
    </AdminLayout>
  );
};

export default ModerationPage;