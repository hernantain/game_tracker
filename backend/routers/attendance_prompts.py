from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import CurrentUser, get_current_user
from ..db import get_db
from ..deps import UserContext, get_user_context, require_registered
from ..schemas import AttendanceBatch
from sqlalchemy.orm import Session

from ..services import prompts as svc

# Every route here requires a registered account, not merely a valid token.
router = APIRouter(
    prefix="/api/attendance-prompts",
    tags=["attendance-prompts"],
    dependencies=[Depends(require_registered)],
)


@router.get("")
def list_prompts(ctx: UserContext = Depends(get_user_context)) -> dict:
    """Games the user has not yet been asked about, oldest first.

    Answer them with PUT /api/attendances/{game_id}, which also advances the
    watermark so they are not asked again.
    """
    return svc.pending(ctx.session, ctx.user.id, ctx.team_id)


@router.put("")
def answer_prompts(
    payload: AttendanceBatch,
    user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> dict:
    """Answer the prompt list: set attendance AND advance the watermark.

    Distinct from PUT /api/attendances, which edits history without touching
    the watermark. Here, every game in the body counts as asked and answered,
    so unticked games are not offered again.
    """
    try:
        return svc.answer_many(
            session, user.id, [(a.gameId, a.attended) for a in payload.answers]
        )
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
