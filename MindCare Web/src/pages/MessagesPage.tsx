// ============================================================
// MindCare — Therapist Console: Messages
// ============================================================

import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { FileText, Video, MoreHorizontal, Link2, Send, Code } from 'lucide-react';
import TherapistLayout from '../components/therapist/TherapistLayout';
import Avatar from '../components/common/Avatar';
import { MESSAGE_THREADS, buildPatientDetailRoute, CONSOLE_ROUTES } from '../constants/therapistConsole';
import { sanitizeText, MAX_LENGTHS } from '../utils/validation';
import type { ChatMessage } from '../types/therapistConsole';

const MessagesPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const requestedPatientId = searchParams.get('patientId');
  const initialThread = MESSAGE_THREADS.find((t) => t.patientId === requestedPatientId) ?? MESSAGE_THREADS[0];

  const [activeThreadId, setActiveThreadId] = useState(initialThread.id);
  const [threads, setThreads] = useState(MESSAGE_THREADS);
  const [draft, setDraft] = useState('');
  const [search, setSearch] = useState('');

  const activeThread = threads.find((t) => t.id === activeThreadId) ?? threads[0];

  const filteredThreads = threads.filter((t) => {
    const query = sanitizeText(search).toLowerCase();
    if (!query) return true;
    return t.patientName.toLowerCase().includes(query) || t.preview.toLowerCase().includes(query);
  });

  const handleSelectThread = (id: string) => {
    setActiveThreadId(id);
    setThreads((prev) => prev.map((t) => (t.id === id ? { ...t, unreadCount: 0 } : t)));
  };

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = sanitizeText(draft);
    if (!clean) return;

    const newMessage: ChatMessage = {
      id: `m-${Date.now()}`,
      sender: 'therapist',
      content: clean,
      time: 'Just now',
      dateGroup: 'Today',
    };

    // TODO: send over an encrypted, authenticated channel — never trust
    // this client-side append as the source of truth for delivery.
    setThreads((prev) =>
      prev.map((t) =>
        t.id === activeThreadId ? { ...t, messages: [...t.messages, newMessage], preview: clean, timeAgo: 'now' } : t
      )
    );
    setDraft('');
  };

  const handleUseAidaDraft = () => {
    if (!activeThread.aidaDraftReply) return;
    setDraft(activeThread.aidaDraftReply);
  };

  return (
    <TherapistLayout breadcrumb={['Practice', 'Messages']}>
      <div className="grid grid-cols-1 lg:grid-cols-[360px_1fr] gap-6 h-[calc(100vh-160px)]">
        {/* Thread list */}
        <div className="bg-[#F5F0E8] flex flex-col min-h-0">
          <h1 className="text-4xl font-black text-gray-900 mb-1">Inbox</h1>
          <p className="text-sm text-gray-500 mb-4">Between-session chat · 48h response window</p>
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value.slice(0, MAX_LENGTHS.shortText))}
            maxLength={MAX_LENGTHS.shortText}
            placeholder="Search messages…"
            className="w-full px-4 py-2.5 text-sm border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white mb-4"
          />

          <div className="flex-1 overflow-y-auto -mx-1 px-1 space-y-1">
            {filteredThreads.map((thread) => {
              const isActive = thread.id === activeThreadId;
              return (
                <button
                  key={thread.id}
                  type="button"
                  onClick={() => handleSelectThread(thread.id)}
                  className={`w-full text-left px-3 py-3 rounded-xl border-l-4 transition-colors ${
                    isActive ? 'bg-white border-gray-900' : 'border-transparent hover:bg-white/60'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className="relative shrink-0">
                      <Avatar initials={thread.patientInitials} color={thread.avatarColor} />
                      {thread.online && (
                        <span
                          className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-emerald-500 border-2 border-[#F5F0E8]"
                          aria-hidden="true"
                        />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <p className="font-bold text-gray-900 truncate">{thread.patientName}</p>
                        <span className="text-xs text-gray-400 shrink-0">{thread.timeAgo}</span>
                      </div>
                      <p className="text-sm text-gray-500 truncate">{thread.preview}</p>
                    </div>
                    {thread.unreadCount > 0 && (
                      <span className="min-w-[1.25rem] h-5 px-1.5 rounded-full bg-orange-500 text-white text-[11px] font-bold flex items-center justify-center shrink-0">
                        {thread.unreadCount}
                      </span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Conversation */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 flex flex-col min-h-0">
          {/* Conversation header */}
          <div className="flex items-center gap-3 px-6 py-4 border-b border-gray-100">
            <Avatar initials={activeThread.patientInitials} color={activeThread.avatarColor} />
            <div className="flex-1 min-w-0">
              <button
                type="button"
                onClick={() => navigate(buildPatientDetailRoute(activeThread.patientId))}
                className="font-bold text-gray-900 hover:underline"
              >
                {activeThread.patientName}
              </button>
              <p className="text-xs text-gray-500">
                {activeThread.online && <span className="text-emerald-600">● Online</span>}
                {activeThread.online && ' · '}
                {activeThread.lastSessionMeta}
              </p>
            </div>
            <div className="flex gap-2 shrink-0">
              <button
                type="button"
                onClick={() => navigate(buildPatientDetailRoute(activeThread.patientId))}
                className="inline-flex items-center gap-1.5 border border-gray-200 text-gray-700 text-xs font-semibold px-3 py-2 rounded-lg hover:border-gray-400"
              >
                <FileText size={13} aria-hidden="true" /> Notes
              </button>
              <button
                type="button"
                onClick={() => navigate(CONSOLE_ROUTES.IN_SESSION)}
                className="inline-flex items-center gap-1.5 bg-gray-900 text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-gray-800"
              >
                <Video size={13} aria-hidden="true" /> Start session
              </button>
              <button
                type="button"
                aria-label="More options"
                className="w-8 h-8 rounded-lg border border-gray-200 flex items-center justify-center text-gray-500 hover:border-gray-400"
              >
                <MoreHorizontal size={14} />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
            {activeThread.messages.map((msg, i) => {
              const showDateHeader = i === 0 || activeThread.messages[i - 1].dateGroup !== msg.dateGroup;
              return (
                <React.Fragment key={msg.id}>
                  {showDateHeader && (
                    <p className="text-center text-xs font-semibold tracking-widest text-gray-400 uppercase py-2">
                      {msg.dateGroup}
                    </p>
                  )}
                  <div className={`flex ${msg.sender === 'therapist' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-md ${msg.sender === 'therapist' ? 'items-end' : 'items-start'} flex flex-col`}>
                      <div
                        className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                          msg.sender === 'therapist' ? 'bg-gray-900 text-white' : 'bg-[#F5F0E8] text-gray-800'
                        }`}
                      >
                        {msg.content}
                      </div>
                      <p className="text-xs text-gray-400 mt-1 px-1">{msg.time}</p>
                    </div>
                  </div>
                </React.Fragment>
              );
            })}

            {activeThread.aidaDraftReply && (
              <div className="bg-[#EFE9DF] border border-gray-200 rounded-2xl p-4 max-w-md">
                <p className="text-xs font-semibold text-gray-500 flex items-center gap-1.5 mb-2">
                  <Code size={12} aria-hidden="true" /> Aida draft reply
                </p>
                <p className="text-sm text-gray-800 italic mb-3">&ldquo;{activeThread.aidaDraftReply}&rdquo;</p>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={handleUseAidaDraft}
                    className="bg-gray-900 text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-gray-800"
                  >
                    Use
                  </button>
                  <button
                    type="button"
                    className="bg-white border border-gray-200 text-gray-700 text-xs font-semibold px-3 py-2 rounded-lg hover:border-gray-400"
                  >
                    Tweak
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Composer */}
          <form onSubmit={handleSend} className="border-t border-gray-100 p-4">
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value.slice(0, MAX_LENGTHS.longText))}
              maxLength={MAX_LENGTHS.longText}
              rows={2}
              placeholder={`Write to ${activeThread.patientName.split(' ')[0]} — replies count toward your 48h window.`}
              className="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white resize-none mb-2"
            />
            <div className="flex items-center justify-between">
              <p className="text-xs text-gray-400">
                End-to-end encrypted · {activeThread.patientName.split(' ')[0]} can see typing indicator
              </p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  aria-label="Attach video"
                  className="w-9 h-9 rounded-lg border border-gray-200 flex items-center justify-center text-gray-500 hover:border-gray-400"
                >
                  <Video size={14} />
                </button>
                <button
                  type="button"
                  aria-label="Attach link"
                  className="w-9 h-9 rounded-lg border border-gray-200 flex items-center justify-center text-gray-500 hover:border-gray-400"
                >
                  <Link2 size={14} />
                </button>
                <button
                  type="submit"
                  disabled={!draft.trim()}
                  className="inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  <Send size={14} aria-hidden="true" /> Send
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </TherapistLayout>
  );
};

export default MessagesPage;