# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Game Tracker: a web app where a user records the football games they attended and sees statistics about them (results, opponents, players, goals, tournaments). FastAPI + SQLAlchemy backend on Supabase Postgres, React + Vite + Tailwind frontend, Supabase Auth (Google sign-in). Deployed to Fly.io (`fly.toml`, app `cancha`, region `gru`) as a single container in which FastAPI serves the built SPA.

## Commands

Python deps are managed with **uv** (`pyproject.toml`, `uv.lock`). Run Python tools through `uv run`, which syncs the environment first. The `seed` dependency group (requests, pillow) is needed only for the seed scripts, so pass `--group seed` for those. To change dependencies, edit them with `uv add` / `uv remove`, or edit `pyproject.toml` and run `uv lock`.

```bash
uv sync                      # backend deps
cd frontend && npm install

./start.sh                   # dev: uvicorn --reload on :3001 + Vite on :5173 (Vite proxies /api -> :3001)
uv run uvicorn backend.main:app --port 3001 --reload   # backend only; OpenAPI docs at /docs
cd frontend && npm run build # production bundle -> frontend/dist

uv run alembic upgrade head                         # apply migrations (reads DATABASE_URL from .env)
uv run alembic revision --autogenerate -m "slug"    # new migration
```

Seed/ingest scripts run as modules from the repo root, and most of them support `--dry-run`:

```bash
uv run --group seed python -m backend.seed.sync_games arg.1 2026 [--team "Racing Club"]
uv run --group seed python -m backend.seed.sync_goals --attended    # slow: one ESPN request per game
uv run --group seed python -m backend.seed.backfill_competitions
uv run --group seed python -m backend.seed.seed_attendances --user-email ...
uv run --group seed python -m backend.seed.download_crests          # likewise resize_crests
```

The repo has no tests, linter or formatter configured.

## Configuration

- Root `.env` (loaded by `backend/config.py` and `alembic/env.py`): `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY` (service_role, used only to delete abandoned unregistered auth users). `DISABLE_AUTH=true` skips JWT verification and acts as `DEV_USER_ID`. It is meant only for local smoke tests.
- `frontend/.env`: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`. Every `VITE_*` var is inlined into the bundle, so never put the secret key there.
- The DB engine is created lazily (`backend/db.py`), so the app can be imported without a database.

## Architecture

**Backend layering:** `routers/` (thin HTTP layer, registered through the `ROUTERS` list in `routers/__init__.py`) → `services/` (all query and stats logic) → `models/` (SQLAlchemy 2.x declarative). Response shapes are defined in `schemas/responses.py`.

**Auth and identity** (`auth.py`, `deps.py`):
- Supabase access tokens (ES256) are verified against the project JWKS. The verified `sub` claim is the *only* source of user identity. Never trust a user id from a path, query or body: SQLAlchemy connects as a role that bypasses RLS, so the database will not catch impersonation.
- A valid token alone is not enough. Data routers declare `dependencies=[Depends(require_registered)]`, which requires a `profiles` row. `/api/me` and `DELETE /api/me` deliberately skip this check.
- `get_user_context` builds a `UserContext` (user, perspective team, attended matches, session). Most stats endpoints take this and pass `ctx.matches` into services.

**Perspective normalization** (`services/attended_games.py`): `games` stores neutral home/away team ids, but every statistic is relative to the user's favourite club ("we scored", W/D/L). `load_attended` returns `MatchRow`s that are already flipped to that team's point of view. Add new stats on top of `MatchRow` rather than re-querying raw games.

**Capabilities** (`services/capabilities.py`, `GET /api/capabilities`): a declared list of which datasets the schema can answer. The frontend (`hooks/useCapabilities.js`) hides charts based on this list instead of hard-coding it, so update it when you add or fill a dataset.

**Table ownership and Alembic:** `teams`, `players`, `games`, `appearances` (ESPN ingest) and `auth.users` (Supabase GoTrue) are mapped with `**EXTERNAL` table info (`models/base.py`) so that foreign keys resolve. `alembic/env.py` filters these tables out, so autogenerate only emits DDL for app-owned tables (profiles, attendances, tournaments, tournament_seasons, goals). RLS policies in migrations are added by hand after autogenerate.

**ESPN data** (`backend/espn.py` + `backend/seed/`): ESPN scores are trusted only once a match is marked completed (scheduled games report 0-0). Kickoff times are UTC and must be converted before taking the local date. Goal scorers are matched by name against that game's appearances. `sync_goals` requires `games.competition` (the league slug), so run `sync_games`/`backfill_competitions` first.

**Static serving:** when `backend/static/` exists (the frontend build is copied there), `main.py` mounts `SPAStaticFiles`. It falls back to `index.html` for client routes, but returns a real 404 for `api/*` and for file-like paths. `start.sh` switches to production mode based on whether that directory exists. Club crests are served from `frontend/public/crests/<size>/<espn_team_id>.png` (sizes 64/128/500).

**Frontend:** React Router pages in `src/pages`. `src/api.js` attaches the Supabase bearer token to every request. Auth state lives in `src/auth/AuthContext.jsx`, and UI strings in `src/i18n/translations.js` (via `LanguageContext`).

## Known stale references

- The usage lines in the seed-script docstrings use an outdated module path. Run them as `uv run --group seed python -m backend.seed.<script>`.
- `backend/requirements.txt` is unused. The Dockerfile installs from `uv.lock` with `uv sync --frozen`, so dependency changes go in `pyproject.toml` followed by `uv lock`.
- `frontend/src/api.js` still has a `legacy` API mode (`VITE_API_MODE`, `isLegacy`), and `main.py` docstrings mention `./start.sh --legacy`. Neither one corresponds to anything that exists.
- `seed_attendances` and `backfill_competitions` read `data/*.json`, which is not in this repo.
- Docstrings mention `EXPERIMENTS/supabase_schema.sql`, which lives outside this repo and is the source of the externally owned tables.
