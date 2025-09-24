"""MLB teams endpoint path params and response models."""

from typing import NamedTuple

from pydantic import field_serializer

from trip_solver.models.api.mlb.common import MLBVenue
from trip_solver.util.models import FrozenModel


class MLBTeamsPathParams(NamedTuple):  # noqa: D101
    teamId: int


class MLBTeamsQueryParams(FrozenModel):  # noqa: D101
    # only tested parameters included
    # see available sport ids at https://statsapi.mlb.com/api/v1/sports
    sportId: int | None = None
    sportIds: list[int] | None = None

    @field_serializer("sportIds")
    def serialize_ids(self, sport_ids: list[int] | None) -> str | None:  # noqa: D102, PLR6301
        if sport_ids is None:
            return None
        return ",".join(str(sport_id) for sport_id in sport_ids)


class MLBTeamMetadata(FrozenModel):  # noqa: D101
    id: int
    name: str
    season: int
    venue: MLBVenue
    teamCode: str
    fileCode: str
    abbreviation: str
    teamName: str
    locationName: str
    shortName: str
    franchiseName: str
    clubName: str


class MLBTeamsResponse(FrozenModel):  # noqa: D101
    teams: list[MLBTeamMetadata]
