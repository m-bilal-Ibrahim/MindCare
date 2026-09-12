// ============================================================
// MindCare — Therapist Console: Schedule ("Your week.")
// ============================================================

import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Plus } from 'lucide-react';
import TherapistLayout from '../components/therapist/TherapistLayout';
import {
  SCHEDULE_WEEK_DAYS,
  SCHEDULE_HOURS,
  SCHEDULE_SUMMARY,
  SCHEDULE_EVENTS,
  buildPatientDetailRoute,
} from '../constants/therapistConsole';
import type { ScheduleEventType } from '../types/therapistConsole';

const ROW_HEIGHT = 64; // px per hour

const TYPE_STYLES: Record<ScheduleEventType, string> = {
  confirmed: 'bg-emerald-100 border-emerald-300 text-emerald-900',
  pending: 'bg-amber-100 border-amber-300 text-amber-900',
  trial: 'bg-rose-100 border-rose-300 text-rose-900',
  block: 'bg-gray-100 border-gray-300 text-gray-600',
};

const formatHour = (hour: number) => {
  const h = hour % 12 === 0 ? 12 : hour % 12;
  return hour < 12 ? `${h} AM` : `${h} PM`;
};

const TherapistSchedulePage: React.FC = () => {
  return (
    <TherapistLayout
      breadcrumb={['Practice', 'Schedule']}
      headerAction={
        <div className="flex items-center gap-2 shrink-0">
          <div className="flex items-center border border-gray-200 rounded-xl overflow-hidden">
            <button type="button" className="p-2.5 hover:bg-gray-100" aria-label="Previous week">
              <ChevronLeft size={16} />
            </button>
            <button type="button" className="px-3 py-2.5 text-sm font-semibold border-x border-gray-200 hover:bg-gray-100">
              Today
            </button>
            <button type="button" className="p-2.5 hover:bg-gray-100" aria-label="Next week">
              <ChevronRight size={16} />
            </button>
          </div>
          <div className="flex items-center border border-gray-200 rounded-xl overflow-hidden">
            <button type="button" className="px-3 py-2.5 text-sm font-semibold bg-gray-100">
              Week
            </button>
            <button type="button" className="px-3 py-2.5 text-sm font-semibold border-l border-gray-200 hover:bg-gray-100">
              Month
            </button>
          </div>
          <button
            type="button"
            className="inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 transition-colors"
          >
            <Plus size={15} aria-hidden="true" /> Add availability
          </button>
        </div>
      }
    >
      <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-2">May · Week 21</p>
      <h1 className="text-5xl font-black text-gray-900 mb-2">
        Your <span className="italic font-serif font-normal">week.</span>
      </h1>
      <p className="text-gray-500 mb-8">
        {SCHEDULE_SUMMARY.confirmed} sessions confirmed · {SCHEDULE_SUMMARY.awaiting} awaiting ·{' '}
        {SCHEDULE_SUMMARY.free} free slots. Drag to move, click a free slot to add.
      </p>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        {/* Day headers */}
        <div className="grid border-b border-gray-100" style={{ gridTemplateColumns: '64px repeat(7, 1fr)' }}>
          <div />
          {SCHEDULE_WEEK_DAYS.map((day) => (
            <div key={day.label} className="px-4 py-3 text-center border-l border-gray-100">
              <p className="text-xs font-semibold tracking-widest text-gray-400">{day.label}</p>
              <p className="text-xl font-black text-gray-900">{day.date}</p>
            </div>
          ))}
        </div>

        {/* Grid body */}
        <div className="grid" style={{ gridTemplateColumns: '64px repeat(7, 1fr)' }}>
          {/* Hour labels */}
          <div>
            {SCHEDULE_HOURS.map((hour) => (
              <div
                key={hour}
                className="text-xs text-gray-400 text-right pr-2 -translate-y-2"
                style={{ height: ROW_HEIGHT }}
              >
                {formatHour(hour)}
              </div>
            ))}
          </div>

          {/* Day columns */}
          {SCHEDULE_WEEK_DAYS.map((day, dayIndex) => (
            <div key={day.label} className="relative border-l border-gray-100">
              {SCHEDULE_HOURS.map((hour) => (
                <div key={hour} className="border-b border-gray-50" style={{ height: ROW_HEIGHT }} />
              ))}

              {SCHEDULE_EVENTS.filter((ev) => ev.day === dayIndex).map((ev) => {
                const top = (ev.startHour - SCHEDULE_HOURS[0]) * ROW_HEIGHT;
                const height = Math.max(28, (ev.durationMin / 60) * ROW_HEIGHT - 4);
                const content = (
                  <div
                    className={`absolute left-1 right-1 rounded-lg border px-2.5 py-1.5 text-xs overflow-hidden ${TYPE_STYLES[ev.type]}`}
                    style={{ top: top + 2, height }}
                  >
                    <p className="font-bold truncate">{ev.patientName ?? ev.label}</p>
                    {ev.patientName && <p className="truncate opacity-80">{ev.label}</p>}
                  </div>
                );

                if (ev.patientId) {
                  return (
                    <Link key={ev.id} to={buildPatientDetailRoute(ev.patientId)} className="block">
                      {content}
                    </Link>
                  );
                }
                return <div key={ev.id}>{content}</div>;
              })}
            </div>
          ))}
        </div>
      </div>
    </TherapistLayout>
  );
};

export default TherapistSchedulePage;