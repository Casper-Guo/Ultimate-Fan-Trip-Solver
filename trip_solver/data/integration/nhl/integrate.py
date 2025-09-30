"""Produce NHL season team, venue, and schedule metadata."""

import logging
from datetime import date, datetime
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


def get_venue_name_info(game: NHLScheduleGame) -> tuple[str, str]:  # noqa: D103
    return game.venue.default, game.homeTeam.placeName.default


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

    venue_ids: dict[tuple[str, str], int] = {}
    unique_teams: set[tuple[int, str]] = set()

    for game in nhl_games:
        # Avicii Arena is in Sweden and the only non-NA NHL venue
        # no good automated way to detect such special cases
        # there is a neutralSite attribute but using that also discards special
        # exhibition series and outdoor games etc.
        if get_venue_name_info(game) not in venue_ids and determine_game_eligibility(game):
            venue_ids[get_venue_name_info(game)] = len(venue_ids) + 1
        unique_teams.add((game.homeTeam.id, format_team_name(game.homeTeam)))
        unique_teams.add((game.awayTeam.id, format_team_name(game.awayTeam)))

    teams = Teams(teams=[Team(id=id_, name=name) for id_, name in sorted(unique_teams)])
    team_index = {team.id: team for team in teams.teams}

    venues = Venues(
        venues=[
            get_venue_info(venue_name, venue_place_name, venue_id)
            for (venue_name, venue_place_name), venue_id in sorted(
                venue_ids.items(),
                key=lambda x: x[1],  # noqa: FURB118 preference
            )
        ],
    )
    logger.info("Finished pinging Places API.")
    venue_index = {venue.name: venue for venue in venues.venues}

    events = Events(
        events=[
            Event(
                id=game.id,
                time=datetime.fromisoformat(game.startTimeUTC),
                venue=venue_index[game.venue.default],
                home_team=team_index[game.homeTeam.id],
                away_team=team_index[game.awayTeam.id],
            )
            for game in nhl_games
            if determine_game_eligibility(game)
        ],
    )

    directory = Path(__file__).parent
    (directory / "teams.json").write_text(teams.model_dump_json(indent=2))
    (directory / "venues.json").write_text(venues.model_dump_json(indent=2))
    (directory / "events.json").write_text(events.model_dump_json(indent=2))
