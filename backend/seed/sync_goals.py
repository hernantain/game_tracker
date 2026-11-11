"""Populate the goals table from ESPN match summaries.

One HTTP request per game, so this is the slow one. It works in batches:
summaries for a batch are fetched on a thread pool, then that batch's rows are
written in a single transaction. Both halves matter -- a naive version spent
most of its time on per-game database round trips, not on ESPN. Every game is
logged with a running count and an ETA, so a long run is never silent.

Source: ESPN's summary endpoint, whose `keyEvents` carries the goal type
("Goal - Header", "Penalty - Scored"), the scoring team, and the minute. The
scorer is not given as an id, only inside the description, so it is matched by
name against the players who actually appeared in that game -- a small, safe
candidate set. Unmatched scorers still record `scorer_name`.

Only games with `games.competition` set can be fetched: the summary endpoint
is per-league, and that column is where the league slug lives. Run
backfill_competitions.py / sync_games.py first if a game is skipped for that.

Idempotent: a game's goals are deleted and rewritten, and games that already
have goals are skipped unless --force.

Run from the repo root:
    .venv/bin/python -m backend_2.seed.sync_goals --attended --dry-run
    .venv/bin/python -m backend_2.seed.sync_goals --attended
    .venv/bin/python -m backend_2.seed.sync_goals --team-id 256 --force
    .venv/bin/python -m backend_2.seed.sync_goals --all --workers 8
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor

import sqlalchemy as sa
from sqlalchemy.orm import Session

from .. import espn
from ..db import get_engine
from ..models import Appearance, Game, Goal, GoalType, Player, Team

#: ESPN keyEvents type.text -> our enum. Anything unlisted becomes `unknown`
#: rather than being guessed at.
TYPE_MAP = {
    "goal": GoalType.regular,
    "goal - header": GoalType.header,
    "header": GoalType.header,
    "penalty - scored": GoalType.penalty,
    "penalty": GoalType.penalty,
    "goal - free-kick": GoalType.free_kick,
    "free kick": GoalType.free_kick,
    "goal - free kick": GoalType.free_kick,
    "own goal": GoalType.own_goal,
    "goal - own goal": GoalType.own_goal,
    "goal - volley": GoalType.volley,
}

#: ESPN writes goal events two ways depending on the competition feed:
#:   verbose: "Goal! Racing Club 1, Aldosivi 1. Adrián Martínez (Racing Club) left..."
#:   terse:   "Gastón Lodico (Racing Club) Goal at 19'"
#: The terse feed fills participants[], which is preferred over either regex.
VERBOSE_RE = re.compile(r"^Goal!.*?\.\s*(.+?)\s*\(", re.S)
TERSE_RE = re.compile(r"^(.+?)\s*\(")
#: Handles "45+2'" and "90'+5'" alike.
CLOCK_RE = re.compile(r"(\d+)\s*'?\s*(?:\+\s*(\d+))?")


def fold(s: str) -> str:
    """Accent- and case-insensitive key for name matching."""
    s = unicodedata.normalize("NFD", s or "")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower().strip()


def parse_scorer(event: dict) -> str | None:
    """Structured fields first; the descriptions are a fallback."""
    for p in event.get("participants") or []:
        name = ((p.get("athlete") or {}).get("displayName") or "").strip()
        if name:
            return name
    for a in event.get("athletesInvolved") or []:
        name = (a.get("displayName") or "").strip()
        if name:
            return name
    text = event.get("text") or ""
    for pattern in (VERBOSE_RE, TERSE_RE):
        m = pattern.match(text)
        if m:
            candidate = m.group(1).strip()
            # The verbose form starts with the scoreline; guard against a
            # match that swallowed it.
            if candidate and not candidate.lower().startswith("goal"):
                return candidate
    return None


def parse_clock(display: str | None) -> tuple[int | None, int | None]:
    if not display:
        return None, None
    m = CLOCK_RE.search(display)
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2)) if m.group(2) else None


def log(msg: str) -> None:
    print(msg, flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--attended", action="store_true",
                    help="only games someone has marked as attended")
    ap.add_argument("--all", action="store_true",
                    help="every game with a competition and a score (~11k: hours)")
    ap.add_argument("--workers", type=int, default=6,
                    help="parallel summary fetches (default: 6)")
    ap.add_argument("--batch", type=int, default=200,
                    help="games per database transaction (default: 200)")
    ap.add_argument("--team-id", type=int, help="only games involving this team")
    ap.add_argument("--limit", type=int, help="stop after N games (for a trial run)")
    ap.add_argument("--delay", type=float, default=0.15,
                    help="seconds between requests per worker (default: 0.15)")
    ap.add_argument("--force", action="store_true",
                    help="refetch games that already have goals")
    ap.add_argument("--dry-run", action="store_true", help="fetch nothing, write nothing")
    args = ap.parse_args()

    engine = get_engine()
    with Session(engine) as session:
        q = (
            sa.select(Game.id, Game.espn_game_id, Game.competition, Game.date,
                      Game.home_team_id, Game.away_team_id,
                      Game.home_score, Game.away_score)
            .where(Game.competition.isnot(None), Game.home_score.isnot(None))
            .order_by(Game.date.desc())
        )
        if args.team_id:
            q = q.where(sa.or_(Game.home_team_id == args.team_id,
                               Game.away_team_id == args.team_id))
        if not (args.attended or args.team_id or args.all):
            sys.exit("choose a scope: --attended, --team-id N, or --all")
        if args.attended:
            q = q.where(sa.exists().where(
                sa.text("attendances.game_id = games.id")
            ).select_from(sa.text("attendances")))
        games = session.execute(q).all()

        done = set(session.execute(
            sa.select(Goal.game_id).distinct()
        ).scalars())
        todo = [g for g in games if args.force or g.id not in done]
        if args.limit:
            todo = todo[: args.limit]

        log(f"candidate games (have a competition and a score): {len(games)}")
        log(f"already have goals: {len(games) - len([g for g in games if g.id not in done])}")
        per_game = (args.delay + 0.6) / max(args.workers, 1)
        log(f"to fetch: {len(todo)}   ~{len(todo) * per_game / 60:.1f} min "
            f"with {args.workers} workers")
        if not todo:
            log("nothing to do")
            return
        if args.dry_run:
            for g in todo[:10]:
                log(f"    would fetch {g.espn_game_id:>10}  {g.date}  {g.competition}")
            log("--dry-run: nothing fetched or written")
            return

        # espn team id -> our id, so keyEvents' team.id can be resolved
        team_by_espn = dict(session.execute(
            sa.select(Team.espn_team_id, Team.team_id)
        ).all())

        started = time.time()
        totals = {"goals": 0, "matched": 0, "unmatched": 0, "shootout": 0,
                  "failed": 0, "no_events": 0}

        def fetch(game):
            """HTTP only -- no database access, so this is thread-safe."""
            time.sleep(args.delay)
            data, error = espn.fetch_summary(game.competition, game.espn_game_id)
            return game, data, error

        pool = ThreadPoolExecutor(max_workers=max(args.workers, 1))
        done_count = 0

        # Batching keeps three things bounded: the appearance lookup is one
        # query per batch instead of one per game, writes are one transaction
        # per batch instead of one per game, and memory never holds the whole
        # season's rosters at once.
        for start in range(0, len(todo), args.batch):
            batch = todo[start : start + args.batch]
            batch_ids = [g.id for g in batch]

            # Candidate scorers for the whole batch: whoever appeared, folded.
            appearances = session.execute(
                sa.select(Appearance.game_id, Player.player_id, Player.player_name)
                .join(Player, Player.player_id == Appearance.player_id)
                .where(Appearance.game_id.in_(batch_ids))
            ).all()
            names_by_game: dict[int, dict[str, int]] = {}
            for row in appearances:
                names_by_game.setdefault(row.game_id, {})[fold(row.player_name)] = row.player_id

            new_rows, written_games = [], []
            for g, data, error in pool.map(fetch, batch):
                done_count += 1
                prefix = f"[{done_count}/{len(todo)}]"
                if error:
                    totals["failed"] += 1
                    log(f"{prefix} espn={g.espn_game_id} {g.date}  ! fetch failed: {error}")
                    continue

                events = [e for e in (data.get("keyEvents") or []) if e.get("scoringPlay")]
                if not events:
                    totals["no_events"] += 1
                    if g.home_score or g.away_score:
                        log(f"{prefix} espn={g.espn_game_id} {g.date}  ! no scoring events "
                            f"but score was {g.home_score}-{g.away_score}")
                    continue

                by_name = names_by_game.get(g.id, {})
                rows, shootout, unmatched_here = [], 0, 0
                for e in events:
                    if e.get("shootout"):
                        shootout += 1
                        continue
                    team_id = team_by_espn.get(str(((e.get("team") or {}).get("id")) or ""))
                    if not team_id:
                        continue
                    type_text = ((e.get("type") or {}).get("text") or "").strip().lower()
                    minute, stoppage = parse_clock((e.get("clock") or {}).get("displayValue"))
                    scorer = parse_scorer(e)
                    player_id = by_name.get(fold(scorer)) if scorer else None
                    if scorer and not player_id:
                        unmatched_here += 1
                    rows.append({
                        "game_id": g.id, "team_id": team_id, "player_id": player_id,
                        "scorer_name": scorer, "minute": minute, "stoppage": stoppage,
                        "type": TYPE_MAP.get(type_text, GoalType.unknown),
                    })

                new_rows.extend(rows)
                written_games.append(g.id)
                totals["goals"] += len(rows)
                totals["matched"] += sum(1 for r in rows if r["player_id"])
                totals["unmatched"] += unmatched_here
                totals["shootout"] += shootout

                elapsed = time.time() - started
                eta = (elapsed / done_count) * (len(todo) - done_count)
                kinds = ", ".join(sorted({r["type"].value for r in rows})) or "-"
                log(f"{prefix} espn={g.espn_game_id} {g.date}  {len(rows)} goals ({kinds})"
                    f"{f', {unmatched_here} scorer unmatched' if unmatched_here else ''}"
                    f"{f', {shootout} shootout skipped' if shootout else ''}"
                    f"   eta {eta/60:.1f}m")

            # One transaction for the whole batch.
            if written_games:
                session.execute(sa.delete(Goal).where(Goal.game_id.in_(written_games)))
            if new_rows:
                session.execute(sa.insert(Goal), new_rows)
            session.commit()
            log(f"  -- batch committed: {len(written_games)} games, {len(new_rows)} goals")

        pool.shutdown(wait=True)
        log("\n" + "-" * 60)
        log(f"games processed : {len(todo)}")
        log(f"goals written   : {totals['goals']}")
        log(f"scorer resolved : {totals['matched']}   unmatched: {totals['unmatched']}")
        log(f"shootout skipped: {totals['shootout']}")
        log(f"fetch failures  : {totals['failed']}   games with no events: {totals['no_events']}")
        log(f"elapsed         : {(time.time() - started)/60:.1f} min")


if __name__ == "__main__":
    main()
