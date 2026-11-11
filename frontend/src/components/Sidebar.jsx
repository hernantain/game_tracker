import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Trophy, Calendar, Users, Swords, Menu, X, Settings } from 'lucide-react';
import { useLanguage } from '../i18n/LanguageContext';
import { useAuth } from '../auth/AuthContext';
import Crest from './Crest';
import UserMenu from './UserMenu';

/**
 * The app's masthead: the signed-in user's club, not a hardcoded one.
 *
 * Falls back to Racing Club when there is no club to show -- legacy mode has
 * no user at all, and the profile has not loaded on the first paint. The
 * fallback badge keeps the brand blue rather than the neutral grey used
 * elsewhere, since this is the app's own identity.
 */
function ClubHeader({ size = 36, subtitle = true }) {
  const { t } = useLanguage();
  const { favoriteTeam } = useAuth();
  const name = favoriteTeam?.team_name || 'Racing Club';
  return (
    <div className="flex items-center gap-3 min-w-0">
      <Crest
        espnId={favoriteTeam?.espn_team_id}
        name={name}
        size={size}
        fallbackClassName="!bg-racing-blue !border-racing-blue !text-white"
      />
      <div className="min-w-0">
        <div className="font-bold text-white text-sm leading-tight truncate" title={name}>
          {name}
        </div>
        {subtitle && <div className="text-xs text-gray-500">{t('appSubtitle')}</div>}
      </div>
    </div>
  );
}

/** Sits directly above the user block, in both the desktop rail and the drawer. */
function SettingsLink({ onNavigate }) {
  const { t } = useLanguage();
  return (
    <NavLink
      to="/settings"
      onClick={onNavigate}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150 ${
          isActive
            ? 'bg-racing-blue/15 text-racing-blue border border-racing-blue/30'
            : 'text-gray-400 hover:text-gray-200 hover:bg-surface-2'
        }`
      }
    >
      <Settings size={18} />
      {t('navSettings')}
    </NavLink>
  );
}

const NAV = [
  { to: '/',            icon: LayoutDashboard, key: 'navDashboard'   },
  { to: '/tournaments', icon: Trophy,          key: 'navTournaments' },
  { to: '/matches',     icon: Calendar,        key: 'navMatches'     },
  { to: '/players',     icon: Users,           key: 'navPlayers'     },
  { to: '/rivals',      icon: Swords,          key: 'navRivals'      },
];

function NavLinks({ onNavigate }) {
  const { t } = useLanguage();
  return (
    <nav className="flex-1 py-4 px-3 space-y-1">
      {NAV.map(({ to, icon: Icon, key }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          onClick={onNavigate}
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150 ${
              isActive
                ? 'bg-racing-blue/15 text-racing-blue border border-racing-blue/30'
                : 'text-gray-400 hover:text-gray-200 hover:bg-surface-2'
            }`
          }
        >
          <Icon size={18} />
          {t(key)}
        </NavLink>
      ))}
    </nav>
  );
}

function LanguageToggle({ lang, setLang, className = '' }) {
  return (
    <div className={`inline-flex rounded-lg border border-surface-3 overflow-hidden text-xs font-semibold ${className}`}>
      <button
        onClick={() => setLang('es')}
        aria-pressed={lang === 'es'}
        className={`flex-1 px-2.5 py-1.5 transition-colors ${
          lang === 'es' ? 'bg-racing-blue text-white' : 'text-gray-400 hover:text-gray-200 hover:bg-surface-2'
        }`}
      >
        ES
      </button>
      <button
        onClick={() => setLang('en')}
        aria-pressed={lang === 'en'}
        className={`flex-1 px-2.5 py-1.5 transition-colors ${
          lang === 'en' ? 'bg-racing-blue text-white' : 'text-gray-400 hover:text-gray-200 hover:bg-surface-2'
        }`}
      >
        EN
      </button>
    </div>
  );
}

export default function Sidebar() {
  const [open, setOpen] = useState(false);
  const { lang, setLang, t } = useLanguage();

  return (
    <>
      {/* Desktop sidebar — unchanged from original */}
      <aside className="hidden lg:flex fixed left-0 top-0 h-screen w-56 bg-surface-1 border-r border-surface-3 flex-col z-30">
        <div className="px-5 py-5 border-b border-surface-3">
          <ClubHeader size={36} />
        </div>
        <NavLinks />
        <div className="px-3 pb-2">
          <SettingsLink />
        </div>
        <div className="px-5 pb-3">
          <UserMenu />
        </div>
        <div className="px-5 pb-4">
          <LanguageToggle lang={lang} setLang={setLang} className="w-full" />
        </div>
        <div className="px-5 py-4 border-t border-surface-3 text-xs text-gray-600">
          {t('dataRange')}
        </div>
      </aside>

      {/* Mobile top bar */}
      <header className="lg:hidden fixed top-0 left-0 right-0 h-14 bg-surface-1 border-b border-surface-3 flex items-center justify-between px-4 z-40">
        <ClubHeader size={32} subtitle={false} />
        <div className="flex items-center gap-3">
          <LanguageToggle lang={lang} setLang={setLang} />
          <button
            onClick={() => setOpen(true)}
            className="p-2 -mr-2 text-gray-300 hover:text-white"
            aria-label={t('openMenu')}
          >
            <Menu size={22} />
          </button>
        </div>
      </header>

      {/* Mobile drawer */}
      {open && (
        <div className="lg:hidden fixed inset-0 z-50">
          <div className="absolute inset-0 bg-black/60" onClick={() => setOpen(false)} />
          <aside className="absolute left-0 top-0 h-screen w-64 max-w-[80vw] bg-surface-1 border-r border-surface-3 flex flex-col">
            <div className="flex items-center justify-between px-5 py-5 border-b border-surface-3">
              <ClubHeader size={36} />
              <button
                onClick={() => setOpen(false)}
                className="p-1 text-gray-400 hover:text-white"
                aria-label={t('closeMenu')}
              >
                <X size={20} />
              </button>
            </div>
            <NavLinks onNavigate={() => setOpen(false)} />
            <div className="px-3 pb-2">
              <SettingsLink onNavigate={() => setOpen(false)} />
            </div>
            <div className="px-5 pb-4">
              <UserMenu onNavigate={() => setOpen(false)} />
            </div>
            <div className="px-5 py-4 border-t border-surface-3 text-xs text-gray-600">
              {t('dataRange')}
            </div>
          </aside>
        </div>
      )}
    </>
  );
}
