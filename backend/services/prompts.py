"""The "did you go to this game?" queue.

A single watermark on the profile (`attendance_checked_through`) records how
far the user has been asked, whether they answered yes or no. Anything newer
than the watermark with a known result is still an open question.

A watermark rather than a per-game answer table because a "no" needs no other
data: not attending is the default, and the only thing worth remembering is
that we already asked.
"""

from __future__ import annotations

import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Session, aliased

from ..models import Attendance, Game, Profile, Team

#: ESPN league slugs -> display names. games.competition is NULL for every row
#: ingested before backend_2/seed/sync_games.py existed, so the card falls back
#: to a placeholder rather than inventing a name.
COMPETITION_LABELS = {
    "arg.1": "Liga Profesional",
    "arg.copa": "Copa Argentina",
    "arg.copa_de_la_superliga": "Copa de la Superliga",
    "arg.copa_lpf": "Copa de la Liga Profesional",
    "arg.supercopa": "Supercopa Argentina",
    "arg.supercopa.internacional": "Supercopa Internacional",
    "arg.trofeo_de_la_campeones": "Trofeo de Campeones",
    "conmebol.libertadores": "Copa Libertadores",
    "conmebol.sudamericana": "Copa Sudamericana",
    "conmebol.recopa": "Recopa Sudamericana",
}


def competition_label(slug: str | None) -> str | None:
    if not slug:
        return None
    return COMPETITION_LABELS.get(slug, slug)


def _effective_watermark(session: Session, user_id: str) -> datetime.date | None:
    """How far the user has been asked.

    Falls back to their newest attendance when the column is NULL, so a user
    who has never seen a prompt is asked about games since they last went --
    not about the club's entire back catalogue. With neither, there is no
    sensible floor, so nothing is asked.
    """
    row = session.execute(
        sa.select(Profile.attendance_checked_through).where(Profile.user_id == user_id)
    ).scalar_one_or_none()
    if row:
        return row
    return session.execute(
        sa.select(sa.func.max(Game.date))
        .select_from(Attendance)
        .join(Game, Game.id == Attendance.game_id)
        .where(Attendance.user_id == user_id)
    ).scalar()


def pending(session: Session, user_id: str, team_id: int | None) -> dict:
    """Games still awaiting an answer, oldest first."""
    watermark = _effective_watermark(session, user_id)
    if team_id is None or watermark is None:
        return {"watermark": watermark, "games": []}

    home = aliased(Team)
    away = aliased(Team)
    rows = session.execute(
        sa.select(
            Game.id, Game.date, Game.competition,
            Game.home_team_id, Game.away_team_id,
            Game.home_score, Game.away_score,
            home.team_name.label("home_name"),
            away.team_name.label("away_name"),
            home.espn_team_id.label("home_espn"),
            away.espn_team_id.label("away_espn"),
        )
        .join(home, home.team_id == Game.home_team_id)
        .join(away, away.team_id == Game.away_team_id)
        .where(
            sa.or_(Game.home_team_id == team_id, Game.away_team_id == team_id),
            Game.date > watermark,
            Game.date <= sa.func.current_date(),
            # Only games with a known result: an unplayed or un-ingested
            # fixture cannot be shown as a scoreline.
            Game.home_score.isnot(None),
            Game.away_score.isnot(None),
            ~sa.exists().where(
                sa.and_(Attendance.user_id == user_id, Attendance.game_id == Game.id)
            ),
        )
        .order_by(Game.date.asc(), Game.id.asc())
    ).all()

    games = []
    for r in rows:
        is_home = r.home_team_id == team_id
        ours, theirs = (r.home_score, r.away_score) if is_home else (r.away_score, r.home_score)
        games.append({
            "gameId": r.id,
            "date": r.date.isoformat(),
            "competition": competition_label(r.competition),
            "isHome": is_home,
            "teamName": r.home_name if is_home else r.away_name,
            "rival": r.away_name if is_home else r.home_name,
            "teamEspnId": r.home_espn if is_home else r.away_espn,
            "rivalEspnId": r.away_espn if is_home else r.home_espn,
            "localScore": ours,
            "rivalScore": theirs,
            "result": "W" if ours > theirs else ("L" if ours < theirs else "D"),
        })
    return {"watermark": watermark.isoformat(), "games": games}


def answer(session: Session, user_id: str, game_id: int, attended: bool) -> dict:
    """Record the answer and advance the watermark past this game.

    Idempotent: answering twice leaves the same state. The watermark only ever
    moves forward, so answering an older game out of order cannot rewind it and
    resurrect questions already dealt with.
    """
    game = session.get(Game, game_id)
    if game is None:
        raise LookupError(f"game {game_id} not found")

    existing = session.get(Attendance, {"user_id": user_id, "game_id": game_id})
    if attended and existing is None:
        session.add(Attendance(user_id=user_id, game_id=game_id))
    elif not attended and existing is not None:
        session.delete(existing)

    profile = session.get(Profile, user_id)
    if profile is not None:
        current = profile.attendance_checked_through
        if current is None or game.date > current:
            profile.attendance_checked_through = game.date
        profile.attendance_checked_at = sa.func.now()

    session.commit()
    return {"gameId": game_id, "attended": attended}


def answer_many(
    session: Session, user_id: str, answers: list[tuple[int, bool]]
) -> dict:
    """Answer a batch of prompts: set the rows, then advance the watermark.

    The row work is delegated to services.attendances.set_many; what belongs
    here is the watermark, which moves to the newest game in the batch so
    everything submitted together is settled together -- including the "no"
    answers, which is the whole point of asking.
    """
    if not answers:
        return {"attended": 0, "declined": 0, "watermark": None}

    from .attendances import set_many

    counts = set_many(session, user_id, answers)

    newest = session.execute(
        sa.select(sa.func.max(Game.date)).where(Game.id.in_([gid for gid, _ in answers]))
    ).scalar()
    profile = session.get(Profile, user_id)
    if profile is not None and newest is not None:
        current = profile.attendance_checked_through
        if current is None or newest > current:
            profile.attendance_checked_through = newest
        profile.attendance_checked_at = sa.func.now()
        session.commit()

    return {**counts, "watermark": newest.isoformat() if newest else None}
