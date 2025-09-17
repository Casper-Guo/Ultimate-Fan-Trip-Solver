"""Generic classes for API integration."""

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any, TypeAlias

import httpx
from pydantic import BaseModel

query_param_type: TypeAlias = str | int | float | bool | None


class HTTPMethod(StrEnum):
    """HTTP methods supported by httpx."""

    GET = "GET"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


def compose_url(base_url: str, path_params: list[str]) -> str:
    """Compose a URL by appending the path params, in order, to the base URL."""
    return "/".join([base_url.rstrip("/"), *path_params])


def model_to_dict(model: BaseModel) -> dict[str, query_param_type]:
    """Convert a Pydantic model to a dictionary, excluding None values."""
    return {
        key: value
        for key, value in model.model_dump().items()
        if isinstance(key, str) and isinstance(value, query_param_type)
    }


class BaseEndpoint(ABC):
    """Base class for API endpoints."""

    base_url: str

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url

    def request(
        self,
        method: HTTPMethod,
        path_params: list[str] | None = None,
        query_params: BaseModel | None = None,
    ) -> httpx.Response:
        """Prepare httpx request from path params and query params modelled with Pydantic."""
        if path_params is None:
            path_params = []
        query_params_dict = {} if query_params is None else model_to_dict(query_params)

        return httpx.request(
            method=method.value,
            url=compose_url(self.base_url, path_params),
            params=query_params_dict,
        )

    def get(
        self, path_params: list[str] | None = None, query_params: BaseModel | None = None
    ) -> httpx.Response:
        """Send a GET request to the endpoint."""
        return self.request(HTTPMethod.GET, path_params, query_params)

    def get_json(
        self, path_params: list[str] | None = None, query_params: BaseModel | None = None
    ) -> Any:  # noqa: ANN401 follow httpx API
        """Send a GET request to the endpoint and return the raw JSON response."""
        response = self.get(path_params, query_params)
        response.raise_for_status()
        return response.json()

    @abstractmethod
    def get_data(
        self,
        path_params: list[str] | None = None,
        query_params: BaseModel | None = None,
    ) -> BaseModel:
        """Implement in the subclasses with the appropriate response model."""
