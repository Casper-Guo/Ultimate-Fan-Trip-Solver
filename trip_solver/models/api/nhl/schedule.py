"""NHL schedule endpoints query params and response models."""

from datetime import date
from enum import IntEnum
from typing import Literal, NamedTuple

from pydantic import field_validator

from trip_solver.util.models import FrozenModel


class NHLGameType(IntEnum):  # noqa: D101
    PRESEASON = 1
    REGULAR_SEASON = 2


class NHLSchedulePathParams(NamedTuple):  # noqa: D101
    time: str = "now"  # YYYY-MM-DD or "now"


class NHLClubSchedulePathParams(NamedTuple):  # noqa: D101
    team: str
    period: Literal["week", "month"]
    time: str = "now"  # YYYY-MM or YYYY-MM-DD or "now" depending on requested period


class NHLClubScheduleSeasonPathParams(NamedTuple):  # noqa: D101
    team: str
    season: str = "now"  # format: "YYYYYYYY", e.g. "20242025", or "now"


class NHLScheduleVenue(FrozenModel):  # noqa: D101
    default: str


class NHLScheduleTeamName(FrozenModel):
    """Model for the commonName and placeName fields as they are structured identically."""

    default: str


class NHLScheduleTeam(FrozenModel):  # noqa: D101
    id: int
    commonName: NHLScheduleTeamName
    placeName: NHLScheduleTeamName
    abbrev: str


class NHLScheduleGame(FrozenModel):  # noqa: D101
    id: int
    season: str
    gameType: NHLGameType
    gameDate: date | None = None
    venue: NHLScheduleVenue
    neutralSite: bool
    startTimeUTC: str  # ISO 8601 date-time string
    awayTeam: NHLScheduleTeam
    homeTeam: NHLScheduleTeam

    @field_validator("gameType", mode="before")
    @classmethod
    def validate_game_type(cls, value: int) -> NHLGameType:  # noqa: D102
        return NHLGameType(value)

    @field_validator("season", mode="before")
    @classmethod
    def convert_season_to_str(cls, season: int) -> str:
        """Season is returned as an int but it is better understood as a str."""
        return str(season)


class NHLScheduleGameday(FrozenModel):  # noqa: D101
    date: date
    dayAbbrev: str
    numberOfGames: int
    games: list[NHLScheduleGame]


class NHLScheduleResponse(FrozenModel):  # noqa: D101
    nextStartDate: date
    previousStartDate: date
    preSeasonStartDate: date
    regularSeasonStartDate: date
    regularSeasonEndDate: date
    playoffEndDate: date
    numberOfGames: int
    gameWeek: list[NHLScheduleGameday]


class NHLClubScheduleResponse(FrozenModel):  # noqa: D101
    previousStartDate: date
    nextStartDate: date
    games: list[NHLScheduleGame]


class NHLClubScheduleSeasonResponse(FrozenModel):  # noqa: D101
    previousSeason: str
    currentSeason: str
    games: list[NHLScheduleGame]

    @field_validator("previousSeason", "currentSeason", mode="before")
    @classmethod
    def convert_season_to_str(cls, season: int) -> str:
        """Season is returned as an int but it is better understood as a str."""
        return str(season)
