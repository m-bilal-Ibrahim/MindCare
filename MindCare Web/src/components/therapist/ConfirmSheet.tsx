// ============================================================
// MindCare — Confirm dialog for console actions (accept, decline,
// end relationship). Optional reason picker; a required reason
// keeps the confirm button disabled until one is chosen.
// ============================================================

import React, { useEffect, useState } from 'react';
import Sheet from '../common/Sheet';

interface ReasonOption {
  value: string;
  label: string;
}

interface ConfirmSheetProps {
  open: boolean;
  title: string;
  body: React.ReactNode;
  confirmLabel: string;
  tone?: 'default' | 'danger';
  reasons?: readonly ReasonOption[];
  reasonRequired?: boolean;
  busy?: boolean;
  error?: string | null;
  onConfirm: (reason: string | null) => void;
  onClose: () => void;
}

const ConfirmSheet: React.FC<ConfirmSheetProps> = ({
  open,
  title,
  body,
  confirmLabel,
  tone = 'default',
  reasons,
  reasonRequired,
  busy,
  error,
  onConfirm,
  onClose,
}) => {
  const [reason, setReason] = useState<string | null>(null);
  useEffect(() => {
    if (open) setReason(null);
  }, [open]);

  const blocked = busy || (reasonRequired && !reason);

  return (
    <Sheet open={open} onClose={busy ? () => {} : onClose} labelledBy="confirm-sheet-title">
      <div className="p-6 sm:p-8">
        <h2 id="confirm-sheet-title" className="text-2xl font-black text-gray-900 mb-2 pr-8">
          {title}
        </h2>
        <div className="text-sm text-gray-600 mb-5">{body}</div>

        {reasons && (
          <fieldset className="mb-5">
            <legend className="text-xs font-semibold tracking-widest text-gray-500 uppercase mb-2">
              Reason{reasonRequired ? '' : ' (optional)'}
            </legend>
            <div className="space-y-2">
              {reasons.map((r) => (
                <label
                  key={r.value}
                  className={`flex items-center gap-3 rounded-xl border px-4 py-3 text-sm cursor-pointer transition-colors ${
                    reason === r.value ? 'border-gray-900 bg-white' : 'border-gray-200 bg-white/60 hover:border-gray-400'
                  }`}
                >
                  <input
                    type="radio"
                    name="confirm-reason"
                    value={r.value}
                    checked={reason === r.value}
                    onChange={() => setReason(r.value)}
                    className="accent-gray-900"
                  />
                  {r.label}
                </label>
              ))}
            </div>
          </fieldset>
        )}

        {error && (
          <p role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl px-4 py-3 mb-4">
            {error}
          </p>
        )}

        <div className="flex flex-col-reverse sm:flex-row gap-3 sm:justify-end">
          <button
            type="button"
            onClick={onClose}
            disabled={busy}
            className="border border-gray-200 bg-white text-gray-700 text-sm font-semibold px-5 py-3 rounded-xl hover:border-gray-400 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => onConfirm(reason)}
            disabled={blocked}
            className={`text-sm font-semibold px-5 py-3 rounded-xl text-white transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${
              tone === 'danger' ? 'bg-red-600 hover:bg-red-700' : 'bg-gray-900 hover:bg-gray-800'
            }`}
          >
            {busy ? 'Working…' : confirmLabel}
          </button>
        </div>
      </div>
    </Sheet>
  );
};

export default ConfirmSheet;
