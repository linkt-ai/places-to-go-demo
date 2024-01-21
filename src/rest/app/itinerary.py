"""This file defines the routes for the itinerary resource."""
from pydantic import BaseModel
from starlette.responses import JSONResponse

from .base import app

from ..config import logger
from ..models import City, Itinerary
from ..graph import graph_itinerary


class HTTPItineraryPOSTRequest(BaseModel):
    """The request model for a POST request to the Itinerary resource."""

    # The user ID for which to create the itinerary
    user_id: str

    # The city for which to create the itinerary
    city: City

    # The start date of the itinerary
    start_date: str

    # The end date of the itinerary
    end_date: str


@app.get("/itinerary")
async def route__get_itinerary(user_id: str = None) -> JSONResponse:
    """Get a user's itinerary.

    Kwargs:
        user_id (str): The user ID for which to get the itinerary.

    Returns:
        JSONResponse (200): The response for the request.

    Raises:
        JSONResponse (500): If there is an internal server error.
        JSONResponse (400): If the user id is not provided.
        JSONResponse (404): If the itinerary is not found.
    """
    try:
        # Assert the the user ID is provided.
        if not user_id:
            return JSONResponse(
                status_code=400, content={"detail": "User ID is required"}
            )

        # Query the database to get a user's itinerary and all the associated events.
        itinerary = graph_itinerary.get_itinerary(user_id)

        if itinerary is None:
            return JSONResponse(status_code=404, content={"detail": "Not found"})

        return JSONResponse(status_code=200, content=itinerary.model_dump())
    except Exception as exp:  # pylint: disable=broad-except
        logger.error(exp)
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )


@app.post("/itinerary")
async def route__create_itinerary(payload: HTTPItineraryPOSTRequest) -> JSONResponse:
    """Create an itinerary for a user.

    Args:
        payload (HTTPItineraryPOSTRequest): The request payload.

    Returns:
        JSONResponse (200): The response for the request.

    Raises:
        JSONResponse (500): If there is an internal server error.
    """

    try:
        # Create the itinerary object
        new_itinerary = Itinerary(events=[], **payload.model_dump())

        # Create the itinerary in the database.
        existed = graph_itinerary.create_itinerary(new_itinerary)
        return JSONResponse(
            status_code=200,
            content={
                "itinerary_created_count": 1 if existed else 0,
                "itinerary": new_itinerary.model_dump(),
            },
        )
    except Exception as exp:  # pylint: disable=broad-except
        logger.error(exp)
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
