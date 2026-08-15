// ============================================================
// MindCare — Therapist Sign In Page ("Welcome back, doctor.")
// ============================================================

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, ArrowRight } from 'lucide-react';
import Logo from '../components/common/Logo';
import Button from '../components/common/Button';
import { ROUTES, THERAPIST_LOGIN_TESTIMONIAL, THERAPIST_WAITING_ITEMS } from '../constants';
import { CONSOLE_ROUTES } from '../constants/therapistConsole';
import { validateEmailOrPmdcId, validatePasswordForSignIn, MAX_LENGTHS } from '../utils/validation';
import { useTherapistAuth } from '../utils/authGuard';
import type { TherapistLoginPayload } from '../types';

const TherapistLoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useTherapistAuth();
  const [form, setForm] = useState<TherapistLoginPayload>({
    identifier: '',
    password: '',
    keepSignedIn: true,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [attempts, setAttempts] = useState(0);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
    setError(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Basic client-side UX guard only — the real rate limit,
    // account lockout, and credential check MUST happen server-side.
    if (attempts >= 5) {
      setError('Too many attempts. Please wait a moment and try again, or reset your password.');
      return;
    }

    const identifier = form.identifier.trim();

    const identifierError = validateEmailOrPmdcId(identifier);
    if (identifierError) {
      setError(identifierError);
      return;
    }

    // Sign-in uses the lighter length-only check — existing accounts
    // predate any policy change, so this only rejects clearly invalid
    // input, not passwords that don't meet the current signup bar.
    const passwordError = validatePasswordForSignIn(form.password);
    if (passwordError) {
      setError(passwordError);
      return;
    }

    setLoading(true);
    setAttempts((prev) => prev + 1);
    // TODO: wire to real auth service — send over HTTPS only, never log
    // the password, and let the backend own rate limiting + lockout.
    window.setTimeout(() => {
      setLoading(false);
      const success = login(identifier, form.password);
      if (success) {
        navigate(CONSOLE_ROUTES.TODAY, { replace: true });
      } else {
        setError('Sign-in failed. Please check your details and try again.');
      }
    }, 800);
  };

  return (
    <div className="min-h-screen bg-[#F5F0E8] grid grid-cols-1 lg:grid-cols-2">
      {/* Left — form */}
      <div className="flex flex-col px-4 sm:px-10 py-8">
        <div className="flex items-center justify-between mb-16">
          <Logo />
          <Link to={ROUTES.HOME} className="text-sm text-gray-500 hover:text-gray-900 transition-colors">
            ← Back
          </Link>
        </div>

        <div className="max-w-md mx-auto w-full flex-1 flex flex-col justify-center">
          <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-4">
            Therapist · Sign in
          </p>
          <h1 className="text-4xl sm:text-5xl font-black text-gray-900 leading-tight mb-4">
            Welcome back, <span className="italic font-serif font-normal">doctor.</span>
          </h1>
          <p className="text-gray-500 mb-10">3 patients are waiting for session notes.</p>

          <form onSubmit={handleSubmit} className="space-y-5" noValidate>
            <div>
              <label htmlFor="identifier" className="block text-xs font-semibold text-gray-700 mb-1.5">
                Email or PMDC ID
              </label>
              <input
                id="identifier"
                name="identifier"
                type="text"
                value={form.identifier}
                onChange={handleChange}
                placeholder="tariq.mahmood@mindcare.pk"
                autoComplete="username"
                maxLength={MAX_LENGTHS.email}
                spellCheck={false}
                className="w-full px-4 py-3.5 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label htmlFor="password" className="text-xs font-semibold text-gray-700">
                  Password
                </label>
                <button type="button" className="text-xs text-gray-500 hover:text-gray-900 underline underline-offset-2">
                  Forgot?
                </button>
              </div>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  value={form.password}
                  onChange={handleChange}
                  autoComplete="current-password"
                  maxLength={MAX_LENGTHS.password}
                  className="w-full px-4 py-3.5 pr-12 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error && (
              <p role="alert" className="text-sm text-red-600 bg-red-50 border border-red-100 px-4 py-3 rounded-xl">
                {error}
              </p>
            )}

            <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
              <input
                type="checkbox"
                name="keepSignedIn"
                checked={form.keepSignedIn}
                onChange={handleChange}
                className="w-4 h-4 rounded border-gray-300 accent-gray-900"
              />
              Keep me signed in on this device
            </label>

            <Button type="submit" variant="primary" size="lg" fullWidth loading={loading}>
              Sign in <ArrowRight size={16} aria-hidden="true" />
            </Button>

            <div className="flex items-center gap-3 py-1">
              <span className="flex-1 h-px bg-gray-200" />
              <span className="text-xs text-gray-400">or</span>
              <span className="flex-1 h-px bg-gray-200" />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <Button type="button" variant="secondary" size="md">
                Google
              </Button>
              <Button type="button" variant="secondary" size="md">
                PMDC SSO
              </Button>
            </div>

            <div className="bg-[#EFE9DF] rounded-xl px-4 py-4 text-sm text-gray-600">
              <span className="font-semibold text-gray-900">New to MindCare?</span> If you&apos;re a
              licensed clinician,{' '}
              <Link to={ROUTES.THERAPIST_REGISTER} className="underline underline-offset-2 font-semibold text-gray-900">
                apply to practice with us
              </Link>
              .
              <br />
              Verification takes 2–3 working days.
            </div>

            <p className="text-center text-xs text-gray-400 pt-2">
              Platform admin?{' '}
              <Link to="/admin/sign-in" className="underline underline-offset-2 text-gray-500 hover:text-gray-700">
                Sign in here
              </Link>
            </p>
          </form>
        </div>
      </div>

      {/* Right — testimonial panel */}
      <div className="hidden lg:flex flex-col justify-between bg-gray-900 px-16 py-16 relative overflow-hidden">
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-orange-600/20 rounded-full blur-3xl" aria-hidden="true" />

        <div className="relative">
          <p className="text-xs font-semibold tracking-widest text-orange-400 uppercase mb-8">
            {THERAPIST_LOGIN_TESTIMONIAL.label}
          </p>
          <blockquote className="text-3xl xl:text-4xl font-black text-white leading-tight mb-6">
            &ldquo;{THERAPIST_LOGIN_TESTIMONIAL.quote}&rdquo;
          </blockquote>
          <p className="text-gray-400">{THERAPIST_LOGIN_TESTIMONIAL.attribution}</p>
        </div>

        <div className="relative">
          <p className="text-xs font-semibold tracking-widest text-orange-400 uppercase mb-4">
            Waiting for you
          </p>
          <div className="space-y-3">
            {THERAPIST_WAITING_ITEMS.map((item) => (
              <div
                key={item.id}
                className="bg-gray-800/60 border border-gray-700/60 rounded-xl px-5 py-4 flex items-center justify-between"
              >
                <div className="flex items-center gap-4">
                  <span className={`w-3 h-3 rounded-full ${item.color}`} aria-hidden="true" />
                  <div>
                    <p className="text-white text-sm font-semibold">{item.title}</p>
                    <p className="text-xs text-gray-400">{item.meta}</p>
                  </div>
                </div>
                <ArrowRight size={16} className="text-gray-500" aria-hidden="true" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TherapistLoginPage;