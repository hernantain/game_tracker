import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import TeamPrompt from './components/TeamPrompt';
import AttendancePrompt from './components/AttendancePrompt';
import Dashboard from './pages/Dashboard';
import Tournaments from './pages/Tournaments';
import TournamentDetail from './pages/TournamentDetail';
import Matches from './pages/Matches';
import Players from './pages/Players';
import Rivals from './pages/Rivals';
import Settings from './pages/Settings';
import Login from './pages/Login';
import Signup from './pages/Signup';
import AuthCallback from './pages/AuthCallback';
import NotRecognized from './pages/NotRecognized';
import { useAuth } from './auth/AuthContext';
import { useLanguage } from './i18n/LanguageContext';
import { isLegacy } from './api';

/** The auth screens render on their own, without the dashboard chrome. */
function AuthShell({ rejected }) {
  return (
    <div className="min-h-screen p-4">
      <Routes>
        {/* Explicit routes first, so the CTAs on NotRecognized stay reachable. */}
        <Route path="/login"         element={<Login />} />
        <Route path="/signup"        element={<Signup />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        {/* Anything else: an unrecognised account lands here and cannot be
            routed past it; everyone else goes to sign-in. */}
        <Route
          path="*"
          element={rejected ? <NotRecognized /> : <Navigate to="/login" replace />}
        />
      </Routes>
    </div>
  );
}

function DashboardShell() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="lg:ml-56 flex-1 min-h-screen p-4 pt-20 lg:p-6 overflow-x-hidden">
        <Routes>
          <Route path="/"                 element={<Dashboard />} />
          <Route path="/tournaments"      element={<Tournaments />} />
          <Route path="/tournaments/:id"  element={<TournamentDetail />} />
          <Route path="/matches"          element={<Matches />} />
          <Route path="/players"          element={<Players />} />
          <Route path="/rivals"           element={<Rivals />} />
          <Route path="/settings"         element={<Settings />} />
          <Route path="/login"            element={<Navigate to="/" replace />} />
          <Route path="/signup"           element={<Navigate to="/" replace />} />
          <Route path="/auth/callback"    element={<AuthCallback />} />
        </Routes>
      </main>
      <TeamPrompt />
      <AttendancePrompt />
    </div>
  );
}

export default function App() {
  const { user, loading, profileLoading, authorized, signInRejected, isConfigured } = useAuth();
  const { t } = useLanguage();
  const location = useLocation();

  // Legacy mode reads the JSON files and has no notion of a user, so the
  // dashboard is open. The SQL app is attendance-scoped: there is nothing to
  // show until we know who is asking.
  if (isLegacy) return <DashboardShell />;

  if (!isConfigured) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="card max-w-sm text-sm text-yellow-500/90">
          {t('authNotConfigured')}
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-sm text-gray-500">
        {t('loading')}
      </div>
    );
  }

  // A session is not access. The app is attendance-scoped, so it requires a
  // profiles row -- checked on every load, not just at the OAuth callback.
  if (signInRejected) return <AuthShell rejected />;

  if (!user) return <AuthShell />;

  // Session restored but registration not yet resolved: hold, rather than
  // flashing the dashboard and then revoking it.
  if (profileLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-sm text-gray-500">
        {t('loading')}
      </div>
    );
  }

  if (!authorized) return <AuthShell rejected />;

  return <DashboardShell />;
}
