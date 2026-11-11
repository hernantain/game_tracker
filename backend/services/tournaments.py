"""Per-competition breakdown of a user's attended games.

Lists tournament *seasons* -- "Libertadores 2015", "Apertura 2025" -- exactly
as the legacy app did, via the tournament_seasons table. Games outside the
legacy data have no season (ESPN knows the league and year but not whether an
arg.1 2025 fixture is the Apertura or the Clausura) and are grouped under a
single unknown entry rather than silently dropped.
"""

from __future__ import annotations

from .attended_games import MatchRow
from .statistics import compute_stats

def summarise(matches: list[MatchRow]) -> list[dict]:
    """One row per tournament season, newest first."""
    groups: dict[str, list[MatchRow]] = {}
    for m in matches:
        groups.setdefault(m.season_id or "", []).append(m)

    out = []
    for season_id, rows in groups.items():
        first = rows[0]
        last = max(m.date for m in rows)
        out.append({
            "id": season_id or None,
            "name": first.season_name,
            "competition": first.competition_name,
            "competitionId": first.competition,
            "type": first.competition_type,
            "year": first.season_year or last.year,
            "lastPlayed": last.isoformat(),
            "firstPlayed": min(m.date for m in rows).isoformat(),
            **compute_stats(rows),
        })
    # Newest season first; anything without a season sinks to the bottom.
    return sorted(out, key=lambda t: (t["id"] is not None, t["year"], t["lastPlayed"]),
                  reverse=True)


def by_type(matches: list[MatchRow]) -> list[dict]:
    """National vs international, for the dashboard chart."""
    buckets: dict[str, dict] = {}
    for m in matches:
        if not m.counts_for_stats or not m.competition_type:
            continue
        b = buckets.setdefault(m.competition_type, {
            "type": m.competition_type,
            # The UI localises from `type`; this is only a safety net.
            "name": m.competition_type,
            "games": 0, "wins": 0, "draws": 0, "losses": 0,
            "goalsScored": 0, "goalsConceded": 0,
        })
        b["games"] += 1
        b["goalsScored"] += m.our_score
        b["goalsConceded"] += m.their_score
        b[{"W": "wins", "D": "draws", "L": "losses"}[m.result]] += 1
    return sorted(buckets.values(), key=lambda x: x["games"], reverse=True)
