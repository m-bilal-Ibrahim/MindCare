// ============================================================
// MindCare — Admin Console: Therapists
// ============================================================

import React, { useMemo, useState } from 'react';
import { Download, Plus, MoreHorizontal, AlertTriangle } from 'lucide-react';
import AdminLayout from '../components/admin/AdminLayout';
import Avatar from '../components/common/Avatar';
import { THERAPIST_DIRECTORY_SUMMARY, THERAPIST_DIRECTORY } from '../constants/adminConsole';
import type { TherapistDirectoryStatus } from '../types/adminConsole';

type StatusFilter = 'All' | 'Active' | 'Onboarding' | 'Paused' | 'Flagged';

const STATUS_STYLES: Record<TherapistDirectoryStatus, string> = {
  Active: 'bg-emerald-100 text-emerald-700',
  Onboarding: 'bg-amber-100 text-amber-700',
  Flagged: 'bg-red-100 text-red-700',
  Paused: 'bg-gray-100 text-gray-600',
  'Pending verify': 'bg-amber-100 text-amber-700',
};

const TherapistsPage: React.FC = () => {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('All');
  const s = THERAPIST_DIRECTORY_SUMMARY;

  const filtered = useMemo(() => {
    return THERAPIST_DIRECTORY.filter((t) => {
      if (statusFilter === 'All') return true;
      return t.status === statusFilter;
    });
  }, [statusFilter]);

  return (
    <AdminLayout
      breadcrumb={['Operations', 'Therapists']}
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
            <Plus size={15} aria-hidden="true" /> Invite therapist
          </button>
        </div>
      }
    >
      <h1 className="text-5xl font-black text-gray-900 mb-2">
        The <span className="italic font-serif font-normal">people</span> doing the work.
      </h1>
      <p className="text-gray-500 mb-6">
        {s.activeCount} active · {s.onboardingCount} onboarding · {s.flaggedCount} flagged. The platform is only as
        good as this list.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-2">Active therapists</p>
          <p className="text-3xl font-black text-gray-900">
            {s.activeCount} <span className="text-base font-semibold text-emerald-700">{s.activeCountDelta}</span>
          </p>
          <p className="text-xs text-gray-500 mt-1">this month</p>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-2">Avg patients / Tx</p>
          <p className="text-3xl font-black text-gray-900">
            {s.avgPatientsPerTx} <span className="text-base font-semibold text-emerald-700">{s.avgPatientsDelta}</span>
          </p>
          <p className="text-xs text-gray-500 mt-1">caseload</p>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-2">Avg rating</p>
          <p className="text-3xl font-black text-amber-600">{s.avgRating}</p>
          <p className="text-xs text-gray-500 mt-1">of 5 · across {s.activeCount} therapists</p>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-2">Avg compliance</p>
          <p className="text-3xl font-black text-gray-900">{s.avgCompliance}%</p>
          <p className="text-xs text-gray-500 mt-1">of weekly plan</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 mb-6">
        {(
          [
            { key: 'All', label: `All · ${s.totalCount}` },
            { key: 'Active', label: `Active · ${s.activeCount}` },
            { key: 'Onboarding', label: `Onboarding · ${s.onboardingCount}` },
            { key: 'Paused', label: `Paused · ${s.pausedCount}` },
            { key: 'Flagged', label: `Flagged · ${s.flaggedCount}` },
          ] as { key: StatusFilter; label: string }[]
        ).map(({ key, label }) => (
          <button
            key={key}
            type="button"
            onClick={() => setStatusFilter(key)}
            className={`text-sm font-semibold px-4 py-2 rounded-full transition-colors ${
              statusFilter === key ? 'bg-gray-900 text-white' : 'bg-white border border-gray-200 text-gray-700 hover:border-gray-400'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs font-semibold tracking-widest text-gray-500 uppercase border-b border-gray-100">
              <th className="px-6 py-4">Therapist</th>
              <th className="px-6 py-4">Specialty</th>
              <th className="px-6 py-4">City</th>
              <th className="px-6 py-4">Patients</th>
              <th className="px-6 py-4">MRR contrib.</th>
              <th className="px-6 py-4">Rating</th>
              <th className="px-6 py-4">Compliance</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.map((t) => (
              <tr key={t.id} className="hover:bg-gray-50/60">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <Avatar initials={t.initials} color={t.avatarColor} />
                    <div className="min-w-0">
                      <p className="font-bold text-gray-900">{t.name}</p>
                      {t.warning && (
                        <p className="text-xs text-red-600 flex items-center gap-1">
                          <AlertTriangle size={11} aria-hidden="true" /> {t.warning}
                        </p>
                      )}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 text-gray-700">{t.specialty}</td>
                <td className="px-6 py-4 text-gray-700">{t.city}</td>
                <td className="px-6 py-4 text-gray-700">{t.patients ?? <span className="text-gray-300">—</span>}</td>
                <td className="px-6 py-4 text-gray-700">{t.mrrContrib ?? <span className="text-gray-300">—</span>}</td>
                <td className="px-6 py-4">
                  {t.rating ? (
                    <span className="text-amber-600 font-semibold">★ {t.rating}</span>
                  ) : (
                    <span className="text-gray-300">—</span>
                  )}
                </td>
                <td className="px-6 py-4">
                  {t.compliance !== null ? (
                    <div className="flex items-center gap-2 w-24">
                      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${t.compliance < 80 ? 'bg-amber-500' : 'bg-emerald-600'}`}
                          style={{ width: `${t.compliance}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500">{t.compliance}%</span>
                    </div>
                  ) : (
                    <span className="text-gray-300">—</span>
                  )}
                </td>
                <td className="px-6 py-4">
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${STATUS_STYLES[t.status]}`}>
                    {t.status === 'Active' && '● '}
                    {t.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-right">
                  <button
                    type="button"
                    aria-label={`More actions for ${t.name}`}
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
    </AdminLayout>
  );
};

export default TherapistsPage;