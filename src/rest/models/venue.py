"""The venue.py file defines the data models for the Venue resource."""
from enum import Enum

from pydantic import BaseModel


class City(Enum):
    """The City class defines the data model for a city."""

    NYC = "NYC"
    LA = "LA"
    CHICAGO = "CHICAGO"
    SCOTTSDALE = "SCOTTSDALE"
    MIAMI = "MIAMI"


class YelpVenue(BaseModel):
    """The YelpVenue class defines the data model for a Yelp venue."""

    _id: str
    city: City
    name: str
    category: str
    thumbnail_url: str
    url: str

    def model_dump(self, **kwargs):
        """Dump the model to a dictionary.

        Returns:
            dict: The model as a dictionary.
        """
        data = super().model_dump(**kwargs)
        city = data.get("city", None)

        # Kind of a redundant check, but we want to make sure that the city is
        # present.
        if city is None:
            raise ValueError("City is required in a YelpVenue model.")

        # Set the city to the value of the city enum.
        data["city"] = city.value
        return data
