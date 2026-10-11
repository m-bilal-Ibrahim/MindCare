// ============================================================
// MindCare — City field with live suggestions
// Suggests verified cities for the chosen country from
// GET /reference/cities/ as the user types, but still accepts any
// name: the register API takes a city *name*, matches it to an
// existing city, or saves a new one for an admin to verify.
// ============================================================

import React, { useEffect, useId, useRef, useState } from 'react';
import { Loader2, MapPin } from 'lucide-react';
import { Field } from './Fields';
import { searchCities, type CityOption } from '../../services/api.service';
import { cn } from '../../utils/cn';

const DEBOUNCE_MS = 250;

interface CityFieldProps {
  label: string;
  /** ISO country code the cities belong to; no suggestions without it. */
  country: string;
  value: string;
  onValue: (v: string) => void;
  error?: string;
  hint?: string;
  required?: boolean;
  placeholder?: string;
  maxLength?: number;
  fieldClassName?: string;
}

const CityField: React.FC<CityFieldProps> = ({
  label,
  country,
  value,
  onValue,
  error,
  hint = 'Start typing to pick from the list. Not listed? Type the full name and we’ll add it.',
  required,
  placeholder,
  maxLength,
  fieldClassName,
}) => {
  const listId = useId();
  const [open, setOpen] = useState(false);
  const [options, setOptions] = useState<CityOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [active, setActive] = useState(-1);
  const requestRef = useRef(0);

  // Fetch suggestions (debounced) while the list is open.
  useEffect(() => {
    if (!open || !country) return;
    const request = ++requestRef.current;
    setLoading(true);
    const t = window.setTimeout(async () => {
      const rows = await searchCities(country, value);
      if (request !== requestRef.current) return; // a newer keystroke won
      setOptions(rows ?? []);
      setActive(-1);
      setLoading(false);
    }, DEBOUNCE_MS);
    return () => window.clearTimeout(t);
  }, [open, country, value]);

  const exact = options.some((o) => o.name.toLowerCase() === value.trim().toLowerCase());
  const showList = open && !!country && (loading || options.length > 0 || value.trim().length > 0);

  const pick = (name: string) => {
    onValue(name);
    setOpen(false);
    setActive(-1);
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setOpen(true);
      setActive((i) => Math.min(i + 1, options.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive((i) => Math.max(i - 1, -1));
    } else if (e.key === 'Enter' && open && active >= 0 && options[active]) {
      e.preventDefault(); // pick the highlighted city instead of submitting the form
      pick(options[active].name);
    } else if (e.key === 'Escape' && open) {
      e.preventDefault();
      setOpen(false);
    }
  };

  return (
    <Field label={label} error={error} hint={country ? hint : 'Choose a country first.'} required={required} className={fieldClassName}>
      {(p) => (
        <div className="relative">
          <input
            {...p}
            type="text"
            role="combobox"
            aria-autocomplete="list"
            aria-expanded={showList}
            aria-controls={listId}
            aria-activedescendant={active >= 0 ? `${listId}-${active}` : undefined}
            autoComplete="off"
            value={value}
            maxLength={maxLength}
            placeholder={placeholder}
            disabled={!country}
            onChange={(e) => {
              onValue(e.target.value);
              setOpen(true);
            }}
            onFocus={() => setOpen(true)}
            onBlur={() => window.setTimeout(() => setOpen(false), 120)} // let a click on an option land first
            onKeyDown={onKeyDown}
            className={cn(p.className, 'pr-10 disabled:bg-gray-50 disabled:text-gray-400')}
          />
          <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" aria-hidden="true">
            {loading ? <Loader2 size={16} className="animate-spin" /> : <MapPin size={16} />}
          </span>

          {showList && (
            <ul
              id={listId}
              role="listbox"
              aria-label={`${label} suggestions`}
              className="absolute z-20 mt-1 w-full max-h-64 overflow-y-auto bg-white border border-gray-200 rounded-xl shadow-lg py-1"
            >
              {options.map((o, i) => (
                <li
                  key={o.id}
                  id={`${listId}-${i}`}
                  role="option"
                  aria-selected={i === active}
                  onMouseDown={(e) => e.preventDefault()} // keep focus in the input
                  onClick={() => pick(o.name)}
                  onMouseEnter={() => setActive(i)}
                  className={cn('px-4 py-2.5 text-sm cursor-pointer', i === active ? 'bg-gray-100 text-gray-900' : 'text-gray-700')}
                >
                  {o.name}
                </li>
              ))}
              {!loading && value.trim().length >= 3 && !exact && (
                <li role="presentation" className="px-4 py-2.5 text-xs text-gray-500 border-t border-gray-100">
                  {options.length ? 'Or keep' : 'No match in our list — we’ll add'} “{value.trim()}” as a new city.
                </li>
              )}
              {loading && options.length === 0 && (
                <li role="presentation" className="px-4 py-2.5 text-sm text-gray-500">
                  Searching…
                </li>
              )}
            </ul>
          )}
        </div>
      )}
    </Field>
  );
};

export default CityField;
