// ============================================================
// MindCare — "The Path" Parallax Banner
// Full-bleed photographic pause between sections, echoing the
// hero's "walking the path" line with a slow scroll parallax.
// ============================================================

import React, { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import Reveal from '../motion/Reveal';

const PathBannerSection: React.FC = () => {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ['start end', 'end start'] });
  const y = useTransform(scrollYProgress, [0, 1], ['-8%', '8%']);

  return (
    <section
      ref={ref}
      className="relative h-[70vh] min-h-[420px] overflow-hidden"
      aria-label="The path, one step at a time"
    >
      <motion.div className="absolute inset-0 scale-110" style={{ y }} aria-hidden="true">
        <img
          src="https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?q=80&w=1800&auto=format&fit=crop"
          alt=""
          loading="lazy"
          className="w-full h-full object-cover"
        />
      </motion.div>
      <div className="absolute inset-0 bg-gray-900/55" aria-hidden="true" />

      <div className="relative h-full max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col items-center justify-center text-center">
        <Reveal>
          <p className="text-xs font-semibold tracking-[0.3em] text-white/70 uppercase mb-6">
            One step, then the next
          </p>
        </Reveal>
        <Reveal delay={0.1}>
          <p
            className="text-3xl sm:text-4xl lg:text-5xl text-white font-medium leading-snug"
            style={{ fontFamily: "'Playfair Display', serif" }}
          >
            "A quieter mind isn't found. It's{' '}
            <em>walked toward</em>, a little further each week."
          </p>
        </Reveal>
      </div>
    </section>
  );
};

export default PathBannerSection;
