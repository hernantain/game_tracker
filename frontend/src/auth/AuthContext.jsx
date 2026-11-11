import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { isSupabaseConfigured, supabase } from '../lib/supabase';
import { fetchProfile, fetchTeams, saveFavoriteTeam } from '../lib/profile';
import { api, isLegacy } from '../api';

const AuthContext = createContext(null);
const RETURN_TO_KEY = 'racing-club-auth-return-to';
const PENDING_TEAM_KEY = 'racing-club-pending-team-id';
const AUTH_INTENT_KEY = 'racing-club-auth-intent';
const SKIP_ONBOARDING_KEY = 'racing-club-skip-team-prompt';

function readStored(key) {
  try { return sessionStorage.getItem(key); } catch { return null; }
}
function writeStored(key, value) {
  try { sessionStorage.setItem(key, value); } catch { /* private mode — value is lost */ }
}
function clearStored(key) {
  try { sessionStorage.removeItem(key); } catch { /* ignore */ }
}

/** Remember where the user was before we bounce them out to Google. */
export function rememberReturnTo(path) {
  writeStored(RETURN_TO_KEY, path);
}

/** Read and clear the stored post-login destination. */
export function takeReturnTo() {
  const stored = readStored(RETURN_TO_KEY);
  clearStored(RETURN_TO_KEY);
  return stored || '/';
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  // Nothing to wait for when auth is not configured.
  const [loading, setLoading] = useState(isSupabaseConfigured);
  const [profile, setProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [teams, setTeams] = useState([]);
  // Set when a sign-in attempt came from an account with no profile row.
  // Holds the email so the sign-up screen can name the account that bounced.
  const [signInRejected, setSignInRejected] = useState(null);
  const [skipPrompt, setSkipPrompt] = useState(() => readStored(SKIP_ONBOARDING_KEY) === '1');

  useEffect(() => {
    if (!supabase) return;
    let active = true;

    // getSession() awaits the client's own initialization, which is what
    // exchanges the ?code= on the OAuth redirect (detectSessionInUrl).
    supabase.auth.getSession().then(({ data }) => {
      if (!active) return;
      setSession(data.session ?? null);
      setLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, next) => {
      if (!active) return;
      setSession(next ?? null);
      setLoading(false);
    });

    return () => {
      active = false;
      subscription.unsubscribe();
    };
  }, []);

  // Team list is public reference data, so it loads once up front — the login
  // screen needs it before anyone has signed in.
  useEffect(() => {
    if (!supabase) return;
    let active = true;
    fetchTeams()
      .then((rows) => { if (active) setTeams(rows); })
      .catch((err) => console.error('[auth] could not load teams:', err?.message || err));
    return () => { active = false; };
  }, []);

  const userId = session?.user?.id ?? null;

  // Sync the profile row whenever the signed-in user changes. A team chosen on
  // the login screen is held in sessionStorage across the Google redirect and
  // flushed here, since signInWithOAuth cannot carry custom data itself.
  useEffect(() => {
    if (!supabase || !userId) {
      setProfile(null);
      return;
    }
    let active = true;
    setProfileLoading(true);

    (async () => {
      try {
        // Peek rather than consume: under StrictMode this effect runs twice,
        // and an idempotent re-upsert is safer than a racing stale read.
        // sessionStorage only holds strings, so the id comes back as text.
        const pendingId = Number(readStored(PENDING_TEAM_KEY));
        const intent = readStored(AUTH_INTENT_KEY);
        // A sign-up is only "in flight" for the one callback that carries both
        // the intent and the chosen club across the Google redirect.
        const completingSignUp =
          intent === 'signup' && Number.isInteger(pendingId) && pendingId > 0;

        // Always read first. Someone who lands on /signup while already
        // registered should simply be signed in -- not have their club
        // silently overwritten by whatever the form happened to hold.
        let row = await fetchProfile(userId);
        if (!row && completingSignUp) {
          // Writing this row is what registers the account.
          row = await saveFavoriteTeam(userId, pendingId);
        }

        // "Registered" means a profiles row exists, and this is checked on
        // EVERY session -- not just at the OAuth callback. The intent lives in
        // sessionStorage and is gone by the next page load, so keying the
        // check on it let a profile-less user in simply by refreshing.
        //
        // GoTrue has already created the auth.users row by the time we get
        // here (OAuth gives the client no chance to refuse), so an
        // unrecognised session is undone rather than prevented.
        if (!row) {
          clearStored(PENDING_TEAM_KEY);
          clearStored(AUTH_INTENT_KEY);
          const email = session?.user?.email ?? null;

          // GoTrue already created the auth.users row -- OAuth gives the
          // client no chance to refuse -- so discard it rather than leaving an
          // orphan. Best effort: never block sign-out on the cleanup.
          if (!isLegacy) {
            try {
              await api.deleteMe();
            } catch (err) {
              console.warn('[auth] could not discard unregistered account:', err?.message || err);
            }
          }

          if (active) {
            setSignInRejected({ email });
            setProfile(null);
            setProfileLoading(false);
          }
          await supabase.auth.signOut();
          return;
        }

        clearStored(PENDING_TEAM_KEY);
        clearStored(AUTH_INTENT_KEY);
        if (active) setProfile(row);
      } catch (err) {
        // Most likely the migration has not been run, or RLS is misconfigured.
        console.error('[auth] profile sync failed:', err?.message || err);
        if (active) setProfile(null);
      } finally {
        if (active) setProfileLoading(false);
      }
    })();

    return () => { active = false; };
  }, [userId]);

  const signInWithGoogle = useCallback(async ({ intent = 'signin', returnTo, teamId } = {}) => {
    if (!supabase) throw new Error('Supabase is not configured');
    setSignInRejected(null);
    if (returnTo) rememberReturnTo(returnTo);
    // Held across the Google redirect because signInWithOAuth cannot carry
    // custom data of its own -- see lib/profile.js for where it lands.
    writeStored(AUTH_INTENT_KEY, intent);
    if (teamId) writeStored(PENDING_TEAM_KEY, String(teamId));
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
    if (error) throw error;
  }, []);

  const signOut = useCallback(async () => {
    if (!supabase) return;
    setSignInRejected(null);
    clearStored(PENDING_TEAM_KEY);
    clearStored(AUTH_INTENT_KEY);
    clearStored(SKIP_ONBOARDING_KEY);
    setSkipPrompt(false);
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
  }, []);

  /** Set or change the favourite team for the already signed-in user. */
  const setFavoriteTeam = useCallback(async (teamId) => {
    if (!userId) throw new Error('Not signed in');
    const row = await saveFavoriteTeam(userId, teamId);
    setProfile(row);
    return row;
  }, [userId]);

  /** Dismiss the onboarding prompt for this browser session only. */
  const dismissTeamPrompt = useCallback(() => {
    writeStored(SKIP_ONBOARDING_KEY, '1');
    setSkipPrompt(true);
  }, []);

  const value = useMemo(() => {
    const user = session?.user ?? null;
    return {
      session,
      user,
      loading,
      isConfigured: isSupabaseConfigured,
      teams,
      profile,
      profileLoading,
      favoriteTeam: profile?.team ?? null,
      // The only reliable "first time" signal: Google OAuth has no sign-up
      // event, so a null favourite team is what marks an unanswered account.
      needsTeam: Boolean(user) && !profileLoading && !profile?.favorite_team_id && !skipPrompt,
      // A session alone is not access: the app requires a profiles row.
      isRegistered: Boolean(profile),
      authorized: Boolean(user) && Boolean(profile),
      signInRejected,
      clearSignInRejected: () => setSignInRejected(null),
      signInWithGoogle,
      signOut,
      setFavoriteTeam,
      dismissTeamPrompt,
    };
  }, [session, loading, teams, profile, profileLoading, skipPrompt, signInRejected,
      signInWithGoogle, signOut, setFavoriteTeam, dismissTeamPrompt]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
