"""The event.py file defines the routes for the event resource."""
from pydantic import BaseModel
from starlette.responses import JSONResponse

from .base import app

from ..config import logger
from ..models import (
    Event,
    InvalidEventTimeError,
    CitiesDoNotMatchError,
    EventTimeOverlapError,
)

from ..graph import graph_venue, graph_itinerary, graph_event


class HTTPEventPOSTRequest(BaseModel):
    """The request model for a POST request to the Event resource."""

    # The user ID for which to create the event
    user_id: str

    # The Yelp Venue ID of the event
    venue_id: str

    # The start time of the event
    start_time: str

    # The end time of the event
    end_time: str


class HTTPEventPUTRequest(BaseModel):
    """The request model for a PUT request to the Event resource."""


class HTTPEventDELETERequest(BaseModel):
    """The request model for a DELETE request to the Event resource."""


@app.post("/event")
async def route__post_event(payload: HTTPEventPOSTRequest) -> JSONResponse:
    """Create an event.

    NOTE: The yelp_id is used to fetch the venue of the event. If the city of the
    venue and the city of the user's current itinerary do not match, a 400 response
    is returned.

    Args:
        event (HTTPEventPOSTRequest): The event to create.

    Returns:
        JSONResponse (200): The response for the request.

    Raises:
        JSONResponse (500): If there is an internal server error.
    """
    try:
        # Get the Yelp Venue and itinerary to validate the cities
        venue = graph_venue.get_venue(payload.venue_id)
        itinerary = graph_itinerary.get_itinerary(payload.user_id)

        # Assert that both results exist
        if venue is None:
            return JSONResponse(
                status_code=404,
                content={"detail": f"Venue with id '{payload.venue_id}' not found"},
            )
        if itinerary is None:
            return JSONResponse(
                status_code=404,
                content={
                    "detail": f"Itinerary for user with id '{payload.user_id}' not found"
                },
            )

        # Create the event object
        event = Event.create_event(
            start_time=payload.start_time,
            end_time=payload.end_time,
            venue=venue,
            itinerary=itinerary,
        )
        graph_event.create_event(event, payload.user_id)

        # Create the event in the database

        # Return the response
        return JSONResponse(status_code=200, content={"event": event.model_dump()})

    except InvalidEventTimeError as exp:
        return JSONResponse(
            status_code=400,
            content={"detail": str(exp)},
        )
    except CitiesDoNotMatchError as exp:
        return JSONResponse(
            status_code=400,
            content={"detail": str(exp)},
        )
    except EventTimeOverlapError as exp:
        return JSONResponse(
            status_code=400,
            content={"detail": str(exp)},
        )
    except Exception as exp:  # pylint: disable=broad-except
        logger.error(exp)
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
