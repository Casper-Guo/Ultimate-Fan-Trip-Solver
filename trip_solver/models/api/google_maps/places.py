"""Google Maps Places API i/o pydantic models."""

from typing import Literal, TypeAlias

from pydantic import Field, field_serializer

from trip_solver.models.api.google_maps.common import LatLng, LocalizedText
from trip_solver.util.models import FrozenModel, StrictModel

# not a complete list, see https://developers.google.com/maps/documentation/places/web-service/text-search#fieldmask
TextSearchReturnFields: TypeAlias = tuple[
    Literal[
        # Places API Text Search Essentials SKU, unlimited usage
        "places.id",
        # contains the place resource name in the form: places/PLACE_ID
        # use places.displayName to access the text name of the place
        "places.name",
        "nextPageToken",
        # Places API Text Search Pro SKU, 5,000 requests/month free
        "places.displayName",
        "places.formattedAddress",
        "places.location",
    ],
    ...,
]


class TextSearchRequestBody(StrictModel):
    """
    Request body for Places API text search.

    Not all available parameters are modelled.
    See https://developers.google.com/maps/documentation/places/web-service/text-search#optional-parameters
    """

    textQuery: str


class TextSearchHeader(StrictModel):  # noqa: D101
    fields: TextSearchReturnFields = Field(
        default=(
            "places.id",
            "places.name",
            "places.displayName",
            "places.formattedAddress",
            "places.location",
        ),
        alias="X-Goog-FieldMask",
    )

    @field_serializer("fields")
    def serialize_fields(self, fields: TextSearchReturnFields) -> str:  # noqa: PLR6301
        """Convert tuple of fields to comma-separated string."""
        return ",".join(fields)


class PlaceResponse(FrozenModel):
    """A Place object returned by the Places API."""

    name: str | None = None
    id: str | None = None
    displayName: LocalizedText | None = None
    formattedAddress: str | None = None
    location: LatLng | None = None


class TextSearchResponse(FrozenModel):
    """
    Returned fields depend on the field mask passed in the request.

    For every new option added to TextSearchReturnFields,
    a corresponding field should be created here.
    """

    places: list[PlaceResponse]
    nextPageToken: str | None = None
