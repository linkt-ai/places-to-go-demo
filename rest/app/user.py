"""This file defines the routes for interacting with the User resource.

Currently, the User resource is managed through Clerk. You can create a username
with a simple username and password combination. Or, you can create a new user by
using the demo webapp. 

All of the resources in the API are assumed to be user specific. Currently, the 
`user_id` field is including in many request payloads or as a query param, to scope
the resources that are accessed based on the user. In the future, it would make sense
to authenticate requests through a JWT that encodes the user ID. This would allow
us to scope the resources based on the user ID in the JWT, rather than having to
pass it around in the request payloads.
"""
from typing import Optional

from pydantic import BaseModel

from starlette.responses import JSONResponse

from .base import app

from ..config import logger
from ..clerk import ClerkClient, ClerkClientError, ClerkUserDoesNotExist


class HTTPUserPOSTRequest(BaseModel):
    """The request model for a POST request to the User resource.

    Attributes:
        email (str): The email of the user.
        first_name (str): The first name of the user.
        last_name (str): The last name of the user.
        password (str): The password of the user.
    """

    # The email of the user
    email: str

    # The first name of the user
    first_name: str

    # The last name of the user
    last_name: str

    # The password of the user (Must be 8 characters long)
    password: str


class HTTPUserDELETERequest(BaseModel):
    """The request model for a DELETE request to the User resource."""

    # The email of the user
    user_id: str


@app.post("/user")
async def route__create_user(payload: HTTPUserPOSTRequest):
    """Create a new user in the database."""

    clerk = ClerkClient()

    try:
        user = clerk.create_user(
            email=payload.email,
            first_name=payload.first_name,
            last_name=payload.last_name,
            password=payload.password,
        )
        return JSONResponse(status_code=200, content=user.model_dump())

    except ClerkClientError as exp:
        logger.error(exp)
        return JSONResponse(status_code=400, content={"detail": exp.message})

    except Exception as exp:  # pylint: disable=broad-except
        logger.error(exp)
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )


@app.get("/user")
async def route__get_users(user_id: Optional[str] = None):
    """Get all users in the database.

    Optionally, the client can provide a `user_id` query param to
    filter for a specific user.
    """
    clerk = ClerkClient()
    try:
        if user_id:
            user = clerk.get_user(user_id)
            if user is None:
                return JSONResponse(status_code=200, content=[])
            return JSONResponse(status_code=200, content=[user.model_dump()])

        users = clerk.list_users()
        return JSONResponse(
            status_code=200, content=[user.model_dump() for user in users]
        )
    except ClerkClientError as exp:
        logger.error(exp)
        return JSONResponse(status_code=400, content={"detail": exp.message})

    except Exception as exp:  # pylint: disable=broad-except
        logger.error(exp)
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )


@app.delete("/user")
async def route__delete_user(payload: HTTPUserDELETERequest):
    """Delete a user from the database."""
    clerk = ClerkClient()

    try:
        clerk.delete_user(payload.user_id)
        return JSONResponse(status_code=200, content={})

    except ClerkClientError as exp:
        logger.error(exp)
        return JSONResponse(status_code=400, content={"detail": exp.message})

    except ClerkUserDoesNotExist as exp:
        logger.error(exp)
        return JSONResponse(status_code=400, content={"detail": exp.message})

    except Exception as exp:  # pylint: disable=broad-except
        logger.error(exp)
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )
