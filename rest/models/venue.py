"""The venue.py file defines the data models for the Venue resource."""
import json
from enum import Enum
from typing import Any, Dict

import pytz

from .base import BaseModel


class City(Enum):
    """The City class defines the data model for a city."""

    NYC = "NYC"
    LA = "LA"
    CHICAGO = "CHICAGO"
    SCOTTSDALE = "SCOTTSDALE"
    MIAMI = "MIAMI"

    @staticmethod
    def schema() -> Dict[str, Any]:
        """Get the schema for the city enum.

        Returns:
            Dict[str, Any]: The schema for the city enum.
        """
        return {
            "type": "string",
            "enum": [
                City.NYC.value,
                City.LA.value,
                City.CHICAGO.value,
                City.SCOTTSDALE.value,
                City.MIAMI.value,
            ],
        }

    @staticmethod
    def get_timezone(city: "City") -> pytz.timezone:
        """Get the timezone of the city.

        Args:
            city (City): The city.

        Returns:
            pytz.timezone: The timezone of the city.
        """
        timezones = {
            City.NYC: "America/New_York",
            City.LA: "America/Los_Angeles",
            City.CHICAGO: "America/Chicago",
            City.SCOTTSDALE: "America/Phoenix",
            City.MIAMI: "America/New_York",
        }
        return pytz.timezone(timezones.get(city, "UTC"))


class YelpVenue(BaseModel):
    """The YelpVenue class defines the data model for a Yelp venue.

    Attributes:
        id (str): The venue ID.
        city (City): The city of the venue.
        name (str): The name of the venue.
        category (str): The category of the venue.
        thumbnail_url (str): The thumbnail URL of the venue.
        url (str): The URL of the venue.
    """

    id: str
    city: City
    name: str
    category: str
    thumbnail_url: str
    url: str

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Dump the model to a dictionary.

        Returns:
            Dict[str, str]: The model as a dictionary.
        """
        json_data = super().model_dump_json(**kwargs)
        data = json.loads(json_data)
        return data
