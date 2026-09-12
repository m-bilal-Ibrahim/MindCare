// ============================================================
// MindCare — Root Application Component
// ============================================================

import React from 'react';
import { MotionConfig } from 'framer-motion';
import AppRouter from './router';

const App: React.FC = () => (
  <MotionConfig reducedMotion="user">
    <AppRouter />
  </MotionConfig>
);

export default App;
