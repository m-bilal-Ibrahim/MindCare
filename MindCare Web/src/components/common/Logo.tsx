// ============================================================
// MindCare — Logo Component
// ============================================================

import React from 'react';
import { Link } from 'react-router-dom';
import { ROUTES } from '../../constants';
import logoMark from '../../assets/logo-mark.png';

interface LogoProps {
  className?: string;
}

const Logo: React.FC<LogoProps> = ({ className = '' }) => (
  <Link
    to={ROUTES.HOME}
    className={`flex items-center gap-2 select-none ${className}`}
    aria-label="MindCare Home"
  >
    <img
      src={logoMark}
      alt=""
      aria-hidden="true"
      className="h-9 w-9 sm:h-10 sm:w-10 object-contain shrink-0"
    />
    <span
      className="text-xl font-bold tracking-tight bg-gradient-to-r from-[#2f5b63] to-[#f97316] bg-clip-text text-transparent"
    >
      MindCare
    </span>
  </Link>
);

export default Logo;
