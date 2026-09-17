// ============================================================
// MindCare — Animated Counter (counts up when scrolled into view)
// Parses leading digits/commas from a stat string, animates them,
// and reattaches any prefix/suffix (e.g. "Rs ", "+", "%").
// ============================================================

import React, { useEffect, useRef, useState } from 'react';
import { motion, useInView, animate } from 'framer-motion';

interface AnimatedCounterProps {
  value: string;
  className?: string;
  duration?: number;
}

const AnimatedCounter: React.FC<AnimatedCounterProps> = ({ value, className, duration = 1.4 }) => {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true, amount: 0.6 });
  const [display, setDisplay] = useState(value.replace(/[\d,]/g, (m) => (m === ',' ? ',' : '0')));

  const match = value.match(/[\d,]+/);
  const numeric = match ? Number(match[0].replace(/,/g, '')) : null;
  const prefix = match ? value.slice(0, match.index) : '';
  const suffix = match ? value.slice((match.index ?? 0) + match[0].length) : value;

  useEffect(() => {
    if (!isInView || numeric === null) return;
    const controls = animate(0, numeric, {
      duration,
      ease: [0.22, 1, 0.36, 1],
      onUpdate: (v) => setDisplay(Math.round(v).toLocaleString('en-US')),
    });
    return () => controls.stop();
  }, [isInView, numeric, duration]);

  if (numeric === null) {
    return <span className={className}>{value}</span>;
  }

  return (
    <motion.span ref={ref} className={className}>
      {prefix}
      {display}
      {suffix}
    </motion.span>
  );
};

export default AnimatedCounter;
