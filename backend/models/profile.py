import datetime
import uuid as uuid_mod
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Profile(Base):
    """Application data hanging off a Supabase auth user.

    One row per user: user_id is both primary and foreign key, which is what
    makes the relationship one-to-one and a second row impossible.
    """

    __tablename__ = "profiles"
    # Name pinned to what migration a1b2c3d4e5f6 created, so autogenerate
    # does not propose a pointless drop-and-recreate rename.
    __table_args__ = (Index("profiles_favorite_team_id_idx", "favorite_team_id"),)

    user_id: Mapped[uuid_mod.UUID] = mapped_column(
        Uuid, ForeignKey("auth.users.id", ondelete="CASCADE"), primary_key=True
    )
    # SET NULL, not CASCADE: retiring a club must not delete people.
    favorite_team_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("teams.team_id", ondelete="SET NULL")
    )
    #: Games up to and including this date have been put to the user, whether
    #: they said yes or no. NULL means never prompted -- the service then falls
    #: back to the newest attendance so a new account is not ambushed with
    #: hundreds of historical fixtures.
    attendance_checked_through: Mapped[Optional[datetime.date]] = mapped_column(Date)
    #: When the user last answered a prompt. Informational.
    attendance_checked_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["AuthUser"] = relationship(back_populates="profile")
    favorite_team: Mapped[Optional["Team"]] = relationship(back_populates="fans")
    attendances: Mapped[list["Attendance"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Profile {self.user_id} team={self.favorite_team_id}>"
