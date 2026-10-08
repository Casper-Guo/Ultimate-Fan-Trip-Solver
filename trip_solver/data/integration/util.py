"""Integration scripts shared utilities."""

import logging
from collections.abc import Iterable

from pydantic import ValidationError

from trip_solver.data.api.google_maps.places import TextSearch
from trip_solver.models.api.google_maps.places import PlaceResponse, TextSearchRequestBody
from trip_solver.models.internal import Venue, Venues

logging.basicConfig(level=logging.INFO, format="%(filename)s\t%(levelname)s\t%(message)s")
logger = logging.getLogger(__name__)

NORTH_AMERICA_COUNTRY_CODES = frozenset({"US", "CA", "MX"})


def get_country_code(place: PlaceResponse) -> str | None:
    """Extract the ISO 3166-1 alpha-2 country code from a place's address components."""
    for component in place.addressComponents or []:
        if "country" in component.types:
            return component.shortText
    return None


def get_venue_info(venue_name: str, venue_place_name: str, venue_id: int | str) -> Venue:
    """Format the response from the Google Maps Places API."""
    try:
        response = (
            TextSearch()
            .post_for_data(
                request_body=TextSearchRequestBody(
                    # filters out venue_place_name if it is the empty string
                    # which symbolizes neutral site games
                    # in which case the query text is the venue name only
                    textQuery=", ".join(filter(None, (venue_name, venue_place_name))),
                ),
            )
            .places[0]
        )
    except ValidationError:
        logger.exception("No matching places for %s", venue_name)
        raise

    if (country := get_country_code(response)) is None:
        raise ValueError(f"Places API returned no country for {venue_name}")

    return Venue(
        # save the name without the city and state
        name=venue_name,
        id=venue_id,
        address=response.formattedAddress,
        place_name=venue_place_name,
        place_id=response.id,
        location=response.location,
        country=country,
    )


def filter_north_american_venues(venues: Iterable[Venue]) -> Venues:
    """Remove venues outside North America, which the solvers should consider unreachable."""
    kept: list[Venue] = []
    for venue in venues:
        if venue.country not in NORTH_AMERICA_COUNTRY_CODES:
            logger.info("Excluding %s (%s): outside North America", venue.name, venue.country)
            continue
        kept.append(venue)
    return Venues(venues=kept)
