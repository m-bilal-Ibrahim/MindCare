// ============================================================
// MindCare — Cookie Policy Page
// ============================================================

import React from 'react';
import LegalPageLayout from '../components/layout/LegalPageLayout';
import { COOKIE_SECTIONS, COOKIE_LAST_UPDATED } from '../constants';

const CookiePolicyPage: React.FC = () => (
  <LegalPageLayout
    eyebrow="Legal"
    title="Cookie Policy"
    intro="Short version: a few cookies to keep you signed in, none to track you around the web. No predatory ads is a promise we keep in our code, not just our marketing."
    lastUpdated={COOKIE_LAST_UPDATED}
    sections={COOKIE_SECTIONS}
  />
);

export default CookiePolicyPage;
