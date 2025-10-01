"""Produce NBA season team, venue, and schedule metadata."""

import json
import logging
from pathlib import Path

from trip_solver.data.api.nba.schedule import NBASchedule
from trip_solver.data.integration import get_venue_info
from trip_solver.models.api.nba.schedule import NBAGame, NBATeam
from trip_solver.models.internal import Event, Events, Team, Teams, Venues
from trip_solver.util.cost_matrix import compute_cost_matrix

logging.basicConfig(level=logging.INFO, format="%(filename)s\t%(levelname)s\t%(message)s")
logger = logging.getLogger(__name__)


def format_team_info(team: NBATeam) -> tuple[int, str]:  # noqa: D103
    return team.teamId, f"{team.teamCity} {team.teamName}"


def get_venue_name_info(game: NBAGame) -> tuple[str, str]:
    """Get NBA venue name and venue place name."""
    return game.arenaName, f"{game.arenaCity} {game.arenaState}"


def determine_game_eligibility(game: NBAGame) -> bool:
    """
    Only includes regular season games played in North America with known participants.

    Counterintuitively, a game in Mexico City is included since it has state specified as MX.
    """
    return game.weekNumber >= 1 and game.homeTeam.teamName is not None and bool(game.arenaState)


if __name__ == "__main__":
    nba_schedule = NBASchedule().get_data()

    # NBA API does not provide an venue ID, so we create it ourselves
    venue_ids: dict[tuple[str, str], int] = {}
    unique_teams: set[tuple[int, str]] = set()

    for game_date in nba_schedule.leagueSchedule.gameDates:
        for game in game_date.games:
            # only include regular season games in north America with known participants
            # An venue in Mexico is included because it has a state specified as MX
            if determine_game_eligibility(game):
                if (venue_full_name := get_venue_name_info(game)) not in venue_ids:
                    venue_ids[venue_full_name] = len(venue_ids) + 1
                unique_teams.add(format_team_info(game.homeTeam))
                unique_teams.add(format_team_info(game.awayTeam))

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
    venue_index = {venue.name: venue for venue in venues.venues}
    distance_matrix, duration_matrix = compute_cost_matrix(venues=venues)

    events = Events(
        events=[
            Event(
                id=game.gameId,
                time=game.gameDateTimeUTC,
                venue=venue_index[game.arenaName],
                home_team=team_index[game.homeTeam.teamId],
                away_team=team_index[game.awayTeam.teamId],
            )
            for game_date in nba_schedule.leagueSchedule.gameDates
            for game in game_date.games
            if determine_game_eligibility(game)
        ],
    )

    directory = Path(__file__).parent
    (directory / "teams.json").write_text(teams.model_dump_json(indent=2))
    (directory / "venues.json").write_text(venues.model_dump_json(indent=2))
    (directory / "distance_matrix.json").write_text(json.dumps(distance_matrix, indent=2))
    (directory / "duration_matrix.json").write_text(json.dumps(duration_matrix, indent=2))
    (directory / "events.json").write_text(events.model_dump_json(indent=2))
