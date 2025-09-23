"""
Google Maps Places API.

Only text search is implemented for now.
"""

import logging

from pydantic import BaseModel

from trip_solver.data.api.google_maps import GoogleMapsAPI
from trip_solver.models.api.google_maps.places import (
    TextSearchHeader,
    TextSearchRequestBody,
    TextSearchResponse,
)

logging.basicConfig(level=logging.INFO, format="%(filename)s\t%(levelname)s\t%(message)s")
logger = logging.getLogger(__name__)


class TextSearch(GoogleMapsAPI):  # noqa: D101
    def __init__(self) -> None:  # noqa: D107
        super().__init__(
            base_url="https://places.googleapis.com/v1/places:searchText",
            name="Google Maps Places API - Text Search",
        )

    def post_for_data(  # noqa: D102
        self,
        # not accepted
        path_params: tuple[str, ...] = (),
        # not accepted
        query_params: BaseModel | None = None,
        # required
        request_body: TextSearchRequestBody | None = None,  # type: ignore[override]
        # default provided
        headers: TextSearchHeader | None = None,  # type: ignore[override]
        response_model: type[BaseModel] = TextSearchResponse,
    ) -> TextSearchResponse:
        if path_params != () or query_params is not None:
            logger.warning(
                "%s does not accept path or query parameters. Ignoring passed value.",
                self.name,
            )
        if request_body is None:
            raise ValueError(f"request_body must be provided for {self.name}.")
        if headers is None:
            headers = TextSearchHeader()
        if response_model is not TextSearchResponse:
            raise TypeError(f"response_model must be TextSearchResponse for {self.name}.")

        response = self.post_for_json((), None, request_body, headers)
        logger.debug("Response JSON: %s", response)
        return response_model(**response)  # type: ignore[return-value]
