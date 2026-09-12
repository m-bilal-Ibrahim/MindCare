// ============================================================
// MindCare — Partners Marquee Section
// ============================================================

import React from 'react';
import { PARTNERS } from '../../constants';

const PartnersSection: React.FC = () => (
  <section
    className="border-t border-b border-gray-200 py-8"
    aria-label="Partners"
  >
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex flex-col sm:flex-row items-center gap-8 sm:gap-16">
        <p className="text-xs font-bold tracking-[0.2em] text-gray-500 uppercase whitespace-nowrap shrink-0">
          Partners
        </p>

        <div
          className="group relative flex-1 overflow-hidden [mask-image:linear-gradient(to_right,transparent,black_10%,black_90%,transparent)]"
        >
          <div className="flex w-max gap-12 sm:gap-16 animate-marquee group-hover:[animation-play-state:paused]">
            {[...PARTNERS, ...PARTNERS].map((p, i) => (
              <span
                key={`${p.name}-${i}`}
                className="text-gray-400 font-semibold text-sm tracking-wide hover:text-gray-700 transition-colors cursor-default whitespace-nowrap"
              >
                {p.name}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  </section>
);

export default PartnersSection;
