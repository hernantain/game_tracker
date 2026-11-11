"""Loads a user's attended games, normalised to one team's point of view.

The SQL schema is neutral -- `games` has home_team_id/away_team_id -- while
every statistic the app shows is relative to one club ("we scored", "we won").
That club is the user's favourite, so the same code works for any team rather
than hard-coding Racing the way the legacy app does.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

import sqlalchemy as sa
from sqlalchemy.orm import Session, aliased

from ..models import Attendance, Game, Profile, Team, Tournament, TournamentSeason


@dataclass(frozen=True)
class MatchRow:
    """One attended game, seen from the perspective team's side."""

    game_id: int
    date: datetime.date
    opponent_id: int
    opponent: str
    our_score: int | None
    their_score: int | None
    is_home: bool
    #: 'W' / 'D' / 'L', or None when the game has no recorded score, or when
    #: the perspective team did not play in it.
    result: str | None
    #: ESPN league slug, NULL for rows ingested before sync_games.py existed.
    competition: str | None = None
    #: Opponent's ESPN team id -- the crest filename in /crests/<size>/.
    opponent_espn_id: str | None = None
    #: Display name and national/international split, via the tournaments FK.
    competition_name: str | None = None
    competition_type: str | None = None
    #: The specific edition -- "Libertadores 2015" -- via tournament_seasons.
    season_id: str | None = None
    season_name: str | None = None
    season_year: int | None = None

    @property
    def counts_for_stats(self) -> bool:
        return self.result is not None


def _result(ours: int, theirs: int) -> str:
    if ours > theirs:
        return "W"
    if ours < theirs:
        return "L"
    return "D"


def get_perspective_team_id(session: Session, user_id: str) -> int | None:
    """The club the user's statistics are computed about."""
    return session.execute(
        sa.select(Profile.favorite_team_id).where(Profile.user_id == user_id)
    ).scalar_one_or_none()


def load_attended(session: Session, user_id: str, team_id: int | None) -> list[MatchRow]:
    """Every game the user attended, oldest first.

    Ordered ascending because the streak calculations below read
    chronologically -- the legacy app relies on the same ordering.
    """
    home = aliased(Team)
    away = aliased(Team)
    rows = session.execute(
        sa.select(
            Game.id, Game.date, Game.home_score, Game.away_score,
            Game.home_team_id, Game.away_team_id, Game.competition,
            home.team_name.label("home_name"),
            away.team_name.label("away_name"),
            home.espn_team_id.label("home_espn"),
            away.espn_team_id.label("away_espn"),
            Tournament.name.label("comp_name"),
            Tournament.type.label("comp_type"),
            TournamentSeason.id.label("season_id"),
            TournamentSeason.name.label("season_name"),
            TournamentSeason.year.label("season_year"),
        )
        .join(Attendance, Attendance.game_id == Game.id)
        .outerjoin(Tournament, Tournament.id == Game.competition)
        .outerjoin(TournamentSeason, TournamentSeason.id == Game.tournament_season_id)
        .join(home, home.team_id == Game.home_team_id)
        .join(away, away.team_id == Game.away_team_id)
        .where(Attendance.user_id == user_id)
        .order_by(Game.date.asc(), Game.id.asc())
    ).all()

    out: list[MatchRow] = []
    for r in rows:
        if team_id == r.home_team_id:
            is_home, ours, theirs = True, r.home_score, r.away_score
            opp_id, opp, opp_espn = r.away_team_id, r.away_name, r.away_espn
        elif team_id == r.away_team_id:
            is_home, ours, theirs = False, r.away_score, r.home_score
            opp_id, opp, opp_espn = r.home_team_id, r.home_name, r.home_espn
        else:
            # Attended a game the perspective team did not play in. Listed,
            # but it cannot contribute a win or a loss.
            out.append(MatchRow(
                game_id=r.id, date=r.date, opponent_id=r.away_team_id,
                opponent=f"{r.home_name} v {r.away_name}",
                our_score=None, their_score=None, is_home=False, result=None,
                competition=r.competition, opponent_espn_id=r.away_espn,
                competition_name=r.comp_name,
                competition_type=r.comp_type.value if r.comp_type else None,
                season_id=r.season_id, season_name=r.season_name,
                season_year=r.season_year,
            ))
            continue

        # A NULL score means the result was never recorded. Treating it as 0
        # would invent a draw, so it is listed without a result instead.
        res = _result(ours, theirs) if ours is not None and theirs is not None else None
        out.append(MatchRow(
            game_id=r.id, date=r.date, opponent_id=opp_id, opponent=opp,
            our_score=ours, their_score=theirs, is_home=is_home, result=res,
            competition=r.competition, opponent_espn_id=opp_espn,
            competition_name=r.comp_name,
            competition_type=r.comp_type.value if r.comp_type else None,
            season_id=r.season_id, season_name=r.season_name,
            season_year=r.season_year,
        ))
    return out


def load_club_games(session: Session, team_id: int | None) -> list[MatchRow]:
    """Every game the perspective club has played, oldest first.

    Unlike load_attended this ignores attendance entirely -- the settings page
    needs the full history so the user can correct it. Games without a result
    are excluded: you cannot have attended a fixture that has not been played
    or whose score was never ingested.
    """
    if team_id is None:
        return []

    home = aliased(Team)
    away = aliased(Team)
    rows = session.execute(
        sa.select(
            Game.id, Game.date, Game.home_score, Game.away_score,
            Game.home_team_id, Game.away_team_id, Game.competition,
            home.team_name.label("home_name"),
            away.team_name.label("away_name"),
            home.espn_team_id.label("home_espn"),
            away.espn_team_id.label("away_espn"),
            Tournament.name.label("comp_name"),
            Tournament.type.label("comp_type"),
            TournamentSeason.id.label("season_id"),
            TournamentSeason.name.label("season_name"),
            TournamentSeason.year.label("season_year"),
        )
        .join(home, home.team_id == Game.home_team_id)
        .join(away, away.team_id == Game.away_team_id)
        .outerjoin(Tournament, Tournament.id == Game.competition)
        .outerjoin(TournamentSeason, TournamentSeason.id == Game.tournament_season_id)
        .where(
            sa.or_(Game.home_team_id == team_id, Game.away_team_id == team_id),
            Game.home_score.isnot(None),
            Game.away_score.isnot(None),
            Game.date <= sa.func.current_date(),
        )
        .order_by(Game.date.asc(), Game.id.asc())
    ).all()

    out: list[MatchRow] = []
    for r in rows:
        is_home = r.home_team_id == team_id
        ours, theirs = (r.home_score, r.away_score) if is_home else (r.away_score, r.home_score)
        opp_id = r.away_team_id if is_home else r.home_team_id
        opp = r.away_name if is_home else r.home_name
        opp_espn = r.away_espn if is_home else r.home_espn
        out.append(MatchRow(
            game_id=r.id, date=r.date, opponent_id=opp_id, opponent=opp,
            our_score=ours, their_score=theirs, is_home=is_home,
            result=_result(ours, theirs), competition=r.competition,
            opponent_espn_id=opp_espn,
            competition_name=r.comp_name,
            competition_type=r.comp_type.value if r.comp_type else None,
            season_id=r.season_id, season_name=r.season_name,
            season_year=r.season_year,
        ))
    return out
