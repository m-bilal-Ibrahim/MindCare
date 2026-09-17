// ============================================================
// MindCare — Custom Hook: useHashScroll
// Scrolls to the element matching the current URL hash (e.g. a
// footer link to `/#how-it-works` landing on this page fresh).
// ============================================================

import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

export function useHashScroll(): void {
  const { hash } = useLocation();

  useEffect(() => {
    if (!hash) return;
    const id = hash.slice(1);
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [hash]);
}
