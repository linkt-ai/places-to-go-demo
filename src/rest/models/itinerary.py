"""The itinerary.py file definees the data models for the Itinerary resource."""
import json
import re
from datetime import date
from typing import Any, Dict, List

from pydantic import BaseModel

from .event import Event
from .venue import City


class Itinerary(BaseModel):
    """The Itinerary class defines the data model for an itinerary.

    Attributes:
        events (List[Event]): The events in the itinerary.
        city (City): The city of the itinerary.
        user_id (str): The user ID of the itinerary.
        start_date (date): The start date of the itinerary.
        end_date (date): The end date of the itinerary.
    """

    events: List[Event]
    city: City
    user_id: str
    start_date: date
    end_date: date

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

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Dump the model to a dictionary.

        Returns:
            Dict[str, Any]: The model as a dictionary.
        """
        json_data = super().model_dump_json(**kwargs)
        data = json.loads(json_data)
        return data
