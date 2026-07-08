// ============================================================
// MindCare — For NGOs Page ("The line we hand people to.")
// ============================================================

import React, { useState } from 'react';
import Navbar from '../components/layout/Navbar';
import Button from '../components/common/Button';
import Avatar from '../components/common/Avatar';
import { NGO_PARTNERS, NGO_STATS, NGO_COVERAGE_TYPES } from '../constants';
import { validateEmail, validateRequiredText, sanitizeText, MAX_LENGTHS } from '../utils/validation';
import type { NGORegisterPayload } from '../types';

const initialForm: NGORegisterPayload = {
  organisationName: '',
  coverageType: NGO_COVERAGE_TYPES[0],
  coverage: '',
  contactEmail: '',
  description: '',
};

type FormErrors = Partial<Record<keyof NGORegisterPayload, string>>;

const ForNGOsPage: React.FC = () => {
  const [form, setForm] = useState<NGORegisterPayload>(initialForm);
  const [errors, setErrors] = useState<FormErrors>({});
  const [honeypot, setHoneypot] = useState(''); // hidden field — real users never fill this in
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    if (errors[name as keyof NGORegisterPayload]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const validate = (): FormErrors => {
    const next: FormErrors = {};
    const nameError = validateRequiredText(form.organisationName, 'Organisation name');
    if (nameError) next.organisationName = nameError;

    const emailError = validateEmail(form.contactEmail);
    if (emailError) next.contactEmail = emailError;

    if (form.description.length > MAX_LENGTHS.longText) {
      next.description = `Description must be under ${MAX_LENGTHS.longText} characters.`;
    }
    if (form.coverage.length > MAX_LENGTHS.shortText) {
      next.coverage = `Coverage must be under ${MAX_LENGTHS.shortText} characters.`;
    }

    return next;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Honeypot check: bots fill every field, including hidden ones.
    // A real user will never type into this invisible field.
    if (honeypot) {
      // Silently pretend success — don't tip off the bot that it was caught.
      setSubmitted(true);
      return;
    }

    const validationErrors = validate();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setSubmitting(true);
    try {
      const payload: NGORegisterPayload = {
        organisationName: sanitizeText(form.organisationName),
        coverageType: form.coverageType,
        coverage: sanitizeText(form.coverage),
        contactEmail: form.contactEmail.trim().toLowerCase(),
        description: sanitizeText(form.description),
      };

      // TODO: replace with real API call once backend endpoint exists.
      // The backend MUST independently re-validate + sanitize this payload —
      // never trust that data arriving here has already been cleaned.
      // eslint-disable-next-line no-console
      console.info('[MindCare] NGO partner registration submitted:', payload);

      setSubmitted(true);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F0E8]">
      <Navbar />

      <main className="pt-16 grid grid-cols-1 lg:grid-cols-2">
        {/* Left — pitch + register form */}
        <div className="px-4 sm:px-6 lg:px-16 pt-16 pb-24">
          <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-6">
            For NGO Partners
          </p>

          <h1 className="text-4xl sm:text-6xl font-black text-gray-900 leading-[1.05] mb-8">
            The line we hand people <span className="italic font-serif font-normal">to.</span>
          </h1>

          <p className="text-gray-600 text-lg leading-relaxed max-w-xl mb-10">
            When MindCare can&apos;t be enough — late-night crises, sliding-scale care, hospital
            escalation — we route to verified NGO partners. No dashboard, no app to learn. Just a
            call, a handover, a closed loop.
          </p>

          <div className="flex flex-wrap gap-x-12 gap-y-6 mb-12">
            {NGO_STATS.map((stat) => (
              <div key={stat.label}>
                <p className="text-3xl font-black text-gray-900">{stat.value}</p>
                <p className="text-sm text-gray-500">{stat.label}</p>
              </div>
            ))}
          </div>

          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 max-w-xl">
            <h2 className="text-xs font-bold tracking-widest text-gray-900 uppercase mb-5">
              Register as a partner
            </h2>

            {submitted ? (
              <div className="py-6 text-center">
                <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-4">
                  <span className="text-xl">✓</span>
                </div>
                <p className="text-gray-900 font-semibold mb-1">Thanks — request received.</p>
                <p className="text-sm text-gray-500">We&apos;ll respond within 5 working days.</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4" noValidate>
                {/* Honeypot field — invisible to real users, catches simple bots.
                    tabIndex=-1 + aria-hidden keep it out of keyboard/screen-reader flow. */}
                <input
                  type="text"
                  name="website"
                  value={honeypot}
                  onChange={(e) => setHoneypot(e.target.value)}
                  tabIndex={-1}
                  autoComplete="off"
                  aria-hidden="true"
                  className="absolute -left-[9999px] w-px h-px opacity-0"
                />

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <input
                      name="organisationName"
                      value={form.organisationName}
                      onChange={handleChange}
                      placeholder="Organisation name"
                      required
                      maxLength={MAX_LENGTHS.shortText}
                      aria-invalid={!!errors.organisationName}
                      aria-describedby={errors.organisationName ? 'org-name-error' : undefined}
                      className={`w-full px-4 py-3 text-sm border rounded-xl focus:outline-none focus:ring-2 bg-gray-50 ${
                        errors.organisationName
                          ? 'border-red-300 focus:ring-red-500'
                          : 'border-gray-200 focus:ring-gray-900'
                      }`}
                    />
                    {errors.organisationName && (
                      <p id="org-name-error" role="alert" className="text-xs text-red-600 mt-1">
                        {errors.organisationName}
                      </p>
                    )}
                  </div>
                  <select
                    name="coverageType"
                    value={form.coverageType}
                    onChange={handleChange}
                    className="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-gray-50"
                  >
                    {NGO_COVERAGE_TYPES.map((type) => (
                      <option key={type} value={type}>
                        {type}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <input
                      name="coverage"
                      value={form.coverage}
                      onChange={handleChange}
                      placeholder="Coverage (city / national)"
                      maxLength={MAX_LENGTHS.shortText}
                      aria-invalid={!!errors.coverage}
                      className={`w-full px-4 py-3 text-sm border rounded-xl focus:outline-none focus:ring-2 bg-gray-50 ${
                        errors.coverage ? 'border-red-300 focus:ring-red-500' : 'border-gray-200 focus:ring-gray-900'
                      }`}
                    />
                    {errors.coverage && (
                      <p role="alert" className="text-xs text-red-600 mt-1">
                        {errors.coverage}
                      </p>
                    )}
                  </div>
                  <div>
                    <input
                      name="contactEmail"
                      type="email"
                      value={form.contactEmail}
                      onChange={handleChange}
                      placeholder="Contact email"
                      required
                      maxLength={MAX_LENGTHS.email}
                      autoComplete="email"
                      inputMode="email"
                      aria-invalid={!!errors.contactEmail}
                      aria-describedby={errors.contactEmail ? 'contact-email-error' : undefined}
                      className={`w-full px-4 py-3 text-sm border rounded-xl focus:outline-none focus:ring-2 bg-gray-50 ${
                        errors.contactEmail
                          ? 'border-red-300 focus:ring-red-500'
                          : 'border-gray-200 focus:ring-gray-900'
                      }`}
                    />
                    {errors.contactEmail && (
                      <p id="contact-email-error" role="alert" className="text-xs text-red-600 mt-1">
                        {errors.contactEmail}
                      </p>
                    )}
                  </div>
                </div>

                <div>
                  <textarea
                    name="description"
                    value={form.description}
                    onChange={handleChange}
                    placeholder="In one paragraph: who you serve, and what you offer"
                    rows={4}
                    maxLength={MAX_LENGTHS.longText}
                    aria-invalid={!!errors.description}
                    className={`w-full px-4 py-3 text-sm border rounded-xl focus:outline-none focus:ring-2 bg-gray-50 resize-none ${
                      errors.description ? 'border-red-300 focus:ring-red-500' : 'border-gray-200 focus:ring-gray-900'
                    }`}
                  />
                  {errors.description && (
                    <p role="alert" className="text-xs text-red-600 mt-1">
                      {errors.description}
                    </p>
                  )}
                </div>

                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pt-2">
                  <p className="text-xs text-gray-500">
                    We&apos;ll respond within 5 working days · MOU + drill follow.
                  </p>
                  <Button type="submit" variant="primary" size="md" className="shrink-0" disabled={submitting}>
                    {submitting ? 'Submitting…' : 'Register →'}
                  </Button>
                </div>
              </form>
            )}
          </div>
        </div>

        {/* Right — current partners (dark panel) */}
        <div className="bg-gray-900 px-4 sm:px-6 lg:px-16 pt-16 pb-24 min-h-[600px]">
          <p className="text-xs font-semibold tracking-widest text-orange-400 uppercase mb-8">
            Current Partners
          </p>

          <div className="space-y-4">
            {NGO_PARTNERS.map((partner) => (
              <div
                key={partner.id}
                className="bg-gray-800/60 border border-gray-700/60 rounded-2xl p-5 flex items-center justify-between"
              >
                <div className="flex items-center gap-4">
                  <Avatar initials={partner.initials} color={partner.color} size="lg" />
                  <div>
                    <p className="text-white font-bold">{partner.name}</p>
                    <p className="text-sm text-gray-400">{partner.description}</p>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-white font-bold">{partner.routedCount.toLocaleString()}</p>
                  <p className="text-xs text-gray-500">routed</p>
                </div>
              </div>
            ))}
          </div>

          <p className="text-sm text-gray-400 leading-relaxed mt-10">
            Partners receive a closed-loop case report after every routed handoff. No PII unless
            you&apos;ve been added to the case lead.
          </p>
        </div>
      </main>
    </div>
  );
};

export default ForNGOsPage;