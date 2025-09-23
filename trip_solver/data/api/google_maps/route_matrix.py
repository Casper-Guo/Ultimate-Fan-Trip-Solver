"""Google Maps Route Matrix API."""

import logging
from typing import Any

from pydantic import BaseModel

from trip_solver.data.api.google_maps import GoogleMapsAPI
from trip_solver.models.api.google_maps.route_matrix import (
    RouteMatrixHeader,
    RouteMatrixRequestBody,
    RouteMatrixResponse,
)

logging.basicConfig(level=logging.INFO, format="%(filename)s\t%(levelname)s\t%(message)s")
logger = logging.getLogger(__name__)


class RouteMatrix(GoogleMapsAPI):  # noqa: D101
    def __init__(self) -> None:  # noqa: D107
        super().__init__(
            base_url="https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix",
            name="Google Maps Route Matrix API",
        )

    def post_for_data(  # noqa: D102
        self,
        # not accepted
        path_params: tuple[Any, ...] = (),
        # not accepted
        query_params: BaseModel | None = None,
        # required
        request_body: RouteMatrixRequestBody | None = None,  # type: ignore[override]
        # default provided
        headers: RouteMatrixHeader | None = None,  # type: ignore[override]
        response_model: type[BaseModel] = RouteMatrixResponse,
    ) -> RouteMatrixResponse:
        if path_params != () or query_params is not None:
            logger.warning(
                "%s does not accept path or query parameters. Ignoring passed value.",
                self.name,
            )
        if request_body is None:
            raise ValueError(f"request_body must be provided for {self.name}.")
        if headers is None:
            headers = RouteMatrixHeader()
        if response_model is not RouteMatrixResponse:
            raise TypeError(f"response_model must be RouteMatrixResponse for {self.name}.")

        response = self.post_for_json((), None, request_body, headers)
        logger.debug("Response JSON: %s", response)
        return response_model(routes=response)  # type: ignore[return-value]
