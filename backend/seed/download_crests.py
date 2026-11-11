"""Download club crests from ESPN's CDN into assets/crests/.

ESPN serves a 500x500 transparent PNG per team at a predictable path keyed by
the espn_team_id we already store, so no API call is needed per team:

    https://a.espncdn.com/i/teamlogos/soccer/500/<espn_team_id>.png

Files are named by espn_team_id rather than our surrogate team_id, because the
ESPN id is stable across a re-ingest while the serial is not. A manifest.json
maps both, so the app can look up either way.

Nothing here wires the images into the frontend -- they are downloaded only.

Run from the repo root:
    .venv/bin/python -m backend_2.seed.download_crests --dry-run
    .venv/bin/python -m backend_2.seed.download_crests
    .venv/bin/python -m backend_2.seed.download_crests --only-played
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import requests
import sqlalchemy as sa
from sqlalchemy.orm import Session

from ..db import get_engine

CDN = "https://a.espncdn.com/i/teamlogos/soccer/500/{espn_id}.png"
OUT_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "crests"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

ALL_TEAMS = sa.text("""
    select team_id, espn_team_id, team_name
      from teams
     where espn_team_id is not null and espn_team_id <> ''
     order by team_name
""")

#: Teams that have actually faced, or been, the club -- the ones the app shows.
PLAYED_TEAMS = sa.text("""
    select distinct t.team_id, t.espn_team_id, t.team_name
      from teams t
      join games g on g.home_team_id = t.team_id or g.away_team_id = t.team_id
     where (g.home_team_id = :team or g.away_team_id = :team)
       and t.espn_team_id is not null and t.espn_team_id <> ''
     order by t.team_name
""")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only-played", action="store_true",
                    help="only teams that appear in the club's games")
    ap.add_argument("--team-id", type=int, default=256,
                    help="club used by --only-played (default: Racing Club)")
    ap.add_argument("--delay", type=float, default=0.15,
                    help="seconds between requests (default: 0.15)")
    ap.add_argument("--force", action="store_true", help="re-download existing files")
    ap.add_argument("--dry-run", action="store_true", help="report, download nothing")
    args = ap.parse_args()

    with Session(get_engine()) as session:
        rows = session.execute(
            PLAYED_TEAMS, {"team": args.team_id}
        ).all() if args.only_played else session.execute(ALL_TEAMS).all()

    print(f"teams to fetch: {len(rows)}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    existing = {p.stem for p in OUT_DIR.glob("*.png")}
    todo = [r for r in rows if args.force or r.espn_team_id not in existing]
    print(f"already downloaded: {len(rows) - len(todo)}   to download: {len(todo)}")

    if args.dry_run:
        for r in todo[:10]:
            print(f"    would fetch {r.espn_team_id:>8}  {r.team_name}")
        print("--dry-run: nothing written")
        return

    saved, failed = 0, []
    session_http = requests.Session()
    session_http.headers.update({"User-Agent": "Mozilla/5.0 (crest-fetch)"})

    for i, row in enumerate(todo, 1):
        url = CDN.format(espn_id=row.espn_team_id)
        try:
            resp = session_http.get(url, timeout=20)
            if resp.status_code != 200:
                failed.append((row.team_name, row.espn_team_id, f"HTTP {resp.status_code}"))
            elif not resp.content.startswith(PNG_MAGIC):
                # ESPN answers some misses with a placeholder or an HTML page.
                failed.append((row.team_name, row.espn_team_id, "not a PNG"))
            else:
                (OUT_DIR / f"{row.espn_team_id}.png").write_bytes(resp.content)
                saved += 1
        except requests.RequestException as exc:
            failed.append((row.team_name, row.espn_team_id, type(exc).__name__))
        if i % 50 == 0:
            print(f"  {i}/{len(todo)} ...")
        time.sleep(args.delay)

    # Manifest maps both ids to the file, so either key works in the app.
    manifest = {
        str(r.team_id): {
            "teamId": r.team_id,
            "espnTeamId": r.espn_team_id,
            "teamName": r.team_name,
            "file": f"{r.espn_team_id}.png",
        }
        for r in rows
        if (OUT_DIR / f"{r.espn_team_id}.png").exists()
    }
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"\nsaved: {saved}   failed: {len(failed)}   manifest entries: {len(manifest)}")
    for name, espn, why in failed[:15]:
        print(f"    ! {name} (espn {espn}): {why}")


if __name__ == "__main__":
    main()
