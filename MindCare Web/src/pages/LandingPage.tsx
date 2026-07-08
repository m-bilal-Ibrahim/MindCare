// ============================================================
// MindCare — Screen 1: Landing Page
// ============================================================

import React from 'react';
import Navbar from '../components/layout/Navbar';
import Footer from '../components/layout/Footer';
import HeroSection from '../components/sections/HeroSection';
import PartnersSection from '../components/sections/PartnersSection';
import HowItWorksSection from '../components/sections/HowItWorksSection';
import VisionMissionSection from '../components/sections/VisionMissionSection';
import FeaturesSection from '../components/sections/FeaturesSection';

const LandingPage: React.FC = () => (
  <>
    <Navbar />
    <main id="main-content">
      <HeroSection />
      <PartnersSection />
      <HowItWorksSection />
      <VisionMissionSection />
      <FeaturesSection />
    </main>
    <Footer />
  </>
);

export default LandingPage;
