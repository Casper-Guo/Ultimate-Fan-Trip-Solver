"""MLB teams metadata endpoint."""

import logging
from typing import Any

from pydantic import BaseModel

from trip_solver.data.api import BaseEndpoint
from trip_solver.models.api.mlb.teams import MLBTeamPathParams, MLBTeamsResponse

logging.basicConfig(level=logging.INFO, format="%(filename)s\t%(levelname)s\t%(message)s")
logger = logging.getLogger(__name__)


class MLBTeams(BaseEndpoint):  # noqa: D101
    def __init__(self) -> None:  # noqa: D107
        super().__init__(
            base_url="https://statsapi.mlb.com/api/v1/teams/",
            name="MLB Teams API",
        )

    def get_data(  # noqa: D102
        self,
        path_params: tuple[Any, ...] = (),
        query_params: BaseModel | None = None,
        request_body: BaseModel | None = None,
        headers: BaseModel | None = None,
        response_model: type[BaseModel] = MLBTeamsResponse,
    ) -> MLBTeamsResponse:
        if not isinstance(path_params, MLBTeamPathParams):
            raise TypeError(
                f"path_params must be provided for {self.name} as MLBTeamPathParams.",
            )
        if query_params is not None or request_body is not None or headers is not None:
            logger.warning(
                "%s does not accept query params, request_body, or headers. Ignoring passed values.",  # noqa: E501
                self.name,
            )
        if response_model is not MLBTeamsResponse:
            raise TypeError(f"response_model must be MLBTeamsResponse for {self.name}.")

        response = self.get_json(path_params, None, None, None)
        logger.debug("Response JSON: %s", response)
        return response_model(**response)  # type: ignore[return-value]
