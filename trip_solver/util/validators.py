"""Pydantic field validation functions."""

from datetime import datetime


def check_acceptable_month_input(month_param: str | None) -> str | None:
    """Check if the input is either None or a string conforming to the YYYY-MM format."""
    if month_param is None:
        return None
    # raising is allowed and intended
    datetime.strptime(month_param, "%Y-%m")  # noqa: DTZ007 only parsing is needed
    return month_param


def check_acceptable_date_input(date_param: str | None) -> str | None:
    """Check if the input is either None or a string conforming to the YYYY-MM-DD format."""
    if date_param is None:
        return None
    # raising is allowed and intended
    datetime.strptime(date_param, "%Y-%m-%d")  # noqa: DTZ007 only parsing is needed
    return date_param
