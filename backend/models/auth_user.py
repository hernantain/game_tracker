"""Partial, read-only mapping of Supabase's auth.users.

GoTrue owns this table. Only the columns worth joining against are mapped;
never write through it, and never let a migration tool manage it.
"""

import datetime
import uuid as uuid_mod
from typing import Optional

from sqlalchemy import DateTime, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class AuthUser(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth", "info": {"is_external": True}}

    id:              Mapped[uuid_mod.UUID] = mapped_column(Uuid, primary_key=True)
    email:           Mapped[Optional[str]] = mapped_column(Text)
    created_at:      Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))
    last_sign_in_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True))

    profile: Mapped[Optional["Profile"]] = relationship(back_populates="user", uselist=False)

    def __repr__(self) -> str:
        return f"<AuthUser {self.id}>"
