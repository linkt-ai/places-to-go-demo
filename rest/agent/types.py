"""This file defines different Enum types and pydantic models that are used in the Agent module."""
import json
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from ..models import Event


class MessageType(Enum):
    """An enumeration of the types of messages that can be sent."""

    USER = "USER"
    AGENT = "AGENT"
    ERROR = "ERROR"


class ActivityType(Enum):
    """An enumeration of the types of activities that can be queried."""

    RESTAURANT = "restaurant"
    ACTIVITY = "activity"
    ENTERTAINMENT = "entertainment"

    @staticmethod
    def schema() -> Dict[str, Any]:
        """Get the schema for the activity type enum.

        Returns:
            Dict[str, Any]: The schema for the activity type enum.
        """
        return {
            "type": "string",
            "enum": [
                ActivityType.RESTAURANT.value,
                ActivityType.ACTIVITY.value,
                ActivityType.ENTERTAINMENT.value,
            ],
        }


class Message(BaseModel):
    """A message sent by the user or agent."""

    def model_dump(self, **kwargs):  # pylint: disable=unused-argument
        """Dump the model to a dictionary."""
        json_data = self.model_dump_json()
        data = json.loads(json_data)
        return data


class AgentMessage(Message):
    """A message sent by the agent."""

    msg_type: MessageType = MessageType.AGENT
    content: str
    events: Optional[List[Event]]


class ErrorMessage(Message):
    """A message sent when an error occurs."""

    msg_type: MessageType = MessageType.ERROR
    content: str
