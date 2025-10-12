"""Linear programming formulator and solver."""

import logging
from itertools import permutations
from math import ceil

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
        # the driving duration matrix is given in seconds
        if available_driving_time(
            event_i,
            event_j,
            max_driving_hours_per_day,
        ) >= ceil(driving_duration_matrix[event_i.id][event_j.id] / 60):
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


def add_tour_constraints(
    problem: pulp.LpProblem,
    events: list[Event],
    edge_variables: dict[tuple[str, str], pulp.LpVariable],
) -> None:
    """Constraint the in and out degrees of non-dummy events to be at most 1."""
    event_ids = [event.id for event in events] + [DUMMY_EVENT_ID]
    for event_i_id in event_ids:
        problem += (
            pulp.lpSum(
                edge_variables.get((event_i_id, event_j_id), 0) for event_j_id in event_ids
            )
            <= 1,
            f"out_degree_{event_i_id}",
        )
        problem += (
            pulp.lpSum(
                edge_variables.get((event_j_id, event_i_id), 0) for event_j_id in event_ids
            )
            <= 1,
            f"in_degree_{event_i_id}",
        )
    for event_i_id in event_ids:
        problem += (
            pulp.lpSum(
                [
                    *[
                        edge_variables.get((event_i_id, event_j_id), 0)
                        for event_j_id in event_ids
                    ],
                    *[
                        -edge_variables.get((event_j_id, event_i_id), 0)
                        for event_j_id in event_ids
                    ],
                ],
            )
            == 0,
            f"equal_degree_{event_i_id}",
        )


def add_opponent_constraints(
    problem: pulp.LpProblem,
    events: list[Event],
    edge_variables: dict[tuple[str, str], pulp.LpVariable],
    matchup_matrix: MatchupMatrix,
    interested_teams: list[Team],
) -> None:
    """Constraint the selected events so all interested teams play at least once."""
    constraints_dict: dict[int, list[pulp.LpAffineExpression]] = {
        team.id: [] for team in interested_teams
    }

    for team in interested_teams:
        for event_i, event_j in permutations(events, 2):
            if (event_i.id, event_j.id) in edge_variables:
                constraints_dict[team.id].append(
                    edge_variables[(event_i.id, event_j.id)]
                    * matchup_matrix[event_j.id].get(team.id, 0),
                )
        for event in events:
            constraints_dict[team.id].append(
                edge_variables[(DUMMY_EVENT_ID, event.id)]
                * matchup_matrix[event.id].get(team.id, 0),
            )

    for team_id, expression in constraints_dict.items():
        problem += (pulp.lpSum(expression) >= 1, f"opponent_{team_id}")


def solve(
    events: list[Event],
    max_driving_hours_per_day: int,
    driving_duration_matrix: CostMatrix,
    cost_matrix: CostMatrix,
    matchup_matrix: MatchupMatrix,
    interested_teams: list[Team],
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

    # objective function
    optimal_trip += (
        pulp.lpSum([
            # minimize the number of events attended even when the cost matrix entry is zero
            # this is especially an issue with MLB teams playing in the same location
            # in consecutive days
            var * (cost_matrix[event_i][event_j] + 1)
            for (event_i, event_j), var in edge_variables.items()
        ]),
        "total_cost",
    )

    # constraints
    add_tour_constraints(optimal_trip, events, edge_variables)
    add_opponent_constraints(
        optimal_trip,
        events,
        edge_variables,
        matchup_matrix,
        interested_teams,
    )

    optimal_trip.solve(solver=pulp.HiGHS(msg=False))
    logger.info("Solver status: %s", pulp.LpStatus[optimal_trip.status])
    return optimal_trip
