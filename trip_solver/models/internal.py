"""Models specifying minimum required inputs for the solver and other internal scripts."""

from datetime import datetime
from typing import TypeAlias

from pydantic import field_serializer, field_validator

from trip_solver.models.api.google_maps.common import LatLng
from trip_solver.util.models import ExtraFrozenModel

# this cannot be a Pydantic model since we do not know the keys in advance
CostMatrix: TypeAlias = dict[int | str, dict[int | str, int]]


class Team(ExtraFrozenModel):  # noqa: D101
    name: str
    id: int


class Teams(ExtraFrozenModel):  # noqa: D101
    teams: list[Team]


class Venue(ExtraFrozenModel):  # noqa: D101
    name: str
    id: int
    address: str
    # best available place name
    # may be city, state, or both depending on the API
    # useful for Google Maps route url generation
    place_name: str
    place_id: str
    location: LatLng


class Venues(ExtraFrozenModel):  # noqa: D101
    venues: list[Venue]


class Event(ExtraFrozenModel):  # noqa: D101
    # we are enforcing the IDs as strs mostly for compatibility with NBA
    # where event IDs are numerical but may contain leading zeros
    id: str
    time: datetime
    venue: Venue
    home_team: Team
    away_team: Team

    @field_validator("id", mode="before")
    @classmethod
    def parse_id(cls, v: int | str) -> str:  # noqa: D102
        return str(v)

    @field_serializer("time")
    @classmethod
    def parse_time(cls, v: datetime) -> str:
        """Convert event time back to ISO string for JSON serialization."""
        return v.isoformat()


class Events(ExtraFrozenModel):  # noqa: D101
    events: list[Event]
