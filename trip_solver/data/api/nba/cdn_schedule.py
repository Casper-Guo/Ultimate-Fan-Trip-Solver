"""
Official NBA schedule endpoint at cdn.nba.com.

This endpoint is no longer publish as of 10-08-2026
"""

import logging

from pydantic import BaseModel

from trip_solver.data.api import BaseEndpoint
from trip_solver.models.api.nba.cdn_schedule import NBACDNScheduleResponse

logging.basicConfig(level=logging.INFO, format="%(filename)s\t%(levelname)s\t%(message)s")
logger = logging.getLogger(__name__)


class NBACDNSchedule(BaseEndpoint):  # noqa: D101
    def __init__(self) -> None:  # noqa: D107
        super().__init__(
            base_url="https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json",
            name="NBA Schedule API",
        )

    def get_data(  # noqa: D102
        self,
        # not accepted
        path_params: tuple[str, ...] = (),
        query_params: BaseModel | None = None,
        request_body: BaseModel | None = None,
        headers: BaseModel | None = None,
        response_model: type[BaseModel] = NBACDNScheduleResponse,
    ) -> NBACDNScheduleResponse:
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

        response = self.get_json((), None, None, None)
        logger.debug("Response JSON: %s", response)
        return response_model(**response)  # type: ignore[return-value]
