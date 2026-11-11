import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { useLanguage } from '../i18n/LanguageContext';

function GoogleLogo({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#4285F4" d="M45.1 24.5c0-1.6-.1-2.8-.5-4H24v7.6h11.9c-.2 2-1.5 5-4.4 7l-.1.3 6.4 5 .4.1c4.1-3.8 6.9-9.4 6.9-16z" />
      <path fill="#34A853" d="M24 46c5.9 0 10.9-1.9 14.5-5.3l-6.9-5.4c-1.9 1.3-4.4 2.2-7.6 2.2a13 13 0 0 1-12.3-9l-.3.1-6.6 5.1-.1.3C8.1 40.8 15.4 46 24 46z" />
      <path fill="#FBBC05" d="M11.7 28.5A12.8 12.8 0 0 1 11 24c0-1.6.3-3.1.7-4.5v-.3l-6.9-5.3-.2.1A21.9 21.9 0 0 0 2 24c0 3.5.9 6.9 2.6 9.9l7.1-5.4z" />
      <path fill="#EA4335" d="M24 11.1c4.2 0 7 1.8 8.6 3.3l6.3-6.1C35 4.8 30 2.7 24 2.7 15.4 2.7 8.1 7.9 4.6 14.2l7.1 5.3A13 13 0 0 1 24 11.1z" />
    </svg>
  );
}

/**
 * Kicks off the Supabase Google OAuth redirect. Google accounts that have never
 * signed in before are created on the fly, so this is both "register" and "login".
 */
export default function GoogleSignInButton({
  returnTo,
  teamId,
  intent = 'signin',
  disabled = false,
  disabledReason,
}) {
  const { signInWithGoogle, isConfigured } = useAuth();
  const { t } = useLanguage();
  const location = useLocation();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState(null);

  const destination = returnTo ?? location.pathname + location.search;

  async function handleClick() {
    setError(null);
    setPending(true);
    try {
      await signInWithGoogle({ intent, returnTo: destination, teamId });
      // On success the browser navigates to Google; `pending` stays true.
    } catch (err) {
      setError(err?.message || t('authError'));
      setPending(false);
    }
  }

  if (!isConfigured) {
    return (
      <p className="text-sm text-yellow-500/90 bg-yellow-900/20 border border-yellow-800/60 rounded-lg px-3 py-2">
        {t('authNotConfigured')}
      </p>
    );
  }

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={handleClick}
        disabled={pending || disabled}
        className="w-full flex items-center justify-center gap-3 px-4 py-2.5 rounded-lg bg-white text-gray-800 text-sm font-semibold
                   hover:bg-gray-100 transition-colors duration-150 disabled:opacity-60 disabled:cursor-not-allowed
                   focus:outline-none focus:ring-2 focus:ring-racing-blue focus:ring-offset-2 focus:ring-offset-surface-1"
      >
        <GoogleLogo />
        {pending
          ? t('authSigningIn')
          : intent === 'signup'
            ? t('authSignUpWithGoogle')
            : t('authSignInWithGoogle')}
      </button>
      {disabled && disabledReason && !error && (
        <p className="text-[11px] text-gray-600">{disabledReason}</p>
      )}
      {error && (
        <p role="alert" className="text-sm text-red-400 bg-red-900/20 border border-red-800/60 rounded-lg px-3 py-2">
          {error}
        </p>
      )}
    </div>
  );
}
