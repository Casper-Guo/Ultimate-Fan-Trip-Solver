"""Produce NBA season team, venue, and schedule metadata."""

import logging
from itertools import starmap
from pathlib import Path

from pydantic import ValidationError

from trip_solver.data.api.google_maps.places import TextSearch
from trip_solver.data.api.nba.schedule import NBASchedule
from trip_solver.models.api.google_maps.places import TextSearchRequestBody
from trip_solver.models.api.nba.schedule import NBAGame, NBATeam
from trip_solver.models.internal import Event, Events, Team, Teams, Venue, Venues

logging.basicConfig(level=logging.INFO, format="%(filename)s\t%(levelname)s\t%(message)s")
logger = logging.getLogger(__name__)


def format_team_info(team: NBATeam) -> tuple[str, str]:  # noqa: D103
    return str(team.teamId), f"{team.teamCity} {team.teamName}"


def get_arena_full_name(game: NBAGame) -> str:
    """Get the full name of an NBA arena."""
    return f"{game.arenaName}, {game.arenaCity} {game.arenaState}"


def get_venue_info(arena_full_name: str, arena_id: str) -> Venue:
    """Format the response from the Google Maps Places API."""
    try:
        response = (
            TextSearch()
            .post_for_data(
                request_body=TextSearchRequestBody(textQuery=arena_full_name),
            )
            .places[0]
        )
    except ValidationError:
        logger.exception("No matching places for %s", arena_full_name)
        raise

    return Venue(
        # save the name without the city and state
        name=arena_full_name.split(",", maxsplit=1)[0],
        id=arena_id,
        address=response.formattedAddress,
        place_id=response.id,
        location=response.location,
    )


def determine_game_eligibility(game: NBAGame) -> bool:
    """
    Only includes regular season games played in North America with known participants.

    Counterintuitively, a game in Mexico City is included since it has state specified as MX.
    """
    return game.weekNumber >= 1 and game.homeTeam.teamName is not None and bool(game.arenaState)


if __name__ == "__main__":
    nba_schedule = NBASchedule().get_data()

    # NBA API does not provide an arena ID, so we create it ourselves
    arena_ids: dict[str, str] = {}
    unique_teams: set[tuple[str, str]] = set()

    for game_date in nba_schedule.leagueSchedule.gameDates:
        for game in game_date.games:
            # only include regular season games in north America with known participants
            # An arena in Mexico is included because it has a state specified as MX
            if determine_game_eligibility(game):
                if (arena_full_name := get_arena_full_name(game)) not in arena_ids:
                    arena_ids[arena_full_name] = str(len(arena_ids) + 1)
                unique_teams.add(format_team_info(game.homeTeam))
                unique_teams.add(format_team_info(game.awayTeam))

    teams = Teams(teams=[Team(id=id_, name=name).model_dump() for id_, name in unique_teams])
    venues = Venues(venues=list(starmap(get_venue_info, arena_ids.items())))
    logger.info("Finished pinging Places API.")

    events = Events(
        events=[
            Event(
                id=game.gameId,
                time=game.gameDateTimeUTC,
                venue_id=arena_ids[get_arena_full_name(game)],
                home_team_id=str(game.homeTeam.teamId),
                away_team_id=str(game.awayTeam.teamId),
            ).model_dump()
            for game_date in nba_schedule.leagueSchedule.gameDates
            for game in game_date.games
            if determine_game_eligibility(game)
        ],
    )

    directory = Path(__file__).parent
    (directory / "teams.json").write_text(teams.model_dump_json(indent=2))
    (directory / "venues.json").write_text(venues.model_dump_json(indent=2))
    (directory / "events.json").write_text(events.model_dump_json(indent=2))
