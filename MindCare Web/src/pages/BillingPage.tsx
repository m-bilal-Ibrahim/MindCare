// ============================================================
// MindCare — Admin Console: Billing
// ============================================================

import React, { useState } from 'react';
import { BarChart, Bar, ResponsiveContainer, XAxis, Tooltip, PieChart, Pie, Cell } from 'recharts';
import { Download, RefreshCw } from 'lucide-react';
import AdminLayout from '../components/admin/AdminLayout';
import Avatar from '../components/common/Avatar';
import {
  BILLING_STATS,
  REVENUE_MONTHS,
  PAYMENT_METHOD_SHARE,
  RECENT_TRANSACTIONS,
  REFUND_QUEUE,
} from '../constants/adminConsole';

type TxFilter = 'All' | 'Charge' | 'Refund' | 'Payout';
type RevenueRange = '12m' | 'YTD' | 'All';

const TX_STATUS_STYLES: Record<string, string> = {
  Success: 'bg-emerald-100 text-emerald-700',
  Pending: 'bg-amber-100 text-amber-700',
  Failed: 'bg-red-100 text-red-700',
};

const BillingPage: React.FC = () => {
  const [txFilter, setTxFilter] = useState<TxFilter>('All');
  const [range, setRange] = useState<RevenueRange>('12m');
  const s = BILLING_STATS;

  const filteredTx = RECENT_TRANSACTIONS.filter((t) => (txFilter === 'All' ? true : t.type === txFilter));

  return (
    <AdminLayout
      breadcrumb={['Platform', 'Billing']}
      headerAction={
        <div className="flex gap-2 shrink-0">
          <button
            type="button"
            className="inline-flex items-center gap-2 border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 transition-colors"
          >
            <Download size={15} aria-hidden="true" /> Statement
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 transition-colors"
          >
            <RefreshCw size={15} aria-hidden="true" /> Reconcile
          </button>
        </div>
      }
    >
      <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-2">May 2026</p>
      <h1 className="text-5xl font-black text-gray-900 mb-2">
        Money <span className="italic font-serif font-normal">in &amp; out.</span>
      </h1>
      <p className="text-gray-500 mb-8 max-w-2xl">
        {s.grossMrr} MRR this month · {s.therapistPayout} to therapists · {s.refunds} refunds · 99.4% collection rate.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-2">Gross MRR</p>
          <p className="text-3xl font-black text-emerald-700 mb-0.5">
            {s.grossMrr} <span className="text-base font-semibold">{s.grossMrrDelta}</span>
          </p>
          <p className="text-xs text-gray-500">Apr: {s.grossMrrPrevMonth}</p>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-2">Therapist payout</p>
          <p className="text-3xl font-black text-gray-900 mb-0.5">{s.therapistPayout}</p>
          <p className="text-xs text-gray-500">{s.revSharePercent}% rev share</p>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-2">Refunds · May</p>
          <p className="text-3xl font-black text-orange-600 mb-0.5">
            {s.refunds} <span className="text-base font-semibold">{s.refundsDelta}</span>
          </p>
          <p className="text-xs text-gray-500">{s.refundsPercentOfGross}% of gross · ↑ flag</p>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-2">Churn · 30D</p>
          <p className="text-3xl font-black text-gray-900 mb-0.5">
            {s.churn}% <span className="text-base font-semibold text-emerald-700">{s.churnDelta}</span>
          </p>
          <p className="text-xs text-gray-500">trial-to-paid {s.trialToPaidPercent}%</p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-6">
        <div className="xl:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase">Revenue · 12 months</p>
            <div className="flex gap-1">
              {(['12m', 'YTD', 'All'] as RevenueRange[]).map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => setRange(r)}
                  className={`text-xs font-semibold px-3 py-1.5 rounded-full transition-colors ${
                    range === r ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-4">MRR, payouts, refunds</h2>

          <div style={{ height: 220 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={REVENUE_MONTHS} margin={{ top: 4, right: 4, bottom: 0, left: 4 }} barGap={2}>
                <XAxis dataKey="label" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#9ca3af' }} />
                <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid #e5e7eb', fontSize: 12 }} />
                <Bar dataKey="mrr" fill="#166534" radius={[3, 3, 0, 0]} name="Gross MRR" />
                <Bar dataKey="payouts" fill="#1a1a1a" radius={[3, 3, 0, 0]} name="Therapist payouts" />
                <Bar dataKey="refunds" fill="#f97316" radius={[3, 3, 0, 0]} name="Refunds (×10 for scale)" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="flex flex-wrap gap-4 text-xs text-gray-500 mt-3">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-emerald-700" /> Gross MRR
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-gray-900" /> Therapist payouts
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-sm bg-orange-500" /> Refunds (×10 for scale)
            </span>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-1">Payment methods · May</p>
          <h3 className="text-lg font-bold text-gray-900 mb-4">How they paid</h3>

          <div style={{ height: 160 }} className="mb-4">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={PAYMENT_METHOD_SHARE}
                  dataKey="percent"
                  nameKey="label"
                  innerRadius={45}
                  outerRadius={70}
                  paddingAngle={2}
                  isAnimationActive={false}
                >
                  {PAYMENT_METHOD_SHARE.map((entry) => (
                    <Cell key={entry.label} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>

          <ul className="space-y-2">
            {PAYMENT_METHOD_SHARE.map((m) => (
              <li key={m.label} className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2 text-gray-700">
                  <span className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ backgroundColor: m.color }} />
                  {m.label}
                </span>
                <span className="font-bold text-gray-900">{m.percent}%</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-1">
            <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase">Recent transactions</p>
            <div className="flex gap-1">
              {(['All', 'Charge', 'Refund', 'Payout'] as TxFilter[]).map((f) => (
                <button
                  key={f}
                  type="button"
                  onClick={() => setTxFilter(f)}
                  className={`text-xs font-semibold px-3 py-1.5 rounded-full transition-colors ${
                    txFilter === f ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {f === 'All' ? 'All' : `${f}s`}
                </button>
              ))}
            </div>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-4">Last 24 hours</h2>

          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] font-semibold tracking-widest text-gray-400 uppercase border-b border-gray-100">
                <th className="py-2">When</th>
                <th className="py-2">Who</th>
                <th className="py-2">Type</th>
                <th className="py-2">Method</th>
                <th className="py-2">Amount</th>
                <th className="py-2">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredTx.map((t) => (
                <tr key={t.id}>
                  <td className="py-3 text-gray-500">{t.whenLabel}</td>
                  <td className="py-3 font-semibold text-gray-900">{t.who}</td>
                  <td className="py-3 text-gray-700">{t.type}</td>
                  <td className="py-3 text-gray-700">{t.method}</td>
                  <td className="py-3 font-semibold text-gray-900">{t.amount}</td>
                  <td className="py-3">
                    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${TX_STATUS_STYLES[t.status]}`}>
                      {t.status}
                    </span>
                  </td>
                </tr>
              ))}
              {filteredTx.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-gray-400">
                    No transactions of this type in the last 24 hours.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-1">Refund queue</p>
          <h3 className="text-lg font-bold text-gray-900 mb-4">{REFUND_QUEUE.length} awaiting decision</h3>

          <ul className="space-y-4">
            {REFUND_QUEUE.map((r) => (
              <li key={r.id} className="flex items-start gap-3">
                <Avatar initials={r.initials} color={r.avatarColor} size="sm" />
                <div className="flex-1 min-w-0">
                  <p className="font-bold text-gray-900 text-sm">
                    {r.name} · <span className="font-normal text-gray-500">{r.amount}</span>
                  </p>
                  <p className="text-xs text-gray-500">{r.reason}</p>
                  <div className="flex gap-2 mt-2">
                    <button
                      type="button"
                      className="border border-gray-200 bg-white text-gray-700 text-xs font-semibold px-3 py-1.5 rounded-lg hover:border-gray-400"
                    >
                      Deny
                    </button>
                    <button
                      type="button"
                      className="bg-gray-900 text-white text-xs font-semibold px-3 py-1.5 rounded-lg hover:bg-gray-800"
                    >
                      Approve
                    </button>
                  </div>
                </div>
              </li>
            ))}
            {REFUND_QUEUE.length === 0 && <p className="text-sm text-gray-400">No refunds awaiting decision.</p>}
          </ul>
        </div>
      </div>
    </AdminLayout>
  );
};

export default BillingPage;