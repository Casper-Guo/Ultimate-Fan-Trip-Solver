"""Generic classes for API integration."""

import logging
from enum import StrEnum
from typing import Any, TypeAlias

import httpx
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(filename)s\t%(levelname)s\t%(message)s")
logger = logging.getLogger(__name__)

query_param_type: TypeAlias = str | int | float | bool


class HTTPMethod(StrEnum):
    """HTTP methods supported by httpx."""

    GET = "GET"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


def compose_url(base_url: str, path_params: tuple[str, ...]) -> str:
    """Compose a URL by appending the path params, in order, to the base URL."""
    return "/".join([base_url.rstrip("/"), *path_params])


class BaseEndpoint:  # noqa: D101
    base_url: str
    name: str

    def __init__(self, base_url: str, name: str) -> None:  # noqa: D107
        self.base_url = base_url
        self.name = name

    def request(
        self,
        method: HTTPMethod,
        path_params: tuple[Any, ...] = (),
        query_params: BaseModel | None = None,
        request_body: BaseModel | None = None,
        headers: BaseModel | None = None,
    ) -> httpx.Response:
        """Prepare httpx request from path params and query params modelled with Pydantic."""
        path_params_tuple = () if path_params is None else tuple(str(i) for i in path_params)
        query_params_dict = (
            {}
            if query_params is None
            else query_params.model_dump(by_alias=True, exclude_none=True)
        )
        request_body_dict = (
            {}
            if request_body is None
            else request_body.model_dump(by_alias=True, exclude_none=True)
        )
        headers_dict = (
            {} if headers is None else headers.model_dump(by_alias=True, exclude_none=True)
        )

        logger.debug(
            "Pinging %s at %s",
            self.name,
            full_url := compose_url(self.base_url, path_params_tuple),
        )
        logger.debug("Method: %s", method)
        logger.debug("Query params: %s", query_params_dict)
        logger.debug("Request body: %s", request_body_dict)
        logger.debug("Headers: %s", headers_dict)

        return httpx.request(
            method=method.value,
            url=full_url,
            params=query_params_dict,
            json=request_body_dict,
            headers=headers_dict,
            follow_redirects=True,
        )

    def get(
        self,
        path_params: tuple[Any, ...] = (),
        query_params: BaseModel | None = None,
        request_body: BaseModel | None = None,
        headers: BaseModel | None = None,
    ) -> httpx.Response:
        """
        Send a GET request to the endpoint.

        Subclasses should change the function signature to use the appropriate namedtuple class
        for the path_params parameter.
        """
        return self.request(HTTPMethod.GET, path_params, query_params, request_body, headers)

    def get_json(
        self,
        path_params: tuple[Any, ...] = (),
        query_params: BaseModel | None = None,
        request_body: BaseModel | None = None,
        headers: BaseModel | None = None,
    ) -> Any:  # noqa: ANN401 follow httpx API
        """Send a GET request to the endpoint and return the raw JSON response."""
        response = self.get(path_params, query_params, request_body, headers)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.exception(exc.response.text)
            raise
        return response.json()

    def get_data(
        self,
        path_params: tuple[Any, ...] = (),
        query_params: BaseModel | None = None,
        request_body: BaseModel | None = None,
        headers: BaseModel | None = None,
        response_model: type[BaseModel] = BaseModel,
    ) -> BaseModel:
        """Send a GET request and parse the returned JSON into a provided Pydantic model."""
        response = self.get_json(path_params, query_params, request_body, headers)
        return response_model(**response)

    def post(
        self,
        path_params: tuple[Any, ...] = (),
        query_params: BaseModel | None = None,
        request_body: BaseModel | None = None,
        headers: BaseModel | None = None,
    ) -> httpx.Response:
        """Send a POST request to the endpoint."""
        return self.request(HTTPMethod.POST, path_params, query_params, request_body, headers)

    def post_for_json(
        self,
        path_params: tuple[Any, ...] = (),
        query_params: BaseModel | None = None,
        request_body: BaseModel | None = None,
        headers: BaseModel | None = None,
    ) -> Any:  # noqa: ANN401 follow httpx API
        """Send a POST request to the endpoint and return the raw JSON response."""
        response = self.post(path_params, query_params, request_body, headers)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.exception(exc.response.text)
            raise
        return response.json()

    def post_for_data(
        self,
        path_params: tuple[Any, ...] = (),
        query_params: BaseModel | None = None,
        request_body: BaseModel | None = None,
        headers: BaseModel | None = None,
        response_model: type[BaseModel] = BaseModel,
    ) -> BaseModel:
        """Send a POST request and parse the returned JSON into a provided Pydantic model."""
        response = self.post_for_json(path_params, query_params, request_body, headers)
        logger.debug("Response JSON: %s", response)
        return response_model(**response)
