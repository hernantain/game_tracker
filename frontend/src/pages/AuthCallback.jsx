import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { takeReturnTo, useAuth } from '../auth/AuthContext';
import { useLanguage } from '../i18n/LanguageContext';

/**
 * Landing route for the Supabase OAuth redirect. The client exchanges the
 * ?code= during its own initialization (detectSessionInUrl), so this page
 * waits for the session to settle, then either bounces the user onward or
 * reports that the account is not registered.
 */
export default function AuthCallback() {
  const { user, loading, profileLoading, signInRejected } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  // Google reports a denied consent screen as ?error= / #error=.
  const providerError = useMemo(() => {
    const search = new URLSearchParams(window.location.search);
    const hash = new URLSearchParams(window.location.hash.replace(/^#/, ''));
    const code = search.get('error') || hash.get('error');
    if (!code) return null;
    return search.get('error_description') || hash.get('error_description') || code;
  }, []);

  const [timedOut, setTimedOut] = useState(false);

  useEffect(() => {
    if (providerError) return;
    const timer = setTimeout(() => setTimedOut(true), 10000);
    return () => clearTimeout(timer);
  }, [providerError]);

  useEffect(() => {
    if (providerError || signInRejected || loading || profileLoading || !user) return;
    navigate(takeReturnTo(), { replace: true });
  }, [providerError, signInRejected, loading, profileLoading, user, navigate]);


  // An unrecognised account never gets here: App routes it to NotRecognized.
  const failure = providerError || (timedOut && !user ? t('authError') : null);

  if (failure) {
    return (
      <div className="max-w-sm mx-auto mt-8 lg:mt-20">
        <div className="card space-y-4">
          <h1 className="text-lg font-bold text-white">{t('authError')}</h1>
          <p role="alert" className="text-sm text-red-400 bg-red-900/20 border border-red-800/60 rounded-lg px-3 py-2">
            {failure}
          </p>
          <div className="flex gap-3">
            <Link to="/login" className="tab-btn active">{t('authRetry')}</Link>
            <Link to="/" className="tab-btn">{t('authBackToDashboard')}</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-sm mx-auto mt-8 lg:mt-20">
      <div className="card text-sm text-gray-400">{t('authCallbackLoading')}</div>
    </div>
  );
}
