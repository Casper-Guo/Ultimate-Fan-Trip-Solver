"""MLB schedule endpoint."""

import logging

from pydantic import BaseModel

from trip_solver.data.api import BaseEndpoint
from trip_solver.models.api.mlb.schedule import MLBScheduleQueryParams, MLBScheduleResponse

logging.basicConfig(level=logging.INFO, format="%(filename)s\t%(levelname)s\t%(message)s")
logger = logging.getLogger(__name__)


class MLBSchedule(BaseEndpoint):  # noqa: D101
    def __init__(self) -> None:  # noqa: D107
        super().__init__(
            base_url="https://statsapi.mlb.com/api/v1/schedule",
            name="MLB Schedule API",
        )

    def get_data(  # noqa: D102
        self,
        # not accepted
        path_params: tuple[str, ...] = (),
        # required
        query_params: MLBScheduleQueryParams | None = None,  # type: ignore[override]
        # not accepted
        request_body: BaseModel | None = None,
        # not accepted
        headers: BaseModel | None = None,
        response_model: type[BaseModel] = MLBScheduleResponse,
    ) -> MLBScheduleResponse:
        if path_params != ():
            logger.warning(
                "%s does not accept path params. Ignoring passed value.",
                self.name,
            )
        if query_params is None:
            raise ValueError(f"query_params must be provided for {self.name}.")
        if request_body is not None or headers is not None:
            logger.warning(
                "%s does not accept request body or headers. Ignoring passed value.",
                self.name,
            )
        if response_model is not MLBScheduleResponse:
            raise TypeError(f"response_model must be MLBScheduleResponse for {self.name}.")

        response = self.get_json((), query_params, None, None)
        logger.debug("Response JSON: %s", response)
        return response_model(**response)  # type: ignore[return-value]
