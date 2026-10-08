"""
NBA teams and schedule endpoints, provided by ESPN.

ESPN does not provide the whole league schedule in one request, only one team at a time.
"""

import logging
from typing import Any

from pydantic import BaseModel

from trip_solver.data.api import BaseEndpoint
from trip_solver.models.api.nba.schedule import (
    NBATeamSchedulePathParams,
    NBATeamScheduleQueryParams,
    NBATeamScheduleResponse,
    NBATeamsResponse,
)

logging.basicConfig(level=logging.INFO, format="%(filename)s\t%(levelname)s\t%(message)s")
logger = logging.getLogger(__name__)

ESPN_NBA_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams"


class NBATeams(BaseEndpoint):  # noqa: D101
    def __init__(self) -> None:  # noqa: D107
        super().__init__(base_url=ESPN_NBA_BASE_URL, name="ESPN NBA Teams API")

    def get_data(  # noqa: D102
        self,
        # not accepted
        path_params: tuple[Any, ...] = (),
        # not accepted
        query_params: BaseModel | None = None,
        # not accepted
        request_body: BaseModel | None = None,
        # not accepted
        headers: BaseModel | None = None,
        response_model: type[BaseModel] = NBATeamsResponse,
    ) -> NBATeamsResponse:
        if path_params != ():
            logger.warning(
                "%s does not accept path params. Ignoring passed values.",
                self.name,
            )
        if query_params is not None or request_body is not None or headers is not None:
            logger.warning(
                "%s does not accept query params, request body, or headers. "
                "Ignoring passed values.",
                self.name,
            )
        if response_model is not NBATeamsResponse:
            raise TypeError(f"response_model must be NBATeamsResponse for {self.name}.")

        response = self.get_json((), None, None, None)
        logger.debug("Response JSON: %s", response)
        return response_model(**response)  # type: ignore[return-value]


class NBATeamSchedule(BaseEndpoint):  # noqa: D101
    def __init__(self) -> None:  # noqa: D107
        super().__init__(base_url=ESPN_NBA_BASE_URL, name="ESPN NBA Team Schedule API")

    def get_data(  # noqa: D102
        self,
        # required
        path_params: tuple[Any, ...] = (),
        # default provided
        query_params: NBATeamScheduleQueryParams | None = None,  # type: ignore[override]
        # not accepted
        request_body: BaseModel | None = None,
        # not accepted
        headers: BaseModel | None = None,
        response_model: type[BaseModel] = NBATeamScheduleResponse,
    ) -> NBATeamScheduleResponse:
        if not isinstance(path_params, NBATeamSchedulePathParams):
            raise TypeError(f"path_params must be NBATeamSchedulePathParams for {self.name}.")
        if query_params is None:
            query_params = NBATeamScheduleQueryParams()
        if request_body is not None or headers is not None:
            logger.warning(
                "%s does not accept request body or headers. Ignoring passed values.",
                self.name,
            )
        if response_model is not NBATeamScheduleResponse:
            raise TypeError(f"response_model must be NBATeamScheduleResponse for {self.name}.")

        response = self.get_json(path_params, query_params, None, None)
        logger.debug("Response JSON: %s", response)
        return response_model(**response)  # type: ignore[return-value]
