"""The event.py file defines the data models for the Event resource."""
import re
from datetime import datetime

from pydantic import BaseModel


class Event(BaseModel):
    """The Event class defines the data model for an event.

    Attributes:
        id (str): The event ID.
        start_time (datetime): The start time of the event.
        end_time (datetime): The end time of the event.
        title (str): The title of the event.
        url (str): The URL of the event.
        thumbnail_url (str): The thumbnail URL of the event.
    """

    id: str
    start_time: datetime
    end_time: datetime
    title: str
    url: str
    thumbnail_url: str

    def __init__(self, convert: bool = True, **kwargs) -> None:
        if convert:
            kwargs = {self._camel_to_snake(k): v for k, v in kwargs.items()}

        super().__init__(**kwargs)

    @staticmethod
    def _camel_to_snake(name):
        """Convert a string from camel case to snake case.

        Args:
            name (str): The string to convert.
        """
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
