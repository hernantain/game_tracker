from sqlalchemy import ForeignKey, SmallInteger, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class TournamentSeason(Base):
    """One edition of a competition: "Apertura 2025", "Libertadores 2015".

    A separate table from `tournaments` because the name cannot be derived
    from (competition, year). Argentine top-flight seasons have irregular
    names -- Torneo Inicial, Transición, Superliga, Apertura -- and two can
    share a year: Apertura 2025 and Clausura 2025 are both arg.1 + 2025.

    The id is the legacy identifier ("apertura_2025"), which is also the id
    the old app used in its URLs, so /tournaments/<id> keeps working.
    """

    __tablename__ = "tournament_seasons"

    id:            Mapped[str] = mapped_column(Text, primary_key=True)
    tournament_id: Mapped[str] = mapped_column(
        Text, ForeignKey("tournaments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name:          Mapped[str] = mapped_column(Text, nullable=False)
    year:          Mapped[int] = mapped_column(SmallInteger, nullable=False)

    tournament: Mapped["Tournament"] = relationship(back_populates="seasons")
    games: Mapped[list["Game"]] = relationship(back_populates="season")

    def __repr__(self) -> str:
        return f"<TournamentSeason {self.id!r} {self.name!r}>"
