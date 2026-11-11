import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { LogIn, LogOut } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { useLanguage } from '../i18n/LanguageContext';
import Crest from './Crest';

function Avatar({ user }) {
  const url = user.user_metadata?.avatar_url;
  const label = user.user_metadata?.full_name || user.email || '?';

  if (url) {
    return (
      <img
        src={url}
        alt=""
        referrerPolicy="no-referrer"
        className="w-8 h-8 rounded-full shrink-0 object-cover bg-surface-2"
      />
    );
  }
  return (
    <div className="w-8 h-8 rounded-full shrink-0 bg-racing-blue/20 text-racing-blue flex items-center justify-center text-xs font-bold uppercase">
      {label.charAt(0)}
    </div>
  );
}

export default function UserMenu({ onNavigate }) {
  const { user, loading, isConfigured, signOut, favoriteTeam } = useAuth();
  const { t } = useLanguage();
  const [pending, setPending] = useState(false);

  if (!isConfigured) return null;

  if (loading) {
    return <div className="h-8 rounded-lg bg-surface-2 animate-pulse" />;
  }

  if (!user) {
    return (
      <NavLink
        to="/login"
        onClick={onNavigate}
        className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-400
                   hover:text-gray-200 hover:bg-surface-2 transition-colors duration-150"
      >
        <LogIn size={18} />
        {t('authSignIn')}
      </NavLink>
    );
  }

  const name = user.user_metadata?.full_name || user.email;

  async function handleSignOut() {
    setPending(true);
    try {
      await signOut();
      onNavigate?.();
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="flex items-center gap-2 min-w-0">
      <Avatar user={user} />
      <div className="min-w-0 flex-1">
        <div className="text-xs font-medium text-gray-200 truncate" title={name}>{name}</div>
        <div className="flex items-center gap-1 text-[11px] text-gray-600 min-w-0"
             title={favoriteTeam?.team_name || undefined}>
          {favoriteTeam && (
            <Crest espnId={favoriteTeam.espn_team_id} name={favoriteTeam.team_name} size={13} />
          )}
          <span className="truncate">{favoriteTeam?.team_name || t('authAccount')}</span>
        </div>
      </div>
      <button
        type="button"
        onClick={handleSignOut}
        disabled={pending}
        title={t('authSignOut')}
        aria-label={t('authSignOut')}
        className="p-1.5 rounded-lg text-gray-500 hover:text-gray-200 hover:bg-surface-2
                   transition-colors duration-150 disabled:opacity-50"
      >
        <LogOut size={16} />
      </button>
    </div>
  );
}
