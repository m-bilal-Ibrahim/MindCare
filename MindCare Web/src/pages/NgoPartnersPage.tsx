// ============================================================
// MindCare — Admin Console: NGO Partners
// ============================================================

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Pencil, Plus, Check } from 'lucide-react';
import AdminLayout from '../components/admin/AdminLayout';
import Avatar from '../components/common/Avatar';
import {
  NGO_PARTNERS_SUMMARY,
  NGO_PARTNER_CARDS,
  SOS_ROUTING_TREE,
  NGO_PARTNER_ONBOARDING,
  ADMIN_ROUTES,
} from '../constants/adminConsole';

const NgoPartnersPage: React.FC = () => {
  const navigate = useNavigate();
  const s = NGO_PARTNERS_SUMMARY;

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
        When the platform can&apos;t be enough — these are the lines we hand people to. {s.activePartners} active
        partners · {s.ytdRouted.toLocaleString()} routed cases this year · {s.closedLoopPercent}% closed-loop.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
        {NGO_PARTNER_CARDS.map((p) => (
          <div key={p.id} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-start gap-4 mb-4">
              <Avatar initials={p.initials} color={p.avatarColor} size="lg" />
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-xl font-black text-gray-900">{p.name}</h3>
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-700">
                    {p.status}
                  </span>
                </div>
                <p className="text-sm text-gray-500">{p.typeLine}</p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-4 pb-4 border-b border-gray-100">
              <div>
                <p className="text-[10px] font-semibold tracking-widest text-gray-500 uppercase mb-1">Pick-up SLA</p>
                <p className="text-lg font-black text-gray-900">{p.pickupSla}</p>
              </div>
              <div>
                <p className="text-[10px] font-semibold tracking-widest text-gray-500 uppercase mb-1">YTD routed</p>
                <p className="text-lg font-black text-gray-900">{p.ytdRouted.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-[10px] font-semibold tracking-widest text-gray-500 uppercase mb-1">SLA hit</p>
                <p className={`text-lg font-black ${p.slaHitPercent >= 90 ? 'text-emerald-700' : 'text-orange-600'}`}>
                  {p.slaHitPercent}%
                </p>
              </div>
            </div>

            <div className="flex items-center justify-between flex-wrap gap-2">
              <p className="text-xs text-gray-500">
                {p.email} · {p.phone}
              </p>
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
        ))}
      </div>

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
                <span
                  className={`w-2.5 h-2.5 rounded-full mt-1.5 shrink-0 ${
                    step.tone === 'critical' ? 'bg-red-500' : 'bg-gray-400'
                  }`}
                />
                <p className="text-sm text-gray-800">{step.label}</p>
              </li>
            ))}
          </ul>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-1">Partner onboarding</p>
          <h3 className="text-xl font-black text-gray-900 mb-1">{NGO_PARTNER_ONBOARDING.name}</h3>
          <p className="text-sm text-gray-500 mb-5">{NGO_PARTNER_ONBOARDING.meta}</p>

          <ul className="space-y-4 mb-5">
            {NGO_PARTNER_ONBOARDING.checklist.map((item) => (
              <li key={item.label} className="flex items-start gap-3">
                <span
                  className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                    item.done ? 'bg-emerald-600' : 'bg-gray-200'
                  }`}
                >
                  {item.done && <Check size={11} className="text-white" />}
                </span>
                <div>
                  <p className="font-bold text-gray-900 text-sm">{item.label}</p>
                  <p className="text-xs text-gray-500">{item.meta}</p>
                </div>
              </li>
            ))}
          </ul>

          <button
            type="button"
            onClick={() => navigate(ADMIN_ROUTES.VERIFICATIONS)}
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