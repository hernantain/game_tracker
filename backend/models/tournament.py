import enum

from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class TournamentType(str, enum.Enum):
    """Who organises the competition, which is the only split the app needs.

    AFA competitions are national even when a final is played abroad -- the
    Supercopa Internacional is the awkward case, and it is AFA's, not
    CONMEBOL's.
    """

    national = "national"
    international = "international"


tournament_type = PgEnum(
    TournamentType,
    name="tournament_type",
    schema="public",
    values_callable=lambda e: [m.value for m in e],
)


class Tournament(Base):
    """A competition, not a season of one.

    The primary key is the ESPN league slug ("arg.1") rather than a serial:
    it is already the natural key the ingest works in, it is already the value
    sitting in games.competition, and using it means the foreign key goes on
    that existing column instead of adding a parallel one that could disagree.
    """

    __tablename__ = "tournaments"

    id:   Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[TournamentType] = mapped_column(tournament_type, nullable=False)

    games: Mapped[list["Game"]] = relationship(back_populates="tournament")
    seasons: Mapped[list["TournamentSeason"]] = relationship(back_populates="tournament")

    def __repr__(self) -> str:
        return f"<Tournament {self.id!r} {self.name!r} {self.type}>"
