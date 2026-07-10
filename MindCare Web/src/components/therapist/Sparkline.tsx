// ============================================================
// MindCare — Sparkline (mini trend chart)
// ============================================================

import React from 'react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';

interface SparklineProps {
  data: number[];
  color?: string;
  height?: number;
  fillOpacity?: number;
}

const Sparkline: React.FC<SparklineProps> = ({ data, color = '#1a1a1a', height = 32 }) => {
  const points = data.map((value, i) => ({ i, value }));

  return (
    <div style={{ width: 90, height }} aria-hidden="true">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points} margin={{ top: 2, right: 2, bottom: 2, left: 2 }}>
          <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2} dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default Sparkline;