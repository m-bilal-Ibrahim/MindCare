// ============================================================
// MindCare — Screen 2: Onboarding Role Selection
// "Are you here to find care, or to give it?"
// ============================================================

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Heart, Code2 } from 'lucide-react';
import OnboardingHeader from '../components/onboarding/OnboardingHeader';
import RoleCard from '../components/onboarding/RoleCard';
import { useOnboarding } from '../hooks/useOnboarding';
import { CLIENT_BENEFITS, CLINICIAN_BENEFITS, ROUTES } from '../constants';
import type { UserRole } from '../types';

const OnboardingPage: React.FC = () => {
  const navigate = useNavigate();
  const { selectRole } = useOnboarding();

  const handleSelect = (role: UserRole) => {
    selectRole(role);
    if (role === 'client') {
      navigate(ROUTES.CLIENT_APP);
    } else {
      navigate(ROUTES.CLINICIAN_APP);
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F0E8] flex flex-col">
      {/* Header */}
      <OnboardingHeader
        backLabel="Back to home"
        backTo={ROUTES.HOME}
        step={1}
        totalSteps={2}
        stepLabel="Who are you today"
      />

      {/* Body */}
      <main className="flex-1 flex flex-col items-center justify-start px-4 sm:px-8 pt-12 pb-16">
        {/* Step indicator */}
        <p className="text-xs font-bold tracking-[0.25em] text-gray-500 uppercase mb-10">
          Step 1 of 2 · Who are you today
        </p>

        {/* Main heading */}
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-center text-gray-900 leading-tight max-w-3xl mb-4">
          Hello there. Are you here
          <br />
          <em style={{ fontFamily: "'Playfair Display', serif" }}>to find care</em>, or{' '}
          <em style={{ fontFamily: "'Playfair Display', serif" }}>to give it?</em>
        </h1>

        <p className="text-gray-500 text-center text-base max-w-md mb-14">
          Two doors, same building. Pick the one that fits today — you can always come
          back.
        </p>

        {/* Role cards */}
        <div className="grid md:grid-cols-2 gap-6 w-full max-w-4xl">
          {/* Client card */}
          <RoleCard
            role="client"
            eyebrow="For people seeking care"
            headline={
              <>
                I'm here for{' '}
                <em style={{ fontFamily: "'Playfair Display', serif" }}>myself</em>.
              </>
            }
            description="Anxiety, burnout, sleep, grief, relationships, addiction — or you just want a steadier inside. MindCare lives on your phone; let's get it there."
            benefits={CLIENT_BENEFITS}
            footer="MindCare lives in your phone. Get the app to begin."
            icon={<Heart size={22} className="text-rose-500" />}
            primaryCta="Get the app →"
            secondaryCta="Learn more"
            onSelect={handleSelect}
          />

          {/* Clinician card */}
          <RoleCard
            role="clinician"
            eyebrow="For clinicians"
            headline={
              <>
                I'm here to{' '}
                <em style={{ fontFamily: "'Playfair Display', serif" }}>practice</em>.
              </>
            }
            description="You're licensed (PMDC) and want a verified, low-friction way to run your practice — sessions, notes, payouts, and a co-pilot you control."
            benefits={CLINICIAN_BENEFITS}
            footer="Apply in 10 minutes. First patient match within 48 hours."
            dark
            icon={<Code2 size={22} className="text-gray-400" />}
            primaryCta="Apply as a clinician →"
            secondaryCta="See how it works"
            onSelect={handleSelect}
          />
        </div>
      </main>
    </div>
  );
};

export default OnboardingPage;
