// ============================================================
// MindCare — Application Router
// Uses React Router v6 with lazy-loaded pages (code-splitting)
// ============================================================

import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ROUTES } from '../constants';

// ——— Lazy page imports ———
const LandingPage = lazy(() => import('../pages/LandingPage'));
const OnboardingPage = lazy(() => import('../pages/OnboardingPage'));
const ClientAppPage = lazy(() => import('../pages/ClientAppPage'));
const ClinicianPage = lazy(() => import('../pages/ClinicianPage'));
const SignInPage = lazy(() => import('../pages/SignInPage'));
const StoriesPage = lazy(() => import('../pages/StoriesPage'));
const ForNGOsPage = lazy(() => import('../pages/ForNGOsPage'));
const ForTherapistsPage = lazy(() => import('../pages/ForTherapistsPage'));
const TherapistLoginPage = lazy(() => import('../pages/TherapistLoginPage'));
const TherapistRegisterPage = lazy(() => import('../pages/TherapistRegisterPage'));

// ——— Full-screen loading fallback ———
const PageLoader: React.FC = () => (
  <div
    className="min-h-screen bg-[#F5F0E8] flex items-center justify-center"
    aria-live="polite"
    aria-label="Loading page"
  >
    <div className="flex flex-col items-center gap-4">
      <div className="w-8 h-8 border-2 border-gray-900 border-t-transparent rounded-full animate-spin" />
      <p className="text-sm text-gray-500 font-medium">Loading…</p>
    </div>
  </div>
);

const AppRouter: React.FC = () => (
  <BrowserRouter>
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Screen 1: Landing */}
        <Route path={ROUTES.HOME} element={<LandingPage />} />

        {/* Screen 2: Onboarding role picker */}
        <Route path={ROUTES.ONBOARDING} element={<OnboardingPage />} />

        {/* Screen 3: Client app download */}
        <Route path={ROUTES.CLIENT_APP} element={<ClientAppPage />} />

        {/* Clinician application */}
        <Route path={ROUTES.CLINICIAN_APP} element={<ClinicianPage />} />

        {/* Auth */}
        <Route path={ROUTES.SIGN_IN} element={<SignInPage />} />

        {/* Screen: Stories */}
        <Route path={ROUTES.STORIES} element={<StoriesPage />} />

        {/* Screen: For NGOs */}
        <Route path={ROUTES.FOR_NGOS} element={<ForNGOsPage />} />

        {/* Screen: For Therapists */}
        <Route path={ROUTES.FOR_THERAPISTS} element={<ForTherapistsPage />} />

        {/* Screen: Therapist auth */}
        <Route path={ROUTES.THERAPIST_LOGIN} element={<TherapistLoginPage />} />
        <Route path={ROUTES.THERAPIST_REGISTER} element={<TherapistRegisterPage />} />

        {/* Catch-all → home */}
        <Route path="*" element={<Navigate to={ROUTES.HOME} replace />} />
      </Routes>
    </Suspense>
  </BrowserRouter>
);

export default AppRouter;