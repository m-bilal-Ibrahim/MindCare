// ============================================================
// MindCare — Custom Hook: useOnboarding
// Manages role selection state; ready for backend auth flow
// ============================================================

import { useState, useCallback } from 'react';
import type { UserRole, OnboardingChoice } from '../types';

interface OnboardingState {
  selectedRole: UserRole | null;
  choice: OnboardingChoice | null;
  isLoading: boolean;
  error: string | null;
}

interface UseOnboardingReturn extends OnboardingState {
  selectRole: (role: UserRole) => void;
  reset: () => void;
}

export function useOnboarding(): UseOnboardingReturn {
  const [state, setState] = useState<OnboardingState>({
    selectedRole: null,
    choice: null,
    isLoading: false,
    error: null,
  });

  const selectRole = useCallback((role: UserRole) => {
    // In future: POST /api/onboarding/role with JWT
    setState({
      selectedRole: role,
      choice: { role, selectedAt: new Date().toISOString() },
      isLoading: false,
      error: null,
    });
  }, []);

  const reset = useCallback(() => {
    setState({ selectedRole: null, choice: null, isLoading: false, error: null });
  }, []);

  return { ...state, selectRole, reset };
}
