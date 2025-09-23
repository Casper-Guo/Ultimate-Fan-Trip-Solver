"""MLB teams endpoint path params and response models."""

from typing import NamedTuple

from trip_solver.models.api.mlb.common import MLBVenue
from trip_solver.util.models import FrozenModel


class MLBTeamPathParams(NamedTuple):  # noqa: D101
    teamId: int


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
