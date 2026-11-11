"""What the SQL schema can and cannot answer yet.

The frontend reads this instead of hard-coding which charts to hide, so
filling a gap in the database turns the matching chart back on with no UI
change.
"""

CAPABILITIES: dict[str, dict] = {
    "results": {
        "available": True,
        "label": "Match results, goals for/against, form, streaks",
    },
    "opponents": {"available": True, "label": "Per-opponent record"},
    "venues": {
        "available": True,
        "label": "Home / away split",
        "note": "New in the SQL app -- the legacy JSON had no home/away flag.",
    },
    "appearances": {
        "available": True,
        "label": "Player appearances (starter / substitute / unused)",
    },
    "tournaments": {
        "available": True,
        "label": "Competitions and competition types",
        "note": "Seasons come from the legacy data. Games ingested only from "
                "ESPN have a competition but no season, since the scoreboard "
                "cannot tell an Apertura fixture from a Clausura one.",
    },
    "playerGoals": {
        "available": True,
        "label": "Goals by player, top scorers",
    },
    "goalMinutes": {
        "available": True,
        "label": "Goals by minute",
        "note": "Stoppage-time goals at 90+ are bucketed as 90+, where the "
                "legacy app filed them under 76-90.",
    },
    "goalTypes": {
        "available": True,
        "label": "How goals were scored (header, penalty, free kick...)",
        "note": "New in the SQL app; the legacy JSON had no goal type.",
    },
}


def capabilities() -> dict:
    return CAPABILITIES


def unavailable() -> list[str]:
    return [k for k, v in CAPABILITIES.items() if not v["available"]]
