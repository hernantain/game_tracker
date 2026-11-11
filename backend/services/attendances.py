"""Create, list and remove the games a user went to."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from ..models import Attendance, Game


def list_for_user(session: Session, user_id: str) -> list[Attendance]:
    return list(session.execute(
        sa.select(Attendance)
        .join(Game, Game.id == Attendance.game_id)
        .where(Attendance.user_id == user_id)
        .order_by(Game.date.desc())
    ).scalars())


def game_exists(session: Session, game_id: int) -> bool:
    return session.get(Game, game_id) is not None


def add(session: Session, user_id: str, game_id: int) -> Attendance:
    existing = session.get(Attendance, {"user_id": user_id, "game_id": game_id})
    if existing:
        return existing
    row = Attendance(user_id=user_id, game_id=game_id)
    session.add(row)
    session.commit()
    return row


def remove(session: Session, user_id: str, game_id: int) -> bool:
    result = session.execute(
        sa.delete(Attendance).where(
            Attendance.user_id == user_id, Attendance.game_id == game_id
        )
    )
    session.commit()
    return result.rowcount > 0


def set_many(session: Session, user_id: str, answers: list[tuple[int, bool]]) -> dict:
    """Set attendance for many games at once. No side effects beyond the rows.

    One statement per branch rather than a call per game: a round trip costs
    far more than the work, so editing a season should be one request.

    Deliberately does NOT touch the prompt watermark -- that belongs to
    answering prompts (services/prompts.answer_many), not to correcting
    history. Editing old games must not silently dismiss pending questions.
    """
    if not answers:
        return {"attended": 0, "declined": 0, "games": 0}

    # Last answer wins if the same game appears twice.
    deduped: dict[int, bool] = dict(answers)
    known = set(
        session.execute(
            sa.select(Game.id).where(Game.id.in_(list(deduped)))
        ).scalars()
    )
    missing = sorted(set(deduped) - known)
    if missing:
        raise LookupError(f"games not found: {missing}")

    attended = [gid for gid, yes in deduped.items() if yes]
    declined = [gid for gid, yes in deduped.items() if not yes]

    if attended:
        session.execute(
            pg_insert(Attendance)
            .values([{"user_id": user_id, "game_id": gid} for gid in attended])
            .on_conflict_do_nothing(index_elements=["user_id", "game_id"])
        )
    if declined:
        session.execute(
            sa.delete(Attendance).where(
                Attendance.user_id == user_id,
                Attendance.game_id.in_(declined),
            )
        )
    session.commit()
    return {"attended": len(attended), "declined": len(declined), "games": len(deduped)}
