// ============================================================
// MindCare — Sign In Page (secure, HIPAA-aligned UX)
// ============================================================

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Eye, EyeOff, Lock, Mail } from 'lucide-react';
import Logo from '../components/common/Logo';
import Button from '../components/common/Button';
import { ROUTES } from '../constants';
import { signIn } from '../services/api.service';
import { validateEmail, validatePassword, MAX_LENGTHS } from '../utils/validation';

interface FormState {
  email: string;
  password: string;
}

const SignInPage: React.FC = () => {
  const [form, setForm] = useState<FormState>({ email: '', password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Basic client-side validation
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
    setError(null);

    const result = await signIn(form);
    setLoading(false);

    if (result.error) {
      setError('Invalid email or password. Please try again.');
    } else {
      // Store token securely (backend should use httpOnly cookies in production)
      if (result.data?.token) {
        sessionStorage.setItem('mc_access_token', result.data.token);
      }
      console.info('[MindCare] Signed in:', result.data?.user);
      setSuccess(true);
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F0E8] flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-6 sm:px-10 py-5 border-b border-gray-200/60">
        <Logo />
        <Link
          to={ROUTES.HOME}
          className="text-sm text-gray-500 hover:text-gray-900 transition-colors"
        >
          ← Back to home
        </Link>
      </header>

      {/* Form area */}
      <main className="flex-1 flex items-center justify-center px-4 py-16">
        <div className="w-full max-w-md">
          {success ? (
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-6">
                <span className="text-2xl">✓</span>
              </div>
              <h2 className="text-2xl font-black text-gray-900 mb-3">Welcome back!</h2>
              <p className="text-gray-500 text-sm mb-8">
                You're signed in. Redirecting to your dashboard…
              </p>
              <Link to={ROUTES.HOME}>
                <Button variant="primary" size="md">
                  Go to dashboard
                </Button>
              </Link>
            </div>
          ) : (
            <>
              <div className="text-center mb-10">
                <h1 className="text-3xl font-black text-gray-900 mb-2">Sign in</h1>
                <p className="text-sm text-gray-500">
                  Don't have an account?{' '}
                  <Link to={ROUTES.ONBOARDING} className="text-gray-900 font-semibold underline underline-offset-2 hover:text-orange-600">
                    Get started →
                  </Link>
                </p>
              </div>

              <form
                onSubmit={handleSubmit}
                className="bg-white rounded-3xl shadow-sm border border-gray-100 px-8 py-8 space-y-5"
                noValidate
                aria-label="Sign in form"
              >
                {/* Email */}
                <div>
                  <label htmlFor="email" className="block text-xs font-semibold text-gray-700 mb-1.5">
                    Email address
                  </label>
                  <div className="relative">
                    <Mail size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" aria-hidden="true" />
                    <input
                      id="email"
                      name="email"
                      type="email"
                      required
                      autoComplete="email"
                      maxLength={MAX_LENGTHS.email}
                      value={form.email}
                      onChange={handleChange}
                      placeholder="you@example.com"
                      className="w-full pl-10 pr-4 py-3 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-gray-50"
                    />
                  </div>
                </div>

                {/* Password */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label htmlFor="password" className="text-xs font-semibold text-gray-700">
                      Password
                    </label>
                    <button
                      type="button"
                      className="text-xs text-gray-500 hover:text-gray-900 underline underline-offset-2 transition-colors"
                    >
                      Forgot password?
                    </button>
                  </div>
                  <div className="relative">
                    <Lock size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" aria-hidden="true" />
                    <input
                      id="password"
                      name="password"
                      type={showPassword ? 'text' : 'password'}
                      required
                      autoComplete="current-password"
                      maxLength={MAX_LENGTHS.password}
                      value={form.password}
                      onChange={handleChange}
                      placeholder="Min. 8 characters"
                      className="w-full pl-10 pr-12 py-3 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-gray-50"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((v) => !v)}
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700 transition-colors"
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>

                {/* Error */}
                {error && (
                  <p
                    role="alert"
                    className="text-sm text-red-600 bg-red-50 border border-red-100 px-4 py-3 rounded-xl"
                  >
                    {error}
                  </p>
                )}

                {/* Submit */}
                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  fullWidth
                  loading={loading}
                >
                  Sign in
                </Button>

                {/* Dummy credentials hint (for testing only) */}
                <div className="bg-amber-50 border border-amber-100 rounded-xl px-4 py-3">
                  <p className="text-xs text-amber-700 font-semibold mb-1">🧪 Demo mode</p>
                  <p className="text-xs text-amber-600">
                    Enter any valid email + 8-char password to test the data flow.
                    <br />
                    e.g. <code className="font-mono">test@mindcare.pk</code> / <code className="font-mono">Test1234</code>
                  </p>
                </div>

                {/* Security note */}
                <p className="text-center text-xs text-gray-400 mt-2 flex items-center justify-center gap-1.5">
                  <Lock size={11} aria-hidden="true" />
                  HIPAA-aligned · Your data is encrypted in transit and at rest.
                </p>
              </form>
            </>
          )}
        </div>
      </main>
    </div>
  );
};

export default SignInPage;