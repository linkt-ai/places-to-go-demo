"""The itinerary.py file definees the data models for the Itinerary resource."""
import json
import re
from datetime import date, datetime
from typing import Any, Dict, List

from pydantic import BaseModel

from .event import Event
from .venue import City


class CitiesDoNotMatchError(Exception):
    """The EventCreationError class defines the exception raised when an event cannot be created."""

    def __init__(self, venue_city: City, itinerary_city: City):
        self.venue_city = venue_city
        self.itinerary_city = itinerary_city

    def __str__(self):
        return f"Venue city ({self.venue_city}) and itinerary city ({self.itinerary_city}) do not match."


class InvalidEventTimeError(Exception):
    """The InvalidTimeError class defines the exception raised when an invalid time is used."""

    def __init__(
        self, start_time: datetime, end_time: datetime, start_date: date, end_date: date
    ):
        self.start_time = start_time
        self.end_time = end_time
        self.start_date = start_date
        self.end_date = end_date

    def __str__(self):
        return f"Start time ({self.start_time}) and end time ({self.end_time}) are not within \
             the range for start date ({self.start_date}) and end date ({self.end_date})."


class EventTimeOverlapError(Exception):
    """The EventTimeOverlapError class defines the exception raised when an event overlaps with another event."""

    def __init__(
        self, start_time: datetime, end_time: datetime, existing_even_name: str
    ):
        self.start_time = start_time
        self.end_time = end_time

        self.existing_event = existing_even_name

    def __str__(self):
        return f"Proposed event with start time {self.start_time} and end time {self.end_time} overlaps with existing event ({self.existing_event})."


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

    def validate_new_event(
        self, city: City, start_time: datetime, end_time: datetime
    ) -> None:
        """Validate a new event.

        Args:
            start_time (datetime): The start time of the event.
            end_time (datetime): The end time of the event.

        Raises:
            InvalidEventTimeError: If the event has an invalid start time or end time.
            CitiesDoNotMatchError: If the city of the event and the city of the itinerary
                do not match.
        """
        # Assert that the start time and end time are within the start date and end date
        if city != self.city:
            raise CitiesDoNotMatchError(city, self.city)

        if start_time.date() < self.start_date or end_time.date() > self.end_date:
            raise InvalidEventTimeError(
                start_time, end_time, self.start_date, self.end_date
            )

        # For each event currently existing in the itinerary, assert the the new event does
        # not have interfering start and end times
        for event in self.events:
            # Check if the event starts during an existing event
            if event.start_time <= start_time <= event.end_time:
                raise EventTimeOverlapError(
                    event.start_time, event.end_time, event.title
                )

            # Check if the event ends during an existing event
            if event.start_time <= end_time <= event.end_time:
                raise EventTimeOverlapError(
                    event.start_time, event.end_time, event.title
                )

            # Check if the event contains an existing event
            if start_time <= event.start_time and end_time >= event.end_time:
                raise EventTimeOverlapError(start_time, end_time, event.title)
