// ============================================================
// MindCare — Admin Console Sidebar (shared across all admin screens)
// ============================================================

import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Home,
  Shield,
  Code,
  Users,
  Flag,
  AlertTriangle,
  Heart,
  FileText,
  Sun,
  LogOut,
  type LucideIcon,
} from 'lucide-react';
import Avatar from '../common/Avatar';
import {
  ADMIN_NAV_OPERATIONS,
  ADMIN_NAV_TRUST_SAFETY,
  ADMIN_NAV_PLATFORM,
  ADMIN_ROUTES,
} from '../../constants/adminConsole';
import { useAdminAuth } from '../../utils/adminAuthGuard';
import type { AdminNavItem } from '../../types/adminConsole';

const ICON_MAP: Record<AdminNavItem['icon'], LucideIcon> = {
  home: Home,
  shield: Shield,
  code: Code,
  users: Users,
  flag: Flag,
  'alert-triangle': AlertTriangle,
  heart: Heart,
  file: FileText,
  sun: Sun,
};

const NavGroup: React.FC<{ title: string; items: AdminNavItem[]; currentPath: string }> = ({
  title,
  items,
  currentPath,
}) => (
  <div className="mb-6">
    <p className="px-3 text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-2">{title}</p>
    <ul className="space-y-0.5">
      {items.map((item) => {
        const Icon = ICON_MAP[item.icon];
        const isActive = item.route === currentPath;
        return (
          <li key={item.id}>
            <Link
              to={item.route}
              className={`flex items-center justify-between gap-2 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                isActive ? 'bg-white/10 text-white font-semibold' : 'text-gray-300 hover:bg-white/5 hover:text-white'
              }`}
            >
              <span className="flex items-center gap-3">
                <Icon size={16} aria-hidden="true" />
                {item.label}
              </span>
              {item.badge ? (
                <span className="min-w-[1.25rem] h-5 px-1.5 rounded-full bg-orange-500 text-white text-[11px] font-bold flex items-center justify-center">
                  {item.badge}
                </span>
              ) : null}
            </Link>
          </li>
        );
      })}
    </ul>
  </div>
);

const AdminSidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { admin, logout } = useAdminAuth();

  const handleSignOut = () => {
    logout();
    navigate(ADMIN_ROUTES.SIGN_IN, { replace: true });
  };

  return (
    <aside className="w-64 shrink-0 bg-gray-950 text-white flex flex-col px-4 py-6">
      <Link to="/" className="text-xl font-bold tracking-tight mb-1 px-2">
        MindCare<span className="text-orange-500">.</span>
      </Link>
      <p className="px-2 text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-8">
        Admin console
      </p>

      <nav className="flex-1 overflow-y-auto">
        <NavGroup title="Operations" items={ADMIN_NAV_OPERATIONS} currentPath={location.pathname} />
        <NavGroup title="Trust & safety" items={ADMIN_NAV_TRUST_SAFETY} currentPath={location.pathname} />
        <NavGroup title="Platform" items={ADMIN_NAV_PLATFORM} currentPath={location.pathname} />
      </nav>

      {admin && (
        <div className="flex items-center gap-3 px-2 pt-4 border-t border-white/10">
          <Avatar initials={admin.initials} color="bg-orange-600" size="sm" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold truncate">{admin.name}</p>
            <p className="text-xs text-gray-500 truncate">{admin.role}</p>
          </div>
          <button
            type="button"
            onClick={handleSignOut}
            aria-label="Sign out"
            title="Sign out"
            className="w-8 h-8 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 flex items-center justify-center shrink-0"
          >
            <LogOut size={15} />
          </button>
        </div>
      )}
    </aside>
  );
};

export default AdminSidebar;