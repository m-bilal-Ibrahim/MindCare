// ============================================================
// MindCare — "What You Get" Features Section
// ============================================================

import React from 'react';
import { FEATURES } from '../../constants';

const FeaturesSection: React.FC = () => (
  <section
    id="features"
    className="bg-[#F5F0E8] py-24"
    aria-labelledby="features-heading"
  >
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="grid lg:grid-cols-2 gap-6 mb-16 items-end">
        <div>
          <p className="text-xs font-semibold tracking-[0.2em] text-gray-500 uppercase mb-4">
            Everything in one place
          </p>
          <h2
            id="features-heading"
            className="text-4xl sm:text-5xl font-black text-gray-900 leading-tight"
          >
            What you get
            <br />
            with MindCare.
          </h2>
        </div>
        <p className="text-gray-500 text-base leading-relaxed lg:text-right">
          One subscription, one therapist, one running thread.
          <br />
          Everything else is built around that.
        </p>
      </div>

      {/* Feature grid */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {FEATURES.map((feature) => (
          <article
            key={feature.id}
            className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm hover:shadow-md transition-all hover:-translate-y-0.5"
          >
            <div
              className={`w-11 h-11 rounded-xl flex items-center justify-center text-xl mb-5 ${feature.color}`}
              aria-hidden="true"
            >
              {feature.icon}
            </div>
            <h3 className="text-base font-bold text-gray-900 mb-2">{feature.title}</h3>
            <p className="text-sm text-gray-500 leading-relaxed">{feature.description}</p>
          </article>
        ))}
      </div>
    </div>
  </section>
);

export default FeaturesSection;
