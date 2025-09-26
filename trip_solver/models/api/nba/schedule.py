"""NBA schedule endpoint response model."""

from datetime import date, datetime

from pydantic import field_validator

from trip_solver.util.models import FrozenModel


class NBATeam(FrozenModel):
    """Some games are scheduled without knowing which teams will play."""

    # when other attributes are not given, teamId is set to 0
    teamId: int
    teamName: str | None = None
    teamCity: str | None = None
    teamTricode: str | None = None
    teamSlug: str | None = None


class NBAGame(FrozenModel):  # noqa: D101
    gameId: str
    gameCode: str
    gameDateTimeUTC: datetime
    # preseason games are all week 0
    weekNumber: int
    # regular season games usually do not get a label
    gameLabel: str
    arenaName: str
    arenaState: str
    arenaCity: str
    isNeutral: bool
    homeTeam: NBATeam
    awayTeam: NBATeam


class NBAGameDate(FrozenModel):  # noqa: D101
    gameDate: date
    games: list[NBAGame]

    @field_validator("gameDate", mode="before")
    @classmethod
    def parse_game_date(cls, v: str) -> date:
        """Game dates are provided in the following format: 10/02/2025 00:00:00."""
        return datetime.strptime(v, "%m/%d/%Y %H:%M:%S").date()  # noqa: DTZ007


class NBALeagueSchedule(FrozenModel):  # noqa: D101
    seasonYear: str
    leagueId: str
    gameDates: list[NBAGameDate]


class NBAScheduleResponse(FrozenModel):  # noqa: D101
    leagueSchedule: NBALeagueSchedule
