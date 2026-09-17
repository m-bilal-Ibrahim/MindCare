// ============================================================
// MindCare — Terms of Service Page
// ============================================================

import React from 'react';
import LegalPageLayout from '../components/layout/LegalPageLayout';
import { TERMS_SECTIONS, TERMS_LAST_UPDATED } from '../constants';

const TermsOfServicePage: React.FC = () => (
  <LegalPageLayout
    eyebrow="Legal"
    title="Terms of Service"
    intro="The plain-language version of what you're agreeing to when you use MindCare — as a client, a therapist, or an NGO partner."
    lastUpdated={TERMS_LAST_UPDATED}
    sections={TERMS_SECTIONS}
  />
);

export default TermsOfServicePage;
