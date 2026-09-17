// ============================================================
// MindCare — Stories Page ("Words from people walking it.")
// ============================================================

import React from 'react';
import Navbar from '../components/layout/Navbar';
import Footer from '../components/layout/Footer';
import Button from '../components/common/Button';
import Avatar from '../components/common/Avatar';
import Reveal, { RevealGroup, RevealItem } from '../components/motion/Reveal';
import { STORIES, STORIES_TOTAL_COUNT } from '../constants';

const StoriesPage: React.FC = () => {
  return (
    <div className="min-h-screen mc-page-glow">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-32 pb-24">
        <Reveal>
          <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-6">
            Stories · Consented, real
          </p>

          <h1 className="text-4xl sm:text-6xl font-black text-gray-900 leading-[1.05] mb-16 max-w-3xl">
            Words from people <span className="italic font-serif font-normal">walking it.</span>
          </h1>
        </Reveal>

        <RevealGroup className="grid grid-cols-1 sm:grid-cols-2 gap-6 lg:ml-auto lg:max-w-3xl" stagger={0.1}>
          {STORIES.map((story) => (
            <RevealItem key={story.id}>
              <article className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 flex flex-col justify-between min-h-[260px] h-full">
                <p className="text-xl text-gray-900 leading-snug font-medium">&ldquo;{story.quote}&rdquo;</p>

                <div className="flex items-center gap-3 mt-8">
                  <Avatar initials={story.avatarInitials} color={story.avatarColor} />
                  <div>
                    <p className="text-sm font-bold text-gray-900">
                      {story.name}, {story.age}
                    </p>
                    <p className="text-xs text-gray-500">
                      {story.location} · {story.tag}
                    </p>
                  </div>
                </div>
              </article>
            </RevealItem>
          ))}
        </RevealGroup>

        <Reveal delay={0.1}>
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 mt-14 pt-8 border-t border-gray-200">
            <p className="text-sm text-gray-500">Names changed in some · all stories shared with explicit consent.</p>
            <div className="flex gap-3 shrink-0">
              <Button variant="secondary" size="md">
                Share your story
              </Button>
              <Button variant="primary" size="md">
                See all {STORIES_TOTAL_COUNT} stories →
              </Button>
            </div>
          </div>
        </Reveal>
      </main>

      <Footer />
    </div>
  );
};

export default StoriesPage;