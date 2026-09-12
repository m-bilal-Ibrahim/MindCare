// ============================================================
// MindCare — Vision / Mission / Promise Dark Section
// ============================================================

import React from 'react';
import { Check } from 'lucide-react';
import { HERO_STATS } from '../../constants';

const promises = [
  'A real, verified human at the center of every plan.',
  'Your data is yours. Always.',
  'No predatory ads, no growth-hack notifications.',
  "If you can't afford it, our NGO partners can.",
];

const VisionMissionSection: React.FC = () => (
  <section
    className="bg-gray-900 text-white py-24"
    aria-label="Vision, mission and our promise"
  >
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="grid md:grid-cols-3 gap-12">
        {/* Vision */}
        <div>
          <p className="text-xs font-bold tracking-[0.2em] text-gray-500 uppercase mb-4">
            Vision
          </p>
          <h2 className="text-3xl font-black leading-tight">
            That every person has access to{' '}
            <em style={{ fontFamily: "'Playfair Display', serif" }}>good,</em>
            <br />
            <em style={{ fontFamily: "'Playfair Display', serif" }}>held</em> mental care.
          </h2>
        </div>

        {/* Mission */}
        <div>
          <p className="text-xs font-bold tracking-[0.2em] text-gray-500 uppercase mb-4">
            Mission
          </p>
          <p className="text-gray-300 text-sm leading-relaxed mb-8">
            To make weekly therapy normal, affordable, and accountable — and to use
            technology to{' '}
            <strong className="text-white">extend the therapist's hand</strong> into the
            rest of the week, not replace it.
          </p>
          {/* Stats */}
          <div className="grid grid-cols-3 gap-4">
            {HERO_STATS.map((s) => (
              <div key={s.label}>
                <p className="text-2xl font-black text-white">{s.value}</p>
                <p className="text-xs text-gray-500 mt-1">{s.label}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Promise */}
        <div>
          <p className="text-xs font-bold tracking-[0.2em] text-gray-500 uppercase mb-4">
            Our Promise
          </p>
          <ul className="space-y-3" role="list">
            {promises.map((p) => (
              <li key={p} className="flex items-start gap-3 text-sm text-gray-300">
                <Check size={14} className="shrink-0 mt-0.5 text-emerald-400" aria-hidden="true" />
                {p}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  </section>
);

export default VisionMissionSection;
