import { supabase } from './lib/supabase';

const BASE = '/api';

/**
 * Which backend is serving us.
 *   'sql'    -> backend_2: reads Postgres, requires a signed-in user
 *   'legacy' -> backend:   reads data/*.json, no auth
 * Set by start.sh (VITE_API_MODE); defaults to the SQL app.
 */
export const API_MODE = import.meta.env.VITE_API_MODE === 'legacy' ? 'legacy' : 'sql';
export const isLegacy = API_MODE === 'legacy';

/** Attach the Supabase access token so the API can verify the JWT. */
async function authHeaders() {
  if (!supabase) return {};
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request(path, { method = 'GET', body } = {}) {
  const headers = await authHeaders();
  if (body) headers['Content-Type'] = 'application/json';
  const res = await fetch(BASE + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return null;
  if (!res.ok) {
    let detail = `API error: ${res.status}`;
    try {
      const payload = await res.json();
      if (payload?.detail) detail = typeof payload.detail === 'string'
        ? payload.detail
        : JSON.stringify(payload.detail);
    } catch {
      // non-JSON error body — keep the status text
    }
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

const qs = (params = {}) => {
  const clean = Object.fromEntries(
    Object.entries(params).filter(([, v]) => v !== '' && v != null),
  );
  const s = new URLSearchParams(clean).toString();
  return s ? `?${s}` : '';
};

/* ------------------------------------------------------------------ legacy */
/* The original JSON-backed API. Kept so ./start.sh --legacy still works. */
const legacyApi = {
  mode: 'legacy',
  capabilities: async () => null,
  me: async () => null,
  statistics:  ()           => request('/overview'),
  games:       (p = {})     => request('/matches' + qs(p)),
  opponents:   ()           => request('/rivals'),
  players:     ()           => request('/players'),
  seasons:     ()           => request('/years'),
  tournaments: ()           => request('/tournaments'),
  tournament:  (id)         => request(`/tournaments/${id}`),
  attendancePrompts: async () => ({ watermark: null, games: [] }),
  setAttendance: async () => null,
  setAttendances: async () => null,
  answerPrompts: async () => null,
  clubGames: async () => [],
};

/* --------------------------------------------------------------------- sql */
/* backend_2: noun-based resources, attendance-scoped, auth required. */
const sqlApi = {
  mode: 'sql',
  capabilities: ()          => request('/capabilities'),
  me:           ()          => request('/me'),
  // Discards an abandoned, unregistered account so OAuth leaves no orphan.
  deleteMe:     ()          => request('/me', { method: 'DELETE' }),
  statistics:   ()          => request('/statistics'),
  games:        (p = {})    => request('/games' + qs(p)),
  // Every game the club has played, each flagged with whether you attended.
  clubGames:    (p = {})    => request('/games' + qs({ ...p, attended: 'all' })),
  game:         (id)        => request(`/games/${id}`),
  opponents:    ()          => request('/opponents'),
  players:      ()          => request('/players'),
  seasons:      ()          => request('/seasons'),
  attendances:  ()          => request('/attendances'),
  addAttendance:    (gameId) => request('/attendances', { method: 'POST', body: { gameId } }),
  removeAttendance: (gameId) => request(`/attendances/${gameId}`, { method: 'DELETE' }),
  attendancePrompts: ()      => request('/attendance-prompts'),
  // Idempotent: states whether the user attended, and advances the watermark
  // either way so a "no" is not asked again.
  setAttendance: (gameId, attended) =>
    request(`/attendances/${gameId}`, { method: 'PUT', body: { attended } }),
  // A whole prompt list in one request. Looping the single-game call would
  // cost one round trip per game, which dominates the actual work.
  // Edits history. Deliberately does NOT move the prompt watermark.
  setAttendances: (answers) =>
    request('/attendances', { method: 'PUT', body: { answers } }),
  // Answers the prompt list: sets attendance AND advances the watermark, so
  // unticked games are not asked about again.
  answerPrompts: (answers) =>
    request('/attendance-prompts', { method: 'PUT', body: { answers } }),
  tournaments:  ()          => request('/tournaments'),
  tournament:   (id)        => request(`/tournaments/${encodeURIComponent(id)}`),
};

export const api = isLegacy ? legacyApi : sqlApi;
