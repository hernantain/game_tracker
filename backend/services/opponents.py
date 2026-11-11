"""Per-opponent breakdown -- the legacy "rivals" view."""

from __future__ import annotations

from .attended_games import MatchRow


def summarise(matches: list[MatchRow]) -> list[dict]:
    rows: dict[int, dict] = {}
    for m in matches:
        if not m.counts_for_stats:
            continue
        r = rows.setdefault(m.opponent_id, {
            "opponentId": m.opponent_id, "rival": m.opponent,
            "espnTeamId": m.opponent_espn_id, "played": 0,
            "wins": 0, "draws": 0, "losses": 0, "goalsFor": 0, "goalsAgainst": 0,
        })
        r["played"] += 1
        r["goalsFor"] += m.our_score
        r["goalsAgainst"] += m.their_score
        r[{"W": "wins", "D": "draws", "L": "losses"}[m.result]] += 1

    out = []
    for r in rows.values():
        out.append({
            **r,
            "goalDiff": r["goalsFor"] - r["goalsAgainst"],
            "winRate": round(r["wins"] / r["played"] * 100),
            "points": r["wins"] * 3 + r["draws"],
        })
    return sorted(out, key=lambda x: x["played"], reverse=True)
