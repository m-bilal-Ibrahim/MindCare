// ============================================================
// MindCare — Admin Console Layout (sidebar + topbar shell)
// ============================================================

import React, { useState, type ReactNode } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Search } from 'lucide-react';
import AdminSidebar from './AdminSidebar';
import AdminBell from './AdminBell';
import { ADMIN_ROUTES } from '../../constants/adminConsole';
import { MAX_LENGTHS, normalizeSingleLine } from '../../utils/validation';

interface AdminLayoutProps {
  breadcrumb: string[];
  headerAction?: ReactNode;
  children: ReactNode;
}

const AdminLayout: React.FC<AdminLayoutProps> = ({ breadcrumb, headerAction, children }) => {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  // On the Users page the box shows the current search.
  const [search, setSearch] = useState(() => params.get('search') ?? '');

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value.slice(0, MAX_LENGTHS.shortText));
  };

  // Searches accounts: names/emails for psychologists and NGOs, pseudonyms only
  // for patients (the backend never matches a patient's real name or email).
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const query = normalizeSingleLine(search);
    navigate(query ? `${ADMIN_ROUTES.USERS}?search=${encodeURIComponent(query)}` : ADMIN_ROUTES.USERS);
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
              Search accounts by name, email or patient pseudonym
            </label>
            <div className="relative">
              <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" aria-hidden="true" />
              <input
                id="admin-search"
                type="search"
                value={search}
                onChange={handleSearchChange}
                maxLength={MAX_LENGTHS.shortText}
                placeholder="Search accounts: name, email or pseudonym…"
                className="w-full pl-9 pr-4 py-2.5 text-sm border border-gray-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-gray-900"
              />
            </div>
          </form>

          <AdminBell />

          {headerAction}
        </header>

        <main className="flex-1 p-8 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
};

export default AdminLayout;