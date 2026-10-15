// ============================================================
// MindCare — Admin Console: NGO Partners
// Partner cards = approved, active NGO accounts from the backend
// (GET /accounts/admin/users/?role=ngo&status=active, then each
// account's NGO profile). "Partner onboarding" = NGOs waiting for
// approval (GET /accounts/admin/pending/?role=ngo).
// ============================================================

import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Pencil, Plus, ShieldCheck } from 'lucide-react';
import AdminLayout from '../components/admin/AdminLayout';
import Avatar from '../components/common/Avatar';
import { ErrorPanel, LoadingPanel, relativeTime } from '../components/therapist/ApiStates';
import { SOS_ROUTING_TREE, ADMIN_ROUTES } from '../constants/adminConsole';
import {
  ADMIN_API_MISSING,
  getAdminUser,
  getPendingNgos,
  listAllAdminUsers,
  type AdminUserRow,
  type PendingNgo,
} from '../services/admin.service';

type NgoProfile = NonNullable<PendingNgo['ngo_profile']>;

interface Partner {
  row: AdminUserRow;
  profile: NgoProfile | null;
}

const AVATAR_COLORS = ['bg-orange-500', 'bg-emerald-700', 'bg-violet-500', 'bg-amber-600', 'bg-sky-600', 'bg-rose-500'];

const initialsOf = (name: string) =>
  name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('') || '?';

const placeOf = (p: NgoProfile | null) => [p?.city?.name, p?.country?.name].filter(Boolean).join(', ');

const serviceAreasOf = (p: NgoProfile | null) =>
  (p?.service_areas ?? [])
    .map((a) => (a.city?.name ? a.city.name : a.country?.name ? `${a.country.name} (nationwide)` : ''))
    .filter(Boolean)
    .join(' · ');

const NgoPartnersPage: React.FC = () => {
  const navigate = useNavigate();
  const [partners, setPartners] = useState<Partner[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [waiting, setWaiting] = useState<PendingNgo[] | null>(null);
  const [waitingError, setWaitingError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    setPartners(null);
    const list = await listAllAdminUsers({ role: 'ngo', status: 'active' });
    if (!list.data) {
      setError(list.error ?? 'Couldn’t load NGO partners.');
      return;
    }
    // Organisation details live on each account's NGO profile.
    const details = await Promise.all(list.data.map((row) => getAdminUser(row.id)));
    setPartners(list.data.map((row, i) => ({ row, profile: (details[i].data?.ngo_profile as NgoProfile | null) ?? null })));
  }, []);

  const loadWaiting = useCallback(async () => {
    setWaitingError(null);
    const res = await getPendingNgos();
    if (res.data) setWaiting(res.data);
    else setWaitingError(res.error ?? 'Couldn’t load applications.');
  }, []);

  useEffect(() => {
    load();
    loadWaiting();
  }, [load, loadWaiting]);

  const count = partners?.length ?? 0;

  return (
    <AdminLayout
      breadcrumb={['Trust & safety', 'NGO partners']}
      headerAction={
        <div className="flex gap-2 shrink-0">
          <button
            type="button"
            className="border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 transition-colors"
          >
            SOS routing rules
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 transition-colors"
          >
            <Plus size={15} aria-hidden="true" /> Add partner
          </button>
        </div>
      }
    >
      <h1 className="text-5xl font-black text-gray-900 mb-2">
        NGO <span className="italic font-serif font-normal">partners.</span>
      </h1>
      <p className="text-gray-500 mb-8 max-w-2xl">
        When the platform can&apos;t be enough — these are the lines we hand people to.
        {partners && ` ${count} active ${count === 1 ? 'partner' : 'partners'}.`}
      </p>

      {error ? (
        <div className="mb-6">
          <ErrorPanel message={error} title={error === ADMIN_API_MISSING ? 'Not available yet' : undefined} onRetry={error === ADMIN_API_MISSING ? undefined : load} />
        </div>
      ) : !partners ? (
        <div className="mb-6">
          <LoadingPanel label="Loading NGO partners…" />
        </div>
      ) : partners.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center mb-6">
          <p className="text-gray-900 font-semibold">No NGO partners yet.</p>
          <p className="text-sm text-gray-500">NGOs appear here once an admin approves their application in Verifications.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
          {partners.map(({ row, profile }, i) => {
            const name = profile?.organization_name || row.display_name;
            const typeLine = [profile?.representative_name, placeOf(profile)].filter(Boolean).join(' · ');
            const areas = serviceAreasOf(profile);
            const contact = [profile?.official_email || row.email, profile?.official_phone].filter(Boolean).join(' · ');
            return (
              <div key={row.id} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <div className="flex items-start gap-4 mb-4">
                  <Avatar initials={initialsOf(name)} color={AVATAR_COLORS[i % AVATAR_COLORS.length]} size="lg" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <h3 className="text-xl font-black text-gray-900">{name}</h3>
                      <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-700">Active</span>
                    </div>
                    {typeLine && <p className="text-sm text-gray-500">{typeLine}</p>}
                  </div>
                </div>

                {areas && (
                  <div className="mb-4 pb-4 border-b border-gray-100">
                    <p className="text-[10px] font-semibold tracking-widest text-gray-500 uppercase mb-1">Service areas</p>
                    <p className="text-sm text-gray-800">{areas}</p>
                  </div>
                )}

                <div className="flex items-center justify-between flex-wrap gap-2">
                  <p className="text-xs text-gray-500 break-all">{contact}</p>
                  <div className="flex gap-2 shrink-0">
                    <button
                      type="button"
                      className="border border-gray-200 bg-white text-gray-700 text-xs font-semibold px-3 py-2 rounded-lg hover:border-gray-400"
                    >
                      Coverage map
                    </button>
                    <button
                      type="button"
                      className="inline-flex items-center gap-1 bg-gray-900 text-white text-xs font-semibold px-3 py-2 rounded-lg hover:bg-gray-800"
                    >
                      <Pencil size={11} aria-hidden="true" /> Edit
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-6">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-1">
            <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase">SOS routing tree · current</p>
            <button
              type="button"
              className="inline-flex items-center gap-1.5 border border-gray-200 bg-white text-gray-700 text-xs font-semibold px-3 py-2 rounded-lg hover:border-gray-400"
            >
              <Pencil size={11} aria-hidden="true" /> Edit tree
            </button>
          </div>
          <h2 className="text-2xl font-black text-gray-900 mb-5">How we hand people off</h2>

          <ul className="space-y-4">
            {SOS_ROUTING_TREE.map((step) => (
              <li key={step.id} className="flex items-start gap-3" style={{ paddingLeft: step.indent * 24 }}>
                <span className={`w-2.5 h-2.5 rounded-full mt-1.5 shrink-0 ${step.tone === 'critical' ? 'bg-red-500' : 'bg-gray-400'}`} />
                <p className="text-sm text-gray-800">{step.label}</p>
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-1">Partner onboarding</p>
          {waitingError ? (
            <p className="text-sm text-gray-600 mb-5">{waitingError}</p>
          ) : !waiting ? (
            <p className="text-sm text-gray-500 mb-5">Loading…</p>
          ) : waiting.length === 0 ? (
            <div className="mb-5">
              <h3 className="text-xl font-black text-gray-900 mb-1">No applications waiting</h3>
              <p className="text-sm text-gray-500 flex items-center gap-1.5">
                <ShieldCheck size={14} className="text-emerald-700" aria-hidden="true" /> New NGO sign-ups appear here.
              </p>
            </div>
          ) : (
            <>
              <h3 className="text-xl font-black text-gray-900 mb-1">
                {waiting.length} waiting for review
              </h3>
              <p className="text-sm text-gray-500 mb-5">Approve or reject them in Verifications.</p>
              <ul className="space-y-4 mb-5">
                {waiting.slice(0, 5).map((n) => (
                  <li key={n.id} className="flex items-start gap-3">
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shrink-0 mt-1.5" aria-hidden="true" />
                    <div className="min-w-0">
                      <p className="font-bold text-gray-900 text-sm truncate">{n.ngo_profile?.organization_name || n.full_name}</p>
                      <p className="text-xs text-gray-500">
                        Applied {relativeTime(n.created_at)}
                        {placeOf(n.ngo_profile) && ` · ${placeOf(n.ngo_profile)}`}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            </>
          )}

          <button
            type="button"
            onClick={() => navigate(`${ADMIN_ROUTES.VERIFICATIONS}?type=ngo`)}
            className="w-full bg-gray-900 text-white text-sm font-semibold py-2.5 rounded-xl hover:bg-gray-800 transition-colors"
          >
            Continue review →
          </button>
        </div>
      </div>
    </AdminLayout>
  );
};

export default NgoPartnersPage;
