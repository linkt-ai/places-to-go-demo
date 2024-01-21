"""Venue API Endpoints."""
from starlette.responses import JSONResponse

from .base import app

from ..config import logger
from ..graph import graph_venue


# REQUEST BODIES


# ROUTES


@app.get("/venue")
async def route__get_venues(venue_id: str = None):
    """Get the list of venues.

    Kwargs:
        venue_id (str): The venue ID for which to get the venues.

    Returns:
        JSONResponse (200): The response for the request.

    Raises:
        JSONResponse (500): If there is an internal server error.
    """
    try:
        # Assert the the venue ID is provided.
        if not venue_id:
            return JSONResponse(
                status_code=400, content={"detail": "Venue ID is required"}
            )

        # Get the venue from the database.
        venue = graph_venue.get_venue(venue_id)

        if not venue:
            return JSONResponse(status_code=404, content={"detail": "Venue not found"})

        return JSONResponse(content=venue.model_dump(), status_code=200)
    except Exception as e:  # pylint: disable=broad-except
        logger.exception(e)
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
