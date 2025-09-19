"""Generic GCP API for handling authentication."""

import httpx
from pydantic import BaseModel, Field

from trip_solver.data.api import BaseEndpoint, HTTPMethod
from trip_solver.util.models import ExtraModel

from ._secret import KEY


class GoogleAPIAuthHeader(ExtraModel):
    """Append API key to custom headers."""

    api_key: str = Field(default=KEY, alias="X-Goog-Api-Key")


class GoogleMapsAPI(BaseEndpoint):
    """Base class for all Google Maps API endpoints that handles authentication."""

    def request(
        self,
        method: HTTPMethod,
        path_params: tuple[str, ...] = (),
        query_params: BaseModel | None = None,
        request_body: BaseModel | None = None,
        headers: BaseModel | None = None,
    ) -> httpx.Response:
        """Prepare httpx request from path params and query params modelled with Pydantic."""
        return super().request(
            method,
            path_params,
            query_params,
            request_body,
            headers=GoogleAPIAuthHeader(**headers.model_dump(by_alias=True))
            if headers is not None
            else GoogleAPIAuthHeader(),
        )
