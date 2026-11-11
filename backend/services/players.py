"""Player appearance statistics for a user's attended games.

Richer than the legacy app: ESPN's roster data distinguishes three states --
starter, substitute who came on, and unused bench -- where the legacy JSON
only had `players` and `substitutes`. Goals come from the goals table.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Session

from ..models import Appearance, AppearanceRole, Player
from .goals import goals_by_player_map, top_scorers


def appearance_stats(
    session: Session, game_ids: list[int], team_id: int | None, limit: int = 40
) -> dict:
    if not game_ids or team_id is None:
        return {"mostAppearances": [], "mostBench": [], "mostTotal": [], "topScorers": []}

    rows = session.execute(
        sa.select(
            Player.player_id,
            Player.player_name,
            sa.func.count().label("total"),
            sa.func.count(sa.case((Appearance.role == AppearanceRole.starter, 1))).label("starters"),
            sa.func.count(sa.case((Appearance.role == AppearanceRole.substitute, 1))).label("subs"),
            sa.func.count(sa.case((Appearance.role == AppearanceRole.unused, 1))).label("unused"),
        )
        .join(Appearance, Appearance.player_id == Player.player_id)
        .where(Appearance.game_id.in_(game_ids), Appearance.team_id == team_id)
        .group_by(Player.player_id, Player.player_name)
    ).all()

    goals = goals_by_player_map(session, game_ids, team_id)
    players = [
        {
            "playerId": r.player_id,
            "name": r.player_name,
            "starters": r.starters,
            # Legacy "bench" meant "named as a substitute", which is subs plus
            # unused -- keep that definition so the numbers line up.
            "bench": r.subs + r.unused,
            "substitute": r.subs,
            "unused": r.unused,
            "total": r.total,
            "goals": goals.get(r.player_id, 0),
        }
        for r in rows
    ]

    return {
        "mostAppearances": sorted(players, key=lambda p: p["starters"], reverse=True)[:limit],
        "mostBench": sorted(players, key=lambda p: p["bench"], reverse=True)[:limit],
        "mostTotal": sorted(players, key=lambda p: p["total"], reverse=True)[:limit],
        # Scorers come from the goals table, not from appearances: a player can
        # score in a game whose roster was never ingested.
        "topScorers": top_scorers(session, game_ids, team_id),
    }
