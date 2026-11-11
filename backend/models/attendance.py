import datetime
import uuid as uuid_mod

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Attendance(Base):
    """A game a user went to.

    Composite primary key rather than a surrogate: nothing will ever reference
    an attendance row, and (user_id, game_id) gives "one attendance per user
    per game" for free. Note this differs from the house style in
    `appearances`, which uses a serial id plus a unique constraint.

    The link carries no business rule of its own -- which games a user may
    record is enforced by the application, not the schema.
    """

    __tablename__ = "attendances"
    # Reverse lookup: "who attended game X". The composite PK already covers
    # the (user_id, ...) direction. Named to match house style.
    __table_args__ = (Index("attendances_game_id_idx", "game_id"),)

    user_id: Mapped[uuid_mod.UUID] = mapped_column(
        Uuid, ForeignKey("profiles.user_id", ondelete="CASCADE"), primary_key=True
    )
    game_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("games.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    profile: Mapped["Profile"] = relationship(back_populates="attendances")
    game: Mapped["Game"] = relationship(back_populates="attendances")

    def __repr__(self) -> str:
        return f"<Attendance user={self.user_id} game={self.game_id}>"
