from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from ..auth import CurrentUser, get_current_user
from ..db import get_db
from ..deps import require_registered
from ..schemas import AttendanceBatch, AttendanceCreate, AttendanceOut, AttendanceSet
from ..services import attendances as svc

# Every route here requires a registered account, not merely a valid token.
router = APIRouter(
    prefix="/api/attendances",
    tags=["attendances"],
    dependencies=[Depends(require_registered)],
)


@router.get("", response_model=list[AttendanceOut])
def list_attendances(
    user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> list[AttendanceOut]:
    rows = svc.list_for_user(session, user.id)
    return [AttendanceOut(gameId=r.game_id, createdAt=r.created_at) for r in rows]


@router.post("", response_model=AttendanceOut, status_code=status.HTTP_201_CREATED)
def create_attendance(
    payload: AttendanceCreate,
    user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> AttendanceOut:
    """Record that the caller attended a game.

    The user id comes from the verified token, never the request body.
    """
    if not svc.game_exists(session, payload.gameId):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Game not found")
    row = svc.add(session, user.id, payload.gameId)
    return AttendanceOut(gameId=row.game_id, createdAt=row.created_at)


@router.delete("/{game_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendance(
    game_id: int,
    user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> Response:
    if not svc.remove(session, user.id, game_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Attendance not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{game_id}")
def set_attendance(
    game_id: int,
    payload: AttendanceSet,
    user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> dict:
    """Set whether the caller attended one game. Idempotent either way.

    Does not move the prompt watermark -- see PUT /api/attendance-prompts for
    the flow that answers questions rather than editing history.
    """
    try:
        return svc.set_many(session, user.id, [(game_id, payload.attended)])
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))


@router.put("")
def set_attendances(
    payload: AttendanceBatch,
    user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> dict:
    """Set attendance for many games at once -- the settings page.

    PUT on the collection because the body states the desired end state for
    each game listed; resubmitting the same body changes nothing. The prompt
    watermark is untouched, so correcting history cannot silently dismiss
    questions the user has not seen yet.
    """
    try:
        return svc.set_many(
            session, user.id, [(a.gameId, a.attended) for a in payload.answers]
        )
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
