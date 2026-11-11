import { Link } from 'react-router-dom';
import { ShieldAlert } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { useLanguage } from '../i18n/LanguageContext';

/**
 * Shown when a Google account authenticated successfully but is not
 * registered with this app -- there is no profiles row for it.
 *
 * Reached on any session that fails the registration invariant, not only at
 * the OAuth callback, so a refresh cannot get past it.
 */
export default function NotRecognized() {
  const { signInRejected, clearSignInRejected } = useAuth();
  const { t } = useLanguage();
  const email = signInRejected?.email;

  return (
    <div className="max-w-sm mx-auto mt-8 lg:mt-20">
      <div className="card space-y-5">
        <div className="flex items-center gap-3">
          <span className="p-2.5 rounded-xl bg-red-900/30 text-red-400 shrink-0">
            <ShieldAlert size={20} />
          </span>
          <div className="min-w-0">
            <h1 className="text-lg font-bold text-white leading-tight">
              {t('authNotRecognizedTitle')}
            </h1>
            {email && (
              <p className="text-xs text-gray-500 truncate" title={email}>{email}</p>
            )}
          </div>
        </div>

        <p className="text-sm text-gray-400">{t('authNotRecognizedBody')}</p>

        <div className="flex flex-col gap-2">
          {/* No clearSignInRejected here: the sign-up screen reuses it to name
              the account that bounced. */}
          <Link
            to="/signup"
            className="w-full text-center px-4 py-2.5 rounded-lg bg-racing-blue text-white
                       text-sm font-semibold hover:bg-racing-dark transition-colors"
          >
            {t('authGoSignUp')}
          </Link>
          <Link
            to="/login"
            onClick={clearSignInRejected}
            className="w-full text-center px-4 py-2 rounded-lg border border-surface-3
                       text-sm text-gray-400 hover:text-gray-200 hover:bg-surface-2 transition-colors"
          >
            {t('authTryAnotherAccount')}
          </Link>
        </div>
      </div>
    </div>
  );
}
