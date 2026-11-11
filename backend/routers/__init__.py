from . import (
    attendance_prompts, attendances, capabilities, games, me,
    opponents, players, seasons, statistics, tournaments,
)

ROUTERS = [
    me.router,
    statistics.router,
    tournaments.router,
    games.router,
    opponents.router,
    players.router,
    seasons.router,
    attendances.router,
    attendance_prompts.router,
    capabilities.router,
]
