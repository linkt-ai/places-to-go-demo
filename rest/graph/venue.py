"""This file defines the graph queries for the Venue resource."""
from typing import Union

from .driver import get_driver
from ..models import YelpVenue


def get_venue(venue_id: str) -> Union[YelpVenue, None]:
    """Get a venue from the graph database.

    Args:
        venue_id (str): The ID of the venue to get.

    Returns:
        Union[YelpVenue, None]: The venue from the graph database or None
            if it does not exist.
    """
    try:
        with get_driver().session() as session:
            result = session.run(
                """
                MATCH (v:Venue {id: $venue_id})
                RETURN v
                """,
                venue_id=venue_id,
            )
            venue = result.single()["v"]
            return YelpVenue(**venue)
    except TypeError:
        return None
