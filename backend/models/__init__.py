"""All mapped models.

Importing this package registers every table on `Base.metadata`, which is what
alembic/env.py targets.
"""

from .appearance import Appearance, AppearanceRole, appearance_role_type
from .attendance import Attendance
from .auth_user import AuthUser
from .base import Base
from .game import Game
from .goal import Goal, GoalType, goal_type
from .player import Player
from .profile import Profile
from .team import Team
from .tournament import Tournament, TournamentType, tournament_type
from .tournament_season import TournamentSeason

__all__ = [
    "Appearance",
    "AppearanceRole",
    "appearance_role_type",
    "Attendance",
    "AuthUser",
    "Base",
    "Game",
    "Goal",
    "GoalType",
    "goal_type",
    "Player",
    "Profile",
    "Team",
    "Tournament",
    "TournamentSeason",
    "TournamentType",
    "tournament_type",
]
