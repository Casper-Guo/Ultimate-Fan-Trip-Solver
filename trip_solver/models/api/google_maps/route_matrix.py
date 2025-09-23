"""Google Maps Route Matrix API i/o pydantic models."""

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal, Self, TypeAlias

from pydantic import Field, field_serializer, field_validator, model_validator

from trip_solver.models.api.google_maps.common import LocalizedText, Waypoint, gRPCCode
from trip_solver.util.models import FrozenModel, StrictModel

RouteMatrixReturnFields: TypeAlias = tuple[
    Literal[
        "status",
        "condition",
        "distanceMeters",
        "duration",
        "staticDuration",
        # available but not modelled
        # "travelAdvisory",
        "fallbackInfo",
        "localizedValues",
        "originIndex",
        "destinationIndex",
    ],
    ...,
]


class VehicleEmissionType(StrEnum):  # noqa: D101
    VEHICLE_EMISSION_TYPE_UNSPECIFIED = "VEHICLE_EMISSION_TYPE_UNSPECIFIED"
    GASOLINE = "GASOLINE"
    ELECTRIC = "ELECTRIC"
    HYBRID = "HYBRID"
    DIESEL = "DIESEL"


class VehicleInfo(StrictModel):  # noqa: D101
    emissionType: VehicleEmissionType = VehicleEmissionType.VEHICLE_EMISSION_TYPE_UNSPECIFIED

    @field_serializer("emissionType")
    def serialize_emission_type(self, emission_type: VehicleEmissionType) -> str:  # noqa: D102, PLR6301
        return emission_type.value


class RouteModifiers(StrictModel):  # noqa: D101
    avoidTolls: bool = False
    avoidHighways: bool = False
    avoidFerries: bool = False
    avoidIndoor: bool = False
    vehicleInfo: VehicleInfo = Field(default_factory=VehicleInfo)
    # available but not modelled/used
    # tollPasses: list[TollPass] | None = None  # noqa: ERA001


class RouteMatrixOrigin(StrictModel):  # noqa: D101
    waypoint: Waypoint
    routeModifiers: RouteModifiers | None = None


class RouteMatrixDestination(StrictModel):  # noqa: D101
    waypoint: Waypoint


class RouteTravelMode(StrEnum):  # noqa: D101
    TRAVEL_MODE_UNSPECIFIED = "TRAVEL_MODE_UNSPECIFIED"
    DRIVE = "DRIVE"
    BICYCLE = "BICYCLE"
    WALK = "WALK"
    TWO_WHEELER = "TWO_WHEELER"
    TRANSIT = "TRANSIT"


class RoutingPreference(StrEnum):  # noqa: D101
    ROUTING_PREFERENCE_UNSPECIFIED = "ROUTING_PREFERENCE_UNSPECIFIED"
    TRAFFIC_AWARE = "TRAFFIC_AWARE"
    TRAFFIC_AWARE_OPTIMAL = "TRAFFIC_AWARE_OPTIMAL"
    TRAFFIC_UNAWARE = "TRAFFIC_UNAWARE"


class Units(StrEnum):  # noqa: D101
    UNITS_UNSPECIFIED = "UNITS_UNSPECIFIED"
    METRIC = "METRIC"
    IMPERIAL = "IMPERIAL"


class TrafficModel(StrEnum):  # noqa: D101
    TRAFFIC_MODEL_UNSPECIFIED = "TRAFFIC_MODEL_UNSPECIFIED"
    BEST_GUESS = "BEST_GUESS"
    PESSIMISTIC = "PESSIMISTIC"
    OPTIMISTIC = "OPTIMISTIC"


class RouteMatrixRequestBody(StrictModel):
    """
    Required and optional parameters for the body of a Route Matrix request.

    See https://developers.google.com/maps/documentation/routes/reference/rest/v2/TopLevel/computeRouteMatrix#request-body
    """

    origins: list[RouteMatrixOrigin]
    destinations: list[RouteMatrixDestination]
    travelMode: RouteTravelMode = RouteTravelMode.DRIVE
    routingPreference: RoutingPreference = RoutingPreference.TRAFFIC_UNAWARE
    departureTime: str | None = None
    arrivalTime: str | None = None
    languageCode: str = "en-US"
    regionCode: str = "us"
    units: Units = Units.IMPERIAL
    trafficModel: TrafficModel = TrafficModel.TRAFFIC_MODEL_UNSPECIFIED
    # available but not modelled/used
    # extraComputations: list[ExtraComputation] | None = None  # noqa: ERA001
    # transitPreferences: TransitPreferences | None = None  # noqa: ERA001

    @field_serializer("travelMode", "routingPreference", "units", "trafficModel")
    def serialize_enums(self, v: StrEnum) -> str:  # noqa: D102, PLR6301
        return v.value

    @field_validator("travelMode", mode="before")
    @classmethod
    def validate_travel_mode(cls, v: str | RouteTravelMode) -> RouteTravelMode:  # noqa: D102
        if isinstance(v, RouteTravelMode):
            return v
        return RouteTravelMode(v)

    @field_validator("routingPreference", mode="before")
    @classmethod
    def validate_routing_preference(cls, v: str | RoutingPreference) -> RoutingPreference:  # noqa: D102
        if isinstance(v, RoutingPreference):
            return v
        return RoutingPreference(v)

    @field_validator("units", mode="before")
    @classmethod
    def validate_units(cls, v: str | Units) -> Units:  # noqa: D102
        if isinstance(v, Units):
            return v
        return Units(v)

    @field_validator("trafficModel", mode="before")
    @classmethod
    def validate_traffic_model(cls, v: str | TrafficModel) -> TrafficModel:  # noqa: D102
        if isinstance(v, TrafficModel):
            return v
        return TrafficModel(v)

    @field_validator("departureTime", "arrivalTime", mode="before")
    @classmethod
    def convert_timestamp_to_rfc3339(cls, v: str | datetime | None) -> str | None:
        """Convert datetime object to RFC 3339 string."""
        if v is None or isinstance(v, str):
            return v
        if isinstance(v, datetime):
            return v.isoformat() + ("Z" if v.tzinfo is None else "")
        raise TypeError("Expected str, datetime, or None")

    @model_validator(mode="after")
    def enforce_elements_limit(self) -> Self:
        """
        Enforce Google API rules about maximum allowed elements in one request.

        See https://developers.google.com/maps/documentation/routes/reference/rest/v2/TopLevel/computeRouteMatrix#request-body
        """
        if (
            len(self.origins) + len(self.destinations) > 50  # noqa: PLR2004
            or len(self.origins) * len(self.destinations) > 625  # noqa: PLR2004
            or (
                len(self.origins) * len(self.destinations) > 100  # noqa: PLR2004
                and (
                    self.routingPreference is RoutingPreference.TRAFFIC_AWARE_OPTIMAL
                    or self.travelMode is RouteTravelMode.TRANSIT
                )
            )
        ):
            raise ValueError("Number of elements exceeds the allowed limits.")
        return self


class RouteMatrixHeader(StrictModel):  # noqa: D101
    fields: RouteMatrixReturnFields = Field(
        default=(
            "status",
            "condition",
            "distanceMeters",
            "staticDuration",
            "originIndex",
            "destinationIndex",
        ),
        alias="X-Goog-FieldMask",
    )
    content_type: str = Field("application/json", alias="Content-Type")

    @field_serializer("fields")
    def serialize_fields(self, fields: RouteMatrixReturnFields) -> str:  # noqa: PLR6301
        """Convert tuple of fields to comma-separated string."""
        return ",".join(fields)


class RouteMatrixStatus(StrictModel):  # noqa: D101
    code: gRPCCode = gRPCCode.OK
    message: str = ""
    details: list[Any] = Field(default_factory=list)

    @field_validator("code", mode="before")
    @classmethod
    def convert_code_to_enum(cls, v: int) -> gRPCCode:  # noqa: D102
        return gRPCCode(v)


class RouteMatrixElementCondition(StrEnum):  # noqa: D101
    ROUTE_MATRIX_ELEMENT_CONDITION_UNSPECIFIED = "ROUTE_MATRIX_ELEMENT_CONDITION_UNSPECIFIED"
    ROUTE_EXISTS = "ROUTE_EXISTS"
    ROUTE_NOT_FOUND = "ROUTE_NOT_FOUND"


class FallbackRoutingMode(StrEnum):  # noqa: D101
    FALLBACK_TRAFFIC_UNAWARE = "FALLBACK_TRAFFIC_UNAWARE"
    FALLBACK_TRAFFIC_AWARE = "FALLBACK_TRAFFIC_AWARE"


class FallbackReason(StrEnum):  # noqa: D101
    FALLBACK_REASON_UNSPECIFIED = "FALLBACK_REASON_UNSPECIFIED"
    SERVER_ERROR = "SERVER_ERROR"
    LATENCY_EXCEEDED = "LATENCY_EXCEEDED"


class RouteMatrixElementFallbackInfo(StrictModel):  # noqa: D101
    routingMode: FallbackRoutingMode
    reason: FallbackReason

    @field_validator("routingMode", mode="before")
    @classmethod
    def convert_routing_mode_to_enum(cls, v: str) -> FallbackRoutingMode:  # noqa: D102
        return FallbackRoutingMode(v)

    @field_validator("reason", mode="before")
    @classmethod
    def convert_reason_to_enum(cls, v: str) -> FallbackReason:  # noqa: D102
        return FallbackReason(v)


class RouteMatrixElementLocalizedValues(StrictModel):  # noqa: D101
    distance: LocalizedText
    duration: LocalizedText
    staticDuration: LocalizedText
    transitDuration: LocalizedText


class RouteMatrixElement(FrozenModel):  # noqa: D101
    status: RouteMatrixStatus | None = None
    condition: RouteMatrixElementCondition | None = RouteMatrixElementCondition.ROUTE_EXISTS
    distanceMeters: int | None = Field(None, ge=0)
    duration: int | None = Field(None, ge=0)
    staticDuration: int | None = Field(None, ge=0)
    fallbackInfo: RouteMatrixElementFallbackInfo | None = None
    localizedValues: RouteMatrixElementLocalizedValues | None = None
    originIndex: int | None = Field(None, ge=0)
    destinationIndex: int | None = Field(None, ge=0)

    @field_validator("condition", mode="before")
    @classmethod
    def convert_condition_to_enum(cls, v: str | None) -> RouteMatrixElementCondition | None:
        """Convert condition string to enum."""
        if v is None:
            return v
        return RouteMatrixElementCondition(v)

    @field_validator("duration", "staticDuration", mode="before")
    @classmethod
    def convert_duration_to_int(cls, v: str | None) -> int | None:
        """
        Convert API returned duration string to the nearest integer number of seconds.

        A duration is returned in seconds with up to nine fractional digits, ending with 's'.

        Example: '3.5s'
        """
        return round(float(v[:-1])) if v is not None else None


class RouteMatrixResponse(FrozenModel):  # noqa: D101
    routes: list[RouteMatrixElement]
