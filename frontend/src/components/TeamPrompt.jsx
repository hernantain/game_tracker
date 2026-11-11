import { useState } from 'react';
import { useAuth } from '../auth/AuthContext';
import { useLanguage } from '../i18n/LanguageContext';
import TeamCombobox from './TeamCombobox';

/**
 * One-time prompt for users who reached the app without a favourite team —
 * they skipped the field on the login screen, or their account predates it.
 * Google OAuth gives no sign-up hook, so this null check is the real signal.
 */
export default function TeamPrompt() {
  const { needsTeam, setFavoriteTeam, dismissTeamPrompt } = useAuth();
  const { t } = useLanguage();
  const [teamId, setTeamId] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  if (!needsTeam) return null;

  async function handleSave() {
    if (!teamId) return;
    setError(null);
    setSaving(true);
    try {
      await setFavoriteTeam(teamId);
    } catch (err) {
      setError(err?.message || t('authError'));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70" />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="team-prompt-title"
        className="relative card w-full max-w-sm space-y-4"
      >
        <h2 id="team-prompt-title" className="text-base font-bold text-white">
          {t('authTeamPromptTitle')}
        </h2>
        <p className="text-sm text-gray-400">{t('authTeamPromptBody')}</p>

        <TeamCombobox value={teamId} onChange={setTeamId} id="team-prompt-select" disabled={saving} />

        {error && (
          <p role="alert" className="text-sm text-red-400 bg-red-900/20 border border-red-800/60 rounded-lg px-3 py-2">
            {error}
          </p>
        )}

        <div className="flex items-center justify-between gap-3 pt-1">
          <button
            type="button"
            onClick={dismissTeamPrompt}
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            {t('authTeamPromptLater')}
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={!teamId || saving}
            className="px-4 py-2 rounded-lg bg-racing-blue text-white text-sm font-semibold
                       hover:bg-racing-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? t('loading') : t('authTeamPromptSave')}
          </button>
        </div>
      </div>
    </div>
  );
}
