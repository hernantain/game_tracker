"""Response/request models.

Field names are camelCase to match what the existing frontend already reads
from the legacy API, so the two backends stay swappable.
"""

from __future__ import annotations

import datetime

from pydantic import BaseModel, Field


class TeamOut(BaseModel):
    teamId: int
    teamName: str
    stadiumName: str | None = None
    #: Crest filename stem: /crests/<size>/<espnTeamId>.png
    espnTeamId: str | None = None


class MeOut(BaseModel):
    userId: str
    email: str | None = None
    favoriteTeam: TeamOut | None = None
    attendedGames: int = 0


class GameOut(BaseModel):
    gameId: int
    date: datetime.date
    rival: str
    localScore: int | None = None
    rivalScore: int | None = None
    result: str | None = None
    isHome: bool
    #: Always None: the legacy tournament concept is not modelled in SQL.
    tournament: str | None = None
    #: Display name of the competition, when games.competition is populated.
    competition: str | None = None
    competitionId: str | None = None
    competitionType: str | None = None
    #: Only set when the request asked for a scope wider than attended games.
    attended: bool | None = None
    opponentId: int | None = None
    #: Crest filename stem for the opponent.
    opponentEspnId: str | None = None
    #: Our scorers in this game: [{name, minute, type}].
    goals: list[dict] = Field(default_factory=list)


class OpponentOut(BaseModel):
    opponentId: int
    rival: str
    espnTeamId: str | None = None
    played: int
    wins: int
    draws: int
    losses: int
    goalsFor: int
    goalsAgainst: int
    goalDiff: int
    winRate: int
    points: int


class PlayerStatsOut(BaseModel):
    playerId: int
    name: str
    starters: int
    bench: int
    substitute: int
    unused: int
    total: int
    goals: int | None = None


class StatisticsOut(BaseModel):
    stats: dict
    byYear: list[dict]
    byType: list[dict] = Field(default_factory=list)
    recentMatches: list[dict]
    form: list[str]
    homeAway: dict
    topScorers: list[dict] = Field(default_factory=list)
    goalsByMinute: list[dict] = Field(default_factory=list)
    goalTypes: list[dict] = Field(default_factory=list)
    unavailable: list[str] = Field(default_factory=list)


class CapabilityOut(BaseModel):
    available: bool
    label: str
    note: str | None = None


class AttendanceCreate(BaseModel):
    gameId: int


class AttendanceOut(BaseModel):
    gameId: int
    createdAt: datetime.datetime


class AttendanceSet(BaseModel):
    """Desired end state for one game: did the user attend it or not?"""

    attended: bool


class AttendanceAnswer(BaseModel):
    gameId: int
    attended: bool


class AttendanceBatch(BaseModel):
    """A whole prompt list answered at once.

    Every game shown must be included -- the ones left unticked are the "no"
    answers, and they are what lets the watermark move past them.
    """

    answers: list[AttendanceAnswer] = Field(default_factory=list, max_length=500)
