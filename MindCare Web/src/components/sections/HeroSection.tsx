// ============================================================
// MindCare — Hero Section (Screen 1)
// ============================================================

import React from 'react';
import { Link } from 'react-router-dom';
import { Shield, Heart, Lock } from 'lucide-react';
import Button from '../common/Button';
import { ROUTES } from '../../constants';

// ——— Floating appointment card ———
const AppointmentCard: React.FC = () => (
  <div className="absolute top-8 right-0 bg-gray-900 text-white rounded-2xl px-5 py-4 shadow-2xl min-w-[220px] z-10">
    <p className="text-[10px] font-semibold tracking-widest text-gray-400 uppercase mb-3">
      Next · Today 5 PM
    </p>
    <div className="flex items-center gap-3">
      <div className="w-9 h-9 rounded-full bg-gradient-to-br from-orange-400 to-rose-400 flex items-center justify-center text-xs font-bold">
        TM
      </div>
      <div>
        <p className="font-semibold text-sm">Dr. Tariq</p>
        <p className="text-gray-400 text-xs">Anxiety · 50 min</p>
      </div>
    </div>
  </div>
);

// ——— Mood mini-card ———
const MoodCard: React.FC = () => (
  <div className="absolute bottom-0 right-8 bg-white rounded-2xl px-5 py-4 shadow-xl border border-gray-100 min-w-[200px]">
    <p className="text-[10px] font-semibold tracking-widest text-gray-500 uppercase mb-2">
      Mood · 14 Days
    </p>
    {/* Tiny SVG sparkline */}
    <svg viewBox="0 0 120 30" className="w-full h-8" aria-hidden="true">
      <polyline
        points="0,20 20,18 40,22 60,14 80,16 100,10 120,12"
        fill="none"
        stroke="#10B981"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
    <div className="flex items-center justify-between mt-2">
      <span className="text-[10px] text-gray-400">2 weeks ago</span>
      <span className="text-[10px] font-semibold text-emerald-600">↑ steady</span>
    </div>
  </div>
);

// ——— Hero avatar group (dummy users) ———
const AvatarGroup: React.FC = () => {
  const colors = ['bg-orange-400', 'bg-emerald-400', 'bg-purple-400', 'bg-blue-400'];
  const labels = ['L', 'A', 'H', 'O'];
  return (
    <div className="flex items-center gap-2">
      <div className="flex -space-x-2">
        {colors.map((c, i) => (
          <div
            key={i}
            className={`w-8 h-8 rounded-full border-2 border-[#F5F0E8] ${c} flex items-center justify-center text-white text-xs font-bold`}
            aria-hidden="true"
          >
            {labels[i]}
          </div>
        ))}
      </div>
      <div>
        <p className="text-xs font-semibold text-gray-900">12,400+</p>
        <p className="text-[10px] text-gray-500">walking the path · 14 cities</p>
      </div>
    </div>
  );
};

// ——— Trust badges ———
const TrustBadges: React.FC = () => (
  <div className="flex flex-wrap gap-6 mt-6">
    {[
      { icon: <Shield size={14} />, text: 'PMDC-verified therapists' },
      { icon: <Heart size={14} />, text: 'Umang · Rozan partner' },
      { icon: <Lock size={14} />, text: 'HIPAA-aligned' },
    ].map(({ icon, text }) => (
      <div key={text} className="flex items-center gap-2 text-xs text-gray-500">
        <span className="text-gray-400">{icon}</span>
        <span>{text}</span>
      </div>
    ))}
  </div>
);

// ——— Decorative abstract blobs ———
const AbstractBlobs: React.FC = () => (
  <div className="relative w-full h-full" aria-hidden="true">
    {/* Background dark pill */}
    <div className="absolute inset-0 bg-gray-900 rounded-3xl overflow-hidden">
      {/* Blobs */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 rounded-full bg-gradient-to-br from-orange-300/30 to-rose-400/40 blur-2xl" />
      <div className="absolute bottom-8 right-8 w-40 h-40 rounded-full bg-gradient-to-br from-stone-600/60 to-stone-800/80" />
      <div className="absolute top-8 left-8 w-32 h-32 rounded-full bg-gradient-to-br from-orange-400/20 to-amber-300/10 blur-xl" />
      {/* Layered organic shapes */}
      <svg className="absolute bottom-0 left-0 w-full h-40 opacity-20" viewBox="0 0 400 120" preserveAspectRatio="none">
        <path d="M0 80 Q100 20 200 60 Q300 100 400 40 L400 120 L0 120 Z" fill="#6B7280" />
        <path d="M0 100 Q150 50 300 80 Q350 95 400 70 L400 120 L0 120 Z" fill="#4B5563" />
      </svg>
    </div>
  </div>
);

// ——— Main Hero Section ———
const HeroSection: React.FC = () => (
  <section
    className="min-h-screen bg-[#F5F0E8] pt-24 pb-16"
    aria-labelledby="hero-heading"
  >
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Eyebrow */}
      <p className="text-xs font-semibold tracking-[0.2em] text-gray-500 uppercase mb-8">
        Mental Care · Weekly · Since 2024
      </p>

      <div className="grid lg:grid-cols-2 gap-12 items-center">
        {/* Left: Copy */}
        <div>
          <h1
            id="hero-heading"
            className="text-5xl sm:text-6xl xl:text-7xl font-black text-gray-900 leading-[1.05] tracking-tight mb-8"
            style={{ fontFamily: "'Inter', sans-serif" }}
          >
            A quieter{' '}
            <em className="not-italic italic" style={{ fontFamily: "'Playfair Display', serif" }}>
              mind
            </em>
            <br />
            is the work
            <br />
            of{' '}
            <em style={{ fontFamily: "'Playfair Display', serif" }}>a year</em>, not
            <br />a download.
          </h1>

          <p className="text-gray-600 text-base sm:text-lg leading-relaxed max-w-md mb-10">
            MindCare pairs you with a verified therapist, supports you between sessions
            with an AI co-pilot they shape, and walks the year with you. Body data,
            journaling, peer circles — held by humans, not just an app.
          </p>

          {/* CTA row */}
          <div className="flex flex-wrap items-center gap-4 mb-8">
            <Link to={ROUTES.ONBOARDING}>
              <Button size="lg" variant="primary" className="rounded-full font-bold">
                Get started →
              </Button>
            </Link>
            <button className="flex items-center gap-2 text-sm font-semibold text-gray-700 hover:text-gray-900 transition-colors">
              <span className="w-10 h-10 rounded-full bg-white shadow-md flex items-center justify-center">
                ▶
              </span>
              Watch · 90 seconds
            </button>
            <AvatarGroup />
          </div>

          <TrustBadges />
        </div>

        {/* Right: Visual card */}
        <div className="relative h-96 lg:h-[520px] hidden md:block">
          <div className="absolute inset-0 lg:inset-8">
            <AbstractBlobs />
          </div>
          <AppointmentCard />
          <MoodCard />
        </div>
      </div>
    </div>
  </section>
);

export default HeroSection;
