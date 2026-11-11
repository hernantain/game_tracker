import { useEffect, useMemo, useRef, useState } from 'react';
import { Check, Search } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { useLanguage } from '../i18n/LanguageContext';
import Crest from './Crest';

const MAX_RESULTS = 8;

/** Fold accents so typing "atletico" finds "Atlético Tucumán". */
function norm(s) {
  return (s || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();
}

/**
 * Searchable picker over the 491-row `teams` table. Value is the integer
 * team_id. A plain <select> is unusable at this size, and several clubs share
 * a name stem -- six are called some variant of "Racing" -- so the stadium is
 * shown as a disambiguator.
 */
export default function TeamCombobox({ value, onChange, id = 'team-combobox', disabled }) {
  const { teams } = useAuth();
  const { t } = useLanguage();
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const boxRef = useRef(null);

  const selected = useMemo(
    () => teams.find((x) => x.team_id === Number(value)) || null,
    [teams, value],
  );

  const matches = useMemo(() => {
    const q = norm(query.trim());
    const pool = q ? teams.filter((x) => norm(x.team_name).includes(q)) : teams;
    return pool.slice(0, MAX_RESULTS);
  }, [teams, query]);

  // Collapse when clicking away rather than trapping focus.
  useEffect(() => {
    if (!open) return;
    function onDown(e) {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener('mousedown', onDown);
    return () => document.removeEventListener('mousedown', onDown);
  }, [open]);

  useEffect(() => setHighlight(0), [query]);

  function pick(team) {
    onChange(team.team_id);
    setQuery('');
    setOpen(false);
  }

  function onKeyDown(e) {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (!open) { setOpen(true); return; }
      const dir = e.key === 'ArrowDown' ? 1 : -1;
      setHighlight((h) => (h + dir + matches.length) % Math.max(matches.length, 1));
    } else if (e.key === 'Enter') {
      if (open && matches[highlight]) {
        e.preventDefault();
        pick(matches[highlight]);
      }
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  }

  const unavailable = teams.length === 0;

  return (
    <div ref={boxRef} className="relative">
      <div className="relative">
        <Search
          size={14}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none"
        />
        <input
          id={id}
          type="text"
          role="combobox"
          aria-expanded={open}
          aria-controls={`${id}-listbox`}
          aria-autocomplete="list"
          autoComplete="off"
          disabled={disabled || unavailable}
          value={open ? query : selected?.team_name ?? ''}
          placeholder={unavailable ? t('authTeamsUnavailable') : t('authTeamPlaceholder')}
          onChange={(e) => { setQuery(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
          className="w-full pl-9 pr-3 py-2 rounded-lg bg-surface-2 border border-surface-3 text-sm text-gray-100
                     placeholder:text-gray-600 focus:outline-none focus:border-racing-blue
                     focus:ring-1 focus:ring-racing-blue transition-colors
                     disabled:opacity-60 disabled:cursor-not-allowed"
        />
      </div>

      {open && !unavailable && (
        <ul
          id={`${id}-listbox`}
          role="listbox"
          className="absolute z-10 mt-1 w-full max-h-64 overflow-y-auto rounded-lg
                     bg-surface-1 border border-surface-3 shadow-xl py-1"
        >
          {matches.length === 0 && (
            <li className="px-3 py-2 text-xs text-gray-500">{t('authTeamNoMatch')}</li>
          )}
          {matches.map((team, i) => {
            const isSel = team.team_id === Number(value);
            return (
              <li
                key={team.team_id}
                role="option"
                aria-selected={isSel}
                onMouseEnter={() => setHighlight(i)}
                onMouseDown={(e) => { e.preventDefault(); pick(team); }}
                className={`px-3 py-2 cursor-pointer flex items-center gap-2 ${
                  i === highlight ? 'bg-racing-blue/15' : ''
                }`}
              >
                <Crest espnId={team.espn_team_id} name={team.team_name} size={22} />
                <span className="min-w-0 flex-1">
                  <span className="block text-sm text-gray-100 truncate">{team.team_name}</span>
                  {team.stadium_name && (
                    <span className="block text-[11px] text-gray-600 truncate">
                      {team.stadium_name}
                    </span>
                  )}
                </span>
                {isSel && <Check size={14} className="text-racing-blue shrink-0" />}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
