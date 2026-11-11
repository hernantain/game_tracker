import { useState } from 'react';
import { Link, Navigate, useLocation } from 'react-router-dom';
import GoogleSignInButton from '../components/GoogleSignInButton';
import TeamCombobox from '../components/TeamCombobox';
import { AlertCircle } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { useLanguage } from '../i18n/LanguageContext';

/**
 * Create an account. The club is required: writing the profiles row is what
 * registers the user, and a profiles row is what the sign-in path checks for.
 */
export default function Signup() {
  const { user, loading, signInRejected } = useAuth();
  const { t } = useLanguage();
  const location = useLocation();
  const [teamId, setTeamId] = useState('');

  if (loading) return <div className="text-gray-500 text-sm">{t('loading')}</div>;
  if (user) return <Navigate to={location.state?.from || '/'} replace />;

  return (
    <div className="max-w-sm mx-auto mt-8 lg:mt-20">
      <div className="card space-y-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-racing-blue flex items-center justify-center text-white font-bold">
            R
          </div>
          <div>
            <h1 className="text-lg font-bold text-white leading-tight">{t('authSignUpTitle')}</h1>
            <p className="text-xs text-gray-500">{t('appSubtitle')}</p>
          </div>
        </div>

        {signInRejected ? (
          <div className="flex gap-2.5 rounded-lg bg-racing-blue/10 border border-racing-blue/30 px-3 py-2.5">
            <AlertCircle size={16} className="text-racing-blue shrink-0 mt-0.5" />
            <p className="text-xs text-gray-300 leading-relaxed">
              {signInRejected.email
                ? t('authRejectedWithEmail', { email: signInRejected.email })
                : t('authNoAccountBody')}
            </p>
          </div>
        ) : (
          <p className="text-sm text-gray-400">{t('authSignUpSubtitle')}</p>
        )}

        <div className="space-y-1.5">
          <label htmlFor="favorite-team" className="block text-xs font-medium text-gray-400">
            {t('authFavoriteClubRequired')}
          </label>
          <TeamCombobox id="favorite-team" value={teamId} onChange={setTeamId} />
          <p className="text-[11px] text-gray-600">{t('authFavoriteTeamHint')}</p>
        </div>

        <GoogleSignInButton
          intent="signup"
          returnTo={location.state?.from}
          teamId={teamId}
          disabled={!teamId}
          disabledReason={t('authPickClubFirst')}
        />

        <p className="text-xs text-gray-600">
          {t('authHaveAccount')}{' '}
          <Link to="/login" className="text-racing-blue hover:underline font-medium">
            {t('authGoSignIn')}
          </Link>
        </p>
      </div>
    </div>
  );
}
