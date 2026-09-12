// ============================================================
// MindCare — Password Strength Meter (client-side UX hint only)
// ============================================================

import React from 'react';
import { getPasswordStrength } from '../../utils/validation';

interface PasswordStrengthMeterProps {
  password: string;
}

const PasswordStrengthMeter: React.FC<PasswordStrengthMeterProps> = ({ password }) => {
  const strength = getPasswordStrength(password);
  const segments = [0, 1, 2, 3];

  if (!password) return null;

  return (
    <div className="mt-2" aria-live="polite">
      <div className="flex gap-1.5 mb-1.5">
        {segments.map((i) => (
          <span
            key={i}
            className="h-1.5 flex-1 rounded-full transition-colors"
            style={{ backgroundColor: i <= strength.score ? strength.color : '#e5e7eb' }}
          />
        ))}
      </div>
      <p className="text-xs" style={{ color: strength.color }}>
        {strength.label}
      </p>
    </div>
  );
};

export default PasswordStrengthMeter;