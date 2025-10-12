"""Utilities for solver setup and result interpretation and formatting."""

from datetime import datetime, timedelta
from itertools import permutations
from typing import TypeAlias
from zoneinfo import ZoneInfo

from trip_solver.models.internal import CostMatrix, Event, Events, Teams
from trip_solver.solver.consts import AVG_EVENT_LENGTH, DUMMY_EVENT_ID
from trip_solver.util.cost_matrix import CostMeasure

# outer map keys are the event IDs
# inner map uses sparse representation
# non-existent key imply the team is not participating in the event
MatchupMatrix: TypeAlias = dict[str, dict[int, int]]

# outer map keys are the event IDs
# inner map keys are the venue IDs
VenueMatrix: TypeAlias = dict[str, dict[int, int]]


def strip_datetime(dt: datetime) -> datetime:
    """Strip datetime to the beginning of the day."""
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def available_driving_time(
    event_1: Event,
    event_2: Event,
    max_driving_hours_per_day: int,
    event_length: int = AVG_EVENT_LENGTH,
) -> int:
    """
    Check whether it is feasible to attend both event_1 and event_2.

    driving_time is given in minutes.

    Drive starts one hour after event_1 ends and must arrive by one hour before event_2 starts.
    """
    if event_1.time >= event_2.time:
        return -1

    event_1_time = event_1.time.astimezone(tz=ZoneInfo("America/New_York"))
    event_2_time = event_2.time.astimezone(tz=ZoneInfo("America/New_York"))

    allowed_start = event_1_time + timedelta(minutes=event_length + 60)
    end_of_start_day = strip_datetime(allowed_start) + timedelta(days=1)
    start_day_driving_time = min(
        (end_of_start_day - allowed_start).total_seconds() // 60,
        60 * max_driving_hours_per_day,
    )

    allowed_end = event_2_time - timedelta(hours=1)
    start_of_end_day = strip_datetime(allowed_end)
    end_day_driving_time = min(
        (allowed_end - strip_datetime(allowed_end)).total_seconds() // 60,
        60 * max_driving_hours_per_day,
    )

    full_days_between = max((start_of_end_day - end_of_start_day).days, 0)
    return int(
        full_days_between * max_driving_hours_per_day * 60
        + start_day_driving_time
        + end_day_driving_time,
    )


def add_dummy_to_matchup_matrix(matchup_matrix: MatchupMatrix) -> MatchupMatrix:
    """Add a dummy event that has no teams."""
    matchup_matrix[DUMMY_EVENT_ID] = {}
    return matchup_matrix


def build_matchup_matrix(events: Events, include_dummy: bool = True) -> MatchupMatrix:
    """Build a matchup matrix that include both teams for every event."""
    ret = {
        event.id: {
            event.home_team.id: 1,
            event.away_team.id: 1,
        }
        for event in events.events
    }
    return add_dummy_to_matchup_matrix(ret) if include_dummy else ret


def build_one_sided_matchup_matrix(
    events: Events,
    focus_team_id: int,
    home_only: bool = False,
    away_only: bool = True,
    include_dummy: bool = True,
) -> MatchupMatrix:
    """
    Build a matchup matrix that only includes the events the focus team participates in.

    This matrix also only includes the opponent of the focus team for each event.
    """
    matrix: MatchupMatrix = {}

    for event in events.events:
        if event.home_team.id == focus_team_id and not away_only:
            matrix[event.id] = {event.away_team.id: 1}
        elif event.away_team.id == focus_team_id and not home_only:
            matrix[event.id] = {event.home_team.id: 1}

    return add_dummy_to_matchup_matrix(matrix) if include_dummy else matrix


def add_dummy_to_venue_matrix(venue_matrix: VenueMatrix) -> VenueMatrix:
    """Add a dummy event that has no venue."""
    venue_matrix[DUMMY_EVENT_ID] = {}
    return venue_matrix


def build_venue_matrix(events: Events, include_dummy: bool = True) -> VenueMatrix:  # noqa: D103
    ret = {event.id: {event.venue.id: 1} for event in events.events}
    return add_dummy_to_venue_matrix(ret) if include_dummy else ret


def add_dummy_to_cost_matrix(cost_matrix: CostMatrix, events: list[Event]) -> CostMatrix:
    """Add a dummy event that has zero cost from and to all other events."""
    cost_matrix[DUMMY_EVENT_ID] = {}
    for event_id in (event.id for event in events):
        if event_id not in cost_matrix:
            # this is usually the last event in the list
            # as it cannot reach any other event, it is omitted from the dummyless cost matrix
            cost_matrix[event_id] = {DUMMY_EVENT_ID: 0}
        cost_matrix[event_id][DUMMY_EVENT_ID] = 0
        cost_matrix[DUMMY_EVENT_ID][event_id] = 0
    return cost_matrix


def build_trip_duration_matrix(events: list[Event], include_dummy: bool = True) -> CostMatrix:
    """
    Return the length of the trip to attend viable event pairs.

    The cost c_ij is only defined if event j is after event i.
    """
    cost_matrix: CostMatrix = {}
    for event_i, event_j in permutations(events, 2):
        if event_i.time >= event_j.time:
            continue
        if event_i.id not in cost_matrix:
            cost_matrix[event_i.id] = {}
        cost_matrix[event_i.id][event_j.id] = (event_j.time.date() - event_i.time.date()).days
    return add_dummy_to_cost_matrix(cost_matrix, events) if include_dummy else cost_matrix


def build_driving_cost_matrix(
    events: list[Event],
    route_matrix: CostMatrix,
    include_dummy: bool = True,
) -> CostMatrix:
    """Construct event cost matrix from venue-indexed route matrix."""
    driving_cost_matrix: CostMatrix = {}
    for event_i, event_j in permutations(events, 2):
        if event_i.id not in driving_cost_matrix:
            driving_cost_matrix[event_i.id] = {}
        driving_cost_matrix[event_i.id][event_j.id] = route_matrix[event_i.venue.id][
            event_j.venue.id
        ]
    return (
        add_dummy_to_cost_matrix(driving_cost_matrix, events)
        if include_dummy
        else driving_cost_matrix
    )


def build_cost_matrix(
    events: list[Event],
    measure: CostMeasure,
    route_matrix: CostMatrix | None = None,
    include_dummy: bool = True,
) -> CostMatrix:
    """Build cost matrix for all event pairs."""
    if measure is CostMeasure.TRIP_DURATION:
        return build_trip_duration_matrix(events, include_dummy)
    if measure is CostMeasure.DRIVING_DISTANCE or measure is CostMeasure.DRIVING_DURATION:
        if route_matrix is None:
            raise ValueError("Route matrix must be provided for driving cost measures.")
        return build_driving_cost_matrix(events, route_matrix, include_dummy)
    raise ValueError(f"Unsupported cost measure: {measure}")


def remove_infeasible_teams(teams: Teams, team_name: str) -> Teams:
    """
    Remove teams pairing that do not face each other in an eligible game.

    For example, in the 2025-26 NHL season, the Nashville Predators do not face
    the Pittsburgh Penguins in North America.
    """
    # NHL Sweden series
    if team_name == "Nashville Predators":
        return Teams(
            teams=[team for team in teams.teams if team.name != "Pittsburgh Penguins"],
        )
    if team_name == "Pittsburgh Penguins":
        return Teams(
            teams=[team for team in teams.teams if team.name != "Nashville Predators"],
        )
    # NBA Europe games
    if team_name == "Orlando Magic":
        return Teams(
            teams=[team for team in teams.teams if team.name != "Memphis Grizzlies"],
        )
    if team_name == "Memphis Grizzlies":
        return Teams(
            teams=[team for team in teams.teams if team.name != "Orlando Magic"],
        )
    return teams
