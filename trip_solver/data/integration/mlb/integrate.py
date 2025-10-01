"""Produce MLB season team, venue, and schedule metadata."""

import json
import logging
from pathlib import Path

from trip_solver.data.api.mlb.schedule import MLBSchedule
from trip_solver.data.api.mlb.teams import MLBTeams
from trip_solver.data.integration import get_venue_info
from trip_solver.models.internal import Event, Events, Team, Teams, Venues
from trip_solver.util.cost_matrix import compute_cost_matrix

logging.basicConfig(level=logging.INFO, format="%(filename)s\t%(levelname)s\t%(message)s")
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    mlb_schedule = MLBSchedule().get_data()
    mlb_teams = MLBTeams().get_data()

    # this list does not contain the all-star teams
    teams = Teams(
        teams=[
            Team(
                id=team.id,
                name=team.name,
            )
            for team in sorted(mlb_teams.teams, key=lambda team: team.id)
        ],
    )
    team_index = {team.id: team for team in teams.teams}

    # construct a mapping from venue ID to the team's location to aid venue lookup
    stadium_locations = {team.venue.id: team.locationName for team in mlb_teams.teams}
    # The As are scheduled to play a few games at the Las Vegas Ballpark
    stadium_locations[5355] = "Las Vegas"

    unique_venues = {
        (game.venue.id, game.venue.name) for date in mlb_schedule.dates for game in date.games
    }
    venues = Venues(
        venues=[
            get_venue_info(
                venue_name,
                stadium_locations.get(venue_id, ""),
                venue_id,
            )
            for venue_id, venue_name in sorted(unique_venues)
        ],
    )
    venue_index = {venue.id: venue for venue in venues.venues}
    distance_matrix, duration_matrix = compute_cost_matrix(venues=venues)

    events = Events(
        events=[
            Event(
                id=game.gamePk,
                time=game.gameDate,
                venue=venue_index[game.venue.id],
                home_team=team_index[game.teams.home.team.id],
                away_team=team_index[game.teams.away.team.id],
            )
            for date in mlb_schedule.dates
            for game in date.games
            if game.seriesDescription == "Regular Season"
        ],
    )

    directory = Path(__file__).parent
    (directory / "teams.json").write_text(teams.model_dump_json(indent=2))
    (directory / "venues.json").write_text(venues.model_dump_json(indent=2))
    (directory / "distance_matrix.json").write_text(json.dumps(distance_matrix, indent=2))
    (directory / "duration_matrix.json").write_text(json.dumps(duration_matrix, indent=2))
    (directory / "events.json").write_text(events.model_dump_json(indent=2))
