// ============================================================
// MindCare — For NGOs Page ("The line we hand people to.")
// ============================================================

import React, { useState } from 'react';
import Navbar from '../components/layout/Navbar';
import Button from '../components/common/Button';
import Avatar from '../components/common/Avatar';
import { NGO_PARTNERS, NGO_STATS, NGO_COVERAGE_TYPES } from '../constants';
import type { NGORegisterPayload } from '../types';

const initialForm: NGORegisterPayload = {
  organisationName: '',
  coverageType: NGO_COVERAGE_TYPES[0],
  coverage: '',
  contactEmail: '',
  description: '',
};

const ForNGOsPage: React.FC = () => {
  const [form, setForm] = useState<NGORegisterPayload>(initialForm);
  const [submitted, setSubmitted] = useState(false);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.organisationName || !form.contactEmail) return;
    // eslint-disable-next-line no-console
    console.info('[MindCare] NGO partner registration submitted:', form);
    setSubmitted(true);
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
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <input
                    name="organisationName"
                    value={form.organisationName}
                    onChange={handleChange}
                    placeholder="Organisation name"
                    required
                    className="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-gray-50"
                  />
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
                  <input
                    name="coverage"
                    value={form.coverage}
                    onChange={handleChange}
                    placeholder="Coverage (city / national)"
                    className="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-gray-50"
                  />
                  <input
                    name="contactEmail"
                    type="email"
                    value={form.contactEmail}
                    onChange={handleChange}
                    placeholder="Contact email"
                    required
                    className="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-gray-50"
                  />
                </div>

                <textarea
                  name="description"
                  value={form.description}
                  onChange={handleChange}
                  placeholder="In one paragraph: who you serve, and what you offer"
                  rows={4}
                  className="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-gray-50 resize-none"
                />

                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pt-2">
                  <p className="text-xs text-gray-500">
                    We&apos;ll respond within 5 working days · MOU + drill follow.
                  </p>
                  <Button type="submit" variant="primary" size="md" className="shrink-0">
                    Register →
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