"""The event.py file defines the routes for the event resource."""
from pydantic import BaseModel
from starlette.responses import JSONResponse

from .base import app

from ..config import logger
from ..models import (
    Event,
    InvalidStartAndEndTimeError,
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

    # The ID of the event
    id: str

    # The user ID for which to create the event
    user_id: str

    # The start time of the event
    start_time: str

    # The end time of the event
    end_time: str


class HTTPEventDELETERequest(BaseModel):
    """The request model for a DELETE request to the Event resource."""

    # The id of the event to delete
    id: str

    # The id of the user who owns the event
    user_id: str


@app.post("/event")
async def route__post_event(  # pylint: disable=too-many-return-statements
    payload: HTTPEventPOSTRequest,
) -> JSONResponse:
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

    except InvalidStartAndEndTimeError as exp:
        return JSONResponse(
            status_code=400,
            content={"detail": str(exp)},
        )
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


@app.put("/event")
async def route__put_event(  # pylint: disable=too-many-return-statements
    payload: HTTPEventPUTRequest,
) -> JSONResponse:
    """Update the times of anevent.

    Args:
        payload (HTTPEventPUTRequest): The request payload.

    Returns:
        JSONResponse (200): The response for the request.

    Raises:
        JSONResponse (404): If the event does not exist.
        JSONResponse (404): If the itinerary does not exist
        JSONResponse (400): If there is an issue with the proposed times
        JSONResponse (500): If there is an internal server error.
    """
    try:
        # Get the itinerary and the event
        itinerary = graph_itinerary.get_itinerary(payload.user_id)
        if itinerary is None:
            return JSONResponse(
                status_code=404,
                content={
                    "detail": f"Itinerary for user with id '{payload.user_id}' not found"
                },
            )

        # Remove the event in the itinerary list
        event = itinerary.pop_event(payload.id)
        if event is None:
            return JSONResponse(
                status_code=404,
                content={
                    "detail": f"Event with id '{payload.id}' not found in the user's itinerary."
                },
            )

        # Now we need to process the times from the payload to make them TZ aware
        aware_start, aware_end = itinerary.make_times_aware(
            payload.start_time, payload.end_time
        )

        # Now we have an existant event. We need to validate the new times
        itinerary.validate_new_event(
            # We can use the itinerary city because we know the event is in the itinerary
            itinerary.city,
            aware_start,
            aware_end,
        )

        # Now, we need to use the event ID and the times to update the event in the database
        updated = graph_event.update_event(payload.id, aware_start, aware_end)

        if not updated:
            return JSONResponse(
                status_code=404,
                content={
                    "detail": f"Event with id '{payload.id}' not found in the database."
                },
            )

        return JSONResponse(status_code=200, content={"event_updated": updated})

    except InvalidStartAndEndTimeError as exp:
        return JSONResponse(
            status_code=400,
            content={"detail": str(exp)},
        )
    except InvalidEventTimeError as exp:
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


@app.delete("/event")
async def route__delete_event(payload: HTTPEventDELETERequest):
    """Delete an event.

    Args:
        payload (HTTPEventDELETERequest): The request payload.

    Returns:
        JSONResponse (200): The response for the request.

    Raises:
        JSONResponse (404): If the event does not exist.
        JSONResponse (404): If the itinerary does not exist
        JSONResponse (500): If there is an internal server error.
    """

    try:
        # First we want to fetch the user's itinerary and get the event from it
        # This is an easy way to verify the user owns the event
        itinerary = graph_itinerary.get_itinerary(payload.user_id)
        if itinerary is None:
            return JSONResponse(
                status_code=404,
                content={
                    "detail": f"Itinerary for user with id '{payload.user_id}' not found"
                },
            )

        # Remove the event in the itinerary list
        event = itinerary.pop_event(payload.id)
        if event is None:
            return JSONResponse(
                status_code=404,
                content={
                    "detail": f"Event with id '{payload.id}' not found in the user's itinerary."
                },
            )

        # now we need to use the ID of the removed event to delete it from the graph
        deleted = graph_event.delete_event(payload.id)

        return JSONResponse(status_code=200, content={"event_deleted": deleted})
    except Exception as exp:  # pylint: disable=broad-except
        logger.error(exp)
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
