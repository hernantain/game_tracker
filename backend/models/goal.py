import enum
from typing import Optional

from sqlalchemy import ForeignKey, Index, Integer, SmallInteger, Text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class GoalType(str, enum.Enum):
    """How the goal was scored, as far as the source says.

    `unknown` is the honest default and will be common: the legacy JSON
    records a type for only 98 of its 304 goals.
    """

    regular = "regular"
    header = "header"
    penalty = "penalty"
    free_kick = "free_kick"
    own_goal = "own_goal"
    volley = "volley"
    unknown = "unknown"


goal_type = PgEnum(
    GoalType,
    name="goal_type",
    schema="public",
    values_callable=lambda e: [m.value for m in e],
)


class Goal(Base):
    """A goal in a game, credited to the team that it counted FOR.

    For an own goal that is the opposing team -- the side that benefited --
    so summing goals per team reproduces the scoreline.

    Penalty shootouts are deliberately absent: they decide a tie, not the
    score, and including them would break that sum.
    """

    __tablename__ = "goals"
    __table_args__ = (
        Index("goals_game_id_idx", "game_id"),
        Index("goals_player_id_idx", "player_id"),
    )

    id:      Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teams.team_id", ondelete="RESTRICT"), nullable=False
    )
    #: Resolved scorer. NULL when the name could not be matched to a player who
    #: appeared in the game -- `scorer_name` still records who the source said.
    player_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("players.player_id", ondelete="SET NULL")
    )
    scorer_name: Mapped[Optional[str]] = mapped_column(Text)
    #: Regulation minute. 45+2 is stored as minute=45, stoppage=2.
    minute:   Mapped[Optional[int]] = mapped_column(SmallInteger)
    stoppage: Mapped[Optional[int]] = mapped_column(SmallInteger)
    type: Mapped[GoalType] = mapped_column(
        goal_type, nullable=False, server_default=GoalType.unknown.value
    )

    game:   Mapped["Game"] = relationship(back_populates="goals")
    team:   Mapped["Team"] = relationship()
    player: Mapped[Optional["Player"]] = relationship()

    def __repr__(self) -> str:
        at = f"{self.minute}" + (f"+{self.stoppage}" if self.stoppage else "")
        return f"<Goal g={self.game_id} team={self.team_id} {at}' {self.type}>"
