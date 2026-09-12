// ============================================================
// MindCare — Therapist Console: Patients ("Your people.")
// ============================================================

import React, { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Download, Plus, SlidersHorizontal, MoreHorizontal } from 'lucide-react';
import TherapistLayout from '../components/therapist/TherapistLayout';
import Sparkline from '../components/therapist/Sparkline';
import Avatar from '../components/common/Avatar';
import {
  CONSOLE_PATIENTS,
  CONSOLE_PATIENT_SUMMARY,
  CONSOLE_FOCUS_FILTERS,
  buildPatientDetailRoute,
} from '../constants/therapistConsole';
import type { PatientStatus } from '../types/therapistConsole';

const STATUS_STYLES: Record<PatientStatus, string> = {
  Active: 'bg-emerald-100 text-emerald-700',
  Trial: 'bg-orange-100 text-orange-700',
  Paused: 'bg-gray-100 text-gray-600',
};

const PAGE_SIZE = 8;

type StatusFilter = 'All' | PatientStatus;

const TherapistPatientsPage: React.FC = () => {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('All');
  const [focusFilter, setFocusFilter] = useState<string | null>(null);
  const [page, setPage] = useState(0);

  const filtered = useMemo(() => {
    return CONSOLE_PATIENTS.filter((p) => {
      if (statusFilter !== 'All' && p.status !== statusFilter) return false;
      if (focusFilter && !p.focus.includes(focusFilter)) return false;
      return true;
    });
  }, [statusFilter, focusFilter]);

  const pageItems = filtered.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE);
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));

  return (
    <TherapistLayout
      breadcrumb={['Practice', 'Patients']}
      headerAction={
        <div className="flex gap-2 shrink-0">
          <button
            type="button"
            className="inline-flex items-center gap-2 border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 transition-colors"
          >
            <Download size={15} aria-hidden="true" /> Export
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 transition-colors"
          >
            <Plus size={15} aria-hidden="true" /> Invite patient
          </button>
        </div>
      }
    >
      <h1 className="text-5xl font-black text-gray-900 mb-2">
        Your <span className="italic font-serif font-normal">people.</span>
      </h1>
      <p className="text-gray-500 mb-6">
        {CONSOLE_PATIENT_SUMMARY.active} active · {CONSOLE_PATIENT_SUMMARY.trials} trials ·{' '}
        {CONSOLE_PATIENT_SUMMARY.paused} paused. Sort, filter, drill in.
      </p>

      <div className="flex flex-wrap items-center gap-2 mb-6">
        {(['All', 'Active', 'Trial', 'Paused'] as StatusFilter[]).map((status) => {
          const count =
            status === 'All'
              ? CONSOLE_PATIENT_SUMMARY.total
              : status === 'Active'
              ? CONSOLE_PATIENT_SUMMARY.active
              : status === 'Trial'
              ? CONSOLE_PATIENT_SUMMARY.trials
              : CONSOLE_PATIENT_SUMMARY.paused;
          const isActive = statusFilter === status;
          return (
            <button
              key={status}
              type="button"
              onClick={() => {
                setStatusFilter(status);
                setPage(0);
              }}
              className={`text-sm font-semibold px-4 py-2 rounded-full transition-colors ${
                isActive ? 'bg-gray-900 text-white' : 'bg-white border border-gray-200 text-gray-700 hover:border-gray-400'
              }`}
            >
              {status} · {count}
            </button>
          );
        })}

        <span className="w-px h-6 bg-gray-300 mx-1" aria-hidden="true" />

        {CONSOLE_FOCUS_FILTERS.slice(0, 4).map((focus) => (
          <button
            key={focus}
            type="button"
            onClick={() => {
              setFocusFilter((prev) => (prev === focus ? null : focus));
              setPage(0);
            }}
            className={`text-sm font-medium px-4 py-2 rounded-full transition-colors ${
              focusFilter === focus ? 'bg-gray-900 text-white' : 'bg-white border border-gray-200 text-gray-600 hover:border-gray-400'
            }`}
          >
            {focus}
          </button>
        ))}
        <span className="text-sm text-gray-400 px-2">+{CONSOLE_FOCUS_FILTERS.length - 4} more</span>

        <button
          type="button"
          className="ml-auto inline-flex items-center gap-2 border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2 rounded-xl hover:border-gray-400"
        >
          <SlidersHorizontal size={14} aria-hidden="true" /> Filters
        </button>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs font-semibold tracking-widest text-gray-500 uppercase border-b border-gray-100">
              <th className="px-6 py-4">Patient</th>
              <th className="px-6 py-4">Focus</th>
              <th className="px-6 py-4">Plan</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">Mood (30d)</th>
              <th className="px-6 py-4">Streak</th>
              <th className="px-6 py-4">Last seen</th>
              <th className="px-6 py-4" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {pageItems.map((patient) => (
              <tr key={patient.id} className="hover:bg-gray-50/60">
                <td className="px-6 py-4">
                  <Link to={buildPatientDetailRoute(patient.id)} className="flex items-center gap-3">
                    <Avatar initials={patient.initials} color={patient.avatarColor} />
                    <div>
                      <p className="font-bold text-gray-900">{patient.name}</p>
                      <p className="text-xs text-gray-500">
                        {patient.age} · {patient.city}
                      </p>
                    </div>
                  </Link>
                </td>
                <td className="px-6 py-4 text-gray-700">{patient.focus.join(' · ')}</td>
                <td className="px-6 py-4">
                  <span className="border border-gray-200 rounded-full px-3 py-1 text-xs font-semibold text-gray-700">
                    {patient.plan}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${STATUS_STYLES[patient.status]}`}>
                    ● {patient.status}
                  </span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-gray-900">{patient.mood30d.toFixed(1)}</span>
                    <Sparkline
                      data={patient.moodTrend}
                      color={patient.moodTrend[patient.moodTrend.length - 1] >= patient.moodTrend[0] ? '#15803d' : '#dc2626'}
                      height={24}
                    />
                  </div>
                </td>
                <td className="px-6 py-4 text-gray-700">{patient.streakDays}d</td>
                <td className="px-6 py-4">
                  <p className="text-gray-700">{patient.lastSeen}</p>
                  {patient.flag && (
                    <span
                      className={`inline-block mt-1 text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                        patient.flagTone === 'warning' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'
                      }`}
                    >
                      {patient.flag}
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 text-right">
                  <button
                    type="button"
                    aria-label={`More actions for ${patient.name}`}
                    className="w-8 h-8 rounded-lg border border-gray-200 inline-flex items-center justify-center text-gray-500 hover:border-gray-400"
                  >
                    <MoreHorizontal size={15} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between mt-4">
        <p className="text-sm text-gray-500">
          Showing {pageItems.length} of {filtered.length}
        </p>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={page === 0}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            className="text-sm font-semibold px-4 py-2 rounded-lg border border-gray-200 text-gray-700 disabled:opacity-40 disabled:cursor-not-allowed hover:border-gray-400"
          >
            ‹ Prev
          </button>
          <button
            type="button"
            disabled={page >= totalPages - 1}
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            className="text-sm font-semibold px-4 py-2 rounded-lg border border-gray-200 text-gray-700 disabled:opacity-40 disabled:cursor-not-allowed hover:border-gray-400"
          >
            Next ›
          </button>
        </div>
      </div>
    </TherapistLayout>
  );
};

export default TherapistPatientsPage;