"""Utilities for solver setup and result interpretation and formatting."""

from datetime import datetime, timedelta
from itertools import permutations
from typing import TypeAlias

from trip_solver.models.internal import CostMatrix, Event, Events
from trip_solver.solver.consts import DUMMY_EVENT_ID
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
    event_length: int = 150,
) -> int:
    """
    Check whether it is feasible to attend both event_1 and event_2.

    driving_time is given in minutes.

    Drive starts one hour after event_1 ends and must arrive by one hour before event_2 starts.
    """
    if event_1.time >= event_2.time:
        return False

    allowed_start = event_1.time + timedelta(minutes=event_length + 60)
    end_of_start_day = strip_datetime(allowed_start) + timedelta(days=1)
    start_day_driving_time = min(
        (end_of_start_day - allowed_start).total_seconds() // 60,
        60 * max_driving_hours_per_day,
    )

    allowed_end = event_2.time - timedelta(hours=1)
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


def build_matchup_matrix(events: Events) -> MatchupMatrix:
    """Build a matchup matrix that include both teams for every event."""
    return {
        event.id: {
            event.home_team.id: 1,
            event.away_team.id: 1,
        }
        for event in events.events
    }


def build_one_sided_matchup_matrix(
    events: Events,
    focus_team_id: int,
    home_only: bool = False,
    away_only: bool = True,
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

    return matrix


def add_dummy_event_to_matchup_matrix(matchup_matrix: MatchupMatrix) -> MatchupMatrix:
    """Add a dummy event that has no teams."""
    matchup_matrix[DUMMY_EVENT_ID] = {}
    return matchup_matrix


def build_venue_matrix(events: Events) -> VenueMatrix:  # noqa: D103
    return {event.id: {event.venue.id: 1} for event in events.events}


def generate_trip_duration_matrix(events: list[Event]) -> CostMatrix:
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
    return cost_matrix


def generate_driving_cost_matrix(events: list[Event], route_matrix: CostMatrix) -> CostMatrix:
    """Construct event cost matrix from venue-indexed route matrix."""
    return {
        event_i.id: {event_j.id: route_matrix[event_i.venue.id][event_j.venue.id]}
        for event_i, event_j in permutations(events, 2)
    }


def add_dummy_event_to_cost_matrix(cost_matrix: CostMatrix) -> CostMatrix:
    """Add a dummy event that has zero cost from and to all other events."""
    for event_id in cost_matrix:
        cost_matrix[event_id][DUMMY_EVENT_ID] = 0
        cost_matrix[DUMMY_EVENT_ID][event_id] = 0
    return cost_matrix


def generate_cost_matrix(
    events: list[Event],
    measure: CostMeasure,
    route_matrix: CostMatrix | None = None,
) -> CostMatrix:
    """Generate cost matrix for all event pairs."""
    if measure is CostMeasure.TOTAL_DURATION:
        return add_dummy_event_to_cost_matrix(generate_trip_duration_matrix(events))
    if measure is CostMeasure.DRIVING_DISTANCE or measure is CostMeasure.DRIVING_DURATION:
        if route_matrix is None:
            raise ValueError("Route matrix must be provided for driving cost measures.")
        return add_dummy_event_to_cost_matrix(
            generate_driving_cost_matrix(events, route_matrix),
        )
    raise ValueError(f"Unsupported cost measure: {measure}")
