// ============================================================
// MindCare — Input Validation & Sanitization Utilities
//
// IMPORTANT: These are FRONTEND UX safeguards only. They catch
// mistakes early and reduce garbage data, but they are NOT a
// security boundary — anyone can bypass client-side JS entirely.
// The backend MUST independently re-validate everything here
// (parameterized queries, server-side length/format checks,
// rate limiting, auth, HTTPS) before trusting any of this data.
// ============================================================

const EMAIL_REGEX = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

// Reasonable max lengths — prevents accidental huge payloads
// and basic denial-of-service-by-textarea abuse.
export const MAX_LENGTHS = {
  shortText: 100, // names, titles
  email: 254, // RFC 5321 limit
  longText: 1000, // paragraphs / descriptions
  password: 128,
} as const;

/**
 * Validates email format. Returns null if valid, or an error message.
 */
export function validateEmail(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return 'Email is required.';
  if (trimmed.length > MAX_LENGTHS.email) return 'Email is too long.';
  if (!EMAIL_REGEX.test(trimmed)) return 'Enter a valid email address.';
  return null;
}

/**
 * Validates a required short text field (names, titles, etc.)
 */
export function validateRequiredText(value: string, label: string, maxLength = MAX_LENGTHS.shortText): string | null {
  const trimmed = value.trim();
  if (!trimmed) return `${label} is required.`;
  if (trimmed.length > maxLength) return `${label} must be under ${maxLength} characters.`;
  return null;
}

/**
 * Strips characters with no legitimate use in plain-text form fields
 * (angle brackets) to reduce accidental markup/script injection surface.
 * NOTE: React already escapes rendered text by default — this is a
 * defence-in-depth measure for data that may later be sent elsewhere
 * (emails, admin dashboards, exports) that might not escape it.
 */
export function sanitizeText(value: string): string {
  return value.replace(/[<>]/g, '').trim();
}

/**
 * Basic password strength check for therapist/clinician accounts.
 * Real enforcement (hashing with bcrypt/argon2, breach-list checks,
 * lockout after failed attempts) happens server-side.
 */
export function validatePassword(value: string): string | null {
  if (!value) return 'Password is required.';
  if (value.length < 8) return 'Password must be at least 8 characters.';
  if (value.length > MAX_LENGTHS.password) return 'Password is too long.';
  if (!/[A-Za-z]/.test(value) || !/[0-9]/.test(value)) {
    return 'Password must include both letters and numbers.';
  }
  return null;
}