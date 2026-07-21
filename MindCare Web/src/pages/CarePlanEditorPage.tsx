// ============================================================
// MindCare — Therapist Console: Care Plan Editor
// ============================================================

import React, { useState } from 'react';
import { Eye, Send, History, GitCompare, Pencil, Trash2, Plus, AlertTriangle } from 'lucide-react';
import TherapistLayout from '../components/therapist/TherapistLayout';
import Avatar from '../components/common/Avatar';
import {
  LAYLA_CARE_PLAN,
  EXERCISE_LIBRARY,
  CARE_PLAN_CATEGORY_STYLES,
} from '../constants/therapistConsole';
import { sanitizeText, MAX_LENGTHS } from '../utils/validation';
import type { CarePlanCategory } from '../types/therapistConsole';

type LibraryFilter = 'All' | CarePlanCategory;
type PlanTab = 'This week' | 'Permanent' | 'Archive';

const CATEGORY_FILTERS: LibraryFilter[] = ['All', 'Breath', 'Body', 'Thinking', 'Reflect', 'Diet', 'Sleep', 'Motivation'];

const CarePlanEditorPage: React.FC = () => {
  const plan = LAYLA_CARE_PLAN;
  const [planTab, setPlanTab] = useState<PlanTab>('This week');
  const [libraryFilter, setLibraryFilter] = useState<LibraryFilter>('All');
  const [librarySearch, setLibrarySearch] = useState('');
  const [blocks, setBlocks] = useState(plan.blocks);

  const filteredLibrary = EXERCISE_LIBRARY.filter((ex) => {
    if (libraryFilter !== 'All' && ex.category !== libraryFilter) return false;
    const query = sanitizeText(librarySearch).toLowerCase();
    if (query && !ex.title.toLowerCase().includes(query)) return false;
    return true;
  });

  const handleApprove = (id: string) => {
    // TODO: real API call to approve Aida-proposed block into the active plan.
    setBlocks((prev) => prev.map((b) => (b.id === id ? { ...b, pending: false, totalCount: 1, doneCount: 0 } : b)));
  };

  const handleDismiss = (id: string) => {
    setBlocks((prev) => prev.filter((b) => b.id !== id));
  };

  const handleRemoveBlock = (id: string) => {
    setBlocks((prev) => prev.filter((b) => b.id !== id));
  };

  return (
    <TherapistLayout
      breadcrumb={['Care', 'Care plans', plan.patientName]}
      headerAction={
        <div className="flex gap-2 shrink-0">
          <button
            type="button"
            className="inline-flex items-center gap-2 border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-4 py-2.5 rounded-xl hover:border-gray-400 transition-colors"
          >
            <Eye size={15} aria-hidden="true" /> Preview as {plan.patientName.split(' ')[0]}
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-2 bg-gray-900 text-white text-sm font-semibold px-4 py-2.5 rounded-xl hover:bg-gray-800 transition-colors"
          >
            <Send size={15} aria-hidden="true" /> Push update to {plan.patientName.split(' ')[0]}
          </button>
        </div>
      }
    >
      <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6 mb-8">
        <div className="flex items-start gap-5">
          <Avatar initials={plan.patientInitials} color={plan.avatarColor} />
          <div>
            <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-1">
              Care plan · {plan.weekLabel} · Next review {plan.nextReview}
            </p>
            <h1 className="text-4xl font-black text-gray-900 mb-2">
              {plan.patientName.split(' ')[0]}&apos;s <span className="italic font-serif font-normal">weekly program</span>
            </h1>
            <p className="text-sm text-gray-500">
              {plan.completedCount} of {plan.totalCount} completed this week · Compliance {plan.compliancePercent}% ·
              Last updated {plan.lastUpdated} · {plan.pendingFromAida} pending from Aida
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs font-semibold text-gray-500 bg-gray-100 px-3 py-1.5 rounded-full">{plan.version}</span>
          <button
            type="button"
            className="inline-flex items-center gap-1.5 border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-3 py-2 rounded-xl hover:border-gray-400"
          >
            <History size={14} aria-hidden="true" /> History
          </button>
          <button
            type="button"
            className="inline-flex items-center gap-1.5 border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-3 py-2 rounded-xl hover:border-gray-400"
          >
            <GitCompare size={14} aria-hidden="true" /> Compare to last week
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Plan blocks */}
        <div className="xl:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-gray-900">
              This week&apos;s program · <span className="text-gray-400 font-normal">{blocks.length} blocks</span>
            </h2>
            <div className="flex gap-1">
              {(['This week', 'Permanent', 'Archive'] as PlanTab[]).map((t) => (
                <button
                  key={t}
                  type="button"
                  onClick={() => setPlanTab(t)}
                  className={`text-sm font-semibold px-3 py-1.5 rounded-full transition-colors ${
                    planTab === t ? 'bg-gray-900 text-white' : 'bg-white border border-gray-200 text-gray-600 hover:border-gray-400'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {planTab !== 'This week' ? (
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center text-gray-400">
              Nothing here yet in this demo.
            </div>
          ) : (
            <div className="space-y-4">
              {blocks.map((block) => {
                const style = CARE_PLAN_CATEGORY_STYLES[block.category];
                return (
                  <div
                    key={block.id}
                    className={`bg-white rounded-2xl shadow-sm border p-5 flex items-center gap-4 ${
                      block.pending ? 'border-orange-300' : 'border-gray-100'
                    }`}
                  >
                    <span className="text-gray-300 cursor-grab select-none" aria-hidden="true">
                      ⠿
                    </span>
                    <span className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${style.bg} ${style.text}`}>
                      {block.category === 'Breath' && '〜'}
                      {block.category === 'Body' && '♥'}
                      {block.category === 'Thinking' && '{ }'}
                      {block.category === 'Reflect' && '✎'}
                      {!['Breath', 'Body', 'Thinking', 'Reflect'].includes(block.category) && '•'}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className={`text-[11px] font-semibold tracking-widest uppercase mb-0.5 ${style.text}`}>
                        {block.category}
                      </p>
                      <p className="font-bold text-gray-900">{block.title}</p>
                      <p className="text-xs text-gray-500">
                        {block.cadence} · added by {block.addedBy} · {block.addedDate}
                      </p>
                    </div>

                    {block.pending ? (
                      <div className="flex items-center gap-2 shrink-0">
                        <span className="text-xs font-semibold text-orange-700 bg-orange-100 px-2.5 py-1 rounded-full">
                          Awaiting your approval
                        </span>
                        <button
                          type="button"
                          onClick={() => handleDismiss(block.id)}
                          className="border border-gray-200 text-gray-700 text-sm font-semibold px-3 py-2 rounded-xl hover:border-gray-400"
                        >
                          Amend
                        </button>
                        <button
                          type="button"
                          onClick={() => handleApprove(block.id)}
                          className="bg-gray-900 text-white text-sm font-semibold px-3 py-2 rounded-xl hover:bg-gray-800"
                        >
                          Approve
                        </button>
                      </div>
                    ) : (
                      <>
                        <div className="w-32 shrink-0">
                          <p className="text-sm text-gray-700 mb-1">
                            {block.doneCount}/{block.totalCount} done
                          </p>
                          <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${block.lowCompliance ? 'bg-red-400' : 'bg-emerald-600'}`}
                              style={{ width: `${block.totalCount ? (block.doneCount / block.totalCount) * 100 : 0}%` }}
                            />
                          </div>
                          {block.lowCompliance && (
                            <p className="text-[11px] text-red-600 font-semibold mt-1 flex items-center gap-1">
                              <AlertTriangle size={11} aria-hidden="true" /> low compliance
                            </p>
                          )}
                        </div>
                        <button
                          type="button"
                          aria-label={`Edit ${block.title}`}
                          className="w-9 h-9 rounded-lg border border-gray-200 flex items-center justify-center text-gray-500 hover:border-gray-400 shrink-0"
                        >
                          <Pencil size={14} />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleRemoveBlock(block.id)}
                          aria-label={`Remove ${block.title}`}
                          className="w-9 h-9 rounded-lg border border-red-200 flex items-center justify-center text-red-500 hover:bg-red-50 shrink-0"
                        >
                          <Trash2 size={14} />
                        </button>
                      </>
                    )}
                  </div>
                );
              })}

              <div className="border-2 border-dashed border-gray-200 rounded-2xl p-6 text-center text-sm text-gray-500">
                Drag from the library, or{' '}
                <button type="button" className="underline underline-offset-2 font-semibold text-gray-800">
                  Ask Aida to suggest a block
                </button>
              </div>

              <div className="bg-[#EFE9DF] rounded-2xl p-5">
                <p className="text-[11px] font-semibold tracking-widest text-gray-500 uppercase mb-2">
                  Quick-relief from Aida · Temporary
                </p>
                <p className="text-sm text-gray-700 leading-relaxed">{plan.quickReliefNote}</p>
              </div>
            </div>
          )}
        </div>

        {/* Exercise library */}
        <aside className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 h-fit">
          <p className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-3">Exercise library</p>
          <input
            type="search"
            value={librarySearch}
            onChange={(e) => setLibrarySearch(e.target.value.slice(0, MAX_LENGTHS.shortText))}
            maxLength={MAX_LENGTHS.shortText}
            placeholder="Search exercises…"
            className="w-full px-3.5 py-2.5 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-gray-900 bg-gray-50 mb-3"
          />
          <div className="flex flex-wrap gap-1.5 mb-4">
            {CATEGORY_FILTERS.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setLibraryFilter(cat)}
                className={`text-xs font-semibold px-3 py-1.5 rounded-full transition-colors ${
                  libraryFilter === cat ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          <div className="space-y-2 max-h-[600px] overflow-y-auto">
            {filteredLibrary.map((ex) => {
              const style = CARE_PLAN_CATEGORY_STYLES[ex.category];
              return (
                <div key={ex.id} className="flex items-center gap-3 border border-gray-100 rounded-xl p-3">
                  <span className="text-gray-300 cursor-grab select-none" aria-hidden="true">
                    ⠿
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className={`text-[10px] font-semibold tracking-widest uppercase ${style.text}`}>{ex.category}</p>
                    <p className="text-sm font-bold text-gray-900 truncate">{ex.title}</p>
                    <p className="text-xs text-gray-500">{ex.meta}</p>
                  </div>
                  <button
                    type="button"
                    aria-label={`Add ${ex.title} to plan`}
                    className="w-8 h-8 rounded-lg border border-gray-200 flex items-center justify-center text-gray-500 hover:border-gray-900 hover:text-gray-900 shrink-0"
                  >
                    <Plus size={14} />
                  </button>
                </div>
              );
            })}
            {filteredLibrary.length === 0 && (
              <p className="text-sm text-gray-400 text-center py-6">No exercises match your search.</p>
            )}
          </div>
        </aside>
      </div>
    </TherapistLayout>
  );
};

export default CarePlanEditorPage;