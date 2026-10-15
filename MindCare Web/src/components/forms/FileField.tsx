// ============================================================
// MindCare — File upload field for the sign-up forms
// One file (license, degree) or several (other documents). Shows
// the chosen file names with a Remove button; the parent checks
// each file and passes back an error message.
// ============================================================

import React, { useId, useRef } from 'react';
import { FileText, Upload, X } from 'lucide-react';
import { cn } from '../../utils/cn';

interface FileFieldProps {
  label: string;
  required?: boolean;
  hint?: string;
  error?: string;
  accept: string;
  files: File[];
  /** 1 for a single file */
  max?: number;
  onAdd: (files: File[]) => void;
  onRemove: (index: number) => void;
}

const sizeLabel = (bytes: number) =>
  bytes >= 1024 * 1024 ? `${(bytes / (1024 * 1024)).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;

const FileField: React.FC<FileFieldProps> = ({ label, required, hint, error, accept, files, max = 1, onAdd, onRemove }) => {
  const id = useId();
  const noteId = `${id}-note`;
  const inputRef = useRef<HTMLInputElement>(null);
  const canAdd = files.length < max;

  return (
    <div>
      <p id={`${id}-label`} className="block text-xs font-bold text-gray-700 uppercase tracking-wide mb-2">
        {label}
        {required && ' *'}
      </p>

      {files.length > 0 && (
        <ul className="space-y-2 mb-2">
          {files.map((f, i) => (
            <li key={`${f.name}-${i}`} className="flex items-center gap-3 border border-gray-200 bg-white rounded-xl px-4 py-2.5">
              <FileText size={16} className="text-gray-500 shrink-0" aria-hidden="true" />
              <span className="min-w-0 flex-1">
                <span className="block text-sm text-gray-900 truncate">{f.name}</span>
                <span className="block text-xs text-gray-500">{sizeLabel(f.size)}</span>
              </span>
              <button
                type="button"
                onClick={() => onRemove(i)}
                aria-label={`Remove ${f.name}`}
                className="w-8 h-8 rounded-lg text-gray-400 hover:text-gray-900 hover:bg-gray-100 flex items-center justify-center shrink-0"
              >
                <X size={15} />
              </button>
            </li>
          ))}
        </ul>
      )}

      {canAdd && (
        <>
          <input
            ref={inputRef}
            id={id}
            type="file"
            accept={accept}
            multiple={max > 1}
            className="sr-only"
            aria-labelledby={`${id}-label`}
            aria-describedby={error || hint ? noteId : undefined}
            aria-invalid={!!error}
            onChange={(e) => {
              const picked = Array.from(e.target.files ?? []).slice(0, max - files.length);
              e.target.value = ''; // allow picking the same file again after removing it
              if (picked.length) onAdd(picked);
            }}
          />
          <label
            htmlFor={id}
            className={cn(
              'flex items-center justify-center gap-2 w-full border border-dashed rounded-xl px-4 py-3 text-sm font-semibold cursor-pointer transition-colors bg-white',
              error ? 'border-red-300 text-red-700' : 'border-gray-300 text-gray-700 hover:border-gray-900'
            )}
          >
            <Upload size={15} aria-hidden="true" />
            {files.length ? 'Add another file' : 'Choose file'}
          </label>
        </>
      )}

      {error ? (
        <p id={noteId} role="alert" className="text-xs text-red-600 mt-1.5">
          {error}
        </p>
      ) : hint ? (
        <p id={noteId} className="text-xs text-gray-500 mt-1.5">
          {hint}
        </p>
      ) : null}
    </div>
  );
};

export default FileField;
