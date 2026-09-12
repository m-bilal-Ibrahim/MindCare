// ============================================================
// MindCare — Admin Console Layout (sidebar + topbar shell)
// ============================================================

import React, { useState, type ReactNode } from 'react';
import { Bell, Search } from 'lucide-react';
import AdminSidebar from './AdminSidebar';
import { sanitizeText, MAX_LENGTHS } from '../../utils/validation';

interface AdminLayoutProps {
  breadcrumb: string[];
  headerAction?: ReactNode;
  children: ReactNode;
}

const AdminLayout: React.FC<AdminLayoutProps> = ({ breadcrumb, headerAction, children }) => {
  const [search, setSearch] = useState('');

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // UX-only cap; a real search endpoint must independently validate/sanitize,
    // scope results by the admin's actual permissions, and audit-log the query
    // since it may surface other users' PII.
    setSearch(e.target.value.slice(0, MAX_LENGTHS.shortText));
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const query = sanitizeText(search);
    if (!query) return;
    // TODO: wire to real search endpoint (users, therapists, tickets)
    // eslint-disable-next-line no-console
    console.info('[MindCare] Admin search submitted:', query);
  };

  return (
    <div className="min-h-screen bg-[#F5F0E8] flex">
      <AdminSidebar />

      <div className="flex-1 flex flex-col min-w-0">
        <header className="flex items-center gap-4 px-8 py-4 border-b border-gray-200 bg-[#F5F0E8]">
          <nav aria-label="Breadcrumb" className="text-sm text-gray-500 shrink-0">
            {breadcrumb.map((crumb, i) => (
              <span key={crumb}>
                {i > 0 && <span className="mx-1.5">/</span>}
                <span className={i === breadcrumb.length - 1 ? 'text-gray-900 font-medium' : ''}>{crumb}</span>
              </span>
            ))}
          </nav>

          <form onSubmit={handleSearchSubmit} role="search" className="flex-1 max-w-md ml-4">
            <label htmlFor="admin-search" className="sr-only">
              Search users, therapists, tickets
            </label>
            <div className="relative">
              <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" aria-hidden="true" />
              <input
                id="admin-search"
                type="search"
                value={search}
                onChange={handleSearchChange}
                maxLength={MAX_LENGTHS.shortText}
                placeholder="Search users, therapists, tickets…"
                className="w-full pl-9 pr-4 py-2.5 text-sm border border-gray-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-gray-900"
              />
            </div>
          </form>

          <button
            type="button"
            className="w-10 h-10 rounded-xl border border-gray-200 bg-white flex items-center justify-center text-gray-600 hover:border-gray-400 shrink-0"
            aria-label="Notifications"
          >
            <Bell size={16} />
          </button>

          {headerAction}
        </header>

        <main className="flex-1 p-8 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
};

export default AdminLayout;