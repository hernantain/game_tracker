import { createClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

// The app is a public stats dashboard, so it must still render when auth is
// unconfigured (e.g. a fresh clone with no .env). Everything auth-related
// degrades to a disabled state instead of crashing the tree.
export const isSupabaseConfigured = Boolean(url && anonKey);

if (!isSupabaseConfigured) {
  console.warn(
    '[auth] VITE_SUPABASE_URL / VITE_SUPABASE_ANON_KEY are not set — sign-in is disabled. ' +
    'Copy frontend/.env.example to frontend/.env and fill them in.'
  );
}

export const supabase = isSupabaseConfigured
  ? createClient(url, anonKey, {
      auth: {
        flowType: 'pkce',
        detectSessionInUrl: true,
        persistSession: true,
        autoRefreshToken: true,
        storageKey: 'racing-club-auth',
      },
    })
  : null;
