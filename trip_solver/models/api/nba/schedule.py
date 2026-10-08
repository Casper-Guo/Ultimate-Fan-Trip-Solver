"""
ESPN NBA teams and team schedule endpoints path params, query params, and response models.

Only the fields used by the integration script are modelled.
"""

from datetime import datetime
from enum import IntEnum
from typing import Literal, NamedTuple

from trip_solver.util.models import FrozenModel, StrictModel


class NBASeasonType(IntEnum):  # noqa: D101
    PRESEASON = 1
    REGULAR_SEASON = 2
    POSTSEASON = 3


class NBATeam(FrozenModel):  # noqa: D101
    id: int
    location: str
    displayName: str


class NBATeamsTeam(FrozenModel):  # noqa: D101
    team: NBATeam


class NBATeamsLeague(FrozenModel):  # noqa: D101
    teams: list[NBATeamsTeam]


class NBATeamsSport(FrozenModel):  # noqa: D101
    leagues: list[NBATeamsLeague]


class NBATeamsResponse(FrozenModel):  # noqa: D101
    sports: list[NBATeamsSport]


class NBATeamSchedulePathParams(NamedTuple):  # noqa: D101
    team_id: int
    resource: Literal["schedule"] = "schedule"


class NBATeamScheduleQueryParams(StrictModel):  # noqa: D101
    # ESPN labels a season by the year it ends in, e.g. 2027 for 2026-27
    # defaults to the current season when omitted
    season: int | None = None
    seasontype: NBASeasonType = NBASeasonType.REGULAR_SEASON


class NBAVenueAddress(FrozenModel):  # noqa: D101
    city: str
    # not provided for venues outside the US and Canada
    state: str | None = None


class NBAVenue(FrozenModel):  # noqa: D101
    fullName: str
    address: NBAVenueAddress


class NBACompetitor(FrozenModel):  # noqa: D101
    homeAway: Literal["home", "away"]
    team: NBATeam


class NBACompetition(FrozenModel):  # noqa: D101
    neutralSite: bool
    venue: NBAVenue
    competitors: list[NBACompetitor]


class NBAEventSeasonType(FrozenModel):  # noqa: D101
    type: NBASeasonType


class NBAGame(FrozenModel):
    """
    A scheduled game.

    Games whose participants are not yet known, e.g. NBA Cup knockout games, are not listed.
    """

    id: str
    date: datetime
    seasonType: NBAEventSeasonType
    # always exactly one competition per game
    competitions: list[NBACompetition]

    def get_team(self, home_away: Literal["home", "away"]) -> NBATeam:
        """Get the home or away team of the game."""
        return next(
            competitor.team
            for competitor in self.competitions[0].competitors
            if competitor.homeAway == home_away
        )


class NBATeamScheduleResponse(FrozenModel):  # noqa: D101
    team: NBATeam
    events: list[NBAGame]
