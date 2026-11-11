"""Seed one user's attendances from the legacy JSON files in data/.

The legacy app reads data/*.json directly; each entry carries an `espn_id`
that matches games.espn_game_id, which is how a legacy match becomes a row in
the SQL-backed app.

Run from the repo root:
    .venv/bin/python -m backend_2.seed.seed_attendances
    .venv/bin/python -m backend_2.seed.seed_attendances --user-email you@example.com
    .venv/bin/python -m backend_2.seed.seed_attendances --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from ..db import get_engine
from ..models import Attendance, AuthUser, Game, Profile, Team

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

#: One legacy entry has no espn_id: recopa_sudamericana_2025.json is dated
#: 20-02-2024, but the file name and the 2-0 scoreline both identify the
#: 2025-02-20 Recopa first leg (Racing Club 2-0 Botafogo), espn 724185. The
#: year in the source file is a typo. Keyed by (file stem, date, rival).
MANUAL_ESPN_IDS = {
    ("recopa_sudamericana_2025", "20-02-2024", "Botafogo"): "724185",
}

DEFAULT_FAVORITE_TEAM = "Racing Club"


def collect_legacy_games() -> tuple[list[tuple[str, str]], list[tuple[str, str, str]]]:
    """Return ([(espn_id, label)], [unresolved]) for every legacy match."""
    resolved: list[tuple[str, str]] = []
    unresolved: list[tuple[str, str, str]] = []
    for path in sorted(DATA_DIR.glob("*.json")):
        stem = path.stem
        for match in json.loads(path.read_text(encoding="utf-8")):
            date = match.get("date", "?")
            rival = match.get("rival", "?")
            espn = match.get("espn_id") or MANUAL_ESPN_IDS.get((stem, date, rival))
            if espn:
                resolved.append((str(espn), f"{stem} {date} vs {rival}"))
            else:
                unresolved.append((stem, date, rival))
    return resolved, unresolved


def resolve_user(session: Session, user_id: str | None, email: str | None) -> str:
    if user_id:
        return user_id
    if email:
        found = session.execute(
            sa.select(AuthUser.id).where(AuthUser.email == email)
        ).scalar_one_or_none()
        if not found:
            sys.exit(f"No auth user with email {email!r}")
        return str(found)
    ids = session.execute(sa.select(AuthUser.id)).scalars().all()
    if len(ids) == 1:
        return str(ids[0])
    sys.exit(
        f"Found {len(ids)} auth users; pass --user-id or --user-email to pick one."
    )


def ensure_profile(session: Session, user_id: str) -> None:
    """attendances.user_id references profiles, so the row must exist."""
    existing = session.get(Profile, user_id)
    if existing:
        return
    team_id = session.execute(
        sa.select(Team.team_id).where(Team.team_name == DEFAULT_FAVORITE_TEAM)
    ).scalar_one_or_none()
    session.add(Profile(user_id=user_id, favorite_team_id=team_id))
    session.flush()
    print(
        f"  created missing profile for {user_id} "
        f"(favourite club: {DEFAULT_FAVORITE_TEAM} = {team_id})"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--user-id", help="auth.users.id to attach attendances to")
    ap.add_argument("--user-email", help="look the user up by email instead")
    ap.add_argument("--dry-run", action="store_true", help="resolve but write nothing")
    args = ap.parse_args()

    legacy, unresolved = collect_legacy_games()
    print(f"legacy matches with a resolvable espn_id : {len(legacy)}")
    if unresolved:
        print(f"UNRESOLVED ({len(unresolved)}):")
        for row in unresolved:
            print(f"    {row}")

    engine = get_engine()
    with Session(engine) as session:
        user_id = resolve_user(session, args.user_id, args.user_email)
        print(f"target user: {user_id}")

        espn_ids = [e for e, _ in legacy]
        rows = session.execute(
            sa.select(Game.id, Game.espn_game_id, Game.home_score, Game.away_score)
            .where(Game.espn_game_id.in_(espn_ids))
        ).all()
        by_espn = {r.espn_game_id: r for r in rows}

        missing = [(e, label) for e, label in legacy if e not in by_espn]
        if missing:
            print(f"NOT FOUND in games ({len(missing)}):")
            for e, label in missing[:10]:
                print(f"    espn_id={e}  {label}")

        game_ids = [by_espn[e].id for e, _ in legacy if e in by_espn]
        no_score = [e for e in espn_ids if e in by_espn and by_espn[e].home_score is None]
        print(f"games matched            : {len(game_ids)}")
        print(f"matched games with NO score in SQL: {len(no_score)}")

        if args.dry_run:
            print("--dry-run: nothing written")
            return

        ensure_profile(session, user_id)
        stmt = pg_insert(Attendance).values(
            [{"user_id": user_id, "game_id": gid} for gid in game_ids]
        ).on_conflict_do_nothing(index_elements=["user_id", "game_id"])
        session.execute(stmt)
        session.commit()

        total = session.execute(
            sa.select(sa.func.count())
            .select_from(Attendance)
            .where(Attendance.user_id == user_id)
        ).scalar()
        print(f"attendances for this user: {total}")


if __name__ == "__main__":
    main()
