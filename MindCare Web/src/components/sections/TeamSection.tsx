// ============================================================
// MindCare — "Built by" Team Section
// Photos are loaded from the backend once available; until then
// each card falls back to an initials avatar.
// ============================================================

import React from 'react';
import { User } from 'lucide-react';
import { TEAM_MEMBERS } from '../../constants';
import { RevealGroup, RevealItem } from '../motion/Reveal';
import type { TeamMember } from '../../types';

const ACCENTS = ['from-orange-400 to-rose-400', 'from-emerald-400 to-teal-400', 'from-purple-400 to-fuchsia-400'];

const TeamPhoto: React.FC<{ member: TeamMember; accent: string }> = ({ member, accent }) =>
  member.photoUrl ? (
    <img
      src={member.photoUrl}
      alt={member.name}
      loading="lazy"
      className="w-24 h-24 rounded-full object-cover shadow-md"
    />
  ) : (
    <div
      className={`w-24 h-24 rounded-full bg-gradient-to-br ${accent} flex items-center justify-center shadow-md`}
      aria-hidden="true"
    >
      <User size={32} className="text-white/90" strokeWidth={1.75} />
    </div>
  );

const TeamSection: React.FC = () => (
  <section className="py-24" aria-labelledby="team-heading">
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
      <p className="text-xs font-semibold tracking-[0.2em] text-gray-500 uppercase mb-4">
        Built by
      </p>
      <h2 id="team-heading" className="text-4xl sm:text-5xl font-black text-gray-900 leading-tight mb-14">
        The people <em style={{ fontFamily: "'Playfair Display', serif" }}>behind it.</em>
      </h2>

      <RevealGroup className="grid sm:grid-cols-3 gap-8 max-w-3xl mx-auto" stagger={0.12}>
        {TEAM_MEMBERS.map((member, i) => (
          <RevealItem key={member.id}>
            <div className="flex flex-col items-center">
              <TeamPhoto member={member} accent={ACCENTS[i % ACCENTS.length]} />
              <p className="mt-4 font-bold text-gray-900">{member.name}</p>
              <p className="text-sm text-gray-500">{member.role}</p>
            </div>
          </RevealItem>
        ))}
      </RevealGroup>
    </div>
  </section>
);

export default TeamSection;
