"""Modified Pydantic model base classes with custom config."""

# ruff: noqa: D101
from pydantic import BaseModel


class ExtraModel(BaseModel, extra="allow"):
    pass


class FrozenModel(BaseModel, frozen=True):
    pass


class StrictModel(BaseModel, strict=True):
    pass


class ExtraFrozenModel(BaseModel, extra="allow", frozen=True):
    pass


class StrictFrozenModel(BaseModel, strict=True, frozen=True):
    pass
