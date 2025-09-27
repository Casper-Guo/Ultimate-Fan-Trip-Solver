"""MLB teams metadata endpoint."""

import logging
from typing import Any

from pydantic import BaseModel

from trip_solver.data.api import BaseEndpoint
from trip_solver.models.api.mlb.teams import (
    MLBTeamsPathParams,
    MLBTeamsQueryParams,
    MLBTeamsResponse,
)

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
        # specify at most one of the following two
        # default provided to return only current MLB teams
        path_params: tuple[Any, ...] = (),
        query_params: MLBTeamsQueryParams | None = None,  # type: ignore[override]
        # not accepted
        request_body: BaseModel | None = None,
        # not accepted
        headers: BaseModel | None = None,
        response_model: type[BaseModel] = MLBTeamsResponse,
    ) -> MLBTeamsResponse:
        if len(path_params) > 0:
            if not isinstance(path_params, MLBTeamsPathParams):
                raise TypeError(
                    f"path_params must be provided for {self.name} as MLBTeamsPathParams.",
                )
            if query_params is not None:
                raise ValueError("Query params have no effect when path_params is provided.")
        elif query_params is None:
            query_params = MLBTeamsQueryParams()
        if request_body is not None or headers is not None:
            logger.warning(
                "%s does not accept request_body or headers. Ignoring passed values.",
                self.name,
            )
        if response_model is not MLBTeamsResponse:
            raise TypeError(f"response_model must be MLBTeamsResponse for {self.name}.")

        response = self.get_json(path_params, query_params, None, None)
        logger.debug("Response JSON: %s", response)
        return response_model(**response)  # type: ignore[return-value]
