from fastapi import APIRouter, Depends, HTTPException, Query

from ..deps import UserContext, get_user_context, require_registered
from ..schemas import GameOut
from ..services import goals as goals_svc
from ..services import prompts
from ..services.attended_games import load_club_games

# Every route here requires a registered account, not merely a valid token.
router = APIRouter(
    prefix="/api/games",
    tags=["games"],
    dependencies=[Depends(require_registered)],
)


def _to_out(m, attended: bool | None = None, scorers=None) -> GameOut:
    return GameOut(
        gameId=m.game_id, date=m.date, rival=m.opponent,
        localScore=m.our_score, rivalScore=m.their_score,
        result=m.result, isHome=m.is_home,
        competition=m.competition_name or prompts.competition_label(m.competition),
        competitionId=m.competition,
        competitionType=m.competition_type,
        attended=attended,
        opponentId=m.opponent_id,
        opponentEspnId=m.opponent_espn_id,
        goals=(scorers or {}).get(m.game_id) or [],
    )


@router.get("", response_model=list[GameOut])
def list_games(
    ctx: UserContext = Depends(get_user_context),
    attended: str = Query(
        "true",
        pattern="^(true|false|all)$",
        description='"true" (default) = only games you attended; "all" = every '
                    'game your club has played, each flagged; "false" = the rest.',
    ),
    year: int | None = Query(None, description="Calendar year of the fixture"),
    competition: str | None = Query(None, description="tournaments.id, e.g. arg.1"),
    competition_type: str | None = Query(
        None, alias="competitionType", pattern="^(national|international)$"
    ),
    result: str | None = Query(None, pattern="^[WDL]$"),
    opponent_id: int | None = Query(None, alias="opponentId"),
    venue: str | None = Query(None, pattern="^(home|away)$"),
    search: str | None = Query(None, description="Case-insensitive opponent name match"),
) -> list[GameOut]:
    """Games, newest first. Scope is set by `attended`."""
    if attended == "true":
        rows = ctx.matches
        attended_ids = None
    else:
        # The attended set is already loaded on the context, so flagging the
        # full history costs one more query rather than two.
        attended_ids = set(ctx.game_ids)
        rows = load_club_games(ctx.session, ctx.team_id)
        if attended == "false":
            rows = [m for m in rows if m.game_id not in attended_ids]
    if year is not None:
        rows = [m for m in rows if m.date.year == year]
    if competition:
        rows = [m for m in rows if m.competition == competition]
    if competition_type:
        rows = [m for m in rows if m.competition_type == competition_type]
    if result:
        rows = [m for m in rows if m.result == result]
    if opponent_id is not None:
        rows = [m for m in rows if m.opponent_id == opponent_id]
    if venue:
        rows = [m for m in rows if m.is_home == (venue == "home")]
    if search:
        q = search.lower()
        rows = [m for m in rows if q in m.opponent.lower()]
    # One query for the page, not one per row.
    scorers = goals_svc.scorers_by_game(
        ctx.session, [m.game_id for m in rows], ctx.team_id
    )
    return [
        _to_out(m, None if attended_ids is None else m.game_id in attended_ids, scorers)
        for m in reversed(rows)
    ]


@router.get("/{game_id}", response_model=GameOut)
def read_game(game_id: int, ctx: UserContext = Depends(get_user_context)) -> GameOut:
    for m in ctx.matches:
        if m.game_id == game_id:
            return _to_out(m)
    raise HTTPException(404, "Game not found among your attended games")
