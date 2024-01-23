"""The chat.py file defines the routes for utilizing the chat resource."""
from pydantic import BaseModel
from starlette.responses import JSONResponse

from .base import app
from ..agent import Agent
from ..config import logger


class HTTPChatPOSTRequest(BaseModel):
    """The request model for a POST request to the Chat resource."""

    # The user ID for the user to chat with
    user_id: str


class HTTPChatPUTRequest(BaseModel):
    """The request model for a PUT request to the Chat resource."""

    # The ID of the chat session. Used to retrieve context from Redis
    chat_id: str

    # The id of the user sending the chat
    user_id: str

    # The message sent by the user
    content: str


@app.put("/chat")
async def route__put_chat(payload: HTTPChatPUTRequest):
    """Send a message to the agent.

    Args:
        payload (HTTPChatPUTRequest): The request payload.

    Returns:
        JSONResponse (200): The response for the request.

    Raises:
        JSONResponse (400): If the chat ID is not provided.
        JSONResponse (500): If there is an internal server error.
    """
    try:
        # Get the chat session from Redis with the Chat ID
        # message_history = redis_client.get(payload.chat_id)

        agent = Agent(
            payload.user_id,
            #   message_history=message_history,
        )
        response = agent(payload.content)

        # Return the response
        return JSONResponse(status_code=200, content=response.model_dump())

    except Exception as e:  # pylint: disable=broad-except
        logger.error(e)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred"},
        )
