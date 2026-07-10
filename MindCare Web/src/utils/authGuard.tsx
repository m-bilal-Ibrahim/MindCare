// ============================================================
// MindCare — Therapist Console Auth Guard
//
// This is a MOCK auth layer so the therapist console screens can
// be reviewed end-to-end with dummy data. It demonstrates the
// correct shape for real auth, but is NOT itself secure — do not
// ship this as-is. Before production:
//
//  1. Session must be a server-issued, short-lived token validated
//     on every request — never trust a client-side "isAuthenticated"
//     flag the way this demo does.
//  2. Store the session token in an httpOnly, Secure, SameSite=Strict
//     cookie set by the backend — never in localStorage/sessionStorage,
//     which is readable by any script (XSS = full account takeover).
//  3. Every route AND every API call must independently re-check
//     that this specific therapist is allowed to see this specific
//     patient (row-level authorization) — a hidden route is not
//     access control, it's just UI. The backend must enforce it.
//  4. All traffic must be HTTPS only (HSTS enabled).
//  5. Patient data here is health information — treat it like PHI:
//     encrypt at rest, log every access (who viewed which patient,
//     when), and apply least-privilege (a therapist should only ever
//     be able to query their own patients, enforced server-side).
//  6. Add session expiry + idle timeout, and require re-auth for
//     sensitive actions (e.g. exporting patient data).
// ============================================================

import React, { createContext, useContext, useState, type ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { ROUTES } from '../constants';

interface MockTherapistSession {
  id: string;
  name: string;
  initials: string;
  license: string;
}

interface AuthContextValue {
  therapist: MockTherapistSession | null;
  isAuthenticated: boolean;
  login: (identifier: string, password: string) => boolean;
  logout: () => void;
}

const MOCK_THERAPIST: MockTherapistSession = {
  id: 'ther-001',
  name: 'Dr. Tariq Mahmood',
  initials: 'TM',
  license: 'PMDC',
};

const AuthContext = createContext<AuthContextValue>({
  therapist: null,
  isAuthenticated: false,
  login: () => false,
  logout: () => {},
});

export const useTherapistAuth = () => useContext(AuthContext);

/**
 * Demo-only provider. Starts logged out so the sign-in flow can be
 * reviewed end-to-end. `login` here just checks both fields are
 * non-empty and accepts — a real implementation replaces this with
 * an API call that returns a session, and never resolves client-side.
 */
export const TherapistAuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<MockTherapistSession | null>(null);

  const login = (identifier: string, password: string): boolean => {
    // TODO: replace with a real API call to the auth endpoint over HTTPS.
    // The backend validates credentials and returns a session — this
    // client-side check is a placeholder so the demo flow works end to end.
    if (!identifier.trim() || !password) return false;
    setSession(MOCK_THERAPIST);
    return true;
  };

  const logout = () => setSession(null);

  return (
    <AuthContext.Provider value={{ therapist: session, isAuthenticated: !!session, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

/**
 * Route guard — redirects to therapist sign-in if no session.
 * Wrap every therapist-console route with this.
 */
export const RequireTherapistAuth: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useTherapistAuth();
  if (!isAuthenticated) {
    return <Navigate to={ROUTES.THERAPIST_LOGIN} replace />;
  }
  return <>{children}</>;
};