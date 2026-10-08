// ============================================================
// MindCare — Profile header from the live backend (GET /psychologists/me/)
// ============================================================

import React, { useCallback, useEffect, useState } from 'react';
import Avatar from '../common/Avatar';
import { ErrorPanel, WakingHint } from './ApiStates';
import { getMyProfile, type MyPsychologistProfile } from '../../services/psychologist.service';

const TAG_COLORS = ['bg-rose-100 text-rose-700', 'bg-violet-100 text-violet-700', 'bg-emerald-100 text-emerald-700', 'bg-sky-100 text-sky-700'];

const ProfileHeader: React.FC = () => {
  const [profile, setProfile] = useState<MyPsychologistProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    const res = await getMyProfile();
    if (res.data) setProfile(res.data);
    else setError(res.error ?? 'Couldn’t load your profile.');
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (error) return <ErrorPanel message={error} onRetry={load} />;
  if (!profile) {
    return (
      <div className="flex items-center gap-5" aria-live="polite">
        <div className="w-14 h-14 rounded-full bg-gray-200 animate-pulse" />
        <div className="space-y-2">
          <div className="h-8 w-56 rounded bg-gray-200 animate-pulse" />
          <WakingHint active />
        </div>
      </div>
    );
  }

  const initials =
    profile.full_name
      .replace(/^dr\.?\s+/i, '')
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((w) => w[0].toUpperCase())
      .join('') || '?';
  const place = [profile.city?.name, profile.country?.name].filter(Boolean).join(', ');
  const facts = [
    profile.years_of_experience != null ? `${profile.years_of_experience} years` : null,
    profile.license_number ? `License ${profile.license_number}` : null,
    place || null,
    profile.timezone || null,
    profile.languages.length ? profile.languages.map((l) => l.name).join(' · ') : null,
  ].filter(Boolean);

  return (
    <div className="flex items-start gap-5">
      <Avatar initials={initials} color="bg-blue-950" size="lg" />
      <div className="min-w-0">
        <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-1">
          {profile.qualifications || 'Psychologist'}
        </p>
        <h1 className="text-4xl font-black text-gray-900 mb-2">{profile.full_name}</h1>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-gray-500 mb-3">
          {facts.map((f) => (
            <span key={f}>{f}</span>
          ))}
        </div>
        {profile.specializations.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {profile.specializations.map((s, i) => (
              <span key={s.slug} className={`text-xs font-semibold px-3 py-1 rounded-full ${TAG_COLORS[i % TAG_COLORS.length]}`}>
                {s.name}
              </span>
            ))}
          </div>
        )}
        {profile.bio && <p className="text-sm text-gray-600 mt-4 max-w-2xl">{profile.bio}</p>}
      </div>
    </div>
  );
};

export default ProfileHeader;
