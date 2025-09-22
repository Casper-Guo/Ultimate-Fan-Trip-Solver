"""Pydantic models common to Google Maps APIs."""

from enum import IntEnum
from typing import Self

from pydantic import Field, model_validator

from trip_solver.util.models import StrictModel


class gRPCCode(IntEnum):  # noqa: N801
    """
    gRPC status codes.

    See https://github.com/googleapis/googleapis/blob/master/google/rpc/code.proto/
    """

    # HTTP 200
    OK = 0
    # HTTP 499
    CANCELLED = 1
    # HTTP 500
    UNKNOWN = 2
    # HTTP 400
    INVALID_ARGUMENT = 3
    # HTTP 504
    DEADLINE_EXCEEDED = 4
    # HTTP 404
    NOT_FOUND = 5
    # HTTP 409
    ALREADY_EXISTS = 6
    # HTTP 403
    PERMISSION_DENIED = 7
    # HTTP 429
    RESOURCE_EXHAUSTED = 8
    # HTTP 400
    FAILED_PRECONDITION = 9
    # HTTP 409
    ABORTED = 10
    # HTTP 400
    OUT_OF_RANGE = 11
    # HTTP 501
    UNIMPLEMENTED = 12
    # HTTP 500
    INTERNAL = 13
    # HTTP 503
    UNAVAILABLE = 14
    # HTTP 500
    DATA_LOSS = 15
    # HTTP 401
    UNAUTHENTICATED = 16


class LocalizedText(StrictModel):  # noqa: D101
    text: str
    languageCode: str


class LatLng(StrictModel):  # noqa: D101
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class Location(StrictModel):  # noqa: D101
    latLng: LatLng
    # by default not considering the side of the dropoff
    # so this is essentially irrelevant
    heading: int = 0


class Waypoint(StrictModel):  # noqa: D101
    via: bool = False
    vehicleStopover: bool = True
    sideOfRoad: bool = False
    # one and exactly one of the following must be set
    location: Location | None = None
    placeId: str | None = None
    # human readable address or a plus code
    address: str | None = None

    @model_validator(mode="after")
    def check_location_type(self) -> Self:
        """Ensure exactly one of location, placeId, address is set."""
        count = sum(x is not None for x in (self.location, self.placeId, self.address))
        if count != 1:
            raise ValueError("Exactly one of location, placeId, address must be set")
        return self
