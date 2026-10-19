// ============================================================
// MindCare — Change password (admins and psychologists)
// POST /accounts/password/change/. Also the forced "Choose a new
// password" screen for an admin a super-admin just created: until
// they change the temporary password, the console guards send them
// here and every admin endpoint answers 403.
// On success the backend signs out every other session and returns a
// new token pair for this one.
// ============================================================

import React, { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { ArrowRight, Eye, EyeOff, KeyRound } from 'lucide-react';
import Logo from '../components/common/Logo';
import Button from '../components/common/Button';
import { ROUTES } from '../constants';
import { changePassword, flattenFieldErrors } from '../services/api.service';
import { useAuth, homeForRole } from '../utils/auth';
import { MAX_LENGTHS } from '../utils/validation';

// The backend's (Django) rules that can be checked while typing; "too common" and
// "too similar to your email / name" are checked only by the backend.
const MIN_LENGTH = 8;
const lengthError = (v: string) =>
  v.length < MIN_LENGTH ? `This password is too short. It must contain at least ${MIN_LENGTH} characters.` : null;
const numericError = (v: string) => (/^\d+$/.test(v) ? 'This password is entirely numeric.' : null);

type Field = 'current_password' | 'new_password' | 'confirm';

const inputClass = (error?: string) =>
  `w-full px-4 py-3.5 pr-12 text-sm border rounded-xl focus:outline-none focus:ring-2 bg-white ${
    error ? 'border-red-300 focus:ring-red-500' : 'border-gray-200 focus:ring-gray-900'
  }`;

const PasswordInput: React.FC<{
  id: Field;
  label: string;
  value: string;
  onChange: (v: string) => void;
  autoComplete: string;
  error?: string;
  hint?: React.ReactNode;
}> = ({ id, label, value, onChange, autoComplete, error, hint }) => {
  const [show, setShow] = useState(false);
  return (
    <div>
      <label htmlFor={id} className="block text-xs font-semibold text-gray-700 mb-1.5">
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          type={show ? 'text' : 'password'}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          autoComplete={autoComplete}
          maxLength={MAX_LENGTHS.password}
          aria-invalid={!!error}
          aria-describedby={error || hint ? `${id}-note` : undefined}
          className={inputClass(error)}
        />
        <button
          type="button"
          onClick={() => setShow((v) => !v)}
          className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700"
          aria-label={show ? 'Hide password' : 'Show password'}
        >
          {show ? <EyeOff size={16} /> : <Eye size={16} />}
        </button>
      </div>
      {error ? (
        <p id={`${id}-note`} role="alert" className="text-xs text-red-600 mt-1.5">
          {error}
        </p>
      ) : hint ? (
        <div id={`${id}-note`} className="mt-1.5">
          {hint}
        </div>
      ) : null}
    </div>
  );
};

const Check: React.FC<{ ok: boolean; children: React.ReactNode }> = ({ ok, children }) => (
  <p className={`text-xs ${ok ? 'text-emerald-700' : 'text-gray-500'}`}>
    {ok ? '✓' : '•'} {children}
  </p>
);

const ChangePasswordPage: React.FC = () => {
  const { session, passwordChanged, signOut } = useAuth();
  const navigate = useNavigate();
  const [values, setValues] = useState<Record<Field, string>>({ current_password: '', new_password: '', confirm: '' });
  const [errors, setErrors] = useState<Partial<Record<Field | '_', string>>>({});
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  if (!session) return <Navigate to={ROUTES.HOME} replace />;
  const forced = session.mustChangePassword;
  const home = homeForRole(session.role);

  const set = (field: Field) => (v: string) => {
    setValues((prev) => ({ ...prev, [field]: v }));
    if (errors[field]) setErrors((prev) => ({ ...prev, [field]: undefined }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const found: Partial<Record<Field, string>> = {};
    if (!values.current_password) found.current_password = forced ? 'Enter your temporary password.' : 'Enter your current password.';
    const np = values.new_password;
    const npError = !np ? 'Enter a new password.' : lengthError(np) ?? numericError(np);
    if (npError) found.new_password = npError;
    else if (np === values.current_password) found.new_password = 'Choose a password different from your current one.';
    if (!found.new_password && values.confirm !== np) found.confirm = 'The passwords don’t match.';
    setErrors(found);
    if (Object.keys(found).length) return;

    setLoading(true);
    const res = await changePassword(values.current_password, np);
    setLoading(false);
    if (res.data) {
      passwordChanged(res.data.access, res.data.refresh);
      setDone(true);
      return;
    }
    if (res.status === 400 && res.errorBody) {
      const fe = flattenFieldErrors(res.errorBody);
      setErrors({
        current_password: fe.current_password,
        new_password: fe.new_password,
        _: fe._ ?? (fe.current_password || fe.new_password ? undefined : res.error ?? undefined),
      });
      return;
    }
    setErrors({ _: res.error ?? 'Couldn’t change your password. Please try again.' });
  };

  const np = values.new_password;

  return (
    <div className="min-h-screen bg-[#F5F0E8] flex flex-col items-center justify-center px-4 py-16">
      <div className="w-full max-w-md">
        <div className="flex items-center justify-between mb-10">
          <Logo />
          {!forced && !done && (
            <Link to={home} className="text-sm text-gray-500 hover:text-gray-900 transition-colors">
              ← Back
            </Link>
          )}
        </div>

        <div className="bg-white rounded-3xl shadow-sm border border-gray-100 px-8 py-8">
          <div className="flex items-center gap-2 mb-2">
            <KeyRound size={16} className="text-gray-400" aria-hidden="true" />
            <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase">
              {forced ? 'Temporary password' : 'Account · Password'}
            </p>
          </div>

          {done ? (
            <>
              <h1 className="text-3xl font-black text-gray-900 mb-2">Password changed.</h1>
              <p className="text-sm text-gray-500 mb-8">
                You’re still signed in here. Any other device you were signed in on has been signed out.
              </p>
              <Button type="button" variant="primary" size="lg" fullWidth onClick={() => navigate(home, { replace: true })}>
                Continue <ArrowRight size={16} aria-hidden="true" />
              </Button>
            </>
          ) : (
            <>
              <h1 className="text-3xl font-black text-gray-900 mb-2">{forced ? 'Choose a new password.' : 'Change password.'}</h1>
              <p className="text-sm text-gray-500 mb-8">
                {forced
                  ? 'You signed in with a temporary password. Choose your own to continue.'
                  : 'Other devices you’re signed in on will be signed out.'}
              </p>

              <form onSubmit={handleSubmit} className="space-y-5" noValidate>
                <PasswordInput
                  id="current_password"
                  label={forced ? 'Temporary password' : 'Current password'}
                  value={values.current_password}
                  onChange={set('current_password')}
                  autoComplete="current-password"
                  error={errors.current_password}
                />
                <PasswordInput
                  id="new_password"
                  label="New password"
                  value={np}
                  onChange={set('new_password')}
                  autoComplete="new-password"
                  error={errors.new_password}
                  hint={
                    <div className="space-y-0.5">
                      <Check ok={np.length >= MIN_LENGTH}>At least {MIN_LENGTH} characters</Check>
                      <Check ok={np.length > 0 && !/^\d+$/.test(np)}>Not only numbers</Check>
                    </div>
                  }
                />
                <PasswordInput
                  id="confirm"
                  label="Confirm new password"
                  value={values.confirm}
                  onChange={set('confirm')}
                  autoComplete="new-password"
                  error={errors.confirm}
                />

                {errors._ && (
                  <p role="alert" className="text-sm text-red-600 bg-red-50 border border-red-100 px-4 py-3 rounded-xl">
                    {errors._}
                  </p>
                )}

                <Button type="submit" variant="primary" size="lg" fullWidth loading={loading}>
                  {forced ? 'Save and continue' : 'Change password'} <ArrowRight size={16} aria-hidden="true" />
                </Button>

                {forced && (
                  <p className="text-center text-sm">
                    <button
                      type="button"
                      onClick={() => {
                        signOut();
                        navigate(ROUTES.HOME, { replace: true });
                      }}
                      className="text-gray-500 hover:text-gray-900 underline"
                    >
                      Sign out
                    </button>
                  </p>
                )}
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChangePasswordPage;
