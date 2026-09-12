// ============================================================
// MindCare — "In Practice" Photo Gallery Section
// Three-column photographic showcase of the actual work:
// a real session, the days between, and quiet peer circles.
// ============================================================

import React from 'react';
import { motion } from 'framer-motion';
import { RevealGroup, RevealItem } from '../motion/Reveal';

interface GalleryCard {
  id: string;
  image: string;
  tag: string;
  title: string;
  description: string;
  accent: string;
}

const CARDS: GalleryCard[] = [
  {
    id: 'session',
    image: 'https://images.unsplash.com/photo-1573497620053-ea5300f94f21?q=80&w=900&auto=format&fit=crop',
    tag: 'Weekly · 50 min',
    title: 'A real session',
    description: 'Face to face with a verified therapist. Not a chatbot pretending to listen.',
    accent: 'bg-emerald-100 text-emerald-700',
  },
  {
    id: 'journal',
    image: 'https://images.unsplash.com/photo-1544027993-37dbfe43562a?q=80&w=900&auto=format&fit=crop',
    tag: 'Every day',
    title: 'The days between',
    description: 'Journaling, body data, tiny exercises — quietly reviewed by your therapist.',
    accent: 'bg-orange-100 text-orange-700',
  },
  {
    id: 'circle',
    image: 'https://images.unsplash.com/photo-1552196563-55cd4e45efb3?q=80&w=900&auto=format&fit=crop',
    tag: 'Anonymous · moderated',
    title: 'Quiet peer circles',
    description: 'Anxiety, grief, sober walks, new parents — held by people who get it.',
    accent: 'bg-rose-100 text-rose-700',
  },
];

const PracticeGallerySection: React.FC = () => (
  <section className="py-24" aria-labelledby="practice-heading">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <RevealGroup className="mb-14 max-w-2xl">
        <RevealItem>
          <p className="text-xs font-semibold tracking-[0.2em] text-gray-500 uppercase mb-4">
            What it actually looks like
          </p>
        </RevealItem>
        <RevealItem>
          <h2 id="practice-heading" className="text-4xl sm:text-5xl font-black text-gray-900 leading-tight">
            In practice, <em style={{ fontFamily: "'Playfair Display', serif" }}>not in theory.</em>
          </h2>
        </RevealItem>
      </RevealGroup>

      <RevealGroup className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6" stagger={0.15}>
        {CARDS.map((card) => (
          <RevealItem key={card.id}>
            <motion.article
              whileHover="hover"
              initial="rest"
              animate="rest"
              className="group relative rounded-3xl overflow-hidden shadow-sm border border-gray-100 bg-white h-full"
            >
              <div className="relative h-64 overflow-hidden">
                <motion.img
                  src={card.image}
                  alt={card.title}
                  loading="lazy"
                  variants={{ rest: { scale: 1 }, hover: { scale: 1.08 } }}
                  transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-black/0 to-transparent" />
                <span
                  className={`absolute top-4 left-4 text-[10px] font-bold tracking-widest uppercase px-3 py-1.5 rounded-full ${card.accent}`}
                >
                  {card.tag}
                </span>
              </div>
              <div className="p-6">
                <h3 className="text-base font-bold text-gray-900 mb-2">{card.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{card.description}</p>
              </div>
            </motion.article>
          </RevealItem>
        ))}
      </RevealGroup>
    </div>
  </section>
);

export default PracticeGallerySection;
