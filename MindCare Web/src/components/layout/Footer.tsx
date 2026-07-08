// ============================================================
// MindCare — Footer Component
// ============================================================

import React from 'react';
import { Link } from 'react-router-dom';
import Logo from '../common/Logo';

const Footer: React.FC = () => (
  <footer className="bg-gray-900 text-gray-400 pt-16 pb-10" role="contentinfo">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-10 mb-12">
        {/* Brand */}
        <div className="md:col-span-1">
          <Logo className="text-white" />
          <p className="mt-4 text-sm leading-relaxed">
            Weekly therapy, AI co-pilot, and the days between — all in one place.
          </p>
          <p className="mt-4 text-xs text-gray-600">© {new Date().getFullYear()} MindCare. All rights reserved.</p>
        </div>

        {/* Platform */}
        <div>
          <h3 className="text-white text-sm font-semibold mb-4 uppercase tracking-widest">Platform</h3>
          <ul className="space-y-2 text-sm">
            {['How it works', 'For therapists', 'For NGOs', 'Pricing', 'Stories'].map((l) => (
              <li key={l}>
                <a href="#" className="hover:text-white transition-colors">{l}</a>
              </li>
            ))}
          </ul>
        </div>

        {/* Company */}
        <div>
          <h3 className="text-white text-sm font-semibold mb-4 uppercase tracking-widest">Company</h3>
          <ul className="space-y-2 text-sm">
            {['About us', 'Careers', 'Press', 'Help'].map((l) => (
              <li key={l}>
                <a href="#" className="hover:text-white transition-colors">{l}</a>
              </li>
            ))}
          </ul>
        </div>

        {/* Legal */}
        <div>
          <h3 className="text-white text-sm font-semibold mb-4 uppercase tracking-widest">Legal</h3>
          <ul className="space-y-2 text-sm">
            {['Privacy Policy', 'Terms of Service', 'HIPAA Alignment', 'Cookie Policy'].map((l) => (
              <li key={l}>
                <a href="#" className="hover:text-white transition-colors">{l}</a>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-gray-800 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-gray-600">
        <p>PMDC-verified therapists · Umang · Rozan partner · HIPAA-aligned</p>
        <div className="flex gap-4">
          <Link to="/sign-in" className="hover:text-gray-400 transition-colors">Sign in</Link>
          <Link to="/get-started" className="hover:text-gray-400 transition-colors">Get started</Link>
        </div>
      </div>
    </div>
  </footer>
);

export default Footer;
