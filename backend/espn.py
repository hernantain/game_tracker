"""Minimal ESPN client for the seed scripts.

Vendored from the original ingest pipeline (EXPERIMENTS/supabase_sync.py and
its espn_* helpers) so this project has no dependency on that directory. Only
the parts the seed scripts actually use are here: fetching a season's
scoreboard, fetching one match summary, and turning a scoreboard event into a
game row.

The awkward parts are kept as they were, because they encode real quirks:
  * a scheduled game still reports 0-0, so scores are trusted only once ESPN
    marks the match completed;
  * kickoff times are UTC and have to be converted before the local date is
    read, or late games land on the wrong day.
"""

from __future__ import annotations

import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import requests

SCOREBOARD_URL_TMPL = "https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard"
SUMMARY_URL_TMPL = "https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/summary"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

#: Argentina has no DST, so a fixed offset is correct here.
ARGENTINA_TZ = timezone(timedelta(hours=-3))

RETRY_STATUS = (429, 500, 502, 503, 504)

#: The competitions this project tracks.
LEAGUES = [
    "arg.1",
    "arg.copa",
    "arg.copa_de_la_superliga",
    "arg.copa_lpf",
    "arg.supercopa",
    "arg.supercopa.internacional",
    "arg.trofeo_de_la_campeones",
    "conmebol.libertadores",
    "conmebol.sudamericana",
    "conmebol.recopa",
]


class Failures:
    """Records that could not be read, with enough identity to act on them."""

    def __init__(self, fail_fast: bool = False):
        self.items: list[dict] = []
        self.fail_fast = fail_fast

    def add(self, stage, record, reason, payload=None):
        self.items.append(
            {"stage": stage, "record": record, "reason": reason, "payload": payload}
        )
        print(f"  ! [{stage}] {record} -- {reason}", file=sys.stderr)
        if self.fail_fast:
            self.report()
            sys.exit("Aborting on the first failure (--fail-fast).")

    def __len__(self) -> int:
        return len(self.items)

    def report(self) -> None:
        if not self.items:
            return
        by_stage = defaultdict(list)
        for item in self.items:
            by_stage[item["stage"]].append(item)
        print(f"\n{'=' * 72}", file=sys.stderr)
        print(f"{len(self.items)} failure(s) across {len(by_stage)} stage(s):", file=sys.stderr)
        for stage, items in by_stage.items():
            print(f"\n  [{stage}]  {len(items)} failure(s)", file=sys.stderr)
            for item in items:
                print(f"    - {item['record']}\n        {item['reason']}", file=sys.stderr)
        print(f"{'=' * 72}", file=sys.stderr)


def _body_snippet(response, limit: int = 200) -> str:
    try:
        return " ".join(response.text.split())[:limit]
    except Exception:
        return "<unreadable body>"


def get_json(url, params=None, attempts: int = 3):
    """GET -> (json, None) or (None, reason).

    Retries 429/5xx with backoff. The reason always names the status and a
    snippet of the body, so a failure says what ESPN actually replied.
    """
    reason = "no attempt made"
    for attempt in range(attempts):
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        except requests.RequestException as exc:
            reason = f"{exc.__class__.__name__}: {exc}"
            time.sleep(1 + attempt)
            continue

        if response.status_code in RETRY_STATUS:
            reason = (f"HTTP {response.status_code} after {attempt + 1} attempt(s): "
                      f"{_body_snippet(response)}")
            time.sleep(2 ** attempt)
            continue

        if not response.ok:
            return None, f"HTTP {response.status_code}: {_body_snippet(response)}"

        try:
            return response.json(), None
        except ValueError:
            return None, (f"HTTP {response.status_code} but body is not JSON: "
                          f"{_body_snippet(response)}")

    return None, reason


def fetch_season_events(league: str, season: int):
    """-> (events, None) or (None, reason)."""
    data, error = get_json(
        SCOREBOARD_URL_TMPL.format(league=league),
        params={"dates": season, "limit": 1000},
    )
    if error:
        return None, error
    return data.get("events") or [], None


def fetch_summary(league: str, espn_game_id: str):
    """One match's detail, including keyEvents. -> (json, None) or (None, reason)."""
    return get_json(SUMMARY_URL_TMPL.format(league=league), params={"event": espn_game_id})


def split_kickoff(utc_date: str) -> tuple[str, str]:
    """'2026-01-22T20:00Z' -> ('2026-01-22', '17:00:00') in Argentina time."""
    local = datetime.fromisoformat(utc_date.replace("Z", "+00:00")).astimezone(ARGENTINA_TZ)
    return local.date().isoformat(), local.time().isoformat()


def _parse_score(competitor: dict, completed: bool):
    # A scheduled game still reports '0'-'0', so only trust the score once
    # ESPN marks the match completed.
    if not completed:
        return None
    score = competitor.get("score")
    if score is None or str(score).strip() == "":
        return None
    try:
        return int(score)
    except (TypeError, ValueError):
        raise ValueError(
            f"non-numeric score {score!r} for {competitor.get('homeAway')} side"
        )


def parse_event(event: dict, league: str, season: int, failures: Failures):
    """-> (game_dict, [(espn_team_id, display_name)]) or (None, None).

    Malformed events are reported by id and skipped rather than killing a run
    over hundreds of games.
    """
    event_id = str(event.get("id") or "<no id>")
    label = f"event {event_id} ({league} {season})"
    try:
        competitions = event.get("competitions") or []
        if not competitions:
            raise ValueError("event has no competitions[]")
        competition = competitions[0]

        competitors = competition.get("competitors") or []
        home = next((c for c in competitors if c.get("homeAway") == "home"), None)
        away = next((c for c in competitors if c.get("homeAway") == "away"), None)
        if home is None or away is None:
            found = [c.get("homeAway") for c in competitors]
            raise ValueError(f"no home/away pair, competitors were {found}")

        sides = []
        for side in (home, away):
            team = side.get("team") or {}
            team_id = team.get("id")
            if not team_id:
                raise ValueError(f"{side.get('homeAway')} competitor has no team id")
            sides.append((str(team_id), team.get("displayName") or f"team {team_id}"))

        if not event.get("date"):
            raise ValueError("event has no date")
        date, local_time = split_kickoff(event["date"])

        completed = ((competition.get("status") or {}).get("type") or {}).get("completed", False)
        game = {
            "espn_game_id": event_id,
            "date": date,
            "local_time": local_time,
            "_completed": bool(completed),
            "_label": f"{sides[0][1]} vs {sides[1][1]} on {date}",
            "_home_espn_team_id": sides[0][0],
            "_away_espn_team_id": sides[1][0],
            "home_score": _parse_score(home, completed),
            "away_score": _parse_score(away, completed),
        }
    except Exception as exc:
        failures.add("espn event parse", label,
                     f"{exc.__class__.__name__}: {exc}", payload=event.get("name"))
        return None, None

    return game, sides
