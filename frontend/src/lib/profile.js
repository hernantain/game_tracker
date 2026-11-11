import { supabase } from './supabase';

// `team:teams!...` embeds through the profiles.favorite_team_id FK. The
// constraint is named explicitly so the embed cannot be mis-resolved if a
// second teams FK is ever added to profiles.
const PROFILE_FIELDS =
  'user_id, favorite_team_id, created_at, updated_at, ' +
  'team:teams!profiles_favorite_team_id_fkey ( team_id, team_name, stadium_name, espn_team_id )';

/**
 * Reference list for the picker. Readable while signed out thanks to the
 * "public read teams" RLS policy. ~491 rows, well under PostgREST's default
 * 1000-row cap, so one unpaged fetch is fine.
 */
export async function fetchTeams() {
  if (!supabase) return [];
  const { data, error } = await supabase
    .from('teams')
    .select('team_id, team_name, stadium_name, espn_team_id')
    .order('team_name', { ascending: true });
  if (error) throw error;
  return data ?? [];
}

/** Read the signed-in user's profile row, or null when there isn't one yet. */
export async function fetchProfile(userId) {
  if (!supabase || !userId) return null;
  const { data, error } = await supabase
    .from('profiles')
    .select(PROFILE_FIELDS)
    .eq('user_id', userId)
    .maybeSingle();
  if (error) throw error;
  return data;
}

/**
 * Set the user's one favourite club. RLS (`auth.uid() = user_id`) confines the
 * write to the caller's own row, so the user id never has to be trusted from
 * anywhere but the live session.
 */
export async function saveFavoriteTeam(userId, teamId) {
  if (!supabase || !userId) return null;
  const id = Number(teamId);
  if (!Number.isInteger(id) || id <= 0) {
    throw new Error(`Invalid team id: ${teamId}`);
  }
  const { data, error } = await supabase
    .from('profiles')
    .upsert({ user_id: userId, favorite_team_id: id }, { onConflict: 'user_id' })
    .select(PROFILE_FIELDS)
    .single();
  if (error) throw error;
  return data;
}
