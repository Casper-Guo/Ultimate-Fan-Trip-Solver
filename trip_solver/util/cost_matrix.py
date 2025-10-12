"""Calculate the cost matrix for a set of events or the distance matrix for a set of venues."""

import logging
import zoneinfo
from collections.abc import Iterator
from datetime import datetime, timezone
from enum import StrEnum, auto
from itertools import permutations

from trip_solver.data.api.google_maps import (
    TRAFFIC_UNAWARE_MAX_ELEMENTS,
    TRAFFIC_UNAWARE_MAX_ORIGINS_DESTINATIONS,
)
from trip_solver.data.api.google_maps.route_matrix import RouteMatrix
from trip_solver.models.api.google_maps.common import Waypoint, gRPCCode
from trip_solver.models.api.google_maps.route_matrix import (
    RouteMatrixDestination,
    RouteMatrixElementCondition,
    RouteMatrixOrigin,
    RouteMatrixRequestBody,
    RouteMatrixResponse,
)
from trip_solver.models.internal import CostMatrix, Events, Venues

logging.basicConfig(level=logging.INFO, format="%(filename)s\t%(levelname)s\t%(message)s")
logger = logging.getLogger(__name__)


class CostMeasure(StrEnum):
    """The measure to use for the cost matrix."""

    DRIVING_DISTANCE = auto()
    DRIVING_DURATION = auto()
    TRIP_DURATION = auto()


def partition_route_matrix(venues: Venues) -> Iterator[tuple[int, int, RouteMatrixResponse]]:
    """
    Partition the route matrix calculation into chunks that fit Google Maps API limits.

    Let the number of events be n_e, eventually we want to produce a n_e x n_e cost matrix.

    If every row of the matrix is the same origin and every column is the same destination,
    then we proceed column by column, requesting as many rows as possible at once.

    In practice, this means for every origin included in the request, the number of destinations
    queried is the same.
    """
    route_matrix_endpoint = RouteMatrix()
    num_origins = min(len(venues.venues), TRAFFIC_UNAWARE_MAX_ORIGINS_DESTINATIONS - 1)
    num_destinations = min(
        TRAFFIC_UNAWARE_MAX_ELEMENTS // num_origins,
        TRAFFIC_UNAWARE_MAX_ORIGINS_DESTINATIONS - num_origins,
        len(venues.venues),
    )
    for origin_index_start in range(0, len(venues.venues), num_origins):
        for destination_index_start in range(0, len(venues.venues), num_destinations):
            yield (
                origin_index_start,
                destination_index_start,
                route_matrix_endpoint.post_for_data(
                    request_body=RouteMatrixRequestBody(
                        origins=[
                            RouteMatrixOrigin(waypoint=Waypoint(placeId=venue.place_id))
                            for venue in venues.venues[
                                origin_index_start : origin_index_start + num_origins
                            ]
                        ],
                        destinations=[
                            RouteMatrixDestination(waypoint=Waypoint(placeId=venue.place_id))
                            for venue in venues.venues[
                                destination_index_start : destination_index_start
                                + num_destinations
                            ]
                        ],
                    ),
                ),
            )


def compute_driving_cost_matrix(venues: Venues) -> tuple[CostMatrix, CostMatrix]:
    """
    Use Google Maps Route Matrix API to compute driving distances and durations between venues.

    Estimates are traffic-unaware by default to reduce API usage and produce a good average.

    Note that this matrix is asymmetric.
    """
    distance_matrix = {venue.id: {venue.id: 0} for venue in venues.venues}
    duration_matrix = {venue.id: {venue.id: 0} for venue in venues.venues}

    for origin_index_start, destination_index_start, response in partition_route_matrix(venues):
        for element in response.routes:
            if element.originIndex is None or element.destinationIndex is None:
                raise AttributeError(
                    "Route Matrix API calls must include origin and destination indices.",
                )

            origin_index = origin_index_start + element.originIndex
            destination_index = destination_index_start + element.destinationIndex

            if origin_index == destination_index:
                continue

            if element.condition is RouteMatrixElementCondition.ROUTE_NOT_FOUND:
                raise ValueError(
                    f"No routes found between {venues.venues[origin_index].name} "
                    f"and {venues.venues[destination_index].name}",
                )
            if element.status is not None and element.status.code != gRPCCode.OK:
                logger.warning("gRPC code: %s", element.status.code)
                logger.warning("gRPC message: %s", element.status.message)
                logger.warning("gRPC details: %s", element.status.details)
            if element.distanceMeters is None:
                raise ValueError(
                    "Route Matrix API calls must include distanceMeters to compute "
                    "driving distance cost matrix.",
                )
            if element.staticDuration is None:
                raise ValueError(
                    "Route Matrix API calls must include staticDuration to compute "
                    "driving duration cost matrix.",
                )

            distance_matrix[venues.venues[origin_index].id][
                venues.venues[destination_index].id
            ] = element.distanceMeters
            duration_matrix[venues.venues[origin_index].id][
                venues.venues[destination_index].id
            ] = element.staticDuration

    return distance_matrix, duration_matrix  # type: ignore[return-value] compatible subtype


def utc_to_eastern(dt: datetime) -> datetime:
    """Convert a UTC datetime, whether timezone-aware or naive, to US Eastern time."""
    eastern = zoneinfo.ZoneInfo("America/New_York")
    dt = dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
    return dt.astimezone(eastern)


def compute_total_duration_matrix(events: Events) -> CostMatrix:
    """
    Total duration is a day-level measure for the length of a trip.

    By definition, a trip visiting one event has a total duration of 0.

    This cost matrix is triangular, as the cost from a event to another event
    in its past is undefined.
    """
    # defining these values are not strictly necessary
    # but it is a nice way to initialize the dict
    cost_matrix = {event.id: {event.id: 0} for event in events.events}

    # using combinations would be faster but requires the assumption that the events
    # are listed in chronological order
    for event_1, event_2 in permutations(events.events, 2):
        if event_1.time >= event_2.time:
            # the permutations iterator gives both [1, 2] and [2, 1] order
            continue
        time_1, time_2 = utc_to_eastern(event_1.time), utc_to_eastern(event_2.time)

        cost_matrix[event_1.id][event_2.id] = (time_2.date() - time_1.date()).days

    return cost_matrix  # type: ignore[return-value] compatible subtype


def compute_cost_matrix(
    measure: CostMeasure = CostMeasure.DRIVING_DISTANCE,
    events: Events | None = None,
    venues: Venues | None = None,
) -> CostMatrix | tuple[CostMatrix, CostMatrix]:
    """
    Entry point for computing the cost matrix using various supported measures.

    The driving distance and duration cost matrix are always returned together
    to reduce API usage.
    """
    match measure:
        case CostMeasure.DRIVING_DISTANCE | CostMeasure.DRIVING_DURATION:
            if venues is None:
                raise TypeError("Venues must be provided for driving cost matrix.")
            return compute_driving_cost_matrix(venues)
        case CostMeasure.TRIP_DURATION:
            if events is None:
                raise TypeError("Events must be provided for total duration cost matrix.")
            return compute_total_duration_matrix(events)
        case _:
            raise ValueError(f"Unknown cost measure: {measure}")


def convert_cost_matrix_str_keys(matrix: dict[str, dict[str, int]]) -> CostMatrix:
    """Recover integer cost matrix keys that are converted to strs when dumped to JSON."""
    converted_matrix: CostMatrix = {}
    for key, value in matrix.items():
        converted_matrix[int(key)] = {
            int(inner_key): inner_val for inner_key, inner_val in value.items()
        }
    return converted_matrix
