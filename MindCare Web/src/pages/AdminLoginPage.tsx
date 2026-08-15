// ============================================================
// MindCare — Admin Sign In Page
// ============================================================

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, ArrowRight, ShieldCheck } from 'lucide-react';
import Logo from '../components/common/Logo';
import Button from '../components/common/Button';
import { ROUTES } from '../constants';
import { ADMIN_ROUTES } from '../constants/adminConsole';
import { validateEmail, validatePassword, MAX_LENGTHS } from '../utils/validation';
import { useAdminAuth } from '../utils/adminAuthGuard';

const AdminLoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAdminAuth();
  const [form, setForm] = useState({ email: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [attempts, setAttempts] = useState(0);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Basic client-side UX guard only — real rate limiting, MFA
    // enforcement, and lockout MUST happen server-side. See the
    // security notes in src/utils/adminAuthGuard.tsx.
    if (attempts >= 5) {
      setError('Too many attempts. Please wait a moment and try again.');
      return;
    }

    const emailError = validateEmail(form.email);
    if (emailError) {
      setError(emailError);
      return;
    }
    const passwordError = validatePassword(form.password);
    if (passwordError) {
      setError(passwordError);
      return;
    }

    setLoading(true);
    setAttempts((prev) => prev + 1);
    // TODO: wire to real admin auth service — MFA challenge, httpOnly
    // session cookie, audit-log the login attempt (success or failure).
    window.setTimeout(() => {
      setLoading(false);
      const success = login(form.email, form.password);
      if (success) {
        navigate(ADMIN_ROUTES.OVERVIEW, { replace: true });
      } else {
        setError('Sign-in failed. Please check your details and try again.');
      }
    }, 800);
  };

  return (
    <div className="min-h-screen bg-[#F5F0E8] flex flex-col items-center justify-center px-4 py-16">
      <div className="w-full max-w-md">
        <div className="flex items-center justify-between mb-10">
          <Logo />
          <Link to={ROUTES.HOME} className="text-sm text-gray-500 hover:text-gray-900 transition-colors">
            ← Back
          </Link>
        </div>

        <div className="bg-white rounded-3xl shadow-sm border border-gray-100 px-8 py-8">
          <div className="flex items-center gap-2 mb-2">
            <ShieldCheck size={16} className="text-gray-400" aria-hidden="true" />
            <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase">Admin console · Sign in</p>
          </div>
          <h1 className="text-3xl font-black text-gray-900 mb-2">Restricted access.</h1>
          <p className="text-sm text-gray-500 mb-8">
            This console holds sensitive platform data. Access is limited to authorized staff.
          </p>

          <form onSubmit={handleSubmit} className="space-y-5" noValidate>
            <div>
              <label htmlFor="email" className="block text-xs font-semibold text-gray-700 mb-1.5">
                Work email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                value={form.email}
                onChange={handleChange}
                placeholder="ayesha.sultan@mindcare.pk"
                autoComplete="email"
                maxLength={MAX_LENGTHS.email}
                className="w-full px-4 py-3.5 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-white"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-xs font-semibold text-gray-700 mb-1.5">
                Password
              </label>
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

            <Button type="submit" variant="primary" size="lg" fullWidth loading={loading}>
              Sign in <ArrowRight size={16} aria-hidden="true" />
            </Button>

            <p className="text-center text-xs text-gray-400 flex items-center justify-center gap-1.5 pt-2">
              <ShieldCheck size={12} aria-hidden="true" />
              MFA and audit logging required before production use.
            </p>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AdminLoginPage;