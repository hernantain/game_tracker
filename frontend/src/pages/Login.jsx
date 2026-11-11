import { Link, Navigate, useLocation } from 'react-router-dom';
import GoogleSignInButton from '../components/GoogleSignInButton';
import { useAuth } from '../auth/AuthContext';
import { useLanguage } from '../i18n/LanguageContext';

/** Sign in only. No club field -- a returning user already has one. */
export default function Login() {
  const { user, loading } = useAuth();
  const { t } = useLanguage();
  const location = useLocation();

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
            <h1 className="text-lg font-bold text-white leading-tight">{t('authLoginTitle')}</h1>
            <p className="text-xs text-gray-500">{t('appSubtitle')}</p>
          </div>
        </div>

        <p className="text-sm text-gray-400">{t('authLoginSubtitle')}</p>

        <GoogleSignInButton intent="signin" returnTo={location.state?.from} />

        <p className="text-xs text-gray-600">
          {t('authNoAccount')}{' '}
          <Link to="/signup" className="text-racing-blue hover:underline font-medium">
            {t('authGoSignUp')}
          </Link>
        </p>
      </div>
    </div>
  );
}
