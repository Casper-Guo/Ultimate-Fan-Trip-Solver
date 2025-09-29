"""Produce NHL season team, venue, and schedule metadata."""

import logging
from datetime import date, datetime
from itertools import starmap
from pathlib import Path

from trip_solver.data.api.nhl.schedule import NHLSchedule
from trip_solver.data.integration import get_venue_info
from trip_solver.models.api.nhl.schedule import (
    NHLScheduleGame,
    NHLSchedulePathParams,
    NHLScheduleTeam,
)
from trip_solver.models.internal import Event, Events, Team, Teams, Venues

logging.basicConfig(level=logging.INFO, format="%(filename)s\t%(levelname)s\t%(message)s")
logger = logging.getLogger(__name__)


def format_team_name(team: NHLScheduleTeam) -> str:  # noqa: D103
    return f"{team.placeName.default} {team.commonName.default}"


def get_arena_full_name(game: NHLScheduleGame) -> str:  # noqa: D103
    return f"{game.venue.default}, {game.homeTeam.placeName.default}"


def determine_game_eligibility(game: NHLScheduleGame) -> bool:  # noqa: D103
    return game.venue.default != "Avicii Arena"


if __name__ == "__main__":
    nhl_schedule = NHLSchedule()
    nhl_schedule_now = NHLSchedule().get_data()

    nhl_games: list[NHLScheduleGame] = []
    next_start_date: date | None = nhl_schedule_now.regularSeasonStartDate

    while (
        next_start_date is not None and next_start_date <= nhl_schedule_now.regularSeasonEndDate
    ):
        game_week = nhl_schedule.get_data(
            path_params=NHLSchedulePathParams(time=next_start_date.strftime("%Y-%m-%d")),
        )
        for game_day in game_week.gameWeek:
            nhl_games.extend(game_day.games)
        next_start_date = game_week.nextStartDate

    arena_ids: dict[str, str] = {}
    unique_teams: set[tuple[int, str]] = set()

    for game in nhl_games:
        # Avicii Arena is in Sweden and the only non-NA NHL venue
        # no good automated way to detect such special cases
        # there is a neutralSite attribute but using that also discards special
        # exhibition series and outdoor games etc.
        if game.venue.default not in arena_ids and determine_game_eligibility(game):
            arena_ids[game.venue.default] = str(len(arena_ids) + 1)
        unique_teams.add((game.homeTeam.id, format_team_name(game.homeTeam)))
        unique_teams.add((game.awayTeam.id, format_team_name(game.awayTeam)))

    teams = Teams(teams=[Team(id=id_, name=name) for id_, name in unique_teams])
    venues = Venues(venues=list(starmap(get_venue_info, arena_ids.items())))
    logger.info("Finished pinging Places API.")
    events = Events(
        events=[
            Event(
                id=game.id,
                time=datetime.fromisoformat(game.startTimeUTC),
                venue_id=arena_ids[game.venue.default],
                home_team_id=game.homeTeam.id,
                away_team_id=game.awayTeam.id,
            )
            for game in nhl_games
            if determine_game_eligibility(game)
        ],
    )

    directory = Path(__file__).parent
    (directory / "teams.json").write_text(teams.model_dump_json(indent=2))
    (directory / "venues.json").write_text(venues.model_dump_json(indent=2))
    (directory / "events.json").write_text(events.model_dump_json(indent=2))
