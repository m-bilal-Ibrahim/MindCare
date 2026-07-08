// ============================================================
// MindCare — Logo Component
// ============================================================

import React from 'react';
import { Link } from 'react-router-dom';
import { ROUTES } from '../../constants';

interface LogoProps {
  className?: string;
}

const Logo: React.FC<LogoProps> = ({ className = '' }) => (
  <Link
    to={ROUTES.HOME}
    className={`text-xl font-bold tracking-tight text-gray-900 select-none ${className}`}
    aria-label="MindCare Home"
  >
    MindCare
    <span className="text-orange-500">.</span>
  </Link>
);

export default Logo;
