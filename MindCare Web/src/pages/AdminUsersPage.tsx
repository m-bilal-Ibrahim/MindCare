// ============================================================
// MindCare — Admin Console: Users
// ============================================================

import React, { useMemo, useState } from 'react';
import { Download, SlidersHorizontal, MoreHorizontal } from 'lucide-react';
import AdminLayout from '../components/admin/AdminLayout';
import Avatar from '../components/common/Avatar';
import { PLATFORM_USERS, USERS_SUMMARY } from '../constants/adminConsole';
import type { PlatformUserStatus } from '../types/adminConsole';

type StatusFilter = 'All' | 'Active' | 'Trial' | 'Paused' | 'HasFlags' | 'RefundPending' | 'WearableIssues';

const STATUS_STYLES: Record<PlatformUserStatus, string> = {
  Active: 'bg-emerald-100 text-emerald-700',
  Trial: 'bg-orange-100 text-orange-700',
  Paused: 'bg-gray-100 text-gray-600',
  Onboarding: 'bg-amber-100 text-amber-700',
};

const FLAG_STYLES: Record<string, string> = {
  support: 'bg-amber-100 text-amber-700',
  refund: 'bg-amber-100 text-amber-700',
  sensor: 'bg-amber-100 text-amber-700',
};

const PAGE_SIZE = 9;

const AdminUsersPage: React.FC = () => {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('All');
  const [page, setPage] = useState(0);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  const filtered = useMemo(() => {
    return PLATFORM_USERS.filter((u) => {
      if (statusFilter === 'Active') return u.status === 'Active';
      if (statusFilter === 'Trial') return u.status === 'Trial';
      if (statusFilter === 'Paused') return u.status === 'Paused';
      if (statusFilter === 'HasFlags') return !!u.flag;
      if (statusFilter === 'RefundPending') return u.flag === 'refund';
      if (statusFilter === 'WearableIssues') return u.flag === 'sensor';
      return true;
    });
  }, [statusFilter]);

  const pageItems = filtered.slice(page * PAGE_SIZE, page * PAGE_SIZE + PAGE_SIZE);
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === pageItems.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(pageItems.map((u) => u.id)));
    }
  };

  return (
    <AdminLayout
      breadcrumb={['Operations', 'Users']}
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
            className="inline-flex items-center gap-2 border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 transition-colors"
          >
            <SlidersHorizontal size={15} aria-hidden="true" /> Filters
          </button>
        </div>
      }
    >
      <h1 className="text-5xl font-black text-gray-900 mb-2">
        Users <span className="italic font-serif font-normal">on the platform.</span>
      </h1>
      <p className="text-gray-500 mb-6">
        {USERS_SUMMARY.active.toLocaleString()} active · {USERS_SUMMARY.trialsThisMonth.toLocaleString()} trials this
        month · {USERS_SUMMARY.pausedOrRefund} paused / refund requests
      </p>

      <div className="flex flex-wrap items-center gap-2 mb-6">
        {(
          [
            { key: 'All', label: 'All', count: PLATFORM_USERS.length },
            { key: 'Active', label: 'Active', count: USERS_SUMMARY.activeCount },
            { key: 'Trial', label: 'Trial', count: USERS_SUMMARY.trialCount },
            { key: 'Paused', label: 'Paused', count: USERS_SUMMARY.pausedCount },
          ] as { key: StatusFilter; label: string; count: number }[]
        ).map(({ key, label, count }) => (
          <button
            key={key}
            type="button"
            onClick={() => {
              setStatusFilter(key);
              setPage(0);
            }}
            className={`text-sm font-semibold px-4 py-2 rounded-full transition-colors ${
              statusFilter === key ? 'bg-gray-900 text-white' : 'bg-white border border-gray-200 text-gray-700 hover:border-gray-400'
            }`}
          >
            {label} · {count.toLocaleString()}
          </button>
        ))}

        <span className="w-px h-6 bg-gray-300 mx-1" aria-hidden="true" />

        {(
          [
            { key: 'HasFlags', label: 'Has flags', count: USERS_SUMMARY.hasFlagsCount },
            { key: 'RefundPending', label: 'Refund pending', count: USERS_SUMMARY.refundPendingCount },
            { key: 'WearableIssues', label: 'Wearable issues', count: USERS_SUMMARY.wearableIssuesCount },
          ] as { key: StatusFilter; label: string; count: number }[]
        ).map(({ key, label, count }) => (
          <button
            key={key}
            type="button"
            onClick={() => {
              setStatusFilter(key);
              setPage(0);
            }}
            className={`text-sm font-medium px-4 py-2 rounded-full transition-colors ${
              statusFilter === key ? 'bg-gray-900 text-white' : 'bg-white border border-gray-200 text-gray-600 hover:border-gray-400'
            }`}
          >
            {label} · {count}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs font-semibold tracking-widest text-gray-500 uppercase border-b border-gray-100">
              <th className="px-6 py-4 w-10">
                <input
                  type="checkbox"
                  checked={pageItems.length > 0 && selectedIds.size === pageItems.length}
                  onChange={toggleSelectAll}
                  className="w-4 h-4 rounded border-gray-300 accent-gray-900"
                  aria-label="Select all users on this page"
                />
              </th>
              <th className="px-6 py-4">User</th>
              <th className="px-6 py-4">City</th>
              <th className="px-6 py-4">Plan</th>
              <th className="px-6 py-4">Therapist</th>
              <th className="px-6 py-4">Joined</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">Flags</th>
              <th className="px-6 py-4" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {pageItems.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50/60">
                <td className="px-6 py-4">
                  <input
                    type="checkbox"
                    checked={selectedIds.has(user.id)}
                    onChange={() => toggleSelect(user.id)}
                    className="w-4 h-4 rounded border-gray-300 accent-gray-900"
                    aria-label={`Select ${user.name}`}
                  />
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <Avatar initials={user.initials} color={user.avatarColor} />
                    <div className="min-w-0">
                      <p className="font-bold text-gray-900 truncate">{user.name}</p>
                      <p className="text-xs text-gray-500 truncate">{user.emailMasked}</p>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 text-gray-700">{user.city}</td>
                <td className="px-6 py-4">
                  {user.plan ? (
                    <span className="border border-gray-200 rounded-full px-3 py-1 text-xs font-semibold text-gray-700">
                      {user.plan}
                    </span>
                  ) : (
                    <span className="text-gray-300">—</span>
                  )}
                </td>
                <td className="px-6 py-4 text-gray-700">{user.therapistName ?? <span className="text-gray-300">—</span>}</td>
                <td className="px-6 py-4 text-gray-700">{user.joined}</td>
                <td className="px-6 py-4">
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${STATUS_STYLES[user.status]}`}>
                    ● {user.status}
                  </span>
                </td>
                <td className="px-6 py-4">
                  {user.flag ? (
                    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${FLAG_STYLES[user.flag] ?? 'bg-gray-100 text-gray-600'}`}>
                      {user.flag}
                    </span>
                  ) : (
                    <span className="text-gray-300">—</span>
                  )}
                </td>
                <td className="px-6 py-4 text-right">
                  <button
                    type="button"
                    aria-label={`More actions for ${user.name}`}
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
          {selectedIds.size > 0 && <span className="ml-2 font-semibold text-gray-700">· {selectedIds.size} selected</span>}
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
    </AdminLayout>
  );
};

export default AdminUsersPage;