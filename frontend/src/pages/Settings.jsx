import { useEffect, useMemo, useState } from 'react';
import { Check, Search } from 'lucide-react';
import Crest from '../components/Crest';
import { api } from '../api';
import { useAuth } from '../auth/AuthContext';
import { useLanguage } from '../i18n/LanguageContext';

/**
 * Attendance history for the user's club: every game it has played, each
 * ticked or not.
 *
 * Saves through PUT /api/attendances, which does not move the prompt
 * watermark -- correcting old games must not silently dismiss questions about
 * recent ones. Only changed rows are sent, so a one-game correction is a
 * one-item request rather than 673.
 */
export default function Settings() {
  const { favoriteTeam } = useAuth();
  const { t, lang } = useLanguage();
  const [games, setGames] = useState(null);
  const [attended, setAttended] = useState(() => new Set());
  const [original, setOriginal] = useState(() => new Set());
  const [year, setYear] = useState('');
  const [search, setSearch] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    api.clubGames()
      .then((rows) => {
        if (!active) return;
        const set = new Set(rows.filter((g) => g.attended).map((g) => g.gameId));
        setGames(rows);
        setAttended(new Set(set));
        setOriginal(set);
      })
      .catch((err) => { if (active) setError(err?.message || t('failedToLoad')); });
    return () => { active = false; };
  }, [t]);

  const dateFmt = useMemo(
    () => new Intl.DateTimeFormat(lang === 'en' ? 'en-GB' : 'es-AR',
      { day: '2-digit', month: 'short', year: 'numeric' }),
    [lang],
  );

  const years = useMemo(
    () => [...new Set((games ?? []).map((g) => g.date.slice(0, 4)))].sort().reverse(),
    [games],
  );

  const visible = useMemo(() => {
    let rows = games ?? [];
    if (year) rows = rows.filter((g) => g.date.startsWith(year));
    if (search) {
      const q = search.toLowerCase();
      rows = rows.filter((g) => g.rival.toLowerCase().includes(q));
    }
    return rows;
  }, [games, year, search]);

  // Only what actually changed, so a small correction stays a small request.
  const changed = useMemo(() => {
    const out = [];
    for (const g of games ?? []) {
      const now = attended.has(g.gameId);
      if (now !== original.has(g.gameId)) out.push({ gameId: g.gameId, attended: now });
    }
    return out;
  }, [games, attended, original]);

  function toggle(gameId) {
    setAttended((prev) => {
      const next = new Set(prev);
      next.has(gameId) ? next.delete(gameId) : next.add(gameId);
      return next;
    });
  }

  async function save() {
    setError(null);
    setSaving(true);
    try {
      await api.setAttendances(changed);
      // Reload so every page recomputes against the new attendance set.
      window.location.reload();
    } catch (err) {
      setError(err?.message || t('authError'));
      setSaving(false);
    }
  }

  if (games === null && !error) {
    return <div className="text-gray-500 text-sm">{t('loading')}</div>;
  }

  return (
    <div className="space-y-5 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-white">{t('settingsTitle')}</h1>
        <p className="text-gray-500 text-sm mt-0.5">
          {t('settingsSubtitle', {
            club: favoriteTeam?.team_name || '—',
            count: games?.length ?? 0,
          })}
        </p>
      </div>

      {error && (
        <p role="alert" className="text-sm text-red-400 bg-red-900/20 border border-red-800/60 rounded-lg px-3 py-2">
          {error}
        </p>
      )}

      <div className="card space-y-3">
        {/* Filters */}
        <div className="flex flex-wrap gap-2">
          <div className="relative flex-1 min-w-[180px]">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={t('filterOpponent')}
              className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-surface-2 border border-surface-3 text-sm
                         text-gray-100 placeholder:text-gray-600 focus:outline-none focus:border-racing-blue"
            />
          </div>
          <select
            value={year}
            onChange={(e) => setYear(e.target.value)}
            className="bg-surface-2 border border-surface-3 rounded-lg px-3 py-1.5 text-sm text-gray-300
                       focus:outline-none focus:border-racing-blue"
          >
            <option value="">{t('allYears')}</option>
            {years.map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>

        {/* Fixed-height scrolling list */}
        <ul className="h-[55vh] overflow-y-auto space-y-1.5 pr-1">
          {visible.length === 0 && (
            <li className="text-center text-gray-500 py-10 text-sm">{t('noMatchesFound')}</li>
          )}
          {visible.map((g) => {
            const isSel = attended.has(g.gameId);
            const home = g.isHome ? favoriteTeam?.team_name || t('settingsYourClub') : g.rival;
            const away = g.isHome ? g.rival : favoriteTeam?.team_name || t('settingsYourClub');
            const hs = g.isHome ? g.localScore : g.rivalScore;
            const as = g.isHome ? g.rivalScore : g.localScore;
            const homeEspn = g.isHome ? favoriteTeam?.espnTeamId : g.opponentEspnId;
            const awayEspn = g.isHome ? g.opponentEspnId : favoriteTeam?.espnTeamId;
            return (
              <li key={g.gameId}>
                <label
                  className={`flex items-center gap-3 p-2.5 rounded-lg cursor-pointer border transition-colors ${
                    isSel ? 'bg-racing-blue/10 border-racing-blue/40'
                          : 'bg-surface-2/40 border-surface-3 hover:bg-surface-2'
                  }`}
                >
                  <input type="checkbox" checked={isSel} onChange={() => toggle(g.gameId)} className="sr-only" />
                  <span
                    aria-hidden="true"
                    className={`w-5 h-5 rounded shrink-0 flex items-center justify-center border transition-colors ${
                      isSel ? 'bg-racing-blue border-racing-blue text-white'
                            : 'border-surface-3 text-transparent'
                    }`}
                  >
                    <Check size={13} />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="flex items-baseline justify-between gap-2">
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-racing-blue truncate">
                        {g.competition || t('attendanceUnknownCompetition')}
                      </span>
                      <span className="text-[10px] text-gray-600 shrink-0">
                        {dateFmt.format(new Date(`${g.date}T12:00:00`))}
                      </span>
                    </span>
                    <span className="flex items-center gap-2 mt-0.5">
                      <span className="flex-1 flex items-center justify-end gap-1.5 min-w-0">
                        <span className="text-xs text-gray-300 truncate">{home}</span>
                        <Crest espnId={homeEspn} name={home} size={20} />
                      </span>
                      <span className="text-sm font-bold text-white tabular-nums shrink-0">{hs}-{as}</span>
                      <span className="flex-1 flex items-center gap-1.5 min-w-0">
                        <Crest espnId={awayEspn} name={away} size={20} />
                        <span className="text-xs text-gray-300 truncate">{away}</span>
                      </span>
                    </span>
                  </span>
                </label>
              </li>
            );
          })}
        </ul>

        {/* Footer */}
        <div className="flex items-center justify-between gap-3 pt-1 border-t border-surface-3">
          <span className="text-xs text-gray-500 pt-3">
            {t('settingsAttendedCount', { count: attended.size })}
            {changed.length > 0 && ` · ${t('settingsChangedCount', { count: changed.length })}`}
          </span>
          <button
            type="button"
            onClick={save}
            disabled={saving || changed.length === 0}
            className="mt-3 px-4 py-2 rounded-lg bg-racing-blue text-white text-sm font-semibold
                       hover:bg-racing-dark transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {saving ? t('attendanceSaving') : t('settingsSave')}
          </button>
        </div>
      </div>
    </div>
  );
}
