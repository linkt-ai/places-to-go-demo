"""The redis.py file defines a simple Redis client that can be used to get, update, and 
delete chat conversations.
"""

import json
from typing import Dict, List, Union

from redis import Redis

from .config import settings


class RedisClient:
    """The RedisClient class is responsible for communicating with the Redis endpoint."""

    def __init__(self):
        """Setup the connection to the Redis endpoint."""
        self._url = settings.REDIS_ENDPOINT
        self._client = Redis.from_url(self._url, socket_timeout=5.0)

    def get_chat_history(self, chat_id: str) -> Union[List[Dict[str, str]], None]:
        """Get the chat history from the Redis endpoint."""
        chat_history = self._client.get(chat_id)
        if chat_history is not None:
            data = chat_history.decode("utf-8")
            message_history = json.loads(data)
            return message_history

        return None

    def update_chat_history(
        self, chat_id: str, chat_history: List[Dict[str, str]]
    ) -> None:
        """Update the chat history in the Redis endpoint.

        Should overwrite the current history with the `chat_history` argument.
        """
        data = []
        for message in chat_history:
            if isinstance(message, dict):
                data.append(message)
            else:
                data.append(message.dict())
        encoded_data = json.dumps(data)
        self._client.set(chat_id, encoded_data)

    def delete_chat_history(self, chat_id: str) -> None:
        """Delete the chat history from the Redis endpoint."""
        self._client.delete(chat_id)


redis_client = RedisClient()
