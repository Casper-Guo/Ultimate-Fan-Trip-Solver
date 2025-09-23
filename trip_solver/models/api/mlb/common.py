"""Common data models for MLB endpoints."""

from trip_solver.util.models import FrozenModel


class MLBVenue(FrozenModel):  # noqa: D101
    id: int
    name: str
