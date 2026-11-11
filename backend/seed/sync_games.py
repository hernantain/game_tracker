"""Refresh game results from ESPN, recording which competition each came from.

Narrow job: bring `games` up to date for one league/season and record
`games.competition`, which the attendance prompt and the tournament views need.

Teams, players and rosters are not touched -- this only inserts or updates
games whose teams the database already knows. ESPN access lives in
backend_2/espn.py.

Run from the repo root:
    .venv/bin/python -m backend_2.seed.sync_games arg.1 2026 --dry-run
    .venv/bin/python -m backend_2.seed.sync_games arg.1 2026
    .venv/bin/python -m backend_2.seed.sync_games arg.1 2026 --team "Racing Club"
"""

from __future__ import annotations

import argparse

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from .. import espn
from ..db import get_engine
from ..models import Game, Team


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("league", nargs="?", help="ESPN league slug, e.g. arg.1")
    ap.add_argument("season", nargs="?", type=int, help="season year, e.g. 2026")
    ap.add_argument("--all", action="store_true",
                    help="every league the pipeline knows, across --from-year..--to-year")
    ap.add_argument("--from-year", type=int, default=2012)
    ap.add_argument("--to-year", type=int, default=2026)
    ap.add_argument("--team", help="only games involving this team name")
    ap.add_argument("--dry-run", action="store_true", help="report, write nothing")
    args = ap.parse_args()

    if args.all:
        combos = [(lg, yr) for lg in espn.LEAGUES
                  for yr in range(args.from_year, args.to_year + 1)]
        print(f"--all: {len(espn.LEAGUES)} leagues x "
              f"{args.to_year - args.from_year + 1} seasons = {len(combos)} scoreboard requests")
        for i, (league, season) in enumerate(combos, 1):
            print(f"\n[{i}/{len(combos)}] {league} {season}", flush=True)
            _run_one(league, season, args)
        return

    if not args.league or not args.season:
        ap.error("give a league and season, or use --all")
    _run_one(args.league, args.season, args)


def _run_one(league: str, season: int, args) -> None:
    events, error = espn.fetch_season_events(league, season)
    if error:
        print(f"  ! ESPN fetch failed: {error}"); return
    print(f"  ESPN {league} {season}: {len(events)} events")

    failures = espn.Failures()
    parsed: list[tuple[dict, list]] = []
    for event in events:
        game, sides = espn.parse_event(event, league, season, failures)
        if game:
            parsed.append((game, sides))
    if not parsed:
        print("  no parsable events"); return
    print(f"  parsed: {len(parsed)}  (parse failures: {len(failures.items)})")

    engine = get_engine()
    with Session(engine) as session:
        # ESPN team ids -> our surrogate team ids. Teams this database has
        # never seen are skipped rather than invented: creating them is the
        # pipeline's job, and guessing here would produce duplicates.
        team_by_espn = {
            espn: tid
            for espn, tid in session.execute(
                sa.select(Team.espn_team_id, Team.team_id)
            ).all()
        }

        rows, skipped_unknown, skipped_filter = [], [], 0
        for game, sides in parsed:
            names = [name for _, name in sides]
            if args.team and args.team not in names:
                skipped_filter += 1
                continue
            home = team_by_espn.get(game["_home_espn_team_id"])
            away = team_by_espn.get(game["_away_espn_team_id"])
            if not home or not away:
                skipped_unknown.append(game["_label"])
                continue
            rows.append({
                "espn_game_id": game["espn_game_id"],
                "date": game["date"],
                "local_time": game["local_time"],
                "home_team_id": home,
                "away_team_id": away,
                "home_score": game["home_score"],
                "away_score": game["away_score"],
                "competition": league,
            })

        if args.team:
            print(f"filtered to {args.team!r}: {len(rows)} games ({skipped_filter} others skipped)")
        if skipped_unknown:
            print(f"SKIPPED {len(skipped_unknown)} games whose teams are not in the database:")
            for label in skipped_unknown[:5]:
                print(f"    {label}")
            print("  -> these teams must be ingested before their games can be stored")

        if not rows:
            print("nothing to write")
            return

        existing = {
            espn: (d, hs, aws, comp)
            for espn, d, hs, aws, comp in session.execute(
                sa.select(
                    Game.espn_game_id, Game.date, Game.home_score,
                    Game.away_score, Game.competition,
                ).where(Game.espn_game_id.in_([r["espn_game_id"] for r in rows]))
            ).all()
        }
        new = [r for r in rows if r["espn_game_id"] not in existing]
        newly_scored = [
            r for r in rows
            if r["espn_game_id"] in existing
            and existing[r["espn_game_id"]][1] is None
            and r["home_score"] is not None
        ]
        print(f"to insert: {len(new)}   results filled in: {len(newly_scored)}   total upserted: {len(rows)}")
        for r in newly_scored[:10]:
            print(f"    {r['date']}  espn={r['espn_game_id']}  {r['home_score']}-{r['away_score']}")

        if args.dry_run:
            print("--dry-run: nothing written")
            return

        stmt = pg_insert(Game).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=["espn_game_id"],
            set_={
                "date": stmt.excluded.date,
                "local_time": stmt.excluded.local_time,
                "home_team_id": stmt.excluded.home_team_id,
                "away_team_id": stmt.excluded.away_team_id,
                "home_score": stmt.excluded.home_score,
                "away_score": stmt.excluded.away_score,
                "competition": stmt.excluded.competition,
            },
        )
        session.execute(stmt)
        session.commit()
        print(f"upserted {len(rows)} games")


if __name__ == "__main__":
    main()
