// ============================================================
// MindCare — About Us Page ("Built by people who had to look for care.")
// ============================================================

import React from 'react';
import Navbar from '../components/layout/Navbar';
import Footer from '../components/layout/Footer';
import { ABOUT_INTRO, ABOUT_VALUES, ABOUT_TIMELINE } from '../constants';

const AboutUsPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#F5F0E8]">
      <Navbar />

      <main className="pt-16 grid grid-cols-1 lg:grid-cols-2">
        {/* Left — story */}
        <div className="px-4 sm:px-6 lg:px-16 pt-24 pb-24">
          <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-6">About us</p>

          <h1 className="text-4xl sm:text-6xl font-black text-gray-900 leading-[1.05] mb-8">
            Built by people who had to <span className="italic font-serif font-normal">look</span>
            <br />
            for care, and didn&apos;t always <span className="italic font-serif font-normal">find</span> it.
          </h1>

          <p className="text-gray-600 text-lg leading-relaxed max-w-xl mb-12">{ABOUT_INTRO}</p>

          <h2 className="text-xs font-bold tracking-widest text-gray-900 uppercase mb-6">Our path so far</h2>
          <ol className="space-y-6">
            {ABOUT_TIMELINE.map((entry) => (
              <li key={entry.id} className="flex gap-4">
                <span className="flex flex-col items-center pt-1.5 shrink-0">
                  <span
                    className={`w-2.5 h-2.5 rounded-full ${entry.current ? 'bg-orange-500' : 'bg-gray-900'}`}
                    aria-hidden="true"
                  />
                  <span className="w-px flex-1 bg-gray-200 mt-1" aria-hidden="true" />
                </span>
                <div className="pb-1">
                  <p className="text-sm text-gray-500 mb-0.5">{entry.date}</p>
                  <p className="text-gray-900 font-medium">{entry.description}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>

        {/* Right — values + team */}
        <div className="px-4 sm:px-6 lg:px-16 pt-24 pb-24 bg-[#EFE9DF] flex flex-col">
          <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-6">
            Values we&apos;re trying to hold
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-14">
            {ABOUT_VALUES.map((value) => (
              <div key={value.id} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <p className="font-bold text-gray-900 mb-1">{value.title}</p>
                <p className="text-sm text-gray-500 leading-relaxed">{value.description}</p>
              </div>
            ))}
          </div>

          <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-4">The team</p>
          <p className="text-sm text-gray-500 mb-auto">
            Team bios coming soon — we&apos;re a small crew of clinicians, engineers, and designers
            building this together.
          </p>

          <div className="flex flex-wrap gap-3 mt-10">
            <button
              type="button"
              className="bg-gray-900 text-white text-sm font-semibold px-5 py-3 rounded-full hover:bg-gray-800 transition-colors"
            >
              Careers · 4 open
            </button>
            <button
              type="button"
              className="bg-white border border-gray-200 text-gray-900 text-sm font-semibold px-5 py-3 rounded-full hover:border-gray-400 transition-colors"
            >
              Press kit
            </button>
            <button
              type="button"
              className="bg-white border border-gray-200 text-gray-900 text-sm font-semibold px-5 py-3 rounded-full hover:border-gray-400 transition-colors"
            >
              Contact
            </button>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
};

export default AboutUsPage;