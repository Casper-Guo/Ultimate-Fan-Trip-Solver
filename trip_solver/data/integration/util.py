"""Integration scripts shared utilities."""

import logging

from pydantic import ValidationError

from trip_solver.data.api.google_maps.places import TextSearch
from trip_solver.models.api.google_maps.places import TextSearchRequestBody
from trip_solver.models.internal import Venue

logging.basicConfig(level=logging.INFO, format="%(filename)s\t%(levelname)s\t%(message)s")
logger = logging.getLogger(__name__)


def get_venue_info(venue_name: str, venue_place_name: str, venue_id: int | str) -> Venue:
    """Format the response from the Google Maps Places API."""
    try:
        response = (
            TextSearch()
            .post_for_data(
                request_body=TextSearchRequestBody(
                    textQuery=f"{venue_name}, {venue_place_name}",
                ),
            )
            .places[0]
        )
    except ValidationError:
        logger.exception("No matching places for %s", venue_name)
        raise

    return Venue(
        # save the name without the city and state
        name=venue_name,
        id=venue_id,
        address=response.formattedAddress,
        place_name=venue_place_name,
        place_id=response.id,
        location=response.location,
    )
