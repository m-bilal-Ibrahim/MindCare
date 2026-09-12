// ============================================================
// MindCare — Custom Hook: useScrollPosition
// Tracks window scroll for sticky navbar shadow / bg change
// ============================================================

import { useState, useEffect } from 'react';

export function useScrollPosition(): number {
  const [scrollY, setScrollY] = useState<number>(0);

  useEffect(() => {
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return scrollY;
}
