import { useEffect, useMemo, useState } from 'react';
import { Check } from 'lucide-react';
import Crest from './Crest';
import { api, isLegacy } from '../api';
import { useAuth } from '../auth/AuthContext';
import { useLanguage } from '../i18n/LanguageContext';

/**
 * Asks which of the recently played games the user went to.
 *
 * The whole list is answered in one submit rather than one game at a time: a
 * user catching up on a season could face dozens of fixtures, and a request
 * per game would be both slow and tedious. Unticked rows are the "no" answers,
 * which is what lets the server watermark move past them.
 */
export default function AttendancePrompt() {
  const { authorized } = useAuth();
  const { t, lang } = useLanguage();
  const [games, setGames] = useState([]);
  const [selected, setSelected] = useState(() => new Set());
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (isLegacy || !authorized) return;
    let active = true;
    api.attendancePrompts()
      .then((d) => { if (active) setGames(d?.games ?? []); })
      .catch((err) => console.warn('[attendance] could not load prompts:', err?.message || err));
    return () => { active = false; };
  }, [authorized]);

  const dateFmt = useMemo(
    () => new Intl.DateTimeFormat(lang === 'en' ? 'en-GB' : 'es-AR',
      { day: 'numeric', month: 'short', year: 'numeric' }),
    [lang],
  );

  function toggle(gameId) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(gameId) ? next.delete(gameId) : next.add(gameId);
      return next;
    });
  }

  async function submit() {
    setError(null);
    setSaving(true);
    try {
      // Every listed game is answered: ticked = attended, unticked = not.
      await api.answerPrompts(
        games.map((g) => ({ gameId: g.gameId, attended: selected.has(g.gameId) })),
      );
      // Reload so every page recomputes against the new attendance set --
      // the stats are derived server-side and fetched per page on mount.
      window.location.reload();
    } catch (err) {
      setError(err?.message || t('authError'));
      setSaving(false);
    }
  }

  if (isLegacy || !authorized || dismissed || games.length === 0) return null;

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70" />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="attendance-prompt-title"
        className="relative card w-full max-w-md flex flex-col max-h-[80vh] p-0 overflow-hidden"
      >
        {/* Header — fixed */}
        <div className="px-5 pt-5 pb-3 border-b border-surface-3 shrink-0">
          <h2 id="attendance-prompt-title" className="text-base font-bold text-white">
            {t('attendancePromptTitle')}
          </h2>
          <p className="text-xs text-gray-500 mt-0.5">
            {t('attendancePromptSubtitle', { count: games.length })}
          </p>
        </div>

        {/* List — the only part that scrolls */}
        <ul className="flex-1 overflow-y-auto px-3 py-2 space-y-1.5 min-h-0">
          {games.map((g) => {
            const isSel = selected.has(g.gameId);
            const home = g.isHome ? g.teamName : g.rival;
            const away = g.isHome ? g.rival : g.teamName;
            const hs = g.isHome ? g.localScore : g.rivalScore;
            const as = g.isHome ? g.rivalScore : g.localScore;
            const homeEspn = g.isHome ? g.teamEspnId : g.rivalEspnId;
            const awayEspn = g.isHome ? g.rivalEspnId : g.teamEspnId;
            return (
              <li key={g.gameId}>
                <label
                  className={`flex items-start gap-3 p-2.5 rounded-lg cursor-pointer border transition-colors ${
                    isSel
                      ? 'bg-racing-blue/10 border-racing-blue/40'
                      : 'bg-surface-2/50 border-surface-3 hover:bg-surface-2'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isSel}
                    onChange={() => toggle(g.gameId)}
                    className="sr-only"
                  />
                  <span
                    aria-hidden="true"
                    className={`mt-0.5 w-5 h-5 rounded shrink-0 flex items-center justify-center border transition-colors ${
                      isSel
                        ? 'bg-racing-blue border-racing-blue text-white'
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
                    <span className="flex items-center gap-2 mt-1">
                      <span className="flex-1 flex items-center justify-end gap-1.5 min-w-0">
                        <span className="text-xs text-gray-300 truncate">{home}</span>
                        <Crest espnId={homeEspn} name={home} size={20} />
                      </span>
                      <span className="text-sm font-bold text-white tabular-nums shrink-0">
                        {hs}-{as}
                      </span>
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

        {/* Footer — fixed */}
        <div className="px-5 py-4 border-t border-surface-3 shrink-0 space-y-3">
          {error && (
            <p role="alert" className="text-sm text-red-400 bg-red-900/20 border border-red-800/60 rounded-lg px-3 py-2">
              {error}
            </p>
          )}
          <div className="flex items-center justify-between gap-3">
            <span className="text-xs text-gray-500">
              {t('attendanceSelectedCount', { count: selected.size })}
            </span>
            <button
              type="button"
              onClick={submit}
              disabled={saving}
              className="px-4 py-2 rounded-lg bg-racing-blue text-white text-sm font-semibold
                         hover:bg-racing-dark transition-colors disabled:opacity-50"
            >
              {saving ? t('attendanceSaving') : t('attendanceSubmit')}
            </button>
          </div>
          <button
            type="button"
            onClick={() => setDismissed(true)}
            disabled={saving}
            className="w-full text-xs text-gray-600 hover:text-gray-400 transition-colors disabled:opacity-50"
          >
            {t('attendanceLater')}
          </button>
        </div>
      </div>
    </div>
  );
}
