// ============================================================
// MindCare — How It Works Section
// ============================================================

import React from 'react';
import { HOW_IT_WORKS } from '../../constants';

const HowItWorksSection: React.FC = () => (
  <section
    id="how-it-works"
    className="bg-[#F5F0E8] py-24"
    aria-labelledby="how-it-works-heading"
  >
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="grid lg:grid-cols-2 gap-12 items-start">
        {/* Left heading */}
        <div className="lg:sticky lg:top-24">
          <p className="text-xs font-semibold tracking-[0.2em] text-gray-500 uppercase mb-4">
            How It Works
          </p>
          <h2
            id="how-it-works-heading"
            className="text-4xl sm:text-5xl font-black text-gray-900 leading-tight"
          >
            Not an app.
            <br />
            <em style={{ fontFamily: "'Playfair Display', serif" }}>A practice.</em>
          </h2>
          <p className="mt-6 text-gray-600 text-base leading-relaxed max-w-sm">
            You'll meet someone trained. They'll meet you weekly. And the days in between
            won't be empty — they'll be the work.
          </p>
        </div>

        {/* Right: Steps grid */}
        <div className="grid sm:grid-cols-2 gap-4">
          {HOW_IT_WORKS.map((step) => (
            <article
              key={step.number}
              className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-shadow"
            >
              <div className="w-9 h-9 rounded-xl bg-orange-50 border border-orange-100 flex items-center justify-center mb-4">
                <span className="text-xs font-black text-orange-600">{step.number}</span>
              </div>
              <h3 className="text-base font-bold text-gray-900 mb-2">{step.title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">{step.description}</p>
            </article>
          ))}
        </div>
      </div>
    </div>
  </section>
);

export default HowItWorksSection;
