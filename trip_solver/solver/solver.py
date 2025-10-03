"""Linear programming formulator and solver."""

import logging
from itertools import permutations

import pulp  # type: ignore

from trip_solver.models.internal import CostMatrix, Event, Team
from trip_solver.solver.consts import DUMMY_EVENT_ID
from trip_solver.util.solver_util import MatchupMatrix, available_driving_time

logging.basicConfig(level=logging.INFO, format="%(filename)s\t%(levelname)s\t%(message)s")
logger = logging.getLogger(__name__)


def create_edge_variables(
    events: list[Event],
    max_driving_hours_per_day: int,
    driving_duration_matrix: CostMatrix,
) -> dict[tuple[str, str], pulp.LpVariable]:
    """
    Create one edge variable for each feasible pair of events.

    At most one of x_ij and x_ji is defined. x_ii is never defined.
    """
    edge_variable_dict: dict[tuple[str, str], pulp.LpVariable] = {}
    for event_i, event_j in permutations(events, 2):
        if (
            available_driving_time(
                event_i,
                event_j,
                max_driving_hours_per_day,
            )
            <= driving_duration_matrix[event_i.id][event_j.id]
        ):
            edge_variable_dict[(event_i.id, event_j.id)] = pulp.LpVariable(
                f"x_{event_i.id}_{event_j.id}",
                cat=pulp.LpBinary,
            )

    # add the dummy event edge variables
    for event in events:
        edge_variable_dict[(DUMMY_EVENT_ID, event.id)] = pulp.LpVariable(
            f"x_{DUMMY_EVENT_ID}_{event.id}",
            cat=pulp.LpBinary,
        )
        edge_variable_dict[(event.id, DUMMY_EVENT_ID)] = pulp.LpVariable(
            f"x_{event.id}_{DUMMY_EVENT_ID}",
            cat=pulp.LpBinary,
        )

    return edge_variable_dict


def create_order_variables(events: list[Event]) -> dict[str, pulp.LpVariable]:
    """Create one order variable for each event."""
    order_variables = {
        event.id: pulp.LpVariable(
            f"u_{event.id}",
            lowBound=0,
            upBound=len(events) + 1,
            cat=pulp.LpContinuous,
        )
        for event in events
    }

    # add the dummy event order variable and fix it to 1
    order_variables[DUMMY_EVENT_ID] = pulp.LpVariable(
        f"u_{DUMMY_EVENT_ID}",
        lowBound=0,
        upBound=len(events) + 1,
        cat=pulp.LpContinuous,
    )
    order_variables[DUMMY_EVENT_ID].setInitialValue(1)
    order_variables[DUMMY_EVENT_ID].fixValue()
    return order_variables


def add_tour_constraints(
    problem: pulp.LpProblem,
    events: list[Event],
    edge_variables: dict[tuple[str, str], pulp.LpVariable],
) -> None:
    """Constraint the in and out degrees of non-dummy events to be at most 1."""
    event_ids = [event.id for event in events]
    for event_i_id in event_ids:
        problem += (
            pulp.lpSum(
                edge_variables.get((event_i_id, event_j_id), 0)
                for event_j_id in [*event_ids, DUMMY_EVENT_ID]
            ),
            f"in_degree_{event_i_id}",
        )
        problem += (
            pulp.lpSum(
                edge_variables.get((event_j_id, event_i_id), 0)
                for event_j_id in [*event_ids, DUMMY_EVENT_ID]
            ),
            f"out_degree_{event_i_id}",
        )


def add_dummy_event_ordering_constraint(
    problem: pulp.LpProblem,
    events: list[Event],
    edge_variables: dict[tuple[str, str], pulp.LpVariable],
) -> None:
    """Constraint dummy event in and out degree to be exactly 1."""
    problem += (
        pulp.lpSum(edge_variables[(DUMMY_EVENT_ID, event.id)] for event in events) == 1,
        "dummy_event_out_degree",
    )
    problem += (
        pulp.lpSum(edge_variables[(event.id, DUMMY_EVENT_ID)] for event in events) == 1,
        "dummy_event_in_degree",
    )


def add_subtour_elimination_constraints(  # noqa: D103
    problem: pulp.LpProblem,
    events: list[Event],
    edge_variables: dict[tuple[str, str], pulp.LpVariable],
    order_variables: dict[str, pulp.LpVariable],
    num_teams: int,
) -> None:
    event_ids = [event.id for event in events] + [DUMMY_EVENT_ID]
    for event_i_id, event_j_id in permutations(event_ids, 2):
        if (event_i_id, event_j_id) in edge_variables:
            problem += (
                order_variables[event_i_id]
                - order_variables[event_j_id]
                + (num_teams + 2) * edge_variables[(event_i_id, event_j_id)]
                <= num_teams + 1,
                f"subtour_elimination_{event_i_id}_{event_j_id}",
            )


def add_opponent_constraints(
    problem: pulp.LpProblem,
    events: list[Event],
    edge_variables: dict[tuple[str, str], pulp.LpVariable],
    matchup_matrix: MatchupMatrix,
    opponent_teams: list[Team],
) -> None:
    """Constraint the selected events so all opponent teams are involved exactly once each."""
    for team in opponent_teams:
        problem += (
            pulp.lpSum([
                edge_variables[(event_i.id, event_j.id)]
                * matchup_matrix[event_i.id].get(team.id, 0)
                for event_i, event_j in permutations(events, 2)
                if (event_i.id, event_j.id) in edge_variables
            ])
            == 1,
            f"opponent_{team.id}",
        )


def solve(
    events: list[Event],
    max_driving_hours_per_day: int,
    driving_duration_matrix: CostMatrix,
    cost_matrix: CostMatrix,
    matchup_matrix: MatchupMatrix,
    opponent_teams: list[Team],
) -> pulp.LpProblem:
    """
    Driver function for creating and solving the linear program.

    This function is designed for solving for problem variants in parallel
    with one team per process. Concretely, this means that all inputs only
    contains data relevant to the team in question and can be reused.
    """
    optimal_trip = pulp.LpProblem("optimal_trip", pulp.LpMinimize)

    # tunable variables
    edge_variables = create_edge_variables(
        events,
        max_driving_hours_per_day,
        driving_duration_matrix,
    )
    order_variables = create_order_variables(events)

    # objective function
    optimal_trip += (
        pulp.LpAffineExpression(
            [var, cost_matrix[event_i][event_j]]
            for (event_i, event_j), var in edge_variables.items()
        ),
        "total_cost",
    )

    # constraints
    add_tour_constraints(optimal_trip, events, edge_variables)
    add_dummy_event_ordering_constraint(optimal_trip, events, edge_variables)
    add_subtour_elimination_constraints(
        optimal_trip,
        events,
        edge_variables,
        order_variables,
        len(opponent_teams),
    )
    add_opponent_constraints(
        optimal_trip,
        events,
        edge_variables,
        matchup_matrix,
        opponent_teams,
    )

    optimal_trip.solve()
    logger.info("Solver status: %s", pulp.LpStatus[optimal_trip.status])
    return optimal_trip
