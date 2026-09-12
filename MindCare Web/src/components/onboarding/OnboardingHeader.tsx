// ============================================================
// MindCare — Onboarding Header (step indicator + back link)
// ============================================================

import React from 'react';
import { Link } from 'react-router-dom';
import Logo from '../common/Logo';

interface OnboardingHeaderProps {
  backLabel: string;
  backTo: string;
  step: number;
  totalSteps: number;
  stepLabel: string;
}

const OnboardingHeader: React.FC<OnboardingHeaderProps> = ({
  backLabel,
  backTo,
  step: _step,
  totalSteps: _totalSteps,
  stepLabel: _stepLabel,
}) => (
  <header className="flex items-center justify-between px-6 sm:px-10 py-5 border-b border-gray-200/60">
    <Logo />
    <Link
      to={backTo}
      className="text-sm text-gray-500 hover:text-gray-900 transition-colors flex items-center gap-1"
    >
      ← {backLabel}
    </Link>
  </header>
);

export default OnboardingHeader;
