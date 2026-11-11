from fastapi import APIRouter, Depends

from ..deps import require_registered, UserContext, get_user_context
from ..services import capabilities as caps
from ..services import players as svc

# Every route here requires a registered account, not merely a valid token.
router = APIRouter(
    prefix="/api/players",
    tags=["players"],
    dependencies=[Depends(require_registered)],
)


@router.get("")
def list_players(ctx: UserContext = Depends(get_user_context)) -> dict:
    """Appearance leaderboards across the caller's attended games.

    `topScorers` is absent by design -- goal events are not in the database.
    """
    data = svc.appearance_stats(ctx.session, ctx.game_ids, ctx.team_id)
    return {**data, "unavailable": ["playerGoals"] if "playerGoals" in caps.unavailable() else []}
