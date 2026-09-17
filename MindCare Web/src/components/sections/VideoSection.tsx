// ============================================================
// MindCare — "See it in action" Video Section
// Reserves the player space; the actual clip is injected once the
// backend serves a URL (pass `videoUrl` — poster shows until then).
// ============================================================

import React, { useState } from 'react';
import { Play } from 'lucide-react';
import Reveal from '../motion/Reveal';

interface VideoSectionProps {
  videoUrl?: string;
  posterUrl?: string;
}

const DEFAULT_POSTER =
  'https://images.unsplash.com/photo-1573497620053-ea5300f94f21?q=80&w=1600&auto=format&fit=crop';

const VideoSection: React.FC<VideoSectionProps> = ({ videoUrl, posterUrl = DEFAULT_POSTER }) => {
  const [playing, setPlaying] = useState(false);

  return (
    <section id="watch" className="py-24 scroll-mt-20" aria-labelledby="watch-heading">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <Reveal>
          <p className="text-xs font-semibold tracking-[0.2em] text-gray-500 uppercase mb-4 text-center">
            See it in action
          </p>
          <h2
            id="watch-heading"
            className="text-4xl sm:text-5xl font-black text-gray-900 leading-tight text-center mb-12"
          >
            90 seconds,{' '}
            <em style={{ fontFamily: "'Playfair Display', serif" }}>one honest look.</em>
          </h2>
        </Reveal>

        <Reveal delay={0.1}>
          <div className="relative aspect-video rounded-3xl overflow-hidden shadow-xl bg-gray-900">
            {videoUrl && playing ? (
              // Real clip, once the backend provides a URL
              <video
                src={videoUrl}
                controls
                autoPlay
                className="absolute inset-0 w-full h-full object-cover"
              />
            ) : (
              <>
                <img
                  src={posterUrl}
                  alt="MindCare product preview"
                  loading="lazy"
                  className="absolute inset-0 w-full h-full object-cover opacity-70"
                />
                <div className="absolute inset-0 bg-gray-900/40" />
                <button
                  type="button"
                  onClick={() => videoUrl && setPlaying(true)}
                  aria-label="Play the MindCare overview video"
                  className="absolute inset-0 flex items-center justify-center group"
                >
                  <span className="w-20 h-20 rounded-full bg-white/95 shadow-2xl flex items-center justify-center transition-transform group-hover:scale-105">
                    <Play size={28} className="text-gray-900 ml-1" fill="currentColor" aria-hidden="true" />
                  </span>
                </button>
                {!videoUrl && (
                  <span className="absolute bottom-5 left-1/2 -translate-x-1/2 text-[11px] font-semibold tracking-widest text-white/70 uppercase">
                    Video coming soon
                  </span>
                )}
              </>
            )}
          </div>
        </Reveal>
      </div>
    </section>
  );
};

export default VideoSection;
