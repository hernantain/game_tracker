import datetime
from typing import Optional

from sqlalchemy import Date, ForeignKey, Integer, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import EXTERNAL, Base


class Game(Base):
    """A fixture. Note the table holds unplayed games too: scores stay NULL
    until a result exists, and 139 past-dated rows have no score at all
    (ingest gaps), so never treat a NULL score as "future"."""

    __tablename__ = "games"
    __table_args__ = EXTERNAL

    id:           Mapped[int] = mapped_column(Integer, primary_key=True)
    date:         Mapped[datetime.date] = mapped_column(Date, nullable=False)
    local_time:   Mapped[Optional[datetime.time]] = mapped_column(Time)
    home_team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.team_id"), nullable=False)
    away_team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.team_id"), nullable=False)
    home_score:   Mapped[Optional[int]] = mapped_column(Integer)
    away_score:   Mapped[Optional[int]] = mapped_column(Integer)
    espn_game_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    #: ESPN league slug (e.g. "arg.1"), recorded by backend_2/seed/sync_games.py
    #: and foreign-keyed to tournaments.id. NULL for rows ingested before that
    #: script existed, so the UI still needs a placeholder.
    competition: Mapped[Optional[str]] = mapped_column(
        Text, ForeignKey("tournaments.id", ondelete="SET NULL")
    )

    home_team: Mapped["Team"] = relationship(
        back_populates="home_games", foreign_keys=[home_team_id]
    )
    away_team: Mapped["Team"] = relationship(
        back_populates="away_games", foreign_keys=[away_team_id]
    )
    appearances: Mapped[list["Appearance"]] = relationship(back_populates="game")
    attendances: Mapped[list["Attendance"]] = relationship(back_populates="game")
    goals: Mapped[list["Goal"]] = relationship(
        back_populates="game", cascade="all, delete-orphan"
    )
    #: Which edition of the competition. NULL for games outside the legacy
    #: data: the ESPN scoreboard knows the league and year but not whether an
    #: arg.1 2025 fixture belongs to the Apertura or the Clausura.
    tournament_season_id: Mapped[Optional[str]] = mapped_column(
        Text, ForeignKey("tournament_seasons.id", ondelete="SET NULL")
    )

    tournament: Mapped[Optional["Tournament"]] = relationship(back_populates="games")
    season: Mapped[Optional["TournamentSeason"]] = relationship(back_populates="games")

    def __repr__(self) -> str:
        return f"<Game {self.id} {self.date} {self.home_team_id}v{self.away_team_id}>"
