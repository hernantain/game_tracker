from fastapi import APIRouter, Depends

from ..deps import require_registered, UserContext, get_user_context
from ..schemas import StatisticsOut
from ..services import capabilities as caps
from ..services import goals as goals_svc
from ..services import statistics as stats
from ..services import tournaments as tsvc

# Every route here requires a registered account, not merely a valid token.
router = APIRouter(
    prefix="/api/statistics",
    tags=["statistics"],
    dependencies=[Depends(require_registered)],
)


@router.get("", response_model=StatisticsOut)
def read_statistics(ctx: UserContext = Depends(get_user_context)) -> StatisticsOut:
    """Dashboard aggregate over the caller's attended games."""
    return StatisticsOut(
        stats=stats.compute_stats(ctx.matches),
        byYear=stats.by_year(ctx.matches),
        byType=tsvc.by_type(ctx.matches),
        recentMatches=stats.recent_matches(
            ctx.matches,
            scorers=goals_svc.scorers_by_game(
                ctx.session, [m.game_id for m in ctx.matches[-10:]], ctx.team_id
            ),
        ),
        form=stats.form(ctx.matches),
        homeAway=stats.home_away(ctx.matches),
        topScorers=goals_svc.top_scorers(ctx.session, ctx.game_ids, ctx.team_id, limit=10),
        goalsByMinute=goals_svc.goals_by_minute(ctx.session, ctx.game_ids, ctx.team_id),
        goalTypes=goals_svc.goal_types(ctx.session, ctx.game_ids, ctx.team_id),
        unavailable=caps.unavailable(),
    )
