"""The venue.py file defines the data models for the Venue resource."""
import json
from enum import Enum
from typing import Any, Dict

from pydantic import BaseModel


class City(Enum):
    """The City class defines the data model for a city."""

    NYC = "NYC"
    LA = "LA"
    CHICAGO = "CHICAGO"
    SCOTTSDALE = "SCOTTSDALE"
    MIAMI = "MIAMI"


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
