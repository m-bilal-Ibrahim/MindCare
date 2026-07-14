// ============================================================
// MindCare — Clinician Application Page
// (After selecting "I'm here to practice")
// ============================================================

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Check, Shield, Clock, CreditCard } from 'lucide-react';
import Logo from '../components/common/Logo';
import Button from '../components/common/Button';
import { ROUTES } from '../constants';
import { signUp } from '../services/api.service';
import { validateRequiredText, validatePmdcLicense, validateEmail, sanitizeText, MAX_LENGTHS } from '../utils/validation';

// ——— Dummy form state type ———
interface ClinicianForm {
  name: string;
  email: string;
  pmdc: string;
  specialty: string;
  city: string;
}

const SPECIALTIES = [
  'Anxiety & Stress',
  'Depression',
  'Trauma & PTSD',
  'Addiction',
  'Grief & Loss',
  'Relationships',
  'Child & Adolescent',
  'Other',
];

const CITIES = ['Karachi', 'Lahore', 'Islamabad', 'Rawalpindi', 'Faisalabad', 'Other'];

const perks = [
  { icon: <Shield size={16} />, text: 'PMDC-verified badge on your profile' },
  { icon: <Clock size={16} />, text: 'You set your schedule and session pace' },
  { icon: <CreditCard size={16} />, text: 'Fast, transparent payouts fortnightly' },
];

const ClinicianPage: React.FC = () => {
  const [form, setForm] = useState<ClinicianForm>({
    name: '',
    email: '',
    pmdc: '',
    specialty: '',
    city: '',
  });
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof ClinicianForm, string>>>({});

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    if (fieldErrors[name as keyof ClinicianForm]) {
      setFieldErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const validateForm = (): boolean => {
    const errors: Partial<Record<keyof ClinicianForm, string>> = {};

    const nameError = validateRequiredText(form.name, 'Full name');
    if (nameError) errors.name = nameError;

    const emailError = validateEmail(form.email);
    if (emailError) errors.email = emailError;

    const pmdcError = validatePmdcLicense(form.pmdc);
    if (pmdcError) errors.pmdc = pmdcError;

    if (!form.specialty) errors.specialty = 'Please select a specialty.';
    if (!form.city) errors.city = 'Please select a city.';

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validateForm()) {
      setError('Please fix the highlighted fields below.');
      return;
    }

    setLoading(true);

    const cleanForm: ClinicianForm = {
      name: sanitizeText(form.name),
      email: form.email.trim().toLowerCase(),
      pmdc: sanitizeText(form.pmdc),
      specialty: form.specialty,
      city: form.city,
    };

    // Dummy call — replace with real API
    const result = await signUp({
      name: cleanForm.name,
      email: cleanForm.email,
      password: 'temp-set-on-backend',
      role: 'clinician',
    });

    setLoading(false);

    if (result.error) {
      setError('Application failed. Please try again.');
    } else {
      setSubmitted(true);
      console.info('[MindCare] Clinician application submitted', cleanForm);
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F0E8] flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-6 sm:px-10 py-5 border-b border-gray-200/60">
        <Logo />
        <Link
          to={ROUTES.ONBOARDING}
          className="text-sm text-gray-500 hover:text-gray-900 transition-colors"
        >
          ← Choose again
        </Link>
      </header>

      <main className="flex-1 grid md:grid-cols-2">
        {/* Left: Info */}
        <div className="bg-gray-900 text-white px-8 sm:px-14 py-16 flex flex-col justify-center">
          <p className="text-[10px] font-black tracking-[0.25em] text-orange-400 uppercase mb-6">
            Step 2 · Clinician · Apply
          </p>
          <h1 className="text-4xl sm:text-5xl font-black text-white leading-tight mb-6">
            Join MindCare
            <br />
            <em style={{ fontFamily: "'Playfair Display', serif" }}>as a clinician.</em>
          </h1>
          <p className="text-gray-400 text-base leading-relaxed mb-10 max-w-sm">
            Run your practice your way — we handle the scheduling, billing, and
            between-session support. You stay in charge of clinical decisions.
          </p>

          {/* Perks */}
          <ul className="space-y-4 mb-10" role="list">
            {perks.map(({ icon, text }) => (
              <li key={text} className="flex items-center gap-3 text-sm text-gray-300">
                <span className="text-orange-400">{icon}</span>
                {text}
              </li>
            ))}
          </ul>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-4 border-t border-gray-800 pt-8">
            {[
              { v: '184', l: 'Active therapists' },
              { v: '50 min', l: 'Session length' },
              { v: '48 hrs', l: 'First match' },
            ].map(({ v, l }) => (
              <div key={l}>
                <p className="text-xl font-black text-white">{v}</p>
                <p className="text-xs text-gray-500 mt-1">{l}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Application form */}
        <div className="px-8 sm:px-14 py-16 flex flex-col justify-center">
          {submitted ? (
            <div className="flex flex-col items-center text-center">
              <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center mb-6">
                <Check size={28} className="text-emerald-600" />
              </div>
              <h2 className="text-2xl font-black text-gray-900 mb-3">Application received!</h2>
              <p className="text-gray-500 text-sm max-w-xs mb-8">
                We'll review your PMDC credentials and get back to you within 48 hours.
              </p>
              <Link to={ROUTES.HOME}>
                <Button variant="primary" size="md">
                  Back to home
                </Button>
              </Link>
            </div>
          ) : (
            <>
              <h2 className="text-2xl font-black text-gray-900 mb-2">Apply in 10 minutes</h2>
              <p className="text-sm text-gray-500 mb-8">
                Fill in your details. We verify your PMDC licence before your first patient.
              </p>

              <form onSubmit={handleSubmit} className="space-y-5" noValidate>
                {/* Full name */}
                <div>
                  <label htmlFor="name" className="block text-xs font-semibold text-gray-700 mb-1.5">
                    Full name <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="name"
                    name="name"
                    type="text"
                    required
                    autoComplete="name"
                    maxLength={MAX_LENGTHS.shortText}
                    value={form.name}
                    onChange={handleChange}
                    placeholder="Dr. Ayesha Khan"
                    aria-invalid={!!fieldErrors.name}
                    className={`w-full px-4 py-3 text-sm border rounded-xl focus:outline-none focus:ring-2 bg-white ${
                      fieldErrors.name ? 'border-red-300 focus:ring-red-500' : 'border-gray-200 focus:ring-gray-900'
                    }`}
                  />
                  {fieldErrors.name && (
                    <p role="alert" className="text-xs text-red-600 mt-1.5">
                      {fieldErrors.name}
                    </p>
                  )}
                </div>

                {/* Email */}
                <div>
                  <label htmlFor="email" className="block text-xs font-semibold text-gray-700 mb-1.5">
                    Work email <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    autoComplete="email"
                    maxLength={MAX_LENGTHS.email}
                    value={form.email}
                    onChange={handleChange}
                    placeholder="ayesha@clinic.pk"
                    aria-invalid={!!fieldErrors.email}
                    className={`w-full px-4 py-3 text-sm border rounded-xl focus:outline-none focus:ring-2 bg-white ${
                      fieldErrors.email ? 'border-red-300 focus:ring-red-500' : 'border-gray-200 focus:ring-gray-900'
                    }`}
                  />
                  {fieldErrors.email && (
                    <p role="alert" className="text-xs text-red-600 mt-1.5">
                      {fieldErrors.email}
                    </p>
                  )}
                </div>

                {/* PMDC number */}
                <div>
                  <label htmlFor="pmdc" className="block text-xs font-semibold text-gray-700 mb-1.5">
                    PMDC registration number <span className="text-red-500">*</span>
                  </label>
                  <input
                    id="pmdc"
                    name="pmdc"
                    type="text"
                    required
                    maxLength={MAX_LENGTHS.shortText}
                    value={form.pmdc}
                    onChange={handleChange}
                    placeholder="PMDC-12345-P"
                    aria-invalid={!!fieldErrors.pmdc}
                    className={`w-full px-4 py-3 text-sm border rounded-xl focus:outline-none focus:ring-2 bg-white ${
                      fieldErrors.pmdc ? 'border-red-300 focus:ring-red-500' : 'border-gray-200 focus:ring-gray-900'
                    }`}
                  />
                  {fieldErrors.pmdc && (
                    <p role="alert" className="text-xs text-red-600 mt-1.5">
                      {fieldErrors.pmdc}
                    </p>
                  )}
                </div>

                {/* Specialty */}
                <div>
                  <label htmlFor="specialty" className="block text-xs font-semibold text-gray-700 mb-1.5">
                    Primary specialty <span className="text-red-500">*</span>
                  </label>
                  <select
                    id="specialty"
                    name="specialty"
                    required
                    value={form.specialty}
                    onChange={handleChange}
                    aria-invalid={!!fieldErrors.specialty}
                    className={`w-full px-4 py-3 text-sm border rounded-xl focus:outline-none focus:ring-2 bg-white ${
                      fieldErrors.specialty ? 'border-red-300 focus:ring-red-500' : 'border-gray-200 focus:ring-gray-900'
                    }`}
                  >
                    <option value="">Select specialty</option>
                    {SPECIALTIES.map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                  {fieldErrors.specialty && (
                    <p role="alert" className="text-xs text-red-600 mt-1.5">
                      {fieldErrors.specialty}
                    </p>
                  )}
                </div>

                {/* City */}
                <div>
                  <label htmlFor="city" className="block text-xs font-semibold text-gray-700 mb-1.5">
                    City <span className="text-red-500">*</span>
                  </label>
                  <select
                    id="city"
                    name="city"
                    required
                    value={form.city}
                    onChange={handleChange}
                    aria-invalid={!!fieldErrors.city}
                    className={`w-full px-4 py-3 text-sm border rounded-xl focus:outline-none focus:ring-2 bg-white ${
                      fieldErrors.city ? 'border-red-300 focus:ring-red-500' : 'border-gray-200 focus:ring-gray-900'
                    }`}
                  >
                    <option value="">Select city</option>
                    {CITIES.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                  {fieldErrors.city && (
                    <p role="alert" className="text-xs text-red-600 mt-1.5">
                      {fieldErrors.city}
                    </p>
                  )}
                </div>

                {error && (
                  <p className="text-sm text-red-500 bg-red-50 px-4 py-3 rounded-xl" role="alert">
                    {error}
                  </p>
                )}

                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  fullWidth
                  loading={loading}
                  disabled={!form.name || !form.email || !form.pmdc || !form.specialty || !form.city}
                >
                  Submit application →
                </Button>

                <p className="text-xs text-center text-gray-400 mt-2">
                  By applying you agree to our{' '}
                  <a href="#" className="underline hover:text-gray-700">Terms</a> and{' '}
                  <a href="#" className="underline hover:text-gray-700">Privacy Policy</a>.
                </p>
              </form>
            </>
          )}
        </div>
      </main>
    </div>
  );
};

export default ClinicianPage;