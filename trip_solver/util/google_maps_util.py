"""Google Maps related utilities."""

from trip_solver.models.internal import Venue


def format_route_url(route: list[Venue]) -> str:
    """Produce the Google Map URL for a given route."""
    waypoints = "/".join(
        f"{venue.name} {venue.place_name}".replace(" ", "+") for venue in route
    )
    return f"https://www.google.com/maps/dir/{waypoints}"
