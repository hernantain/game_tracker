"""Set games.competition and games.tournament_season_id from the legacy files.

sync_games.py records the competition going forward, but only for seasons it
has been run on -- 34 games at the time of writing. The legacy files in data/
already encode the competition in their filename for all 139 historical
matches, so they can fill the gap without 150 more ESPN requests.

Only games already present in the database are touched, matched on espn_id
exactly as the attendance seed does.

Run from the repo root:
    .venv/bin/python -m backend_2.seed.backfill_competitions --dry-run
    .venv/bin/python -m backend_2.seed.backfill_competitions
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.orm import Session

from ..db import get_engine
from ..models import Game, TournamentSeason

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

#: See backend_2/seed/seed_attendances.py -- the Recopa entry's year is a typo.
MANUAL_ESPN_IDS = {
    ("recopa_sudamericana_2025", "20-02-2024", "Botafogo"): "724185",
}

#: Legacy filename prefix -> ESPN league slug (tournaments.id).
PREFIX_TO_SLUG = (
    ("libertadores",   "conmebol.libertadores"),
    ("sudamericana",   "conmebol.sudamericana"),
    ("recopa",         "conmebol.recopa"),
    ("copa_superliga", "arg.copa_de_la_superliga"),
    ("copa_argentina", "arg.copa"),
)
#: Everything else is a league season: Apertura, Clausura, Superliga, Torneo...
DEFAULT_SLUG = "arg.1"


def slug_for(stem: str) -> str:
    for prefix, slug in PREFIX_TO_SLUG:
        if stem.startswith(prefix):
            return slug
    return DEFAULT_SLUG


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--overwrite", action="store_true",
                    help="also replace a competition already set")
    args = ap.parse_args()

    # espn_id -> (competition slug, legacy season id). The filename is the
    # season id, which is also what tournament_seasons was seeded with.
    wanted: dict[str, tuple[str, str]] = {}
    for path in sorted(DATA_DIR.glob("*.json")):
        stem = path.stem
        for match in json.loads(path.read_text(encoding="utf-8")):
            espn = match.get("espn_id") or MANUAL_ESPN_IDS.get(
                (stem, match.get("date", ""), match.get("rival", ""))
            )
            if espn:
                wanted[str(espn)] = (slug_for(stem), stem)

    print(f"legacy matches resolved to a competition: {len(wanted)}")
    for slug, n in Counter(v[0] for v in wanted.values()).most_common():
        print(f"    {slug:28} {n}")
    print(f"distinct seasons referenced: {len({v[1] for v in wanted.values()})}")

    with Session(get_engine()) as session:
        known_seasons = set(
            session.execute(sa.select(TournamentSeason.id)).scalars()
        )
        unknown = sorted({v[1] for v in wanted.values()} - known_seasons)
        if unknown:
            print(f"  ! seasons missing from tournament_seasons: {unknown}")

        rows = session.execute(
            sa.select(
                Game.id, Game.espn_game_id, Game.competition,
                Game.tournament_season_id,
            ).where(Game.espn_game_id.in_(list(wanted)))
        ).all()
        found = {r.espn_game_id for r in rows}
        print(f"\nmatched in games: {len(rows)} of {len(wanted)}")
        if missing := sorted(set(wanted) - found):
            print(f"  not in database ({len(missing)}): {missing[:5]}")

        to_set = [
            r for r in rows
            if args.overwrite
            or r.competition is None
            or r.tournament_season_id is None
        ]
        conflicts = [
            (r.espn_game_id, r.competition, wanted[r.espn_game_id][0])
            for r in rows
            if r.competition is not None and r.competition != wanted[r.espn_game_id][0]
        ]
        print(f"to update: {len(to_set)}   already set and agreeing: "
              f"{len(rows) - len(to_set) - len(conflicts)}   disagreeing: {len(conflicts)}")
        for espn, have, want in conflicts[:10]:
            print(f"    ! espn={espn} database={have} legacy={want}")

        if args.dry_run:
            print("--dry-run: nothing written")
            return

        for r in to_set:
            slug, season_id = wanted[r.espn_game_id]
            session.execute(
                sa.update(Game)
                .where(Game.id == r.id)
                .values(competition=slug, tournament_season_id=season_id)
            )
        session.commit()

        comp = session.execute(
            sa.select(sa.func.count()).select_from(Game).where(Game.competition.isnot(None))
        ).scalar()
        seas = session.execute(
            sa.select(sa.func.count()).select_from(Game)
            .where(Game.tournament_season_id.isnot(None))
        ).scalar()
        print(f"updated {len(to_set)} games; {comp} have a competition, {seas} have a season")


if __name__ == "__main__":
    main()
