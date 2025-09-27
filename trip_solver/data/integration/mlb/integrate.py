"""Produce MLB season team, venue, and schedule metadata."""

import logging
from pathlib import Path

from pydantic import ValidationError

from trip_solver.data.api.google_maps.places import TextSearch
from trip_solver.data.api.mlb.schedule import MLBSchedule
from trip_solver.data.api.mlb.teams import MLBTeams
from trip_solver.models.api.google_maps.places import TextSearchRequestBody
from trip_solver.models.internal import Event, Events, Team, Teams, Venue, Venues

logging.basicConfig(level=logging.INFO, format="%(filename)s\t%(levelname)s\t%(message)s")
logger = logging.getLogger(__name__)


def get_venue_info(venue_full_name: str, venue_id: int) -> Venue:
    """Format the response from the Google Maps Places API."""
    try:
        response = (
            TextSearch()
            .post_for_data(
                request_body=TextSearchRequestBody(textQuery=venue_full_name),
            )
            .places[0]
        )
    except ValidationError:
        logger.exception("No matching places for %s", venue_full_name)
        raise

    return Venue(
        # save the name without the city and state
        name=venue_full_name.split(",", maxsplit=1)[0],
        id=str(venue_id),
        address=response.formattedAddress,
        place_id=response.id,
        location=response.location,
    )


if __name__ == "__main__":
    mlb_schedule = MLBSchedule().get_data()
    mlb_teams = MLBTeams().get_data()

    # this list does not contain the all-star teams
    teams = Teams(
        teams=[
            Team(
                id=str(team.id),
                name=team.name,
            )
            for team in mlb_teams.teams
        ],
    )

    # construct a mapping from venue ID to the team's location to aid venue lookup
    stadium_locations = {team.venue.id: team.locationName for team in mlb_teams.teams}
    # The As are scheduled to play a few games in Las Vegas
    stadium_locations[5355] = "Las Vegas"

    unique_venues = {
        (game.venue.name, game.venue.id) for date in mlb_schedule.dates for game in date.games
    }
    venues = Venues(
        venues=[
            get_venue_info(
                f"{venue_name}, {stadium_locations.get(venue_id, '')}",
                venue_id,
            )
            for venue_name, venue_id in unique_venues
        ],
    )
    logger.info("Finished pinging Places API.")

    events = Events(
        events=[
            Event(
                id=str(game.gamePk),
                time=game.gameDate,
                venue_id=str(game.venue.id),
                home_team_id=str(game.teams.home.team.id),
                away_team_id=str(game.teams.away.team.id),
            )
            for date in mlb_schedule.dates
            for game in date.games
            if game.seriesDescription == "Regular Season"
        ],
    )

    directory = Path(__file__).parent
    (directory / "teams.json").write_text(teams.model_dump_json(indent=2))
    (directory / "venues.json").write_text(venues.model_dump_json(indent=2))
    (directory / "events.json").write_text(events.model_dump_json(indent=2))
