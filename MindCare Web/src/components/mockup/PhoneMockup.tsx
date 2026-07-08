// ============================================================
// MindCare — Phone Mockup Component (Screen 3 visual)
// Renders a realistic phone frame with app UI inside
// ============================================================

import React from 'react';
import { DUMMY_MOOD_DATA } from '../../constants';

// ——— Tiny sparkline inside mockup ———
const MiniSparkline: React.FC = () => {
  const max = 7;
  const pts = DUMMY_MOOD_DATA.map((d, i) => {
    const x = (i / (DUMMY_MOOD_DATA.length - 1)) * 160;
    const y = 30 - (d.value / max) * 26;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg viewBox="0 0 160 34" className="w-full h-8" aria-hidden="true">
      <polyline
        points={pts}
        fill="none"
        stroke="#10B981"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

const PhoneMockup: React.FC = () => (
  <div
    className="relative mx-auto"
    style={{ width: 320, maxWidth: '100%' }}
    aria-label="MindCare mobile app mockup"
  >
    {/* Phone outer shell */}
    <div
      className="relative rounded-[44px] bg-gray-900 shadow-[0_40px_100px_rgba(0,0,0,0.35)]"
      style={{ padding: '12px' }}
    >
      {/* Status bar */}
      <div className="flex items-center justify-between px-5 pt-2 pb-1">
        <span className="text-white text-xs font-semibold">9:41</span>
        {/* Dynamic island */}
        <div className="w-24 h-5 bg-black rounded-full" />
        <div className="flex gap-1 items-center">
          <div className="w-1 h-1 bg-white rounded-full opacity-70" />
          <div className="w-1 h-1 bg-white rounded-full opacity-70" />
          <div className="w-1 h-1 bg-white rounded-full opacity-70" />
        </div>
      </div>

      {/* App screen */}
      <div
        className="rounded-[34px] overflow-hidden bg-[#F5F0E8]"
        style={{ minHeight: 560 }}
      >
        {/* App content */}
        <div className="px-5 pt-5 pb-4">
          {/* Date */}
          <p className="text-[10px] font-semibold text-gray-500 tracking-widest uppercase">
            Wednesday · May 27
          </p>
          <h3 className="text-xl font-black text-gray-900 mt-1 mb-0.5">
            Good morning,
          </h3>
          <h3 className="text-xl font-black text-gray-900 mb-1">
            <em style={{ fontFamily: "'Playfair Display', serif" }}>Layla</em>.
          </h3>
          <p className="text-xs text-gray-500 mb-4">Soft start. Let's check in.</p>

          {/* Next session card */}
          <div className="bg-gray-900 text-white rounded-2xl px-4 py-3.5 mb-3">
            <p className="text-[9px] font-bold tracking-widest text-gray-400 uppercase mb-2">
              Next · Today 11:00
            </p>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-orange-400 to-rose-400 flex items-center justify-center text-xs font-bold">
                T
              </div>
              <div>
                <p className="font-semibold text-sm">Dr. Tariq</p>
                <p className="text-gray-400 text-xs">Session 7 · 50 min</p>
              </div>
            </div>
          </div>

          {/* Mood card */}
          <div className="bg-white rounded-2xl px-4 py-3 mb-3 border border-gray-100">
            <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-widest mb-1">
              Mood · 7d
            </p>
            <MiniSparkline />
          </div>

          {/* Bottom row */}
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-emerald-50 rounded-2xl px-4 py-3">
              <p className="text-[9px] font-bold tracking-widest text-emerald-600 uppercase mb-1">
                Breath
              </p>
              <p className="text-base font-black text-gray-900">4-7-8</p>
            </div>
            <div className="bg-rose-50 rounded-2xl px-4 py-3">
              <p className="text-[9px] font-bold tracking-widest text-rose-500 uppercase mb-1">
                Journal
              </p>
              <p className="text-base font-black text-gray-900">3 lines</p>
            </div>
          </div>
        </div>

        {/* Bottom nav bar */}
        <div className="absolute bottom-0 left-0 right-0 bg-white border-t border-gray-100 rounded-b-[34px] px-5 py-3">
          <div className="flex justify-around items-center">
            {[
              { label: 'Today', active: true },
              { label: 'Talk', active: false },
              { label: 'Body', active: false },
              { label: 'You', active: false },
            ].map(({ label, active }) => (
              <div key={label} className="flex flex-col items-center gap-1">
                <div
                  className={`w-6 h-6 rounded-md ${active ? 'bg-gray-900' : 'bg-gray-200'}`}
                />
                <span className={`text-[9px] font-semibold ${active ? 'text-gray-900' : 'text-gray-400'}`}>
                  {label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  </div>
);

export default PhoneMockup;
