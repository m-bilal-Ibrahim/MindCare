// ============================================================
// MindCare — Partners & Press Marquee Section
// ============================================================

import React from 'react';
import { PARTNERS } from '../../constants';

const PartnersSection: React.FC = () => (
  <section
    className="bg-[#F5F0E8] border-t border-b border-gray-200 py-8"
    aria-label="Partners and press"
  >
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex flex-col sm:flex-row items-center gap-8 sm:gap-16">
        <p className="text-xs font-bold tracking-[0.2em] text-gray-500 uppercase whitespace-nowrap shrink-0">
          Partners &amp; Press
        </p>
        <div className="flex flex-wrap items-center gap-8 sm:gap-12 overflow-hidden">
          {PARTNERS.map((p) => (
            <span
              key={p.name}
              className="text-gray-400 font-semibold text-sm tracking-wide hover:text-gray-700 transition-colors cursor-default"
            >
              {p.name}
            </span>
          ))}
        </div>
      </div>
    </div>
  </section>
);

export default PartnersSection;
