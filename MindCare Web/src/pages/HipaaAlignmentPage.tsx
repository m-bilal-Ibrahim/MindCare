// ============================================================
// MindCare — HIPAA Alignment Page
// ============================================================

import React from 'react';
import LegalPageLayout from '../components/layout/LegalPageLayout';
import { HIPAA_SECTIONS, HIPAA_LAST_UPDATED } from '../constants';

const HipaaAlignmentPage: React.FC = () => (
  <LegalPageLayout
    eyebrow="Legal · Security"
    title="HIPAA Alignment"
    intro="MindCare operates in Pakistan, outside HIPAA's jurisdiction — but mental health records deserve US-grade safeguards no matter where they're held. Here's what we hold ourselves to, and why."
    lastUpdated={HIPAA_LAST_UPDATED}
    sections={HIPAA_SECTIONS}
  />
);

export default HipaaAlignmentPage;
