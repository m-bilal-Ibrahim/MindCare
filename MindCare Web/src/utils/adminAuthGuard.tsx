// ============================================================
// MindCare — Admin Console Auth Guard
//
// This is a MOCK auth layer so the admin console screens can be
// reviewed end-to-end with dummy data. It is NOT itself secure —
// do not ship this as-is. Admin accounts see far more than a
// therapist account (every user's PII, every therapist's
// credentials, NGO partner banking/legal details, billing data),
// so this boundary matters even more than the therapist one:
//
//  1. Admin sessions must require MFA at login — a compromised
//     password alone should never be enough to reach this console.
//  2. Session must be a server-issued, short-lived token validated
//     on every request, stored in an httpOnly/Secure/SameSite cookie
//     — never in localStorage/sessionStorage.
//  3. Enforce role-based access control (RBAC) server-side: not
//     every admin should be able to approve verifications, issue
//     refunds, or export user data. Model these as distinct
//     permissions, not a single "is admin" flag.
//  4. Every sensitive action (approve/reject a verification, view
//     a user's unmasked contact info, export data, issue a refund)
//     must be audit-logged server-side with who/when/what — this
//     is both a security and compliance requirement.
//  5. Mask PII by default in the UI (as these mock screens do —
//     phone numbers and emails are partially redacted) and require
//     a specific, logged action to reveal full details.
//  6. Consider IP allowlisting and shorter session lifetimes for
//     admin accounts compared to regular user/therapist sessions.
// ============================================================

import React, { createContext, useContext, useState, type ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { ADMIN_ROUTES } from '../constants/adminConsole';

interface MockAdminSession {
  id: string;
  name: string;
  initials: string;
  role: string;
}

interface AdminAuthContextValue {
  admin: MockAdminSession | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => boolean;
  logout: () => void;
}

const MOCK_ADMIN: MockAdminSession = {
  id: 'admin-001',
  name: 'Ayesha Sultan',
  initials: 'AS',
  role: 'Ops admin',
};

const AdminAuthContext = createContext<AdminAuthContextValue>({
  admin: null,
  isAuthenticated: false,
  login: () => false,
  logout: () => {},
});

export const useAdminAuth = () => useContext(AdminAuthContext);

/**
 * Demo-only provider. Starts logged out so the sign-in flow can be
 * reviewed end-to-end. `login` here just checks both fields are
 * non-empty/valid — a real implementation replaces this with an API
 * call (plus MFA challenge) that returns a session, never resolved
 * client-side.
 */
export const AdminAuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<MockAdminSession | null>(null);

  const login = (email: string, password: string): boolean => {
    // TODO: replace with a real API call + MFA challenge over HTTPS.
    if (!email.trim() || !password) return false;
    setSession(MOCK_ADMIN);
    return true;
  };

  const logout = () => setSession(null);

  return (
    <AdminAuthContext.Provider value={{ admin: session, isAuthenticated: !!session, login, logout }}>
      {children}
    </AdminAuthContext.Provider>
  );
};

/**
 * Route guard — redirects to admin sign-in if no session.
 * Wrap every admin-console route with this.
 */
export const RequireAdminAuth: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAdminAuth();
  if (!isAuthenticated) {
    return <Navigate to={ADMIN_ROUTES.SIGN_IN} replace />;
  }
  return <>{children}</>;
};