"""Goal statistics -- the legacy app's scorer and minute charts.

Scoped to one team's goals, because "top scorers" means ours, not everyone
who scored in a game we attended. The goals table holds both sides so the
scoreline reconciles; these helpers filter.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Session

from ..models import Goal, Player

#: The legacy buckets, in the legacy order.
BUCKETS = (
    ("0-15", 1, 15),
    ("16-30", 16, 30),
    ("31-45", 31, 45),
    ("46-60", 46, 60),
    ("61-75", 61, 75),
    ("76-90", 76, 90),
    ("90+", 91, 200),
)


def top_scorers(
    session: Session, game_ids: list[int], team_id: int | None, limit: int | None = None
) -> list[dict]:
    """Goals per player, most first.

    `matchesScored` is the number of distinct games they scored in, which is
    what the legacy app showed alongside the total.
    """
    if not game_ids or team_id is None:
        return []
    rows = session.execute(
        sa.select(
            Player.player_id,
            Player.player_name,
            sa.func.count().label("goals"),
            sa.func.count(sa.distinct(Goal.game_id)).label("matches"),
        )
        .join(Player, Player.player_id == Goal.player_id)
        .where(Goal.game_id.in_(game_ids), Goal.team_id == team_id)
        .group_by(Player.player_id, Player.player_name)
        .order_by(sa.desc("goals"), Player.player_name)
    ).all()
    out = [
        {
            "playerId": r.player_id,
            "name": r.player_name,
            "goals": r.goals,
            "matchesScored": r.matches,
        }
        for r in rows
    ]
    return out[:limit] if limit else out


def goals_by_minute(
    session: Session, game_ids: list[int], team_id: int | None
) -> list[dict]:
    """Goals per quarter-hour bucket.

    Differs from the legacy app in one deliberate way: a 90+5 goal lands in
    "90+", not "76-90". Legacy truncated at the "+" before bucketing, so every
    stoppage-time winner was filed as if it arrived on the 90th minute.
    First-half stoppage (45+2) still sits in "31-45", where it belongs.
    """
    if not game_ids or team_id is None:
        return [{"range": name, "goals": 0} for name, _, _ in BUCKETS]

    rows = session.execute(
        sa.select(Goal.minute, Goal.stoppage)
        .where(Goal.game_id.in_(game_ids), Goal.team_id == team_id)
    ).all()

    counts = {name: 0 for name, _, _ in BUCKETS}
    for minute, stoppage in rows:
        if minute is None:
            continue
        effective = 91 if (minute >= 90 and stoppage) else minute
        for name, lo, hi in BUCKETS:
            if lo <= effective <= hi:
                counts[name] += 1
                break
    return [{"range": name, "goals": counts[name]} for name, _, _ in BUCKETS]


def goals_by_player_map(
    session: Session, game_ids: list[int], team_id: int | None
) -> dict[int, int]:
    """player_id -> goals, for decorating appearance leaderboards."""
    if not game_ids or team_id is None:
        return {}
    return {
        r.player_id: r.goals
        for r in session.execute(
            sa.select(Goal.player_id, sa.func.count().label("goals"))
            .where(
                Goal.game_id.in_(game_ids),
                Goal.team_id == team_id,
                Goal.player_id.isnot(None),
            )
            .group_by(Goal.player_id)
        ).all()
    }


def goal_types(
    session: Session, game_ids: list[int], team_id: int | None
) -> list[dict]:
    """Breakdown by how the goal was scored -- new, the legacy app had no type."""
    if not game_ids or team_id is None:
        return []
    rows = session.execute(
        sa.select(Goal.type, sa.func.count().label("goals"))
        .where(Goal.game_id.in_(game_ids), Goal.team_id == team_id)
        .group_by(Goal.type)
        .order_by(sa.desc("goals"))
    ).all()
    return [{"type": r.type.value, "goals": r.goals} for r in rows]


def scorers_by_game(
    session: Session, game_ids: list[int], team_id: int | None
) -> dict[int, list[dict]]:
    """game_id -> [{name, minute}], for the match-row scorer lists.

    One query for the whole page rather than one per row: a 139-row match list
    would otherwise be 139 round trips.
    """
    if not game_ids or team_id is None:
        return {}
    rows = session.execute(
        sa.select(Goal.game_id, Goal.scorer_name, Goal.minute, Goal.stoppage, Goal.type)
        .where(Goal.game_id.in_(game_ids), Goal.team_id == team_id)
        .order_by(Goal.game_id, Goal.minute.nulls_last(), Goal.stoppage.nulls_first())
    ).all()
    out: dict[int, list[dict]] = {}
    for r in rows:
        minute = ""
        if r.minute is not None:
            minute = f"{r.minute}+{r.stoppage}" if r.stoppage else str(r.minute)
        out.setdefault(r.game_id, []).append({
            "name": r.scorer_name,
            "minute": minute,
            "type": r.type.value,
        })
    return out
