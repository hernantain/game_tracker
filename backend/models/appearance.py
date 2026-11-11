import enum
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, SmallInteger, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import EXTERNAL, Base


class AppearanceRole(str, enum.Enum):
    """Values of the public.appearance_role Postgres enum.

    ESPN's `starter` + `subbedIn` flags describe three states, not two: a
    starter, a substitute who came on, and an unused bench player. Around a
    third of roster rows are unused, so collapsing them would inflate every
    appearance count.
    """

    starter = "starter"
    substitute = "substitute"
    unused = "unused"


appearance_role_type = PgEnum(
    AppearanceRole,
    name="appearance_role",
    schema="public",
    values_callable=lambda e: [m.value for m in e],
    create_type=False,  # the type already exists in the database
)


class Appearance(Base):
    __tablename__ = "appearances"
    __table_args__ = (
        UniqueConstraint("game_id", "player_id", name="appearances_game_id_player_id_key"),
        EXTERNAL,
    )

    appearance_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id:       Mapped[int] = mapped_column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    player_id:     Mapped[int] = mapped_column(
        Integer, ForeignKey("players.player_id"), nullable=False
    )
    team_id:       Mapped[int] = mapped_column(
        Integer, ForeignKey("teams.team_id"), nullable=False
    )
    role:          Mapped[AppearanceRole] = mapped_column(appearance_role_type, nullable=False)
    subbed_out:    Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    shirt_number:  Mapped[Optional[int]] = mapped_column(SmallInteger)
    position:      Mapped[Optional[str]] = mapped_column(Text)

    game:   Mapped["Game"]   = relationship(back_populates="appearances")
    player: Mapped["Player"] = relationship(back_populates="appearances")
    team:   Mapped["Team"]   = relationship(back_populates="appearances")

    def __repr__(self) -> str:
        return f"<Appearance {self.appearance_id} g={self.game_id} p={self.player_id}>"
