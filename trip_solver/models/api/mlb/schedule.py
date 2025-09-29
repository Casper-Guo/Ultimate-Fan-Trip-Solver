"""MLB schedule endpoints query params and response models."""

from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Self

from pydantic import AfterValidator, field_serializer, field_validator, model_validator

from trip_solver.models.api.mlb.common import MLBVenue
from trip_solver.util.models import FrozenModel, StrictModel
from trip_solver.util.validators import check_acceptable_date_input

DateParam = Annotated[str | None, AfterValidator(check_acceptable_date_input)]


class MLBGameType(StrEnum):  # noqa: D101
    SPRING_TRAINING = "S"
    REGULAR_SEASON = "R"
    WILD_CARD = "F"
    DIVISION_SERIES = "D"
    LEAGUE_CHAMPIONSHIP_SERIES = "L"
    WORLD_SERIES = "W"
    CHAMPIONSHIP = "C"
    NINETEENTH_CENTURY_SERIES = "N"
    PLAYOFFS = "P"
    ALL_STAR_GAME = "A"
    INTRASQUAD = "I"
    EXHIBITION = "E"


class MLBScheduleQueryParams(StrictModel):
    """
    Required and optional query parameters for the MLB schedule endpoint.

    Only tested and understood parameters are implemented.
    See all available at https://github.com/toddrob99/MLB-StatsAPI/wiki/Endpoints#endpoint-schedule
    """

    sportId: int = 1  # MLB
    season: int = 2026
    # does not appear to be effective
    # gamePk: int  # noqa: ERA001
    teamId: int | None = None
    teamIds: list[int] | None = None
    venueIds: list[int] | None = None
    gameType: MLBGameType | None = MLBGameType.REGULAR_SEASON
    gameTypes: list[MLBGameType] | None = None
    # would be easy to have these as date objects
    # but that requires additional validators and serializers
    date: DateParam = None  # YYYY-MM-DD
    startDate: DateParam = None  # YYYY-MM-DD
    endDate: DateParam = None  # YYYY-MM-DD
    opponentId: int | None = None

    @field_validator("gameType", mode="before")
    @classmethod
    def validate_game_type(cls, v: str | MLBGameType | None) -> MLBGameType | None:  # noqa: D102
        if v is None or isinstance(v, MLBGameType):
            return v
        return MLBGameType(v)

    @field_validator("gameTypes", mode="before")
    @classmethod
    def validate_game_types(cls, v: list[str | MLBGameType] | None) -> list[MLBGameType] | None:  # noqa: D102
        if v is None:
            return v
        return [item if isinstance(item, MLBGameType) else MLBGameType(item) for item in v]

    @model_validator(mode="after")
    def check_complete_matchup(self) -> Self:  # noqa: D102
        if (self.opponentId is not None) and (self.teamId is None):
            raise ValueError("Must specify teamId when setting opponentId")
        return self

    @field_serializer("teamIds", "venueIds")
    def serialize_ids(self, ids: list[int] | None) -> str | None:  # noqa: D102, PLR6301
        if ids is None:
            return None
        return ",".join(str(i) for i in ids)

    @field_serializer("gameType", "gameTypes")
    def serialize_game_type(  # noqa: D102, PLR6301
        self,
        game_types: MLBGameType | list[MLBGameType] | None,
    ) -> str | None:
        if game_types is None:
            return None
        if isinstance(game_types, list):
            return ",".join([game_type.value for game_type in game_types])
        return game_types.value


class MLBTeamLeagueRecord(FrozenModel):  # noqa: D101
    wins: int
    losses: int
    pct: float


class MLBTeamId(FrozenModel):  # noqa: D101
    id: int
    name: str


class MLBTeam(FrozenModel):  # noqa: D101
    # not needed at the moment
    # leagueRecord: MLBTeamLeagueRecord  # noqa: ERA001
    team: MLBTeamId


class MLBTeams(FrozenModel):  # noqa: D101
    away: MLBTeam
    home: MLBTeam


class MLBGame(FrozenModel):  # noqa: D101
    gamePk: int
    gameType: MLBGameType
    season: int
    gameDate: datetime  # ISO 8601 date-time string
    officialDate: date  # YYYY-MM-DD
    teams: MLBTeams
    venue: MLBVenue
    seriesDescription: str

    @field_validator("gameType", mode="before")
    @classmethod
    def validate_game_type(cls, v: str) -> MLBGameType:  # noqa: D102
        return MLBGameType(v)

    @field_validator("season", mode="before")
    @classmethod
    def convert_season_to_int(cls, v: str | int) -> int:  # noqa: D102
        return int(v)


class MLBDate(FrozenModel):  # noqa: D101
    date: date  # YYYY-MM-DD
    totalItems: int
    totalGames: int
    games: list[MLBGame]


class MLBScheduleResponse(FrozenModel):  # noqa: D101
    totalItems: int
    totalGames: int
    dates: list[MLBDate]
