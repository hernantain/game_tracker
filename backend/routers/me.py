import logging

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from ..auth import CurrentUser, get_current_user
from ..db import get_db
from ..deps import UserContext, get_user_context
from ..models import Team
from ..schemas import MeOut
from ..services import accounts

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/me", tags=["me"])


@router.get("", response_model=MeOut)
def read_me(ctx: UserContext = Depends(get_user_context)) -> MeOut:
    """The caller's identity, favourite club and attendance count."""
    team = None
    if ctx.team_id is not None:
        row = ctx.session.execute(
            sa.select(Team).where(Team.team_id == ctx.team_id)
        ).scalar_one_or_none()
        if row:
            team = {
                "teamId": row.team_id,
                "teamName": row.team_name,
                "stadiumName": row.stadium_name,
                "espnTeamId": row.espn_team_id,
            }
    return MeOut(
        userId=ctx.user.id,
        email=ctx.user.email,
        favoriteTeam=team,
        attendedGames=len(ctx.matches),
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> Response:
    """Discard an abandoned, unregistered account.

    Called when someone reaches the sign-in flow with a Google account that was
    never registered. GoTrue has already created the auth.users row by then, so
    this removes it instead of leaving an orphan behind.

    Deliberately narrow:
      * the id comes from the verified token, so only the caller's own account
        can ever be targeted;
      * a caller WITH a profiles row is refused, so this can never destroy a
        real account. Deleting a registered account is a separate concern that
        would need its own confirmed flow.
    """
    if accounts.is_registered(session, user.id):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This account is registered; use a dedicated account-deletion flow.",
        )
    try:
        accounts.delete_auth_user(user.id)
    except accounts.AccountDeletionError as exc:
        # Cleanup is best-effort: never block sign-out on it. The orphan can be
        # collected later, and the caller is signed out either way.
        log.warning("could not delete unregistered user %s: %s", user.id, exc)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
