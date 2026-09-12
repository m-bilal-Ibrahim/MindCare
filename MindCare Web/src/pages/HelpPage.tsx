// ============================================================
// MindCare — Help Center Page ("How can we help?")
// ============================================================

import React, { useState } from 'react';
import { Users, Calendar, FileText, Activity, Code, Heart, Phone, MessageCircle, Send, Video, ArrowRight, type LucideIcon } from 'lucide-react';
import Navbar from '../components/layout/Navbar';
import Footer from '../components/layout/Footer';
import {
  HELP_POPULAR_LINKS,
  HELP_CATEGORIES,
  HELP_TOP_QUESTIONS,
  HELP_CRISIS_PHONE,
  HELP_CRISIS_PHONE_TEL,
  HELP_EMAIL,
  HELP_EMAIL_MAILTO,
} from '../constants';
import { sanitizeText, MAX_LENGTHS } from '../utils/validation';
import type { HelpCategory } from '../types';

const ICON_MAP: Record<HelpCategory['icon'], LucideIcon> = {
  users: Users,
  calendar: Calendar,
  'file-text': FileText,
  activity: Activity,
  code: Code,
  heart: Heart,
};

const HelpPage: React.FC = () => {
  const [search, setSearch] = useState('');

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Cap length client-side; real search is server-side and must
    // independently validate/sanitize the query before using it.
    setSearch(e.target.value.slice(0, MAX_LENGTHS.shortText));
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const query = sanitizeText(search);
    if (!query) return;
    // TODO: wire to real help-search endpoint
    // eslint-disable-next-line no-console
    console.info('[MindCare] Help search submitted:', query);
  };

  // Using buttons + window.location instead of anchor tags with tel:/mailto:
  // for reliability — plain, no markup fragility either way.
  const callUmang = () => {
    window.location.href = HELP_CRISIS_PHONE_TEL;
  };
  const emailHelp = () => {
    window.location.href = HELP_EMAIL_MAILTO;
  };

  return (
    <div className="min-h-screen bg-[#F5F0E8]">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-32 pb-24 grid grid-cols-1 lg:grid-cols-2 gap-10">
        {/* Left column */}
        <div>
          <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-6">Help center</p>
          <h1 className="text-4xl sm:text-6xl font-black text-gray-900 leading-[1.05] mb-6">
            How can we <span className="italic font-serif font-normal">help?</span>
          </h1>
          <p className="text-gray-600 text-lg mb-8">Search 240+ guides, or ping us — humans answer within 4 hours.</p>

          <form onSubmit={handleSearchSubmit} className="mb-4" role="search">
            <label htmlFor="help-search" className="sr-only">
              Search help articles
            </label>
            <input
              id="help-search"
              type="search"
              value={search}
              onChange={handleSearchChange}
              maxLength={MAX_LENGTHS.shortText}
              placeholder="Search help articles…"
              className="w-full px-5 py-3.5 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white"
            />
          </form>

          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm mb-12">
            <span className="text-gray-500">Popular:</span>
            {HELP_POPULAR_LINKS.map((link, i) => (
              <React.Fragment key={link}>
                <button type="button" className="text-gray-700 underline underline-offset-2 hover:text-gray-900">
                  {link}
                </button>
                {i < HELP_POPULAR_LINKS.length - 1 && <span className="text-gray-300">·</span>}
              </React.Fragment>
            ))}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {HELP_CATEGORIES.map((cat) => {
              const Icon = ICON_MAP[cat.icon];
              return (
                <button
                  key={cat.id}
                  type="button"
                  className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 flex items-center justify-between text-left hover:border-gray-300 transition-colors"
                >
                  <span className="flex items-center gap-4">
                    <span className="w-11 h-11 rounded-xl bg-[#EFE9DF] flex items-center justify-center text-gray-700 shrink-0">
                      <Icon size={18} aria-hidden="true" />
                    </span>
                    <span>
                      <span className="block font-bold text-gray-900">{cat.title}</span>
                      <span className="block text-sm text-gray-500">{cat.articleCount} articles</span>
                    </span>
                  </span>
                  <ArrowRight size={16} className="text-gray-300 shrink-0" aria-hidden="true" />
                </button>
              );
            })}
          </div>
        </div>

        {/* Right column */}
        <div>
          {/* Crisis box */}
          <div className="bg-orange-50 border border-orange-200 rounded-2xl p-8 mb-6">
            <p className="text-xs font-semibold tracking-widest text-orange-600 uppercase mb-4 flex items-center gap-2">
              ⚠ If you need help right now
            </p>
            <h2 className="text-2xl font-black text-gray-900 mb-3">Crisis support, free, 24/7.</h2>
            <p className="text-gray-700 leading-relaxed mb-6">
              If you or someone you love is in danger, please call Umang. A trained human picks up
              in under 90 seconds.
            </p>
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={callUmang}
                className="inline-flex items-center gap-2 bg-red-600 text-white text-sm font-semibold px-5 py-3 rounded-full hover:bg-red-700 transition-colors"
              >
                <Phone size={15} aria-hidden="true" /> Call Umang · {HELP_CRISIS_PHONE}
              </button>
              <button
                type="button"
                className="bg-white border border-gray-200 text-gray-900 text-sm font-semibold px-5 py-3 rounded-full hover:border-gray-400 transition-colors"
              >
                Tap SOS in the app
              </button>
            </div>
          </div>

          {/* Top questions */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
            <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-1">Top questions</p>
            <h3 className="text-lg font-bold text-gray-900 mb-5">The 5 we get most</h3>

            <ol className="divide-y divide-gray-100">
              {HELP_TOP_QUESTIONS.map((q, i) => (
                <li key={q.id}>
                  <button
                    type="button"
                    className="w-full flex items-center justify-between gap-4 py-4 text-left hover:text-gray-900"
                  >
                    <span className="flex items-baseline gap-4">
                      <span className="text-sm text-gray-400 font-mono">{String(i + 1).padStart(2, '0')}</span>
                      <span className="text-gray-800 font-medium">{q.question}</span>
                    </span>
                    <ArrowRight size={15} className="text-gray-300 shrink-0" aria-hidden="true" />
                  </button>
                </li>
              ))}
            </ol>

            <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-100 text-center">
              <button type="button" className="flex flex-col items-center gap-2 hover:opacity-80">
                <span className="w-11 h-11 rounded-full bg-[#EFE9DF] flex items-center justify-center">
                  <MessageCircle size={18} aria-hidden="true" />
                </span>
                <span className="text-sm font-semibold text-gray-900">Chat</span>
                <span className="text-xs text-gray-500">within 4 hours</span>
              </button>
              <button type="button" onClick={emailHelp} className="flex flex-col items-center gap-2 hover:opacity-80">
                <span className="w-11 h-11 rounded-full bg-[#EFE9DF] flex items-center justify-center">
                  <Send size={18} aria-hidden="true" />
                </span>
                <span className="text-sm font-semibold text-gray-900">Email</span>
                <span className="text-xs text-gray-500">{HELP_EMAIL}</span>
              </button>
              <button type="button" className="flex flex-col items-center gap-2 hover:opacity-80">
                <span className="w-11 h-11 rounded-full bg-[#EFE9DF] flex items-center justify-center">
                  <Video size={18} aria-hidden="true" />
                </span>
                <span className="text-sm font-semibold text-gray-900">Call back</span>
                <span className="text-xs text-gray-500">we ring you</span>
              </button>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default HelpPage;