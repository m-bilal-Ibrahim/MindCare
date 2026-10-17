// ============================================================
// MindCare — Admin top-bar bell: what's waiting for an admin,
// from GET /accounts/admin/overview/ (real counts only).
// ============================================================

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { Bell, ChevronRight } from 'lucide-react';
import { ADMIN_ROUTES } from '../../constants/adminConsole';
import { getAdminOverview, type AdminOverview } from '../../services/admin.service';

const AdminBell: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const boxRef = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    setLoading(true);
    const res = await getAdminOverview();
    setLoading(false);
    if (res.data) {
      setOverview(res.data);
      setError(null);
    } else {
      setError(res.error ?? 'Couldn’t load.');
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // Close on outside click / Escape.
  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false);
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  const items = overview
    ? [
        {
          label: 'Psychologists waiting for approval',
          count: overview.pending_approvals.psychologist,
          to: ADMIN_ROUTES.VERIFICATIONS,
        },
        {
          label: 'NGOs waiting for approval',
          count: overview.pending_approvals.ngo,
          to: `${ADMIN_ROUTES.VERIFICATIONS}?type=ngo`,
        },
        { label: 'Open reports', count: overview.open_reports, to: ADMIN_ROUTES.MODERATION },
      ]
    : [];
  const total = items.reduce((n, i) => n + i.count, 0);

  return (
    <div ref={boxRef} className="relative shrink-0">
      <button
        type="button"
        onClick={() => {
          setOpen((o) => !o);
          if (!open) load();
        }}
        aria-label={total ? `Waiting for you: ${total}` : 'Waiting for you'}
        aria-expanded={open}
        aria-haspopup="true"
        className="relative w-10 h-10 rounded-xl border border-gray-200 bg-white flex items-center justify-center text-gray-600 hover:border-gray-400"
      >
        <Bell size={16} />
        {total > 0 && (
          <span className="absolute -top-1.5 -right-1.5 min-w-[1.25rem] h-5 px-1 rounded-full bg-orange-500 text-white text-[11px] font-bold flex items-center justify-center">
            {total > 99 ? '99+' : total}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 bg-white border border-gray-200 rounded-2xl shadow-lg z-30 overflow-hidden">
          <p className="px-4 py-3 text-xs font-semibold tracking-widest text-gray-500 uppercase border-b border-gray-100">
            Waiting for you
          </p>
          {error ? (
            <p className="px-4 py-4 text-sm text-gray-600">{error}</p>
          ) : !overview ? (
            <p className="px-4 py-4 text-sm text-gray-500">{loading ? 'Loading…' : '—'}</p>
          ) : (
            <ul>
              {items.map((item) => (
                <li key={item.label}>
                  <Link
                    to={item.to}
                    onClick={() => setOpen(false)}
                    className="flex items-center justify-between gap-3 px-4 py-3 text-sm hover:bg-gray-50"
                  >
                    <span className="text-gray-700">{item.label}</span>
                    <span className="flex items-center gap-1.5">
                      <span
                        className={`min-w-[1.5rem] text-center text-xs font-bold px-1.5 py-0.5 rounded-full ${
                          item.count ? 'bg-orange-100 text-orange-700' : 'bg-gray-100 text-gray-500'
                        }`}
                      >
                        {item.count}
                      </span>
                      <ChevronRight size={14} className="text-gray-400" aria-hidden="true" />
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
};

export default AdminBell;
