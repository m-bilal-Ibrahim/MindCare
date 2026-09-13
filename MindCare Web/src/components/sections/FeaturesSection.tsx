// ============================================================
// MindCare — "What You Get" Features Section
// ============================================================

import React from 'react';
import { motion } from 'framer-motion';
import { Stethoscope, Bot, Watch, NotebookPen, HeartHandshake, LifeBuoy, type LucideIcon } from 'lucide-react';
import { FEATURES } from '../../constants';
import Reveal, { RevealGroup, RevealItem } from '../motion/Reveal';
import type { FeatureIcon } from '../../types';

const ICON_MAP: Record<FeatureIcon, LucideIcon> = {
  therapist: Stethoscope,
  aida: Bot,
  mindband: Watch,
  journal: NotebookPen,
  circles: HeartHandshake,
  sos: LifeBuoy,
};

const FeaturesSection: React.FC = () => (
  <section
    id="features"
    className="py-24"
    aria-labelledby="features-heading"
  >
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="grid lg:grid-cols-2 gap-6 mb-16 items-end">
        <div>
          <Reveal>
            <p className="text-xs font-semibold tracking-[0.2em] text-gray-500 uppercase mb-4">
              Everything in one place
            </p>
          </Reveal>
          <Reveal delay={0.08}>
            <h2
              id="features-heading"
              className="text-4xl sm:text-5xl font-black text-gray-900 leading-tight"
            >
              What you get
              <br />
              with MindCare.
            </h2>
          </Reveal>
        </div>
        <Reveal delay={0.1}>
          <p className="text-gray-500 text-base leading-relaxed lg:text-right">
            One subscription, one therapist, one running thread.
            <br />
            Everything else is built around that.
          </p>
        </Reveal>
      </div>

      {/* Feature grid */}
      <RevealGroup className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6" stagger={0.08}>
        {FEATURES.map((feature) => {
          const Icon = ICON_MAP[feature.icon];
          return (
            <RevealItem key={feature.id}>
              <motion.article
                whileHover={{ y: -6 }}
                transition={{ duration: 0.25, ease: 'easeOut' }}
                className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm hover:shadow-md h-full"
              >
                <div
                  className={`w-11 h-11 rounded-xl flex items-center justify-center mb-5 bg-gradient-to-br text-white shadow-sm ${feature.color}`}
                  aria-hidden="true"
                >
                  <Icon size={20} strokeWidth={2.25} />
                </div>
                <h3 className="text-base font-bold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{feature.description}</p>
              </motion.article>
            </RevealItem>
          );
        })}
      </RevealGroup>
    </div>
  </section>
);

export default FeaturesSection;
