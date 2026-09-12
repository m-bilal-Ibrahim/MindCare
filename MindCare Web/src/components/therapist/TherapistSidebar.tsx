// ============================================================
// MindCare — Therapist Console Sidebar (shared across all console screens)
// ============================================================

import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  Home,
  Users,
  Calendar,
  Inbox,
  MessageSquare,
  ClipboardList,
  UsersRound,
  FileText,
  Sun,
  LogOut,
  type LucideIcon,
} from 'lucide-react';
import Avatar from '../common/Avatar';
import {
  THERAPIST_NAV_PRACTICE,
  THERAPIST_NAV_CARE,
  THERAPIST_NAV_ACCOUNT,
} from '../../constants/therapistConsole';
import { ROUTES } from '../../constants';
import { useTherapistAuth } from '../../utils/authGuard';
import type { TherapistNavItem } from '../../types/therapistConsole';

const ICON_MAP: Record<TherapistNavItem['icon'], LucideIcon> = {
  home: Home,
  users: Users,
  calendar: Calendar,
  inbox: Inbox,
  message: MessageSquare,
  clipboard: ClipboardList,
  'circle-users': UsersRound,
  file: FileText,
  sun: Sun,
};

const NavGroup: React.FC<{ title: string; items: TherapistNavItem[]; currentPath: string }> = ({
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

const TherapistSidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { therapist, logout } = useTherapistAuth();

  const handleSignOut = () => {
    logout();
    navigate(ROUTES.THERAPIST_LOGIN, { replace: true });
  };

  return (
    <aside className="w-64 shrink-0 bg-gray-950 text-white flex flex-col px-4 py-6">
      <Link to="/" className="text-xl font-bold tracking-tight mb-1 px-2">
        MindCare<span className="text-orange-500">.</span>
      </Link>
      <p className="px-2 text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-8">
        Therapist console
      </p>

      <nav className="flex-1 overflow-y-auto">
        <NavGroup title="Practice" items={THERAPIST_NAV_PRACTICE} currentPath={location.pathname} />
        <NavGroup title="Care" items={THERAPIST_NAV_CARE} currentPath={location.pathname} />
        <NavGroup title="Account" items={THERAPIST_NAV_ACCOUNT} currentPath={location.pathname} />
      </nav>

      {therapist && (
        <div className="flex items-center gap-3 px-2 pt-4 border-t border-white/10">
          <Avatar initials={therapist.initials} color="bg-orange-600" size="sm" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold truncate">{therapist.name}</p>
            <p className="text-xs text-gray-500 truncate">Clinical psych · {therapist.license}</p>
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

export default TherapistSidebar;