"""
NHL schedule endpoints.

There does not seem to be a way to get every game for every team all at once.

Instead, the following three APIs are provided:

- /v1/schedule/: provides the schedule for all teams for up to a week
- /v1/club-schedule/: provides the schedule for one team for a week or a month
- /v1/club-schedule-season/: provides the schedule for one team for an entire season

There is also a /v1/schedule-calendar/ API but it does not actually provide the schedule.
"""

import logging

from pydantic import BaseModel

from trip_solver.data.api import BaseEndpoint
from trip_solver.models.api.nhl.schedule import (
    NHLClubSchedulePathParams,
    NHLClubScheduleResponse,
    NHLClubScheduleSeasonPathParams,
    NHLClubScheduleSeasonResponse,
    NHLSchedulePathParams,
    NHLScheduleResponse,
)

logging.basicConfig(level=logging.INFO, format="%(filename)s\t%(levelname)s\t%(message)s")
logger = logging.getLogger(__name__)


class NHLSchedule(BaseEndpoint):  # noqa: D101
    def __init__(self) -> None:  # noqa: D107
        super().__init__(
            base_url="https://api-web.nhle.com/v1/schedule",
            name="NHL Schedule API",
        )

    def get_data(  # noqa: D102
        self,
        # default provided
        path_params: tuple[str, ...] = (),
        # not accepted
        query_params: BaseModel | None = None,
        # not accepted
        request_body: BaseModel | None = None,
        # not accepted
        headers: BaseModel | None = None,
        response_model: type[BaseModel] = NHLScheduleResponse,
    ) -> NHLScheduleResponse:
        if path_params == ():
            path_params = NHLSchedulePathParams()
        elif not isinstance(path_params, NHLSchedulePathParams):
            raise TypeError(f"path_params must be NHLSchedulePathParams for {self.name}.")
        if query_params is not None or request_body is not None or headers is not None:
            logger.warning(
                "%s does not accept query params, request body, or headers. "
                "Ignoring passed values.",
                self.name,
            )
        if response_model is not NHLScheduleResponse:
            raise TypeError(f"response_model must be NHLScheduleResponse for {self.name}.")

        response = self.get_json(path_params, None, None, None)
        logger.debug("Response JSON: %s", response)
        return response_model(**response)  # type: ignore[return-value]


class NHLClubSchedule(BaseEndpoint):  # noqa: D101
    def __init__(self) -> None:  # noqa: D107
        super().__init__(
            base_url="https://api-web.nhle.com/v1/club-schedule",
            name="NHL Club Schedule API",
        )

    def get_data(  # noqa: D102
        self,
        # required
        path_params: tuple[str, ...] = (),
        # not accepted
        query_params: BaseModel | None = None,
        # not accepted
        request_body: BaseModel | None = None,
        # not accepted
        headers: BaseModel | None = None,
        response_model: type[BaseModel] = NHLClubScheduleResponse,
    ) -> NHLClubScheduleResponse:
        if not isinstance(path_params, NHLClubSchedulePathParams):
            raise TypeError(f"path_params must be NHLClubSchedulePathParams for {self.name}.")
        if query_params is not None or request_body is not None or headers is not None:
            logger.warning(
                "%s does not accept query params, request body, or headers. "
                "Ignoring passed values.",
                self.name,
            )
        if response_model is not NHLClubScheduleResponse:
            raise TypeError(f"response_model must be NHLClubScheduleResponse for {self.name}.")

        response = self.get_json(path_params, None, None, None)
        logger.debug("Response JSON: %s", response)
        return response_model(**response)  # type: ignore[return-value]


class NHLClubScheduleSeason(BaseEndpoint):  # noqa: D101
    def __init__(self) -> None:  # noqa: D107
        super().__init__(
            base_url="https://api-web.nhle.com/v1/club-schedule-season",
            name="NHL Club Schedule Season API",
        )

    def get_data(  # noqa: D102
        self,
        # required
        path_params: tuple[str, ...] = (),
        # not accepted
        query_params: BaseModel | None = None,
        # not accepted
        request_body: BaseModel | None = None,
        # not accepted
        headers: BaseModel | None = None,
        response_model: type[BaseModel] = NHLClubScheduleSeasonResponse,
    ) -> NHLClubScheduleSeasonResponse:
        if not isinstance(path_params, NHLClubScheduleSeasonPathParams):
            raise TypeError(
                f"path_params must be NHLClubScheduleSeasonPathParams for {self.name}.",
            )
        if query_params is not None or request_body is not None or headers is not None:
            logger.warning(
                "%s does not accept query params, request body, or headers. "
                "Ignoring passed values.",
                self.name,
            )
        if response_model is not NHLClubScheduleSeasonResponse:
            raise TypeError(
                f"response_model must be NHLClubScheduleSeasonResponse for {self.name}.",
            )

        response = self.get_json(path_params, None, None, None)
        logger.debug("Response JSON: %s", response)
        return response_model(**response)  # type: ignore[return-value]
