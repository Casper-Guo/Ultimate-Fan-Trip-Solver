"""Driver script for reading in data and running the solver."""

import argparse
import logging
from math import ceil
from multiprocessing import Pool
from pathlib import Path

import pulp  # type: ignore

from trip_solver.models.internal import CostMatrix, Event, Events, Teams
from trip_solver.solver.consts import DUMMY_EVENT_ID
from trip_solver.solver.solver import solve
from trip_solver.util.cost_matrix import CostMeasure, load_cost_matrix_from_json
from trip_solver.util.solver_util import (
    build_cost_matrix,
    build_matchup_matrix,
    remove_infeasible_teams,
)

logging.basicConfig(level=logging.INFO, format="%(filename)s\t%(levelname)s\t%(message)s")
logger = logging.getLogger(__name__)

TOL = 1e-5


def format_lp_output(problem: pulp.LpProblem, driving_hours_per_day: int) -> str:
    """
    For a solved problem, output the following format.

    The first line of the output is the total cost. The second line is the hours
    of driving needed per day. Each subsequent line contains an event ID in the
    order visited.
    """
    next_event: dict[str, str] = {}

    for variable in problem.variables():
        # in theory this should not be needed as the edge variables are binary
        # in practice there is a bug in the HiGHS solver's dependency that causes
        # inexact values to be returned
        if abs(variable.varValue - 1) < TOL and variable.name.startswith("x_"):
            _, from_event, to_event = variable.name.split("_")
            next_event[from_event] = to_event

    path: list[str] = []
    current_event_id = DUMMY_EVENT_ID

    while True:
        next_event_id = next_event[current_event_id]
        if next_event_id == DUMMY_EVENT_ID:
            break
        path.append(next_event_id)
        current_event_id = next_event_id

    return f"{pulp.value(problem.objective)}\n" + f"{driving_hours_per_day}\n" + "\n".join(path)


def binary_search_driving_hours(
    events: list[Event],
    driving_duration_matrix: CostMatrix,
    cost_matrix: CostMatrix,
    matchup_matrix: dict[str, dict[int, int]],
    teams: Teams,
) -> tuple[pulp.LpProblem, int]:
    """Find the smallest integer driving hours per day to make the trip feasible."""
    left = 1
    right = 24
    min_driving_hours = None
    min_driving_solution = None

    while left != right:
        middle = left + ceil((right - left) / 2)
        solution = solve(
            events,
            middle,
            driving_duration_matrix,
            cost_matrix,
            matchup_matrix,
            teams.teams,
        )
        if solution.status != pulp.LpStatusOptimal:
            # need to try a higher driving hours allowance
            left = middle
        else:
            min_driving_hours = middle
            min_driving_solution = solution
            right = middle - 1

    solution = solve(
        events,
        left,
        driving_duration_matrix,
        cost_matrix,
        matchup_matrix,
        teams.teams,
    )
    if solution.status == pulp.LpStatusOptimal:
        min_driving_hours = left
        min_driving_solution = solution

    if min_driving_hours is None:
        raise RuntimeError
    return min_driving_solution, min_driving_hours


def run_solver(
    output_dir: Path,
    teams: Teams,
    events: Events,
    distance_matrix: CostMatrix,
    duration_matrix: CostMatrix,
    team_id: int,
) -> None:
    """Set up the solver, then produce, format, and output the solutions."""
    relevant_events = [event for event in events.events if event.away_team.id == team_id]
    trip_duration_matrix = build_cost_matrix(
        relevant_events,
        CostMeasure.TRIP_DURATION,
        include_dummy=True,
    )
    driving_distance_matrix = build_cost_matrix(
        relevant_events,
        CostMeasure.DRIVING_DISTANCE,
        distance_matrix,
        include_dummy=True,
    )
    driving_duration_matrix = build_cost_matrix(
        relevant_events,
        CostMeasure.DRIVING_DURATION,
        duration_matrix,
        include_dummy=True,
    )
    matchup_matrix = build_matchup_matrix(
        Events(events=relevant_events),
        include_dummy=True,
    )

    team_name = next(team.name for team in teams.teams if team.id == team_id)
    teams = remove_infeasible_teams(teams, team_name)

    # Some MLB interleague pairings do not play home-and-home
    away_opponents = {event.home_team for event in relevant_events}
    teams = Teams(teams=list(away_opponents.intersection(set(teams.teams))))

    # reformat team names to be filesystem-friendly
    # not done earlier to avoid mixing the two formats when dealing with matchup edge cases
    team_name = team_name.replace(" ", "_").lower()

    try:
        # only need to run binary search once to find the lower bound for feasible driving hours
        trip_duration_sol, driving_hours = binary_search_driving_hours(
            relevant_events,
            driving_duration_matrix,
            trip_duration_matrix,
            matchup_matrix,
            teams,
        )
        Path(output_dir / team_name).mkdir(parents=True, exist_ok=True)
        Path(output_dir / team_name / "trip_duration.txt").write_text(
            format_lp_output(trip_duration_sol, driving_hours),
            encoding="utf-8",
        )
    except RuntimeError as e:
        raise RuntimeError(f"No feasible trip found for team {team_name}") from e
    driving_distance_sol = solve(
        relevant_events,
        driving_hours,
        driving_duration_matrix,
        driving_distance_matrix,
        matchup_matrix,
        teams.teams,
    )
    Path(output_dir / team_name / "driving_distance.txt").write_text(
        format_lp_output(driving_distance_sol, driving_hours),
        encoding="utf-8",
    )
    driving_duration_sol = solve(
        relevant_events,
        driving_hours,
        driving_duration_matrix,
        driving_duration_matrix,
        matchup_matrix,
        teams.teams,
    )
    Path(output_dir / team_name / "driving_duration.txt").write_text(
        format_lp_output(driving_duration_sol, driving_hours),
        encoding="utf-8",
    )
    logger.info(
        "Finished solving for team: %s. Driving hours needed: %d",
        team_name,
        driving_hours,
    )


def main() -> None:
    """
    Compute the optimal trips using the data in the input directory.

    The input directory are required to provide the following files:
    - distance_matrix.json
    - duration_matrix.json
    - events.json
    - teams.json
    in the format specified by the internal data models.

    The optimal trips will be computed using the three available criteria: total duration,
    driving distance, and driving duration. The number of driving hours per day will be
    the smallest integer value where a trip is feasible.
    """
    parser = argparse.ArgumentParser(description="Ultimate Fan Trip Solver CLI")
    parser.add_argument("input_dir", type=str, help="Path to the input directory")
    parser.add_argument("output_dir", type=str, help="Path to the output directory")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    if not input_dir.is_dir():
        raise ValueError(
            f"Input directory '{input_dir}' does not exist or is not a directory.",
        )

    for required_file in [
        "distance_matrix.json",
        "duration_matrix.json",
        "events.json",
        "teams.json",
    ]:
        if not (input_dir / required_file).is_file():
            raise ValueError(f"Required file '{required_file}' not found in input directory.")

    output_dir.mkdir(parents=True, exist_ok=True)

    teams = Teams.model_validate_json((input_dir / "teams.json").read_text())
    events = Events.model_validate_json((input_dir / "events.json").read_text())
    distance_matrix = load_cost_matrix_from_json(input_dir / "distance_matrix.json")
    duration_matrix = load_cost_matrix_from_json(input_dir / "duration_matrix.json")

    with Pool(processes=16) as pool:
        pool.starmap(
            run_solver,
            [
                (
                    output_dir,
                    teams,
                    events,
                    distance_matrix,
                    duration_matrix,
                    team.id,
                )
                for team in teams.teams
            ],
        )
        pool.close()
        pool.join()


if __name__ == "__main__":
    main()
