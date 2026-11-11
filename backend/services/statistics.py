"""Aggregate statistics over a user's attended games.

Mirrors the legacy `compute_stats` in backend/main.py field for field, so the
two apps can be compared directly.
"""

from __future__ import annotations

from .attended_games import MatchRow

RESULT_KEY = {"W": "wins", "D": "draws", "L": "losses"}


def compute_stats(matches: list[MatchRow]) -> dict:
    played = [m for m in matches if m.counts_for_stats]

    wins = draws = losses = goals_scored = goals_conceded = 0
    clean_sheets = failed_to_score = 0
    win_streak = max_win_streak = unbeaten = max_unbeaten = 0
    biggest_win = biggest_loss = None
    biggest_win_diff = biggest_loss_diff = -1

    for m in played:
        ours, theirs = m.our_score, m.their_score
        if m.result == "W":
            wins += 1
            win_streak += 1
            unbeaten += 1
        elif m.result == "D":
            draws += 1
            win_streak = 0
            unbeaten += 1
        else:
            losses += 1
            win_streak = 0
            unbeaten = 0

        max_win_streak = max(max_win_streak, win_streak)
        max_unbeaten = max(max_unbeaten, unbeaten)

        goals_scored += ours
        goals_conceded += theirs
        if theirs == 0:
            clean_sheets += 1
        if ours == 0:
            failed_to_score += 1

        diff = ours - theirs
        if diff > biggest_win_diff:
            biggest_win_diff, biggest_win = diff, m
        if -diff > biggest_loss_diff:
            biggest_loss_diff, biggest_loss = -diff, m

    total = len(played)
    stats: dict = {
        "totalGames": total,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "goalsScored": goals_scored,
        "goalsConceded": goals_conceded,
        "goalDifference": goals_scored - goals_conceded,
        "cleanSheets": clean_sheets,
        "failedToScore": failed_to_score,
        "winRate": round(wins / total * 100) if total else 0,
        "avgGoalsScored": round(goals_scored / total, 2) if total else 0,
        "avgGoalsConceded": round(goals_conceded / total, 2) if total else 0,
        "points": wins * 3 + draws,
        "maxWinStreak": max_win_streak,
        "maxUnbeaten": max_unbeaten,
    }

    def extreme(m: MatchRow) -> dict:
        return {
            "rival": m.opponent,
            "rivalEspnId": m.opponent_espn_id,
            "localScore": m.our_score,
            "rivalScore": m.their_score,
            # Competition is not modelled in SQL yet -- see /api/capabilities.
            "tournament": None,
            "date": m.date.isoformat(),
        }

    if biggest_win:
        stats["biggestWin"] = extreme(biggest_win)
    if biggest_loss and biggest_loss_diff > 0:
        stats["biggestLoss"] = extreme(biggest_loss)
    return stats


def by_year(matches: list[MatchRow]) -> list[dict]:
    buckets: dict[int, dict] = {}
    for m in matches:
        if not m.counts_for_stats:
            continue
        y = m.date.year
        b = buckets.setdefault(y, {
            "year": y, "games": 0, "wins": 0, "draws": 0, "losses": 0,
            "goalsScored": 0, "goalsConceded": 0,
        })
        b["games"] += 1
        b["goalsScored"] += m.our_score
        b["goalsConceded"] += m.their_score
        b[RESULT_KEY[m.result]] += 1
    return sorted(buckets.values(), key=lambda x: x["year"])


def recent_matches(
    matches: list[MatchRow], limit: int = 10,
    scorers: dict[int, list[dict]] | None = None,
) -> list[dict]:
    return [
        {
            "gameId": m.game_id,
            "rival": m.opponent,
            "rivalEspnId": m.opponent_espn_id,
            "localScore": m.our_score,
            "rivalScore": m.their_score,
            "date": m.date.isoformat(),
            "isHome": m.is_home,
            "tournament": None,
            "result": m.result,
            "goals": (scorers or {}).get(m.game_id) or [],
        }
        for m in reversed(matches[-limit:])
    ]


def form(matches: list[MatchRow], limit: int = 5) -> list[str]:
    played = [m for m in matches if m.counts_for_stats]
    return [m.result for m in reversed(played[-limit:])]


def home_away(matches: list[MatchRow]) -> dict:
    """Split the record by venue -- new in the SQL app; the legacy JSON had no
    home/away flag at all, only Racing's score and the opponent's."""
    out = {
        "home": {"games": 0, "wins": 0, "draws": 0, "losses": 0, "goalsScored": 0, "goalsConceded": 0},
        "away": {"games": 0, "wins": 0, "draws": 0, "losses": 0, "goalsScored": 0, "goalsConceded": 0},
    }
    for m in matches:
        if not m.counts_for_stats:
            continue
        side = out["home" if m.is_home else "away"]
        side["games"] += 1
        side["goalsScored"] += m.our_score
        side["goalsConceded"] += m.their_score
        side[RESULT_KEY[m.result]] += 1
    return out
