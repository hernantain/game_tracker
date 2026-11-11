from typing import Optional

from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import EXTERNAL, Base


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = EXTERNAL

    team_id:      Mapped[int] = mapped_column(Integer, primary_key=True)
    espn_team_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    team_name:    Mapped[str] = mapped_column(Text, nullable=False)
    stadium_name: Mapped[Optional[str]] = mapped_column(Text)

    # Two FK paths from games to teams, so each side names its own.
    home_games: Mapped[list["Game"]] = relationship(
        back_populates="home_team", foreign_keys="Game.home_team_id"
    )
    away_games: Mapped[list["Game"]] = relationship(
        back_populates="away_team", foreign_keys="Game.away_team_id"
    )
    appearances: Mapped[list["Appearance"]] = relationship(back_populates="team")
    fans: Mapped[list["Profile"]] = relationship(back_populates="favorite_team")

    def __repr__(self) -> str:
        return f"<Team {self.team_id} {self.team_name!r}>"
