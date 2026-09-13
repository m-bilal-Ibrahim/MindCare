// ============================================================
// MindCare — How It Works Section
// ============================================================

import React from 'react';
import { HOW_IT_WORKS } from '../../constants';
import Reveal, { RevealGroup, RevealItem } from '../motion/Reveal';

const STEP_ACCENTS = [
  { chip: 'bg-orange-50 border-orange-100', text: 'text-orange-600' },
  { chip: 'bg-emerald-50 border-emerald-100', text: 'text-emerald-600' },
  { chip: 'bg-rose-50 border-rose-100', text: 'text-rose-600' },
  { chip: 'bg-purple-50 border-purple-100', text: 'text-purple-600' },
];

const HowItWorksSection: React.FC = () => (
  <section
    id="how-it-works"
    className="py-24 scroll-mt-20"
    aria-labelledby="how-it-works-heading"
  >
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="grid lg:grid-cols-2 gap-12 items-start">
        {/* Left heading */}
        <div className="lg:sticky lg:top-24">
          <Reveal>
            <p className="text-xs font-semibold tracking-[0.2em] text-gray-500 uppercase mb-4">
              How It Works
            </p>
          </Reveal>
          <Reveal delay={0.08}>
            <h2
              id="how-it-works-heading"
              className="text-4xl sm:text-5xl font-black text-gray-900 leading-tight"
            >
              Not an app.
              <br />
              <em
                className="bg-gradient-to-r from-orange-500 to-rose-500 bg-clip-text text-transparent"
                style={{ fontFamily: "'Playfair Display', serif" }}
              >
                A practice.
              </em>
            </h2>
          </Reveal>
          <Reveal delay={0.16}>
            <p className="mt-6 text-gray-600 text-base leading-relaxed max-w-sm">
              You'll meet someone trained. They'll meet you weekly. And the days in between
              won't be empty — they'll be the work.
            </p>
          </Reveal>
        </div>

        {/* Right: Steps grid */}
        <RevealGroup className="grid sm:grid-cols-2 gap-4" stagger={0.12}>
          {HOW_IT_WORKS.map((step, i) => {
            const accent = STEP_ACCENTS[i % STEP_ACCENTS.length];
            return (
              <RevealItem key={step.number}>
                <article className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-md hover:-translate-y-0.5 transition-all h-full">
                  <div className={`w-9 h-9 rounded-xl border flex items-center justify-center mb-4 ${accent.chip}`}>
                    <span className={`text-xs font-black ${accent.text}`}>{step.number}</span>
                  </div>
                  <h3 className="text-base font-bold text-gray-900 mb-2">{step.title}</h3>
                  <p className="text-sm text-gray-500 leading-relaxed">{step.description}</p>
                </article>
              </RevealItem>
            );
          })}
        </RevealGroup>
      </div>
    </div>
  </section>
);

export default HowItWorksSection;
