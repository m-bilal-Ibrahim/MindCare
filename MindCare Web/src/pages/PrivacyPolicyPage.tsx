// ============================================================
// MindCare — Privacy Policy Page
// ============================================================

import React from 'react';
import LegalPageLayout from '../components/layout/LegalPageLayout';
import { PRIVACY_SECTIONS, PRIVACY_LAST_UPDATED } from '../constants';

const PrivacyPolicyPage: React.FC = () => (
  <LegalPageLayout
    eyebrow="Legal"
    title="Privacy Policy"
    intro="Your care record is the most sensitive thing you'll ever put in an app. Here's exactly what we collect, why, and who can see it."
    lastUpdated={PRIVACY_LAST_UPDATED}
    sections={PRIVACY_SECTIONS}
  />
);

export default PrivacyPolicyPage;
