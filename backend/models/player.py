from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import EXTERNAL, Base


class Player(Base):
    __tablename__ = "players"
    __table_args__ = EXTERNAL

    player_id:      Mapped[int] = mapped_column(Integer, primary_key=True)
    espn_player_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    player_name:    Mapped[str] = mapped_column(Text, nullable=False)

    appearances: Mapped[list["Appearance"]] = relationship(back_populates="player")

    def __repr__(self) -> str:
        return f"<Player {self.player_id} {self.player_name!r}>"
