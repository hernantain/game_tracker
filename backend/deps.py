"""Shared request dependencies."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.orm import Session

from fastapi import HTTPException, status

from .auth import CurrentUser, get_current_user
from .db import get_db
from .services.accounts import is_registered
from .services.attended_games import MatchRow, get_perspective_team_id, load_attended


@dataclass
class UserContext:
    """Everything a stats endpoint needs: who is asking, which club their
    numbers are about, and the games they attended."""

    user: CurrentUser
    team_id: int | None
    matches: list[MatchRow]
    session: Session

    @property
    def game_ids(self) -> list[int]:
        return [m.game_id for m in self.matches]


def get_user_context(
    user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> UserContext:
    team_id = get_perspective_team_id(session, user.id)
    matches = load_attended(session, user.id, team_id)
    return UserContext(user=user, team_id=team_id, matches=matches, session=session)


def require_registered(
    user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> CurrentUser:
    """Reject callers who authenticated but are not registered with the app.

    A valid Supabase token only proves the Google sign-in worked -- anyone can
    obtain one. Registration is a profiles row, so the data endpoints check for
    it server-side rather than trusting the UI to hide them.

    Deliberately NOT applied to /api/me (a caller must be able to discover its
    own state) or to DELETE /api/me (which exists precisely to clean up an
    unregistered account).
    """
    if not is_registered(session, user.id):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Account is not registered. Complete sign-up to access this data.",
        )
    return user
