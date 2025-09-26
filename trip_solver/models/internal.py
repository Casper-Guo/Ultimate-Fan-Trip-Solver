"""Models specifying minimum required inputs for the solver and other internal scripts."""

from datetime import datetime
from typing import TypeAlias

from pydantic import field_serializer

from trip_solver.models.api.google_maps.common import LatLng
from trip_solver.util.models import ExtraFrozenModel

# this cannot be a Pydantic model since we do not know the keys in advance
CostMatrix: TypeAlias = dict[str, dict[str, int]]


class Team(ExtraFrozenModel):  # noqa: D101
    name: str
    id: str


class Teams(ExtraFrozenModel):  # noqa: D101
    teams: list[Team]


class Venue(ExtraFrozenModel):  # noqa: D101
    name: str
    id: str
    address: str
    place_id: str
    location: LatLng


class Venues(ExtraFrozenModel):  # noqa: D101
    venues: list[Venue]


class Event(ExtraFrozenModel):  # noqa: D101
    id: str
    time: datetime
    venue_id: str
    home_team_id: str
    away_team_id: str

    @field_serializer("time")
    @classmethod
    def parse_time(cls, v: datetime) -> str:
        """Convert event time back to ISO string for JSON serialization."""
        return v.isoformat()


class Events(ExtraFrozenModel):  # noqa: D101
    events: list[Event]
