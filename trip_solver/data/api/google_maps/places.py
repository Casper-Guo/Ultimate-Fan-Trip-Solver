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

    def post_for_data(
        self,
        path_params: tuple[str, ...] = (),
        query_params: BaseModel | None = None,
        request_body: TextSearchRequestBody | None = None,  # type: ignore[override]
        headers: TextSearchHeader | None = None,  # type: ignore[override]
        response_model: type[BaseModel] = TextSearchResponse,
    ) -> BaseModel:
        """Implement in the subclasses with the appropriate response model."""
        if path_params != () or query_params is not None:
            logger.warning(
                (
                    "This endpoint does not accept path or query parameters. "
                    "Passing one has no effect."
                ),
            )
        if request_body is None:
            raise ValueError("request_body must be provided.")
        if headers is None:
            headers = TextSearchHeader()

        return response_model(**self.post_for_json((), None, request_body, headers))
