// ============================================================
// MindCare — Therapist Console: Circles (community)
// ============================================================

import React, { useState } from 'react';
import { Video, Link2, Check, ShieldAlert } from 'lucide-react';
import TherapistLayout from '../components/therapist/TherapistLayout';
import Avatar from '../components/common/Avatar';
import {
  THERAPIST_CIRCLES,
  CIRCLES_TOTAL_AVAILABLE,
  CIRCLE_POSTS,
  CIRCLE_QUESTIONS_WAITING,
  CIRCLE_STATS,
} from '../constants/therapistConsole';
import { sanitizeText, MAX_LENGTHS } from '../utils/validation';

type FeedFilter = 'Recent' | 'Questions for therapist' | 'Top this week';

const CirclesPage: React.FC = () => {
  const [activeCircleId, setActiveCircleId] = useState(THERAPIST_CIRCLES[0].id);
  const [feedFilter, setFeedFilter] = useState<FeedFilter>('Recent');
  const [postDraft, setPostDraft] = useState('');
  const [replyDrafts, setReplyDrafts] = useState<Record<string, string>>({});

  const activeCircle = THERAPIST_CIRCLES.find((c) => c.id === activeCircleId) ?? THERAPIST_CIRCLES[0];
  const visiblePosts = CIRCLE_POSTS.filter((p) => p.circleName === activeCircle.name);

  const handlePost = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = sanitizeText(postDraft);
    if (!clean) return;
    // TODO: real API call — server must independently re-check the
    // medical-advice-risk filter before publishing, not just trust the client.
    console.info('[MindCare] Circle post submitted:', { circle: activeCircle.name, content: clean });
    setPostDraft('');
  };

  const handleReplyChange = (postId: string, value: string) => {
    setReplyDrafts((prev) => ({ ...prev, [postId]: value.slice(0, MAX_LENGTHS.longText) }));
  };

  const handlePostAnswer = (postId: string) => {
    const draft = replyDrafts[postId];
    const clean = sanitizeText(draft ?? '');
    if (!clean) return;
    // TODO: real API call. Server-side moderation for medical-advice risk
    // is mandatory here — this is public-facing clinical guidance.
    console.info('[MindCare] Circle answer posted:', { postId, content: clean });
    setReplyDrafts((prev) => ({ ...prev, [postId]: '' }));
  };

  return (
    <TherapistLayout
      breadcrumb={['Care', 'Circles']}
      headerAction={
        <div className="flex gap-2 shrink-0">
          <button
            type="button"
            className="border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 transition-colors"
          >
            Community guidelines
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 transition-colors"
          >
            + Host a Q&amp;A
          </button>
        </div>
      }
    >
      <h1 className="text-5xl font-black text-gray-900 mb-2">
        Where your <span className="italic font-serif font-normal">people</span> talk.
      </h1>
      <p className="text-gray-500 mb-8 max-w-2xl">
        You show up here as a verified therapist — answers carry a green check. No medical advice in DMs.
      </p>

      <div className="grid grid-cols-1 xl:grid-cols-[280px_1fr_320px] gap-6">
        {/* Your circles */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 h-fit">
          <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-1">Your circles</p>
          <p className="text-xs text-gray-400 mb-4">
            {THERAPIST_CIRCLES.length} of {CIRCLES_TOTAL_AVAILABLE} available
          </p>

          <div className="-mx-5">
            {THERAPIST_CIRCLES.map((circle) => {
              const isActive = circle.id === activeCircleId;
              return (
                <button
                  key={circle.id}
                  type="button"
                  onClick={() => setActiveCircleId(circle.id)}
                  className={`w-full text-left px-5 py-3.5 flex items-center gap-3 border-l-4 transition-colors ${
                    isActive ? 'bg-[#F5F0E8] border-gray-900' : 'border-transparent hover:bg-gray-50'
                  }`}
                >
                  <span className={`w-9 h-9 rounded-full shrink-0 ${circle.color}`} aria-hidden="true" />
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-gray-900 truncate">{circle.name}</p>
                    <p className="text-xs text-gray-500">
                      {circle.memberCount.toLocaleString()} members · {circle.role}
                    </p>
                  </div>
                  {circle.unreadCount ? (
                    <span className="min-w-[1.25rem] h-5 px-1.5 rounded-full bg-orange-500 text-white text-[11px] font-bold flex items-center justify-center shrink-0">
                      {circle.unreadCount}
                    </span>
                  ) : null}
                </button>
              );
            })}
          </div>

          <button
            type="button"
            className="w-full mt-4 border border-gray-200 text-gray-700 text-sm font-semibold py-2.5 rounded-xl hover:border-gray-400 transition-colors"
          >
            Browse more circles
          </button>
        </div>

        {/* Feed */}
        <div>
          {/* Composer */}
          <form onSubmit={handlePost} className="bg-[#EFE9DF] rounded-2xl p-5 mb-5">
            <div className="flex gap-3 mb-3">
              <Avatar initials="TM" color="bg-blue-950" />
              <textarea
                value={postDraft}
                onChange={(e) => setPostDraft(e.target.value.slice(0, MAX_LENGTHS.longText))}
                maxLength={MAX_LENGTHS.longText}
                rows={2}
                placeholder={`Share something with the ${activeCircle.name} circle... (your therapist badge will show)`}
                className="flex-1 px-4 py-3 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white resize-none"
              />
            </div>
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold px-3 py-1.5 rounded-full bg-white border border-gray-200 text-gray-700">
                  {activeCircle.name}
                </span>
                <button
                  type="button"
                  aria-label="Attach video"
                  className="w-9 h-9 rounded-lg bg-white border border-gray-200 flex items-center justify-center text-gray-500 hover:border-gray-400"
                >
                  <Video size={14} />
                </button>
                <button
                  type="button"
                  aria-label="Attach link"
                  className="w-9 h-9 rounded-lg bg-white border border-gray-200 flex items-center justify-center text-gray-500 hover:border-gray-400"
                >
                  <Link2 size={14} />
                </button>
                <p className="text-xs text-gray-500 hidden sm:block">
                  Answers in your circles count toward verified-voice score.
                </p>
              </div>
              <button
                type="submit"
                disabled={!postDraft.trim()}
                className="bg-gray-900 text-white text-sm font-semibold px-5 py-2.5 rounded-xl hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                Post
              </button>
            </div>
          </form>

          {/* Feed filters */}
          <div className="flex gap-2 mb-5">
            {(['Recent', 'Questions for therapist', 'Top this week'] as FeedFilter[]).map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => setFeedFilter(f)}
                className={`text-sm font-semibold px-4 py-2 rounded-full transition-colors ${
                  feedFilter === f ? 'bg-gray-900 text-white' : 'bg-white border border-gray-200 text-gray-600 hover:border-gray-400'
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          {/* Posts */}
          <div className="space-y-5">
            {visiblePosts.length === 0 ? (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center text-gray-400">
                No posts in {activeCircle.name} yet in this demo.
              </div>
            ) : (
              visiblePosts.map((post) => (
                <div key={post.id} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-start gap-3">
                      <Avatar initials={post.authorInitial} color={post.authorColor} />
                      <div>
                        <p className="text-sm">
                          <span className="font-bold text-gray-900">Anonymous</span>{' '}
                          <span className="text-gray-400">{post.authorHandle}</span> · in{' '}
                          <span className="font-semibold text-gray-700">{post.circleName}</span>
                        </p>
                        <p className="text-xs text-gray-400">{post.timeAgo}</p>
                      </div>
                    </div>
                    {post.isAskingTherapist && (
                      <span className="text-xs font-semibold text-rose-700 bg-rose-100 px-3 py-1 rounded-full shrink-0">
                        Asking a therapist
                      </span>
                    )}
                  </div>

                  <p className="text-gray-800 leading-relaxed mb-3">{post.content}</p>

                  <div className="flex items-center gap-5 text-sm text-gray-400 mb-4">
                    <span>{post.likes}</span>
                    <span>{post.commentCount} 💬</span>
                    <span>{post.repostCount} ↺</span>
                  </div>

                  {post.therapistReply ? (
                    <div className="bg-emerald-50/60 border border-emerald-200 rounded-xl p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Avatar initials="TM" color="bg-blue-950" size="sm" />
                        <p className="text-sm font-bold text-gray-900 flex items-center gap-1">
                          Your reply <Check size={13} className="text-emerald-600" aria-hidden="true" />
                          <span className="text-emerald-700 font-semibold">verified therapist</span>
                        </p>
                        <span className="text-xs text-gray-400 ml-auto hidden sm:inline">
                          No diagnosing in public · talk to your therapist for that
                        </span>
                      </div>
                      <textarea
                        value={replyDrafts[post.id] ?? post.therapistReply.content}
                        onChange={(e) => handleReplyChange(post.id, e.target.value)}
                        maxLength={MAX_LENGTHS.longText}
                        rows={4}
                        className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white resize-none mb-3"
                      />
                      <div className="flex items-center justify-between flex-wrap gap-2">
                        <p className="text-xs text-gray-500 flex items-center gap-1.5">
                          <ShieldAlert size={12} aria-hidden="true" /> Aida pre-checked for medical-advice risk ·{' '}
                          <span className="text-emerald-600 font-semibold flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-emerald-500" /> clear
                          </span>
                        </p>
                        <div className="flex gap-2">
                          <button
                            type="button"
                            className="border border-gray-200 bg-white text-gray-700 text-xs font-semibold px-3 py-2 rounded-lg hover:border-gray-400"
                          >
                            Save draft
                          </button>
                          <button
                            type="button"
                            onClick={() => handlePostAnswer(post.id)}
                            className="inline-flex items-center gap-1.5 bg-gray-900 text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-gray-800"
                          >
                            <Check size={12} aria-hidden="true" /> Post answer
                          </button>
                        </div>
                      </div>
                    </div>
                  ) : (
                    post.isAskingTherapist && (
                      <div>
                        <textarea
                          value={replyDrafts[post.id] ?? ''}
                          onChange={(e) => handleReplyChange(post.id, e.target.value)}
                          maxLength={MAX_LENGTHS.longText}
                          rows={3}
                          placeholder="Write a verified answer…"
                          className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-900 bg-gray-50 resize-none mb-2"
                        />
                        <button
                          type="button"
                          onClick={() => handlePostAnswer(post.id)}
                          className="bg-gray-900 text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-gray-800"
                        >
                          Post answer
                        </button>
                      </div>
                    )
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right sidebar */}
        <aside className="space-y-6">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-1">
              Verified voice · {CIRCLE_STATS.month}
            </p>
            <h3 className="text-lg font-bold text-gray-900 mb-4">Your reach</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-3xl font-black text-gray-900">{CIRCLE_STATS.answers}</p>
                <p className="text-xs text-gray-500">Answers</p>
              </div>
              <div>
                <p className="text-3xl font-black text-gray-900">{(CIRCLE_STATS.peopleHelped / 1000).toFixed(1)}k</p>
                <p className="text-xs text-gray-500">People helped</p>
              </div>
              <div>
                <p className="text-3xl font-black text-gray-900">{CIRCLE_STATS.helpfulRatePercent}%</p>
                <p className="text-xs text-gray-500">Helpful rate</p>
              </div>
              <div>
                <p className="text-3xl font-black text-gray-900">{CIRCLE_STATS.trialReferrals}</p>
                <p className="text-xs text-gray-500">Trial referrals</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-4">
              Questions waiting for a therapist
            </p>
            <ul className="divide-y divide-gray-100">
              {CIRCLE_QUESTIONS_WAITING.map((q) => (
                <li key={q.id} className="py-3">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-gray-100 text-gray-600">
                      {q.tag}
                    </span>
                    <span className="text-xs text-gray-400">{q.timeAgo}</span>
                  </div>
                  <p className="text-sm text-gray-800 leading-snug">{q.question}</p>
                </li>
              ))}
            </ul>
          </div>

          <div className="bg-[#EFE9DF] rounded-2xl p-6">
            <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-2">Private to you</p>
            <p className="text-sm text-gray-600 leading-relaxed">
              Your patients can&apos;t see what you post here unless they&apos;re members of the same circle — and
              your replies never name them.
            </p>
          </div>
        </aside>
      </div>
    </TherapistLayout>
  );
};

export default CirclesPage;