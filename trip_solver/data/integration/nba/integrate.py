"""Produce NBA season team, venue, and schedule metadata."""

import json
import logging
from pathlib import Path

from trip_solver.data.api.nba.schedule import NBATeams, NBATeamSchedule
from trip_solver.data.integration import filter_north_american_venues, get_venue_info
from trip_solver.models.api.nba.schedule import (
    NBAGame,
    NBASeasonType,
    NBATeamSchedulePathParams,
)
from trip_solver.models.internal import Event, Events, Team, Teams
from trip_solver.util.cost_matrix import compute_cost_matrix

logging.basicConfig(level=logging.INFO, format="%(filename)s\t%(levelname)s\t%(message)s")
logger = logging.getLogger(__name__)


def get_venue_name_info(game: NBAGame) -> tuple[str, str]:
    """
    Get NBA venue name and venue place name.

    Unlike the NHL API, the venue address is the actual location of the venue,
    so it can be used for neutral site games too.
    """
    venue = game.competitions[0].venue
    return venue.fullName, " ".join(filter(None, (venue.address.city, venue.address.state)))


def determine_game_eligibility(game: NBAGame) -> bool:
    """
    Only includes regular season games.

    Games outside North America are removed later based on the venue's country.
    """
    return game.seasonType.type is NBASeasonType.REGULAR_SEASON


if __name__ == "__main__":
    nba_teams = NBATeams().get_data()
    nba_team_schedule = NBATeamSchedule()

    teams = Teams(
        teams=sorted(
            (
                Team(id=team.team.id, name=team.team.displayName)
                for team in nba_teams.sports[0].leagues[0].teams
            ),
            key=lambda team: team.id,
        ),
    )
    team_index = {team.id: team for team in teams.teams}

    # each game appears in both participants' schedules
    nba_games: dict[str, NBAGame] = {}
    for team in teams.teams:
        team_schedule = nba_team_schedule.get_data(
            path_params=NBATeamSchedulePathParams(team_id=team.id),
        )
        nba_games.update(
            (game.id, game) for game in team_schedule.events if determine_game_eligibility(game)
        )
    games = sorted(nba_games.values(), key=lambda game: (game.date, game.id))

    # ESPN does not provide a venue ID, so we create it ourselves
    venue_ids: dict[tuple[str, str], int] = {}
    for game in games:
        if (venue_full_name := get_venue_name_info(game)) not in venue_ids:
            venue_ids[venue_full_name] = len(venue_ids) + 1

    venues = filter_north_american_venues(
        get_venue_info(venue_name, venue_place_name, venue_id)
        for (venue_name, venue_place_name), venue_id in sorted(
            venue_ids.items(),
            key=lambda x: x[1],  # noqa: FURB118 preference
        )
    )
    venue_index = {venue.name: venue for venue in venues.venues}
    distance_matrix, duration_matrix = compute_cost_matrix(venues=venues)

    events = Events(
        events=[
            Event(
                id=game.id,
                time=game.date,
                venue=venue_index[game.competitions[0].venue.fullName],
                home_team=team_index[game.get_team("home").id],
                away_team=team_index[game.get_team("away").id],
            )
            for game in games
            if game.competitions[0].venue.fullName in venue_index
        ],
    )

    directory = Path(__file__).parent
    (directory / "teams.json").write_text(teams.model_dump_json(indent=2))
    (directory / "venues.json").write_text(venues.model_dump_json(indent=2))
    (directory / "distance_matrix.json").write_text(json.dumps(distance_matrix, indent=2))
    (directory / "duration_matrix.json").write_text(json.dumps(duration_matrix, indent=2))
    (directory / "events.json").write_text(events.model_dump_json(indent=2))
