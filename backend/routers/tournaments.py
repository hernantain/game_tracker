from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import UserContext, get_user_context, require_registered
from ..services import goals as goals_svc
from ..services import players as players_svc
from ..services import statistics as stats
from ..services import tournaments as svc

# Every route here requires a registered account, not merely a valid token.
router = APIRouter(
    prefix="/api/tournaments",
    tags=["tournaments"],
    dependencies=[Depends(require_registered)],
)


@router.get("")
def list_tournaments(ctx: UserContext = Depends(get_user_context)) -> list[dict]:
    """Tournament seasons the caller has attended games in, newest first."""
    return svc.summarise(ctx.matches)


@router.get("/{tournament_id}")
def read_tournament(
    tournament_id: str, ctx: UserContext = Depends(get_user_context)
) -> dict:
    """One tournament season: its record plus the attended games.

    Accepts a season id ("libertadores_2015") and falls back to a competition
    id ("conmebol.libertadores"), so both the legacy URLs and the competition
    slugs resolve.
    """
    rows = [m for m in ctx.matches if m.season_id == tournament_id]
    if not rows:
        rows = [m for m in ctx.matches if m.competition == tournament_id]
    if not rows:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "No attended games in that tournament",
        )
    return {
        "id": tournament_id,
        "name": rows[0].season_name or rows[0].competition_name,
        "competition": rows[0].competition_name,
        "type": rows[0].competition_type,
        "year": rows[0].season_year,
        "stats": stats.compute_stats(rows),
        "matches": stats.recent_matches(
            rows, limit=len(rows),
            scorers=goals_svc.scorers_by_game(
                ctx.session, [m.game_id for m in rows], ctx.team_id
            ),
        ),
        "topScorers": goals_svc.top_scorers(
            ctx.session, [m.game_id for m in rows], ctx.team_id
        ),
        # Appearances are, though, so the squad list survives.
        "playerStats": players_svc.appearance_stats(
            ctx.session, [m.game_id for m in rows], ctx.team_id, limit=25
        )["mostAppearances"],
    }
