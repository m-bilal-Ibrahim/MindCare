// ============================================================
// MindCare — Shared layout for legal/policy pages
// (Privacy, Terms, HIPAA Alignment, Cookie Policy)
// ============================================================

import React from 'react';
import Navbar from './Navbar';
import Footer from './Footer';
import Reveal from '../motion/Reveal';
import type { LegalSection } from '../../types';

interface LegalPageLayoutProps {
  eyebrow: string;
  title: React.ReactNode;
  intro: string;
  lastUpdated: string;
  sections: LegalSection[];
}

const LegalPageLayout: React.FC<LegalPageLayoutProps> = ({
  eyebrow,
  title,
  intro,
  lastUpdated,
  sections,
}) => (
  <div className="min-h-screen mc-page-glow">
    <Navbar />

    <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pt-32 pb-24">
      <Reveal>
        <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-6">{eyebrow}</p>
        <h1 className="text-4xl sm:text-5xl font-black text-gray-900 leading-[1.1] mb-4">{title}</h1>
        <p className="text-gray-600 text-lg leading-relaxed max-w-2xl mb-2">{intro}</p>
        <p className="text-xs text-gray-400 mb-14">Last updated · {lastUpdated}</p>
      </Reveal>

      <div className="grid lg:grid-cols-[220px_1fr] gap-12">
        {/* Sticky in-page nav */}
        <nav aria-label="Sections" className="hidden lg:block">
          <ul className="space-y-1 sticky top-28" role="list">
            {sections.map((s) => (
              <li key={s.id}>
                <a
                  href={`#${s.id}`}
                  className="block text-sm text-gray-500 hover:text-gray-900 py-1.5 transition-colors"
                >
                  {s.title}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        {/* Sections */}
        <div className="space-y-12">
          {sections.map((section, i) => (
            <Reveal key={section.id} delay={Math.min(i * 0.05, 0.3)}>
              <section id={section.id} className="scroll-mt-28">
                <h2 className="text-xl font-bold text-gray-900 mb-4">{section.title}</h2>
                <div className="space-y-3">
                  {section.body.map((paragraph, pi) => (
                    <p key={pi} className="text-sm text-gray-600 leading-relaxed">
                      {paragraph}
                    </p>
                  ))}
                </div>
              </section>
            </Reveal>
          ))}
        </div>
      </div>
    </main>

    <Footer />
  </div>
);

export default LegalPageLayout;
